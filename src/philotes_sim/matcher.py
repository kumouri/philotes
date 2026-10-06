"""Matcher v0 (docs/spec.md §7.1): heuristic and exact CP-SAT, over one ``ScoringContext``.

* ``solve_heuristic``: §7.1 steps 1–4. The hard filter is the context's conflict sets; seeds go in
  priority order (wait, newcomer boost, pending ``more`` partners in the pool); each seed is grown
  greedily by marginal score, falling back to a bounded depth-first search when greedy growth
  dead-ends; then first-improvement local search (insert, swap-in, move, swap).
* ``solve_cpsat``: the exact model for small pools, the §7.1/§12 quality baseline.
* ``solve``: dispatch on ``Policy.matcher`` ("heuristic", "cpsat", or "hybrid" = CP-SAT when the
  pool has at most ``cpsat_max_pool`` players).

Both return lobbies as lists of indices into ``ctx.pids``, each satisfying the hard constraints.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass

from ortools.sat.python import cp_model

from .config import Policy
from .scoring import ScoringContext, lobby_feasible, lobby_score, total_score


@dataclass
class MatchResult:
    lobbies: list[list[int]]
    score: int
    method: str
    optimal: bool = False
    bound: float | None = None
    seconds: float = 0.0


# --- shared search primitive -------------------------------------------------------------------


def find_lobby(
    seed: int,
    pool: Iterable[int],
    lo: list[int],
    hi: list[int],
    conflict: list[set[int]],
    node_limit: int,
    order: list[int] | None = None,
) -> tuple[list[int] | None, bool]:
    """Find any feasible lobby containing ``seed`` drawn from ``pool``.

    Feasible means every member's size range admits the lobby size and no pair conflicts. Returns
    ``(lobby, exhausted)``: ``exhausted`` is True when the search finished, so ``None`` then really
    means "no such lobby". It is False when ``node_limit`` cut the search short.
    """
    cands = [
        c
        for c in (order if order is not None else sorted(pool))
        if c != seed and c not in conflict[seed] and max(lo[seed], lo[c]) <= min(hi[seed], hi[c])
    ]
    if order is not None:
        allowed = set(pool)
        cands = [c for c in cands if c in allowed]
    nodes = 0
    found: list[int] | None = None

    def rec(members: list[int], start: int, cur_lo: int, cur_hi: int) -> bool:
        nonlocal nodes, found
        nodes += 1
        if nodes > node_limit:
            return True  # abort
        if cur_lo <= len(members) <= cur_hi:
            found = list(members)
            return True
        if len(members) >= cur_hi or len(members) + (len(cands) - start) < cur_lo:
            return False
        for k in range(start, len(cands)):
            c = cands[k]
            if any(c in conflict[m] for m in members):
                continue
            nlo, nhi = max(cur_lo, lo[c]), min(cur_hi, hi[c])
            if nlo > nhi or len(members) + 1 > nhi:
                continue
            members.append(c)
            stop = rec(members, k + 1, nlo, nhi)
            members.pop()
            if stop:
                return True
        return False

    rec([seed], 0, lo[seed], hi[seed])
    if found is not None:
        return found, True
    return None, nodes <= node_limit


# --- heuristic ---------------------------------------------------------------------------------


def _can_add(ctx: ScoringContext, members: list[int], c: int) -> bool:
    if any(c in ctx.conflict[m] for m in members):
        return False
    lo = max(max(ctx.lo[m] for m in members), ctx.lo[c])
    hi = min(min(ctx.hi[m] for m in members), ctx.hi[c])
    return lo <= hi and len(members) + 1 <= hi


def _grow(ctx: ScoringContext, members: list[int], free: set[int]) -> list[int]:
    """Add the best-marginal compatible player until the lobby is full or nothing improves.

    Adding someone can raise the lobby's minimum size (their range starts higher), so growth can
    pass through infeasible states. Returns the last feasible lobby seen, or the final state if
    none was feasible (the caller checks).
    """
    members = list(members)
    base = lobby_score(ctx, members)
    best_feasible = list(members) if lobby_feasible(ctx, members) else None
    while True:
        best, best_gain = None, None
        for c in sorted(free):
            if c in members or not _can_add(ctx, members, c):
                continue
            gain = lobby_score(ctx, [*members, c]) - base
            if best_gain is None or gain > best_gain:
                best, best_gain = c, gain
        if best is None or best_gain is None or best_gain <= 0:
            return best_feasible if best_feasible is not None else members
        members.append(best)
        base += best_gain
        if lobby_feasible(ctx, members):
            best_feasible = list(members)


def solve_heuristic(ctx: ScoringContext, policy: Policy) -> MatchResult:
    t0 = time.perf_counter()
    n = ctx.n
    free = set(range(n))
    lobbies: list[list[int]] = []
    order = sorted(range(n), key=lambda i: (-ctx.seed_priority[i], i))
    for s in order:
        if s not in free:
            continue
        lob = _grow(ctx, [s], free)
        if not lobby_feasible(ctx, lob):
            # Greedy dead-ended below the minimum size; search for any feasible lobby instead.
            pref = sorted(free, key=lambda c: (-ctx.player_w[c], c))
            found, _ = find_lobby(
                s, free, ctx.lo, ctx.hi, ctx.conflict, policy.dfs_node_limit, order=pref
            )
            if found is None:
                continue
            lob = _grow(ctx, found, free)
            if not lobby_feasible(ctx, lob):
                lob = found
        lobbies.append(lob)
        free -= set(lob)
    lobbies = _repair(ctx, lobbies, free, policy)
    lobbies = _repack(ctx, lobbies, free, policy)
    lobbies = _local_search(ctx, lobbies, free, policy.local_search_passes)
    return MatchResult(
        lobbies=lobbies,
        score=total_score(ctx, lobbies),
        method="heuristic",
        seconds=time.perf_counter() - t0,
    )


def _form_from(
    ctx: ScoringContext, pool: set[int], seeds: list[int], policy: Policy
) -> list[int] | None:
    """A feasible lobby from ``pool``, trying ``seeds`` in order, grown greedily once found."""
    pref = sorted(pool, key=lambda c: (-ctx.player_w[c], c))
    for s in seeds:
        found, _ = find_lobby(s, pool, ctx.lo, ctx.hi, ctx.conflict, policy.dfs_node_limit, pref)
        if found is not None:
            grown = _grow(ctx, found, pool)
            return grown if lobby_feasible(ctx, grown) else found
    return None


def _repair(
    ctx: ScoringContext, lobbies: list[list[int]], free: set[int], policy: Policy
) -> list[list[int]]:
    """Packing repair: free up the player a leftover lobby is missing (§7.1 step 4).

    Greedy growth can spend flexible players on one lobby and strand players whose ranges are
    narrower (e.g. "exactly 4"). Two moves fix that, each accepted only if it places more people:

    * swap-then-form: put leftover ``u`` into a lobby in place of member ``m``, then form a new
      lobby from the leftovers plus ``m``;
    * spare-then-form: take member ``m`` out of a lobby that stays feasible without them, and form
      a new lobby from the leftovers plus ``m``.
    """
    changed = True
    rounds = 0
    while changed and free and rounds < 4 * (len(lobbies) + 1):
        changed = False
        rounds += 1
        order = sorted(free, key=lambda c: (-ctx.seed_priority[c], c))
        for k in range(len(lobbies)):
            lob = lobbies[k]
            for m in lob:
                rest = [x for x in lob if x != m]
                candidates: list[tuple[list[int], int | None]] = []
                if lobby_feasible(ctx, rest):
                    candidates.append((rest, None))
                candidates += [([*rest, u], u) for u in order if lobby_feasible(ctx, [*rest, u])]
                for new_lob, u in candidates:
                    pool = (free - {u}) | {m} if u is not None else free | {m}
                    formed = _form_from(ctx, pool, [m, *sorted(pool - {m})], policy)
                    if formed is None:
                        continue
                    lobbies[k] = new_lob
                    lobbies.append(formed)
                    free.clear()
                    free.update(pool - set(formed))
                    changed = True
                    break
                if changed:
                    break
            if changed:
                break
    return lobbies


def best_partition(
    ctx: ScoringContext, pool: list[int], node_limit: int
) -> tuple[list[list[int]], int]:
    """Bounded exhaustive search for disjoint feasible lobbies in ``pool`` placing the most players.

    Players are branched most-constrained first (narrowest size range, most conflicts); each is
    either put in a feasible lobby with later players or left out. Returns (lobbies, placed).
    """
    order = sorted(pool, key=lambda i: (ctx.hi[i] - ctx.lo[i], -len(ctx.conflict[i]), i))
    best: list[list[list[int]] | int] = [[], 0]
    nodes = 0

    def lobbies_with(p: int, rest: list[int]):
        """All feasible lobbies containing ``p`` drawn from ``rest`` (generator)."""
        cands = [c for c in rest if c not in ctx.conflict[p]]

        def rec(members: list[int], start: int, lo: int, hi: int):
            if lo <= len(members) <= hi:
                yield list(members)
            if len(members) >= hi:
                return
            for k in range(start, len(cands)):
                c = cands[k]
                if any(c in ctx.conflict[m] for m in members):
                    continue
                nlo, nhi = max(lo, ctx.lo[c]), min(hi, ctx.hi[c])
                if nlo > nhi or len(members) + 1 > nhi:
                    continue
                members.append(c)
                yield from rec(members, k + 1, nlo, nhi)
                members.pop()

        yield from rec([p], 0, ctx.lo[p], ctx.hi[p])

    def rec(remaining: list[int], chosen: list[list[int]], placed: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > node_limit or placed + len(remaining) <= best[1]:
            return
        if not remaining:
            best[0], best[1] = [list(x) for x in chosen], placed
            return
        p, rest = remaining[0], remaining[1:]
        for lob in lobbies_with(p, rest):
            taken = set(lob)
            chosen.append(lob)
            rec([r for r in rest if r not in taken], chosen, placed + len(lob))
            chosen.pop()
            if nodes > node_limit:
                return
        rec(rest, chosen, placed)  # leave p out

    rec(order, [], 0)
    return best[0], best[1]  # type: ignore[return-value]


def _repack(
    ctx: ScoringContext, lobbies: list[list[int]], free: set[int], policy: Policy
) -> list[list[int]]:
    """Re-partition one or two lobbies together with the leftovers when that places more people."""
    limit = policy.repack_node_limit
    changed = True
    while changed and free:
        changed = False
        groups = [(k,) for k in range(len(lobbies))]
        groups += [(a, b) for a in range(len(lobbies)) for b in range(a + 1, len(lobbies))]
        for g in groups:
            members = [x for k in g for x in lobbies[k]]
            pool = sorted(set(members) | free)
            if len(pool) > 20:
                continue
            parts, placed = best_partition(ctx, pool, limit)
            if placed > len(members):
                for k in sorted(g, reverse=True):
                    del lobbies[k]
                lobbies.extend(parts)
                free.clear()
                free.update(set(pool) - {x for lob in parts for x in lob})
                changed = True
                break
    return lobbies


def _local_search(
    ctx: ScoringContext, lobbies: list[list[int]], free: set[int], passes: int
) -> list[list[int]]:
    """First-improvement local search over insert, swap-in, move and swap (§7.1 step 4)."""
    scores = [lobby_score(ctx, lob) for lob in lobbies]

    def try_set(k: int, new: list[int]) -> int | None:
        if not lobby_feasible(ctx, new):
            return None
        return lobby_score(ctx, new)

    for _ in range(passes):
        improved = False
        # Insert or swap in an unplaced player.
        for u in sorted(free):
            for k in range(len(lobbies)):
                lob = lobbies[k]
                s = try_set(k, [*lob, u])
                if s is not None and s > scores[k]:
                    lobbies[k], scores[k] = [*lob, u], s
                    free.discard(u)
                    improved = True
                    break
                done = False
                for m in lob:
                    new = [x if x != m else u for x in lob]
                    s = try_set(k, new)
                    if (
                        s is not None
                        and s - ctx.player_w[u] > scores[k] - ctx.player_w[m]
                        and (s > scores[k])
                    ):
                        lobbies[k], scores[k] = new, s
                        free.discard(u)
                        free.add(m)
                        improved = done = True
                        break
                if done:
                    break
        # Move one member, or swap two members, between lobbies.
        for a in range(len(lobbies)):
            for b in range(len(lobbies)):
                if a == b:
                    continue
                for m in list(lobbies[a]):
                    na = [x for x in lobbies[a] if x != m]
                    nb = [*lobbies[b], m]
                    sa, sb = try_set(a, na), try_set(b, nb)
                    if sa is not None and sb is not None and sa + sb > scores[a] + scores[b]:
                        lobbies[a], lobbies[b], scores[a], scores[b] = na, nb, sa, sb
                        improved = True
                        break
                if a < b:
                    for m in list(lobbies[a]):
                        hit = False
                        for o in list(lobbies[b]):
                            na = [x if x != m else o for x in lobbies[a]]
                            nb = [x if x != o else m for x in lobbies[b]]
                            sa, sb = try_set(a, na), try_set(b, nb)
                            if (
                                sa is not None
                                and sb is not None
                                and sa + sb > scores[a] + scores[b]
                            ):
                                lobbies[a], lobbies[b], scores[a], scores[b] = na, nb, sa, sb
                                improved = hit = True
                                break
                        if hit:
                            break
        if not improved:
            break
    return [sorted(lob) for lob in lobbies if lob]


# --- exact CP-SAT ------------------------------------------------------------------------------


def solve_cpsat(ctx: ScoringContext, policy: Policy, seed: int = 0) -> MatchResult:
    """Exact model of the same objective. Deterministic: one worker, deterministic time limit."""
    t0 = time.perf_counter()
    n = ctx.n
    if n == 0:
        return MatchResult([], 0, "cpsat", optimal=True, bound=0.0)
    K = max(1, n // max(1, min(ctx.lo)))
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x{i}_{k}") for k in range(K)] for i in range(n)]
    obj = []
    for i in range(n):
        m.AddAtMostOne(x[i])
    size = []
    for k in range(K):
        sk = m.NewIntVar(0, n, f"size{k}")
        m.Add(sk == sum(x[i][k] for i in range(n)))
        size.append(sk)
        for i in range(n):
            m.Add(sk >= ctx.lo[i]).OnlyEnforceIf(x[i][k])
            m.Add(sk <= ctx.hi[i]).OnlyEnforceIf(x[i][k])
            obj.append(ctx.player_w[i] * x[i][k])
        if k > 0:
            m.Add(size[k - 1] >= sk)  # symmetry breaking: lobbies sorted by size
    for i in range(n):
        for j in ctx.conflict[i]:
            if i < j:
                for k in range(K):
                    m.AddBoolOr([x[i][k].Not(), x[j][k].Not()])
    y: dict[tuple[int, int, int], cp_model.IntVar] = {}
    for (i, j), w in sorted(ctx.pair_w.items()):
        if j in ctx.conflict[i]:
            continue
        for k in range(K):
            v = m.NewBoolVar(f"y{i}_{j}_{k}")
            m.AddImplication(v, x[i][k])
            m.AddImplication(v, x[j][k])
            m.AddBoolOr([x[i][k].Not(), x[j][k].Not(), v])
            y[(i, j, k)] = v
            if w:
                obj.append(w * v)
    n_axes = len(ctx.style[0])
    for k in range(K):
        for axis in range(n_axes):
            neg = [i for i in range(n) if ctx.style[i][axis] == -1]
            pos = [i for i in range(n) if ctx.style[i][axis] == 1]
            if not neg or not pos:
                continue
            hn, hp = m.NewBoolVar(f"hn{k}_{axis}"), m.NewBoolVar(f"hp{k}_{axis}")
            for i in neg:
                m.AddImplication(x[i][k], hn)
            for i in pos:
                m.AddImplication(x[i][k], hp)
            c = m.NewBoolVar(f"conf{k}_{axis}")
            m.AddBoolOr([hn.Not(), hp.Not(), c])
            obj.append(-ctx.w_style * c)
        if ctx.w_interest:
            tags = sorted({t for i in range(n) for t in ctx.tags[i]})
            for t in tags:
                holders = [i for i in range(n) if t in ctx.tags[i]]
                if len(holders) < 2:
                    continue
                s = m.NewBoolVar(f"tag{k}_{t}")
                m.Add(2 * s <= sum(x[i][k] for i in holders))
                obj.append(ctx.w_interest * s)
        if ctx.w_comp and ctx.more_pairs:
            core_terms = [y[(i, j, k)] for (i, j) in sorted(ctx.more_pairs) if (i, j, k) in y]
            if core_terms:
                core = m.NewBoolVar(f"core{k}")
                m.Add(core <= sum(core_terms))
                fresh = []
                for i in range(n):
                    f = m.NewBoolVar(f"fresh{i}_{k}")
                    m.AddImplication(f, x[i][k])
                    for j in ctx.hist[i]:
                        m.AddImplication(f, x[j][k].Not())
                    fresh.append(f)
                comp = m.NewBoolVar(f"comp{k}")
                m.AddImplication(comp, core)
                m.Add(comp <= sum(fresh))
                obj.append(ctx.w_comp * comp)
    m.Maximize(sum(obj))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_deterministic_time = policy.cpsat_det_time
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return MatchResult([], 0, "cpsat", seconds=time.perf_counter() - t0)
    lobbies = []
    for k in range(K):
        lob = [i for i in range(n) if solver.Value(x[i][k])]
        if lob:
            lobbies.append(lob)
    return MatchResult(
        lobbies=lobbies,
        score=total_score(ctx, lobbies),
        method="cpsat",
        optimal=status == cp_model.OPTIMAL,
        bound=solver.BestObjectiveBound(),
        seconds=time.perf_counter() - t0,
    )


def solve(ctx: ScoringContext, policy: Policy, seed: int = 0) -> MatchResult:
    if ctx.n == 0:
        return MatchResult([], 0, policy.matcher)
    if policy.matcher == "cpsat" or (policy.matcher == "hybrid" and ctx.n <= policy.cpsat_max_pool):
        return solve_cpsat(ctx, policy, seed)
    return solve_heuristic(ctx, policy)
