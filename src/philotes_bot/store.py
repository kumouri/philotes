"""SQLite persistence for the bot (docs/spec.md §6 model, §11 data held).

Everything the bot keeps is in these tables, and nothing else is kept (§11): Discord user IDs, the
style and interests a player set, sign-ups, seeds and who was in them, outgoing edges, co-play
records, reports and moderator removals. No message content, presence or names.

Times are UTC epoch seconds. User IDs are Discord snowflakes (integers).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from itertools import combinations

from philotes_sim.edges import HARD, MORE, SOFT, soft_avoid_weight

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    joined_at REAL NOT NULL,
    comms INTEGER NOT NULL DEFAULT 0,      -- -1 voice, +1 text, 0 either
    talk INTEGER NOT NULL DEFAULT 0,       -- -1 chatty, +1 heads-down, 0 either
    intensity INTEGER NOT NULL DEFAULT 0,  -- -1 sweaty, +1 chill, 0 either
    interests TEXT NOT NULL DEFAULT '[]',
    seeds_played INTEGER NOT NULL DEFAULT 0,
    removed_at REAL,                       -- set by a moderator (§10)
    removed_reason TEXT
);
CREATE TABLE IF NOT EXISTS windows (
    id INTEGER PRIMARY KEY,
    opens_at REAL NOT NULL,
    closes_at REAL NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS signups (
    window_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    goals TEXT NOT NULL,                   -- JSON list of goal indices, first choice first
    pref_lo INTEGER NOT NULL, pref_hi INTEGER NOT NULL,
    acc_lo INTEGER NOT NULL, acc_hi INTEGER NOT NULL,
    signed_at REAL NOT NULL,               -- kept when a sign-up carries over (§7.5 fairness)
    PRIMARY KEY (window_id, user_id)
);
CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY,
    goal INTEGER NOT NULL,
    formed_at REAL NOT NULL,
    ends_at REAL NOT NULL,
    channel_id INTEGER,
    cards_sent INTEGER NOT NULL DEFAULT 0,
    channel_closed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS seed_members (
    seed_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (seed_id, user_id)
);
CREATE TABLE IF NOT EXISTS edges (
    author INTEGER NOT NULL,
    target INTEGER NOT NULL,
    kind TEXT NOT NULL,                    -- more | soft | hard
    t REAL NOT NULL,                       -- set or last re-applied
    via_report INTEGER NOT NULL DEFAULT 0, -- a block applied by a report, outside the cap (§10)
    PRIMARY KEY (author, target)
);
CREATE TABLE IF NOT EXISTS coplay (
    a INTEGER NOT NULL,
    b INTEGER NOT NULL,                    -- a < b
    count INTEGER NOT NULL,
    last_t REAL NOT NULL,
    PRIMARY KEY (a, b)
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    reporter INTEGER NOT NULL,
    target INTEGER NOT NULL,
    seed_id INTEGER,
    reason TEXT NOT NULL,
    filed_at REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',   -- open | resolved | abusive | false
    resolution TEXT
);
CREATE TABLE IF NOT EXISTS moderation_audit (
    id INTEGER PRIMARY KEY, actor INTEGER NOT NULL, action TEXT NOT NULL,
    subject TEXT NOT NULL, detail TEXT NOT NULL, t REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS review_notices (
    key TEXT PRIMARY KEY, t REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS ap_jobs (
    seed_id INTEGER PRIMARY KEY REFERENCES seeds(id) ON DELETE CASCADE,
    deadline REAL NOT NULL,
    reminded INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'collecting',
    port INTEGER,
    password TEXT,
    restarts INTEGER NOT NULL DEFAULT 0,
    retry_at REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ap_yamls (
    seed_id INTEGER NOT NULL REFERENCES ap_jobs(seed_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    content BLOB NOT NULL,
    PRIMARY KEY (seed_id, user_id)
);
"""

DAY = 86400.0


@dataclass
class PlayerRow:
    user_id: int
    joined_at: float
    style: tuple[int, int, int]
    interests: tuple[str, ...]
    seeds_played: int
    removed_at: float | None
    removed_reason: str | None


@dataclass
class SignupRow:
    window_id: int
    user_id: int
    goals: tuple[int, ...]
    pref: tuple[int, int]
    acc: tuple[int, int]
    signed_at: float


@dataclass
class SeedRow:
    id: int
    goal: int
    formed_at: float
    ends_at: float
    channel_id: int | None
    cards_sent: bool
    channel_closed: bool


