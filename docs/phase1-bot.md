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
| `transport.py` | Core side effects (DM, create/delete a seed channel, seed posts/files, moderator posts), and `InMemoryTransport`. |
| `console.py`, `cli.py` | `philotes-bot demo`, `philotes-bot console`, `philotes-bot check`. |
| `measurement.py` | Anonymous weekly/cumulative criteria and success-test reporting and CSV/JSON export. |
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
- **Storage is SQLite** from the standard library. Slice 3 adds PyYAML for safe player-file parsing.
- **Archipelago generation is configurable.** With automation disabled, the original manual
  hand-off remains available. Slice 3 below describes the automated path.

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

## Slice 3: Archipelago automation

`archipelago.py` collects and safely validates player YAMLs, invokes Archipelago's generator,
captures its archive and spoiler, and supervises a room process. `Bot.tick()` drives deadlines,
reminders, subprocess completion, timeouts, restarts and cleanup on the existing one-minute timer.
No Archipelago install is bundled, imported into the bot, downloaded or installed automatically.
The target is **Archipelago 0.6.8**. Interfaces were checked against its tagged source:
[Generate.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/Generate.py),
[Main.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/Main.py),
[MultiServer.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/MultiServer.py),
[upload.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/WebHostLib/upload.py) and
[misc.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/WebHostLib/misc.py).
The local automated tests use fake Python executables, with no real Archipelago install or network.

Choices where the spec is silent:

- **Submission is `/yaml seed:<number> file:<Discord attachment>`.** This uses players' existing
  files without transcription into a modal, needs no message-content intent and gives a private
  acceptance/rejection reply. The guild, opted-in player and seed membership are checked before
  reading an attachment, then again before saving. Original filenames never become paths.
  One YAML per member; replacements are allowed while collection is open. `/status` shows the
  member's submission state and `/mydata` includes only their own normalized YAMLs.
- **48-hour deadline, one reminder at 24 hours**, both configurable and capped by the seed's end.
  Reminder and operational messages go only to the private seed channel, without pings or new
  DMs (§13). All members submitted: start early. At the deadline: use only submitted members,
  even one. Zero submissions: mark failed and notify the channel and moderators. Late files are
  refused, and the same job is never automatically generated twice. Missing submitters keep their
  original seed-channel/card seats; this slice does not change the matcher's co-play semantics.
  Goal duration still runs from formation, as in slice 1, rather than restarting after generation.
- **Validation is deliberately narrow.** Default 64 KiB, one UTF-8 document, safe loading only,
  mapping root, literal nonempty `name` (at most 16 characters, unique ignoring case, no name
  placeholders/whitespace padding/reserved `Archipelago`), literal `game` and a game-options
  mapping are required. An offline supported-games manifest exported from the configured install
  must match the configured version; unknown games fail before acceptance. Quantity must be one.
  Aliases/anchors, non-plain values, excessive nesting, linked options and triggers are refused;
  triggers could replace the fields just validated. Game-specific option correctness and required
  ROMs are Archipelago's responsibility at generation. Safe normalized data is staged in numeric
  per-seed/member paths; no player code, shell commands, imports or executable files are run.
- **Archipelago owns generation.** Operator-configured argument arrays run without a shell in the
  configured install directory, with isolated input/output paths, explicit slot count, spoiler
  level 1, plando disabled and no default weights or meta file. Each seed has one generation
  attempt; default timeout is 600 wall-clock seconds, detected on the next timer tick (up to a
  minute later). Output/errors go to a private host log; player content and raw errors are not
  echoed to moderators. Success requires one archive and one multidata/spoiler inside it, within
  configured size limits. Extraction uses fixed target filenames, never archive paths. The
  archive is attached to the seed channel (including its spoiler); a separate spoiler stays on
  the host. Moderators receive success/failure summaries, without passwords or player files.
- **Self-host is the selected mode**, but all automation ships disabled. A distinct free port
  from the configured range is assigned to each seed, with a generated random password stored
  privately in SQLite. The configured MultiServer command receives multidata, bind address,
  port, password and a per-seed save path. Only the seed channel gets connection credentials.
  A process-start notice does not guarantee internet reachability: Ceryce must test the install,
  firewall and address herself. Process exits schedule a restart on the timer, default 60-second
  backoff and three restarts total; exhaustion fails visibly. Port/password/save path are reused.
- **Shutdown stops owned children; ended seeds stop rooms.** Graceful bot restart resumes active
  self-hosted rooms from retained artifacts and save paths; interrupted generation is reported
  failed rather than silently rerun. Use one bot per database. After a forced bot kill or machine
  crash, the host must check for orphan AP processes before restarting; this slice does not add
  an OS service manager. AP saves on its own schedule, so abrupt termination can lose progress
  since its last save. Failures need host intervention; no automatic regeneration or retry command.
