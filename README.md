# Philotes

Group matchmaking for multiplayer games in which friendships form as a side effect. Named for
Philotes, the Greek spirit of friendship and affection.

You say which games you're up for and how many people you want. The matcher builds a group from
whoever is queued at that moment. After the session you can mark someone as *"I like playing with
this person"* or *"avoid"*. The next time you are both queued, the matcher tries to put you back
together, or keeps you apart. You don't get a friends list or profiles to browse, and there's no
swiping.

**Status: Phase 1 under way.** Phase 0's simulator met its exit criteria. The Phase 1 Discord
bot has a local core, Discord adapter and optional Archipelago automation; it has not been
connected to Discord or used by anyone yet.

- [`docs/spec.md`](docs/spec.md) is the canonical spec. It covers the rulings, prior art, model and
  matcher, the density problem, trust & safety, privacy, phases and open questions.
- [`docs/phase0-results.md`](docs/phase0-results.md) has the first sweep's results against the
  Phase 0 exit criteria. Its data is in [`docs/phase0-data/`](docs/phase0-data/).
- [`docs/phase1-bot.md`](docs/phase1-bot.md) covers the Phase 1 bot: what is built, the choices
  made where the spec is silent, and the slices still to come.
  [`docs/SETUP.md`](docs/SETUP.md) has the host's setup steps, and
  [`docs/user-guide.md`](docs/user-guide.md) is what players are told.

Markdown is canonical. Any other format is rendered from the `.md` files.

## Phase 0 simulator

`src/philotes_sim/` is the matcher (spec §7) run against synthetic populations (spec §12). It
covers both pool shapes: a live co-op queue, and an async Archipelago weekly sign-up window.

| Module | What it holds |
|---|---|
| `config.py` | Every scenario knob, with dotted-path overrides |
| `population.py` | Synthetic players, archetypes and availability |
| `edges.py` | `more` / avoid edges, decay, hard-block cap, co-play records |
| `scoring.py` | The §7 objective and hard constraints, shared by both matchers |
| `matcher.py` | Matcher v0: the §7.1 heuristic and the exact CP-SAT baseline |
| `lockout.py` | The §8 hard-block lockout check |
| `rounds.py` | One matcher round over a waiting pool, and batch at close; shared with the bot |
| `sim.py` | The simulation loop for both pool shapes |
| `metrics.py` | Every §12 metric, including the silent-rejection detection test |
| `experiments.py` | The sweep plan and the exit criteria |
| `report.py`, `quality.py`, `cli.py` | CSV / Markdown output, the matcher comparison, the CLI |

### Install

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.13 (pinned in `.python-version`)
and the locked dependencies (OR-Tools, NumPy):

```sh
uv sync
```

### Run

```sh
# One scenario, printing every metric (live is the default shape).
uv run philotes-sim run --set population.M=200 --set shape.habit=generous
uv run philotes-sim run --shape async --set shape.cadence_hours=24 --out results/one

# The Phase 0 sweep: CSVs plus report.md. --groups picks a subset (see `philotes-sim list`).
uv run philotes-sim sweep --replicates 5 --out results/phase0
uv run philotes-sim report --from results/phase0      # rebuild report.md from runs.jsonl

# Heuristic vs exact CP-SAT on pools captured from real runs.
uv run philotes-sim compare-matchers --out results/quality
```

`--set` takes any field path from `config.py`, for example `policy.hard_cap=3`,
`policy.soft_half_life_days=14`, `weights.noise=0.5`, or `policy.matcher=hybrid`. Runs are
deterministic for a given `--seed`. The full sweep takes about 7 minutes on 48 cores. `results/` is
git-ignored.

## Phase 1 bot

`src/philotes_bot/` is the Discord bot for the closed alpha (spec §12 Phase 1): weekly sign-ups for
async Archipelago seeds, seeds formed in one batch at window close by the simulator's own matcher,
the post-seed card, reports to the host community's moderators, and the §11 data rights. This
bot also runs locally on an in-memory transport, with no token and no network.
[`docs/phase1-bot.md`](docs/phase1-bot.md) has the module map and the remaining slices.

```sh
uv run philotes-bot demo       # a scripted two-week run, printed
uv run philotes-bot console    # type commands as any user; move the clock with `advance 7d`
uv run philotes-bot check      # resolved config; says whether DISCORD_TOKEN is set, never its value
uv run philotes-bot run        # host only: connect after following docs/SETUP.md
```

Configuration is `philotes-bot.toml` (copy `philotes-bot.example.toml`). The token goes in an
untracked `.env`. Both are git-ignored. [`docs/SETUP.md`](docs/SETUP.md) has the host's steps.

## Test

```sh
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

The tests never touch the network: `tests/conftest.py` makes any connection attempt fail.
CI (`.github/workflows/ci.yml`) runs the same lint and tests on pushes and pull requests.

## License

[GNU Affero General Public License v3.0](LICENSE). If you run a modified version of Philotes as a
network service, you must make your changes available to its users under the same licence.