@dataclass
class EdgeRow:
    author: int
    target: int
    kind: str
    t: float
    via_report: bool


@dataclass
class ReportRow:
    id: int
    reporter: int
    target: int
    seed_id: int | None
    reason: str
    filed_at: float
    status: str
    resolution: str | None


class Store:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def _one(self, sql: str, *args: object) -> tuple | None:
        return self.db.execute(sql, args).fetchone()

    def _all(self, sql: str, *args: object) -> list[tuple]:
        return self.db.execute(sql, args).fetchall()

    def _exec(self, sql: str, *args: object) -> sqlite3.Cursor:
        cur = self.db.execute(sql, args)
        self.db.commit()
        return cur

    # --- players ---------------------------------------------------------------------------

    def player(self, user_id: int) -> PlayerRow | None:
        r = self._one(
            "SELECT user_id, joined_at, comms, talk, intensity, interests, seeds_played,"
            " removed_at, removed_reason FROM players WHERE user_id = ?",
            user_id,
        )
        if r is None:
            return None
        return PlayerRow(r[0], r[1], (r[2], r[3], r[4]), tuple(json.loads(r[5])), r[6], r[7], r[8])

    def add_player(self, user_id: int, now: float) -> None:
        self._exec("INSERT OR IGNORE INTO players (user_id, joined_at) VALUES (?, ?)", user_id, now)

    def set_style(self, user_id: int, style: tuple[int, int, int]) -> None:
        self._exec(
            "UPDATE players SET comms = ?, talk = ?, intensity = ? WHERE user_id = ?",
            *style,
            user_id,
        )

    def set_interests(self, user_id: int, tags: tuple[str, ...]) -> None:
        self._exec(
            "UPDATE players SET interests = ? WHERE user_id = ?", json.dumps(list(tags)), user_id
        )

    def set_removed(self, user_id: int, now: float | None, reason: str | None) -> None:
        self._exec(
            "UPDATE players SET removed_at = ?, removed_reason = ? WHERE user_id = ?",
            now,
            reason,
            user_id,
        )

    def add_seeds_played(self, user_ids: list[int]) -> None:
        self.db.executemany(
            "UPDATE players SET seeds_played = seeds_played + 1 WHERE user_id = ?",
            [(u,) for u in user_ids],
        )
        self.db.commit()

    def delete_player(self, user_id: int) -> None:
        """§11: removes the player, their sign-ups and seat records, and edges in both directions.

        Reports are kept, per moderation policy (§11).
        """
        for sql in (
            "DELETE FROM players WHERE user_id = ?",
            "DELETE FROM signups WHERE user_id = ?",
            "DELETE FROM seed_members WHERE user_id = ?",
            "DELETE FROM edges WHERE author = ?1 OR target = ?1",
            "DELETE FROM coplay WHERE a = ?1 OR b = ?1",
            "DELETE FROM ap_yamls WHERE user_id = ?",
        ):
            self.db.execute(sql, (user_id,))
        self.db.commit()

    # --- windows and sign-ups --------------------------------------------------------------

    def open_window(self) -> tuple[int, float, float] | None:
        r = self._one(
            "SELECT id, opens_at, closes_at FROM windows WHERE closed = 0 ORDER BY id LIMIT 1"
        )
        return (r[0], r[1], r[2]) if r else None

    def create_window(self, opens_at: float, closes_at: float) -> int:
        cur = self._exec(
            "INSERT INTO windows (opens_at, closes_at) VALUES (?, ?)", opens_at, closes_at
        )
        return int(cur.lastrowid or 0)

    def close_window(self, window_id: int) -> None:
        """§11: at close, sign-ups carry over or are deleted; the row keeps only dates."""
        self._exec("UPDATE windows SET closed = 1 WHERE id = ?", window_id)

    def upsert_signup(self, s: SignupRow) -> None:
        self._exec(
            "INSERT OR REPLACE INTO signups VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            s.window_id,
            s.user_id,
            json.dumps(list(s.goals)),
            *s.pref,
            *s.acc,
            s.signed_at,
        )

    def signup(self, window_id: int, user_id: int) -> SignupRow | None:
        rows = [s for s in self.signups(window_id) if s.user_id == user_id]
        return rows[0] if rows else None

    def signups(self, window_id: int) -> list[SignupRow]:
        return [
            SignupRow(r[0], r[1], tuple(json.loads(r[2])), (r[3], r[4]), (r[5], r[6]), r[7])
            for r in self._all(
                "SELECT * FROM signups WHERE window_id = ? ORDER BY signed_at, user_id", window_id
            )
        ]

    def delete_signup(self, window_id: int, user_id: int) -> bool:
        cur = self._exec(
            "DELETE FROM signups WHERE window_id = ? AND user_id = ?", window_id, user_id
        )
        return cur.rowcount > 0

    def move_signups(self, from_window: int, to_window: int, user_ids: list[int]) -> None:
        self.db.executemany(
            "UPDATE signups SET window_id = ? WHERE window_id = ? AND user_id = ?",
            [(to_window, from_window, u) for u in user_ids],
        )
        self.db.execute("DELETE FROM signups WHERE window_id = ?", (from_window,))
        self.db.commit()

    def delete_user_signups(self, user_id: int) -> None:
        self._exec("DELETE FROM signups WHERE user_id = ?", user_id)

    # --- seeds and co-play -----------------------------------------------------------------

    def create_seed(self, goal: int, members: list[int], now: float, ends_at: float) -> int:
        cur = self.db.execute(
            "INSERT INTO seeds (goal, formed_at, ends_at) VALUES (?, ?, ?)", (goal, now, ends_at)
        )
        sid = int(cur.lastrowid or 0)
        self.db.executemany(
            "INSERT INTO seed_members VALUES (?, ?)", [(sid, u) for u in sorted(members)]
        )
        for a, b in combinations(sorted(members), 2):
            self.db.execute(
                "INSERT INTO coplay VALUES (?, ?, 1, ?) ON CONFLICT (a, b) DO UPDATE"
                " SET count = count + 1, last_t = excluded.last_t",
                (a, b, now),
            )
        self.db.commit()
        return sid

    def set_seed_channel(self, seed_id: int, channel_id: int | None) -> None:
        self._exec("UPDATE seeds SET channel_id = ? WHERE id = ?", channel_id, seed_id)

    def mark_cards_sent(self, seed_id: int) -> None:
        self._exec("UPDATE seeds SET cards_sent = 1 WHERE id = ?", seed_id)

    def mark_channel_closed(self, seed_id: int) -> None:
        self._exec("UPDATE seeds SET channel_closed = 1 WHERE id = ?", seed_id)

    def _seed(self, r: tuple) -> SeedRow:
        return SeedRow(r[0], r[1], r[2], r[3], r[4], bool(r[5]), bool(r[6]))

    def seed(self, seed_id: int) -> SeedRow | None:
        r = self._one("SELECT * FROM seeds WHERE id = ?", seed_id)
        return self._seed(r) if r else None

    def seeds(self) -> list[SeedRow]:
        return [self._seed(r) for r in self._all("SELECT * FROM seeds ORDER BY id")]

    def seeds_of(self, user_id: int) -> list[SeedRow]:
        return [
            self._seed(r)
            for r in self._all(
                "SELECT s.* FROM seeds s JOIN seed_members m ON m.seed_id = s.id"
                " WHERE m.user_id = ? ORDER BY s.id",
                user_id,
            )
        ]

    def seed_members(self, seed_id: int) -> list[int]:
        return [
            r[0]
            for r in self._all(
                "SELECT user_id FROM seed_members WHERE seed_id = ? ORDER BY user_id", seed_id
            )
        ]

    def coplay(self) -> list[tuple[int, int, int, float]]:
        return [(r[0], r[1], r[2], r[3]) for r in self._all("SELECT * FROM coplay")]

    def coplay_of(self, user_id: int) -> list[tuple[int, int, float]]:
        """(other, count, last_t) for everyone ``user_id`` has shared a seed with."""
        return [
            (r[1] if r[0] == user_id else r[0], r[2], r[3])
            for r in self._all("SELECT * FROM coplay WHERE a = ?1 OR b = ?1", user_id)
        ]

    # --- edges -----------------------------------------------------------------------------

    def edges(self) -> list[EdgeRow]:
        return [
            EdgeRow(r[0], r[1], r[2], r[3], bool(r[4]))
            for r in self._all("SELECT * FROM edges ORDER BY author, target")
        ]

    def edges_of(self, author: int) -> list[EdgeRow]:
        return [e for e in self.edges() if e.author == author]

    def edge(self, author: int, target: int) -> EdgeRow | None:
        r = self._one("SELECT * FROM edges WHERE author = ? AND target = ?", author, target)
        return EdgeRow(r[0], r[1], r[2], r[3], bool(r[4])) if r else None

    def set_edge(self, author: int, target: int, kind: str, now: float, via_report=False) -> None:
        assert kind in (MORE, SOFT, HARD)
        self._exec(
            "INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?, ?)",
            author,
            target,
            kind,
            now,
            int(via_report),
        )

    def clear_edge(self, author: int, target: int) -> bool:
        cur = self._exec("DELETE FROM edges WHERE author = ? AND target = ?", author, target)
        return cur.rowcount > 0

    def capped_blocks(self, author: int) -> int:
        """Hard blocks that count toward the cap; report blocks sit outside it (§10)."""
        r = self._one(
            "SELECT COUNT(*) FROM edges WHERE author = ? AND kind = ? AND via_report = 0",
            author,
            HARD,
        )
        return int(r[0]) if r else 0

    def active_avoids_on(self, target: int, now: float, half_life_days: float, neg: float) -> int:
        """How many people currently avoid or block ``target``: the count moderators may see."""
        n = 0
        for e in self.edges():
            if e.target != target or e.kind == MORE:
                continue
            if e.kind == HARD or soft_avoid_weight((now - e.t) / 60.0, half_life_days) >= neg:
                n += 1
        return n

    # --- reports ---------------------------------------------------------------------------

    def add_report(
        self, reporter: int, target: int, seed_id: int | None, reason: str, now: float
    ) -> int:
        cur = self._exec(
            "INSERT INTO reports (reporter, target, seed_id, reason, filed_at)"
            " VALUES (?, ?, ?, ?, ?)",
            reporter,
            target,
            seed_id,
            reason,
            now,
        )
        return int(cur.lastrowid or 0)

    def reports(self, status: str | None = None) -> list[ReportRow]:
        rows = self._all("SELECT * FROM reports ORDER BY id")
        out = [ReportRow(*r) for r in rows]
        return [r for r in out if status is None or r.status == status]

    def resolve_report(self, report_id: int, note: str) -> bool:
        cur = self._exec(
            "UPDATE reports SET status = 'resolved', resolution = ?"
            " WHERE id = ? AND status = 'open'",
            note,
            report_id,
        )
        return cur.rowcount > 0

    def audit(self, actor: int, action: str, subject: str, detail: str, now: float) -> None:
        self._exec(
            "INSERT INTO moderation_audit (actor, action, subject, detail, t)"
            " VALUES (?, ?, ?, ?, ?)",
            actor,
            action,
            subject,
            detail,
            now,
        )

    def review_report(
        self, report_id: int, outcome: str, note: str, actor: int, detail: str, now: float
    ) -> None:
        """Persist the outcome and its audit together, including on interruption."""
        with self.db:
            self.db.execute(
                "UPDATE reports SET status = ?, resolution = ? WHERE id = ?",
                (outcome, note, report_id),
            )
            self.db.execute(
                "INSERT INTO moderation_audit (actor, action, subject, detail, t)"
                " VALUES (?, 'resolve', ?, ?, ?)",
                (actor, str(report_id), detail, now),
            )

    def set_report_outcome(self, report_id: int, outcome: str, note: str) -> bool:
        return (
            self._exec(
                "UPDATE reports SET status = ?, resolution = ? WHERE id = ?",
                outcome,
                note,
                report_id,
            ).rowcount
            > 0
        )

    # --- retention (§11) -------------------------------------------------------------------

    def purge(self, now: float, half_life_days: float, negligible: float, coplay_days: int) -> None:
        """Delete negligible soft avoids, and co-play and seeds older than the retention limit."""
        for e in self.edges():
            weight = soft_avoid_weight((now - e.t) / 60.0, half_life_days)
            if e.kind == SOFT and weight < negligible:
                self.db.execute(
                    "DELETE FROM edges WHERE author = ? AND target = ?", (e.author, e.target)
                )
        cutoff = now - coplay_days * DAY
        self.db.execute("DELETE FROM coplay WHERE last_t < ?", (cutoff,))
        old = [r[0] for r in self._all("SELECT id FROM seeds WHERE ends_at < ?", cutoff)]
        for sid in old:
            self.db.execute("DELETE FROM seed_members WHERE seed_id = ?", (sid,))
            self.db.execute("DELETE FROM seeds WHERE id = ?", (sid,))
        self.db.commit()