- **Files and submissions expire with the seed channel**, default 14 days after the seed ends,
  shorter than the 365-day co-play history. Inputs, archive, spoiler, saves, logs, password and
  job state are deleted together. `/leave` deletes an ungenerated YAML immediately. If a YAML
  was already combined into generated data, the whole local room stops and its files are erased,
  since redacting an AP archive/save safely is unavailable. Its channel is deleted too, to remove
  the bot's posted archive and credentials; this consequence appears in `/leave` confirmation.
  Copies already downloaded by players
  cannot be recalled. The filesystem directory and database must be backed up privately together.
  If co-play retention is configured shorter than channel retention, files are removed before
  that shorter history purge so a deleted seed cannot leave orphan files behind.
- **Upload ships disabled and has never been tested against the live site.** It requires both
  `hosting_mode = "upload"` and `upload_enabled = true`; Ceryce decides whether to opt in.
  The code uses a cookie session, multipart archive upload to `/uploads`, then `/new_room/<seed>`,
  and posts the returned room page. This is the 0.6.8 web UI contract, not a promised stable API.
  Fake responses test the request shape; no live request was made.
  Interrupted uploads fail visibly on restart and are never automatically repeated, since the
  remote operation might already have succeeded. Upload sends the whole archive,
  including player names/game data and spoiler, to archipelago.gg. Its retention and room lifecycle
  belong to the site; local end/deletion does not stop or erase a remote room. Site owner cookies
  are not persisted, and automated remote management/deletion is outside this slice. Discuss that
  limitation with players before enabling it.

Early ending/extending by members remains future work; this slice uses the existing goal-duration
end. No Discord connection, Archipelago download/install, real generator/server or third-party
upload was performed during development. The GitHub PR/CI are the only publishing operations.

## Slice 4: moderation review tools

