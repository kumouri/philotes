# Phase 1: the Discord bot, as built

[Spec §12 Phase 1](spec.md#phase-1-discord-bot-closed-alpha) is what the bot has to do: one
community, async Archipelago multiworlds, 18+, the §9.3 flow, matcher v0 from Phase 0, and
moderation by the host community's mods. This document covers what is built so far, the choices
made where the spec is silent, and the slices still to come. Setting it up on a real server is in
[SETUP.md](SETUP.md). What players are told is in [user-guide.md](user-guide.md).

## Slice 1: the core, runnable locally

Everything the bot decides, end to end, on a fake clock and an in-memory transport. It needs no
token, makes no network calls, and nothing in it imports a Discord library.

| Module (`src/philotes_bot/`) | What it holds |
|---|---|
| `config.py` | One TOML file per host community, plus `DISCORD_TOKEN` only from an untracked `.env`. The matcher settings are the ruled v1 values. |
| `store.py` | SQLite tables for everything the bot keeps (§11), and the retention purge. |
| `matching.py` | Loads the database into Phase 0's `EdgeStore` and runs `philotes_sim.rounds.batch_at_close`. |
| `core.py` | `Bot`: one method per slash command, the card buttons, moderator commands, and `tick()` on a timer. |
| `commands.py` | The slash-command list, declared once. The console uses it now, and the Discord adapter will register the same list. |
| `transport.py` | The four side effects the core needs (DM, create and delete a seed channel, post to mods), and `InMemoryTransport`. |
| `console.py`, `cli.py` | `philotes-bot demo`, `philotes-bot console`, `philotes-bot check`. |
| `text.py` | Wording the spec constrains, including the "avoids are honoured" statement. |

### The flow

1. `/join adult:true` opts in. It is refused outside the configured guild and for Discord accounts
   younger than `min_account_age_days`. Account age comes from the user ID's snowflake, so no API
   call is needed.
2. `/signup goals:short,medium size:4-6 accept:3-8` signs up for this week's window. Goal lengths
   play the part of the async "games" Phase 0 simulated: you are offered your first choice, and
   your other choices only at the §7.5 step 4 rung. `/style` and `/interests` are optional inputs
   to the same objective.
3. When the window closes, `tick()` forms every seed in one batch (§14 #15). There is one strict
   round, then one round per ladder rung (size, other goal lengths, break soft avoids) for whoever
   is still unplaced. Hard blocks never break. Each seed gets a private channel with its members
   and a DM to each member. Nobody else hears anything.
4. When a seed's goal length has run, each member gets a card by DM. It lists each co-player with
   **more · neutral · avoid · block · report** and says plainly that avoids are honoured (§12,
   §14 #15).
5. Reports go to the moderators' channel with the reporter, the target, the reason, and only a
   *count* of the people currently avoiding or blocking the target (§11 lean). Moderators can
   take a player out of matching, put them back, list reports and resolve them.

### Reuse of Phase 0

The bot has no matcher of its own. `philotes_sim.rounds` holds the per-game round the simulator
already ran, moved out of `sim.py` so that both callers share it. `batch_at_close` is the ruled
cadence. The simulator's outputs are unchanged by the move: a fingerprint of sessions and edges
from a live run, a 6-hour async run and a batch-at-close run is byte-identical before and after.
The objective (`scoring.py`), heuristic (`matcher.py`) and edge maths (`edges.py`) are imported
as they are. `scoring.MatchPlayer` now names the attributes the objective reads, so the bot's
sign-ups can stand in for simulated players.

The v1 settings, as ruled: soft-avoid half-life 7 days (§14 #9), hard-block cap 10 (§14 #8), no
newcomer boost, no low-connectivity boost and no anchors (§14 #18), the heuristic matcher, and
Phase 0's other weights and noise unchanged.

### Choices where the spec is silent

The simplest option was taken each time. Each one can be revisited.

- **One weekly window, closing at a fixed UTC hour** (default Sunday 23:00 UTC). The next window
  opens the moment one closes. UTC avoids daylight-saving drift and a time-zone database. Discord
  timestamps show every player the close time in their own zone.
- **Goal lengths** are `short` / `medium` / `long`, running 7 / 14 / 28 days, as in the Phase 0
  async model. Seed sizes run 3–8, with 4–6 preferred by default. All of these are config values.
- **A seed formed by the strict round is not reopened** to fit a leftover sign-up, as in Phase 0.
- **Unplaced sign-ups carry over** to the next week automatically. They keep their original
  sign-up time, so their wait-time priority keeps growing (§7.5 step 7 and its fairness note).
  There is no DM about it, because §13 allows only "your seed formed" and the card. `/status`
  says "carried over".
- **The card arrives when the seed's goal length has run.** That is the async stand-in for §9.3's
  "after the channel has been empty for a while". The seed channel is deleted 14 days after the
  seed ends, matching "recently played with".
- **When you can mark someone:** while you share a running seed, and for 14 days after it ends.
  `/forget` clears a mark at any time. You can report anyone you have shared a seed with, for as
  long as the 12-month co-play record lasts.
- **A block over the cap is saved as an avoid,** with a message saying so. That is the Phase 0
  `EdgeStore.set_hard` rule. A report always blocks, outside the cap (§10 lean).
- **Minimum Discord account age: 30 days** (§10 names the mitigation, not the number).
- **Removed players keep the safety tools.** They can't sign up, but they can still mark, forget,
  report, export and leave.
- **Your data** (`/mydata`) is a JSON export of what the bot holds about you. It includes your own
  marks and never anyone's marks about you. `/leave confirm:true` deletes your profile, sign-ups,
  seat records and co-play records, and every edge in both directions. Reports stay, per moderation
  policy (§11).
- **Storage is SQLite** from the standard library. No new dependencies.
- **Archipelago generation stays manual for now.** The seed channel asks members to share YAMLs and
  pick someone to generate and host, as groups do today (§9.2). Automating it is slice 3.

## Slice 2: Discord connection

`discord_adapter.py` translates the existing `commands.COMMANDS`, `Reply`, `Message` and
`Transport` interface into guild slash commands, ephemeral replies, persistent card buttons,
a report modal, DMs, private seed channels and moderator posts. `philotes-bot run` starts it.
The core still owns matching, eligibility, moderation refusal, card timing and one hand-off DM
per member. Only the nonprivileged guilds intent is enabled; individual members needed for
channel overwrites are fetched by ID, never enumerated.

Choices where the spec is silent:

- discord.py 2.7 is the established, widely used, maintained Python Discord library, supports
  Python 3.13 and provides application commands, dynamic persistent buttons and modals directly.
- One dedicated worker owns SQLite and serializes every core call, including the one-minute
  timer. A synchronous transport bridges to the gateway event loop and waits for delivery results.
- Slash commands are registered only in the configured guild. Moderator authority comes from
  the configured role on the interaction, with no administrator bypass. Replies are ephemeral;
  mentions never ping. Text over Discord's 2,000-character limit becomes a private text attachment.
- Dynamic button IDs survive process restarts without storing Discord message IDs. The core
  validates the actor's co-play history on every press. Report modals collect at most 1,500 characters.
- Tokens are read only from `.env` (or the explicitly selected env file); process environment
  tokens are ignored. Missing tokens or community IDs stop `run` before any connection.
- Discord HTTP delivery failures return the existing transport failure values and log a generic
  warning. There is no retry queue: failed hand-off DMs are not resent; players use `/status` and
  `/recent`. Existing core delivery/persistence crash windows remain; run one process per database.

### Hosting on her Windows desktop (§14 #6)

Ceryce chose her Windows desktop for now (§14 #6); revisit before a wider alpha.
Alternative prices checked 2026-10-07, before tax, backups and extra usage.
These host the gateway bot, not an Archipelago room.

| Option | Cost | Tradeoff |
|---|---|---|
| **Small DigitalOcean VPS** | [From US$4/month](https://www.digitalocean.com/products/droplets); budget US$6/month for 1 GiB | Always-on gateway and local SQLite fit directly; Ceryce maintains OS, service and backups; measure memory before choosing the smallest size. |
| **Her existing Windows desktop** | US$0 hosting fee, plus electricity | Works now with `uv run philotes-bot run`; sleep, reboots and internet outages pause matching. |
| **Railway Hobby with persistent volume** | [US$5/month minimum including US$5 usage](https://docs.railway.com/pricing/plans), overage extra | Less OS maintenance; SQLite needs a mounted volume and one replica, and usage can exceed the minimum. |

Ceryce tries this on her Windows desktop on a private test server first;
[SETUP.md](SETUP.md) contains her steps. Offline tests cover adapter events without logging in.

## Slices still to come

| Slice | What it contains |
|---|---|
| **3. Archipelago hand-off** | Collect each member's YAML (and game) after the seed forms, validate it, generate the multiworld, host or upload the room, and post the room link to the seed channel. This depends on the §9.2 caveats: Archipelago's licence and generation API, and hosting costs for long-running async rooms. Also: members can end a seed early or extend it. |
| **4. Trust & safety review tooling** | Coordinated hard-blocking detection (§8: several accounts that often share seeds blocking the same target within a short window) sent to moderators for review. Per-target report history for moderators, still showing only counts of avoids. Handling for abusive reporting. |
| **5. Alpha measurement** | Privacy-preserving aggregates for the Phase 1 success test (repeat use, reunions, graduation) and the async criteria A1, A3–A8 on real data, so the Phase 0 assumptions can be checked. Also the banter-tolerance axis trial (§14 #16). |