`moderation.py` measures retained avoid/block edges and report outcomes. It never writes edges,
changes matching, removes players or assigns a reputation score. The existing matcher and §7.4
assortativity measurement stay unchanged. Cross-community moderation (§14 #17) waits for Phase 2.

Choices where the spec is silent:

- **Burst detector:** at least three distinct accounts marking the same target within any inclusive
  24-hour window in the last 30 days. **Repeated-pattern detector:** at least three accounts with
  at least three common avoided/blocked targets in that rolling 30-day period. Both include soft
  avoids and hard blocks (including report blocks). Three avoids is a review lead, not proof;
  24 hours catches a short campaign and 30 days covers several weekly seeds. These are initial
  fixed alpha thresholds, not calibrated estimates of abuse. Independent preferences and a shared
  bad experience can also trigger them. Repeated-pattern evidence counts qualifying account triples,
  not necessarily disjoint groups. Detection uses current edges and their last-applied timestamps,
  not a new historical edge/event ledger: overwrites, forget, deletion and decay purge remove evidence.
- **Privacy wins over identifying evidence.** §8 asks for coordinated-blocking review, while §11
  says moderators never see who avoided whom. Notices show counts, burst target and time range,
  or counts of qualifying triples and the repeated-pattern window; never avoider IDs or the shared
  target list. This limits investigation deliberately. Ordinary mass avoidance does not trigger a
  verdict or penalty; coordination notices are leads about a possible group campaign, not allegations
  against the target. Reports still supply the human-review allegation independently.
- **Delivery:** the existing private moderator transport on the timer (and report resolution).
  One notice per burst target, repeated-pattern detector, or repeat reporter per 30 days; successful
  deliveries alone are remembered in SQLite across restarts. Failed delivery retries on the next
  timer. Notice keys expire after 30 days and contain no avoider IDs. Players receive no notices.
- **`/mod history user:<player> page:<n>`** lists retained reports filed and received, newest first,
  ten per page, with filing date, current outcome, resolution note and last outcome date. It also
  shows the reporter's abusive/false count divided by all retained reports filed. Reports and the
  audit log follow the existing moderation policy: retained indefinitely, including after `/leave`;
  no new finite moderation retention period is invented. Co-play/seed retention remains unchanged.
- **`/mod resolve report:<id> outcome:<open|resolved|abusive|false> note:<text>`** defaults to resolved
  for compatibility. Any retained report may be revised or reopened, with previous outcome and note
  in the audit log. All outcomes leave the report's safety block intact: declaring an allegation
  false does not establish that rematching is safe. Only the author can clear that edge with
  `/forget` or another card mark. Reopening never recreates an edge the author cleared.
- **Repeat-reporter review:** at least three reports marked abusive/false and at least 50% of all
  retained reports filed. Open and ordinarily resolved reports remain in the denominator. Three
  avoids a single dispute flagging someone; the rate avoids flagging a prolific reporter for a few
  mistakes. This is a moderator-only descriptive rate, never a matching input or automatic sanction.
- **`/mod audit page:<n>`** shows ten newest audit entries per page: actor ID, action, subject,
  detail and UTC timestamp. Successful remove, restore, resolve/reopen, close-window, report-list,
  history and audit reads are recorded; rejected calls do not create moderator-action entries.
  Resolution notes are capped at 1,500 characters. Existing databases gain additive tables on open;
  existing reports remain compatible. Audit rows contain no avoid-edge identities.

Offline synthetic tests cover detector thresholds/negatives, moderator gates, private delivery,
deduplication, report-history pagination and retention, outcome reversal, safety-block preservation,
rates and persistent audits. No Discord connection, AP process or external moderation service was
used. The GitHub PR and CI are the publishing operations.

## Slice 5: alpha measurement

`measurement.py` reads the bot's own SQLite store. `philotes-bot metrics --db <path>` prints a
JSON report; `--out summary.csv` or `--out summary.json` writes the same anonymous aggregates.
The CLI opens an existing database read-only, needs no token and does not start the core,
Discord, AP or any transport. It can read slice 4 databases without migrating or backfilling them.
`/mod metrics` uses the existing moderator gate and ephemeral reply/attachment handling.
It never posts reports to the moderator channel or sends player messages.

### Definitions and limits

| Test | Live measurement |
|---|---|
| A1 | Placed eligible sign-ups / eligible sign-ups at close; ≥ 90%. |
| A2 | n/a: only applies to rolling cadence; the ruled cadence is batch-at-close. |
| A3 | Preferred-size placements / placed seats; ≥ 75%. Each player's range is checked separately. |
| A4 | Hard-locked sign-ups / eligible sign-ups in the original pool; < 1%. The shared Phase 0 lockout search unions feasible lobbies across all listed goals, ignores soft avoids and uses accepted sizes. Any node-limit unknown makes the criterion n/a. |
| A5 | Measurable from weekly per-player eligible-close and placement totals. The shared simulator reducer requires at least three entries per player in the selected period; n/a without eligible rates. No closed individual sign-ups, goals or size ranges are retained. |
| A6 | Measurable for players joining after this upgrade: join time, completed seed history and first mutual-more milestone (time and completed-session count, no partner). Shared simulator reducer: success within three completed seeds; eligible after three seeds or an early success. Weekly cohorts join in that week, cumulative cohorts join within the retained period. Existing players are excluded rather than relabelled newcomers. Early mutual marks can have count zero (before the first seed ends); no assertion of actual play. |
| A7 | Measurable: snapshot mutual-more state when the second player signs up, while the window is open. At close, count first-choice-compatible mutual pairs and same-seed hits, using the shared simulator ratio. Edits preserve original signup time/state; withdrawal discards the snapshot. Pairs carried together preserve their state with their signup times. Only anonymous close totals survive. Missing legacy snapshots make the criterion n/a, never a guessed denominator. |
| A8 | **not measurable by design**: retaining first-card avoid labels after negligible soft avoids or forgotten marks are deleted would preserve precisely the sensitive relationship §11 deletes. No labels or historical avoid ledger are added. Current edges cannot substitute. Reads `experiments.A8_BAR` for both bar and M threshold: n/a below M = 100 and still n/a above it by design. |
| Phase 1 repeat use | Counts placements of people who already appear in an earlier retained seed. Pass if at least one repeat placement exists, fail if there are seats but none repeat, n/a without seats. |
| Phase 1 reunions | Counts unordered co-player pair events with an earlier retained co-match. Same observed/nonzero test as repeat use. This is reunion formation, not an assertion of actual play or mutual preference. |
| Phase 1 graduation | Optional `/graduated confirm:true` self-report, one per opted-in account; no names, members, links or third-party telemetry. Counts reporters, not distinct groups. Pass on an observed report, n/a without one. Inactivity and `/leave` are never evidence. Overall passes when repeat use, reunions and reported graduation pass; fails if an observed component fails. |

`metric_helpers` supplies the same placement, per-player rate, newcomer and co-signup reducers
to both the simulator and live reports; the metrics are not redefined.
The ruled criteria checks are the simulator's `experiments.check`, not copied thresholds.
Exports use the same metric column names as Phase 0's `summary.csv`; unavailable numbers are
JSON null / blank CSV cells. Each A1–A8 check has pass / FAIL / n/a, a sample size (null if no
valid denominator exists), and a reason for n/a. **There is no claim that the live alpha meets
Phase 0's criteria while A8 is unavailable.** The bot has no synthetic ground-truth enjoyment,
actual played hours, counterfactual friendship or off-platform telemetry, and none is invented.

### Choices where the spec is silent

- Capture anonymous close totals (entries, placed, slots, preferred, locked, unknown and
  seeds) before deleting sign-ups. No historical individual sign-up ledger, avoid ledger or
  third-party analytics is added. Old closes cannot be reconstructed and are not counted as zero
  observations. The initial measurement slice adds `alpha_windows`; this follow-up adds five tables.
  The close's window key prevents duplicate totals. Existing core seed/delivery crash windows remain; this is not a transactional lifecycle
  rewrite.
- Reports group closes and formations into Monday-based UTC calendar weeks. Manual early closes
  count in their actual week. Carried sign-ups count once in each closed pool where they remain
  eligible, matching the simulator's per-window denominator. Removed/nonexistent players are
  excluded. Placement includes manual AP hand-off and seeds whose AP generation later fails:
  these are matcher/formation metrics, not completion metrics.
- Cumulative means **retained data**, not all-time tracking. Close aggregates expire with the
  configured co-play horizon (default 365 days). Reports filter expired aggregates even before
  the next timer purge. Anonymous totals cannot be attributed back to an account and survive
  `/leave` until expiry; identifiable seat and co-play records still disappear on deletion.
  Repeat/reunion counts can fall after deletion or retention expiry. Earlier retained seeds
  provide the baseline for each week's repeat/reunion observations.
- M is the current count of opted-in, nonremoved players, not Discord membership or weekly sign-ups.
  Reports name that basis through the definitions here; it does not reconstruct historical M.
  The output includes the actual 7-day half-life and hard-cap configuration and batch cadence.
- The simulator supplies replicate standard deviations, **no confidence intervals**. A live history
  has no independent simulator replicates. Reports state that uncertainty limitation and expose
  denominators rather than presenting replicate SD as a confidence interval or inventing one.
- Graduation is voluntary own-group reporting, never inferred from usage. `/graduated` explains
  collection before confirmation; duplicate submissions do not add counts. It sends no notifications.
  Banter-tolerance trial (§14 #16) remains a live-alpha experiment, with no new matching axis in
  this measurement slice.

### Follow-up storage and privacy

Opening the store adds five tables with `CREATE TABLE IF NOT EXISTS`; no existing rows are
rewritten, and read-only metrics still tolerate old schemas. `alpha_rates` contains only user ID,
UTC week, entry count and placed count, so A5 has denominators without retaining individual closed
sign-ups. `alpha_newcomers` contains user ID, join time and a first-mutual timestamp/session ordinal,
never the partner. Completed seeds supply the session count at the mark (as in the simulator's
card step);
a mutual mark made while the first seed is active has ordinal zero. The shared reducer
handles this as attainment before the three-seed horizon, without inventing completed play.
Milestones describe first attainment, not current edge state; changes/forget do not erase the fact
of attainment. They never appear in personal exports because that would reveal an incoming mark.

`alpha_pending_pairs` is private transient mutual-state data attached to open sign-ups. It is erased
at close or withdrawal (or moves only with still-open carried sign-ups). `alpha_reunions` stores
only window key, close time, qualifying-pair/hit totals and missing-snapshot count for idempotence.
`alpha_graduations` stores reporter ID/time solely for deduplication and deletion. None of these
fields is a matching input. Reports/CSV/JSON contain aggregate values only, without identities,
partner information or individual labels. `/mydata` adds only the caller's weekly placement totals
and voluntary graduation report; it never exposes incoming marks or mutual snapshots.

All retained summaries use the configured co-play horizon (default 365 days) and reports filter
expiry before timer purge. A5 excludes a partially expired UTC week rather than keeping expired
individual observations. Identifiable rows disappear on `/leave`; anonymous close totals survive
until expiry. A6 cohorts expire by join date. No legacy denominators, mutual timing, cohorts or
co-signup states are fabricated. Weekly A5 may be n/a for a normal one-close week because its
three-entry minimum is deliberately unchanged; cumulative A5 becomes measurable after three
eligible closes. A8 remains n/a by design even after sufficient population/history: its ruled bar
is unchanged, and the alpha cannot claim to satisfy all A1–A8.

Offline tests cover known ratios and fail cases, cross-goal lockout, insufficient samples,
unknown searches, insufficient-history criteria, the A8 constant, repeat use and reunions, gates,
identity-free CSV/JSON, restart persistence, deletion, retention and read-only legacy CLI reports.
No Discord connection, real AP process or external analytics service was used.

## Between the build and live alpha

All five Phase 1 build slices are complete; deployment and real use remain untested. Ceryce needs
to choose the 18+ host community/moderators, configure her desktop and a private Discord test
server, then follow [SETUP.md](SETUP.md) for Discord/AP acceptance testing before inviting players.
The voluntary `/graduated` check and banter-tolerance trial happen during alpha. Member-driven
seed early ending/extending remains a lifecycle follow-up, not part of this five-slice build.
