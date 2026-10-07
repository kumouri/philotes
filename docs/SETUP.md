# Setting up the Philotes bot

There are two parts. **Running it locally** needs nothing but this repo. **Putting it on a Discord
server** is for the host: every step in that part is done by a person with access to the Discord
account and the server. No step is automated, and nothing in the repo creates applications,
tokens or invites.

What the bot does is in [phase1-bot.md](phase1-bot.md). What players are told is in
[user-guide.md](user-guide.md).

## 1. Run it locally (no Discord, no token)

You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run philotes-bot demo       # a scripted two-week run, printed
uv run philotes-bot console    # type commands as any user and move the clock yourself
uv run philotes-bot check      # the resolved configuration, and whether a token is set
```

In the console, `as 101 /join adult=true` runs a command as user 101, `as 900 mod /mod reports`
runs one as a moderator, `as 101 click ph:more:1:102` presses a card button, and `advance 7d` moves
the clock forward and runs the bot's timer. `help` lists the rest. Everything the bot would have
sent appears in the output: DMs, seed channels and moderator posts.

## 2. On a Discord server (the host's steps)

The Discord adapter is available. The host performs the steps below, starting on a private test
server. `philotes-bot check` confirms local configuration without connecting.

### Before anything technical

1. **Choose the host community** ([spec §14 #3](spec.md#14-open-questions), Ceryce's call). Phase 0
   passed its async criteria from about 50 opted-in players, and the silent-rejection bar (A8)
   from 100 ([spec §12](spec.md#phase-0-matcher-simulator-nothing-user-facing)).
2. **Agree moderation with the community's moderators.** They receive reports in a private
   channel and can remove a player from matching (spec §10). There is no central moderation team
   in Phase 1.
3. **Agree the rules post with them.** It should say Philotes is 18+ only, link the
   [user guide](user-guide.md), and include its statement that avoids are honoured (spec §12).

### Create the Discord application

4. In the [Discord Developer Portal](https://discord.com/developers/applications), create an
   application (for example "Philotes").
5. Under **Bot**:
   - **Reset Token** and copy it. Put it in a file named `.env` next to `pyproject.toml` on the
     machine that will run the bot, as `DISCORD_TOKEN=<token>`. `.env` is git-ignored. Never commit
     the token, paste it in chat, or put it in `philotes-bot.toml`. If it leaks, reset it.
   - Turn **Public Bot** off, so only you can add it to servers.
   - Leave all three **Privileged Gateway Intents** off. The bot reads no message content,
     presence or member list (spec §9.3, §11).
6. Under **OAuth2 → URL Generator**, tick the scopes `bot` and `applications.commands`, and these
   bot permissions:
   - **View Channels** and **Send Messages**, to post in seed channels and the moderators' channel;
   - **Manage Channels**, to create and delete private seed channels;
   - **Read Message History** and **Attach Files**, for private replies and larger data exports;
   - **Manage Roles**, which Discord requires before a bot can set per-member permissions on the
     channels it creates.
7. Open the generated URL and add the bot to a **private test server first**. Add it to the host
   community only once slice 2 has been tried there. Adding it needs a server admin.

### Prepare the server

8. In the host server, create:
   - a **category** for seed channels (for example "Philotes seeds"), with the bot allowed to
     manage channels in it;
   - a **private moderators' channel** that only the moderators and the bot can see;
   - choose an existing **moderator role** whose holders may use `/mod` commands.
9. Turn on **Developer Mode** (User Settings → Advanced). Right-click the server, the role, the
   channel and the category, and **Copy ID** for each.

### Configure and check

10. Copy `philotes-bot.example.toml` to `philotes-bot.toml` (git-ignored). Set `[community]`
    `name`, `guild_id`, `mod_role_id`, `mod_channel_id` and `seed_category_id`. Set when the weekly
    window closes in `[window]`. The other defaults are the ruled values.
11. Run `uv run philotes-bot check`. It should list your community and print
    `DISCORD_TOKEN: set`. It never prints the token.
12. Keep `philotes.db` on the host machine only. It holds who marked whom, which is the most
    sensitive data the project keeps (spec §11). Back it up privately.

### Tell players

13. Players who want the post-seed card by DM need **Allow direct messages from server members**
    switched on for the host server (Discord's privacy settings). Anyone who leaves it off can use
    `/recent` instead.

### Start on her Windows desktop and try the private server

14. In PowerShell, from the repo directory, run `uv sync --locked`, then
    `uv run philotes-bot run`. Keep this terminal and the desktop awake. Ctrl+C stops it.
    The token is read only from the untracked `.env`, not from process environment variables.
    A missing token prints a setup message and exits without connecting. The bot uses outbound
    gateway connections; no public web endpoint or inbound firewall rule is needed.
15. Use only the private test server's IDs initially. With at least three consenting adult test
    members (accounts at least 30 days old), try `/help`, `/join adult:true`, `/signup goals:short
    size:3 accept:3`, and `/status`. A holder of the configured moderator role can run
    `/mod close-window` to form the seed; an ordinary member should be refused.
16. Check that each member receives one hand-off DM, can see the seed channel, and an unrelated
    member cannot see it. Discord administrators can always see private channels. Use `/recent`
    to exercise more, neutral, avoid, block and report; submit the report form and check that only
    the moderators see the post. Try `/mod reports`, `/mod history user:<player> page:1`, and `/mod resolve`
    with `outcome:abusive`, `outcome:false`, then `outcome:open` to reverse it. Check `/mod audit`
    for actor, action and dates. Outcomes leave safety blocks intact; only their author clears them.
    Coordination notices contain aggregate evidence without avoider identities. Restart the process and
    try an old card button again. Test a member with DMs closed and use `/status`/`/recent` instead.
17. For a quick card/cleanup trial, use a separate disposable test database and shorten
    `[window] goal_days` in that test configuration, keeping one value per goal. Restore defaults
    before the host community trial. Do not shorten retention in a community database.
18. Use one bot process per database. Keep `.env` and the database private, and back up the database
    while the bot is stopped. The bot runs on [her Windows desktop](phase1-bot.md#hosting-on-her-windows-desktop-14-6)
    for now (§14 #6); revisit hosting before a wider alpha. No application, invite,
    token or hosted service was created during implementation.

## 3. Archipelago automation (Ceryce's installation and configuration)

This slice targets **Archipelago 0.6.8**, checked against
[its release source](https://github.com/ArchipelagoMW/Archipelago/tree/0.6.8).
It ships with `[archipelago] enabled = false` and `upload_enabled = false`. Nothing installs
Archipelago for you. The automated tests use small fake generator/server scripts; they do not
prove a real game can generate or that a room is reachable. Start with consenting players on the
private Discord test server only after the host setup is complete.

1. Install Archipelago 0.6.8 yourself on the machine that runs Philotes, following
   [the upstream setup instructions](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/running%20from%20source.md).
   Keep its runtime/dependencies separate from Philotes' Python 3.13 environment. Prepare any
   required game files/ROMs privately and configure AP's `host.yaml` for unattended generation
   (including race mode off so a spoiler is produced). Use only trusted bundled worlds; the bot
   accepts data files, never players' `.apworld` plugins. Review the upstream licence and individual
   worlds' requirements before hosting. No AP packages or game files are committed here.
2. Export the games from that exact trusted install **offline**, using its Python runtime.
   In PowerShell, from the Archipelago source directory, run (use the install's Python path):

   ```powershell
   .\venv\Scripts\python.exe -c 'import json, pathlib, Utils; from worlds import AutoWorldRegister; pathlib.Path("philotes-games.json").write_text(json.dumps({"version": Utils.__version__, "games": sorted(AutoWorldRegister.world_types)}), encoding="utf-8")'
   ```

   This imports the operator-installed trusted worlds, not any player YAML. Keep the resulting
   manifest private and regenerate it if the install changes. The bot reads this JSON without
   importing AP. A packaged install needs a matching manifest exported from the same release's
   source/runtime with the same installed worlds; do not copy a current online games list.
3. Set `[archipelago]` in the untracked `philotes-bot.toml`. For a source install, an example is:

   ```toml
   [archipelago]
   enabled = true
   version = "0.6.8"
   install_path = 'C:\Archipelago'
   games_manifest = 'C:\Archipelago\philotes-games.json'
   data_path = 'C:\PhilotesPrivate\seeds'
   generator_command = ['C:\Archipelago\venv\Scripts\python.exe', 'C:\Archipelago\Generate.py']
   server_command = ['C:\Archipelago\venv\Scripts\python.exe', 'C:\Archipelago\MultiServer.py']
   hosting_mode = "self_host"
   upload_enabled = false
   public_host = "your-hostname.example"
   bind_host = "0.0.0.0"
   port_start = 38281
   port_end = 38300
   ```

   Relative command executables resolve inside `install_path`; use absolute paths for interpreters
   and script arguments. The example file lists every setting, including 48/24-hour deadline and
   reminder, 64 KiB YAML cap, 600-second generation timeout, 100 MiB artifact cap, restart backoff
   and restart limit. Protect `data_path` and the database with host-only filesystem permissions:
   they include submitted YAMLs, player names, spoilers, saves, logs and room passwords. Do not
   put them in shared folders or commit them. Default `philotes-seeds/` is git-ignored.
4. For remote players, allow inbound TCP for the configured port range on the room host and, if
   needed, forward it on the router. The bot gateway alone needed no inbound rules; a MultiServer
   room does. `localhost`/`127.0.0.1` defaults are for local testing only. Configure a real public
   hostname/address, capacity and availability before offering long async seeds. Each active seed
   occupies one port; no available port or failed binding becomes a visible hosting failure.
5. Run `uv run philotes-bot check` locally, then start the bot yourself on the private test server.
   Form a seed and submit `/yaml seed:1 file:<your YAML attachment>` as each member. Try invalid
   files and duplicate names. Check all-in generation, the archive attachment (it includes spoilers),
   moderator summaries, connection password and an actual client connection. Stop/restart the bot
   and verify AP saves resume. Check a shorter disposable deadline with a missing submitter; do not
   shorten production retention. Detailed game options are finally validated by AP's generator.
6. One process per database. Ctrl+C shuts down owned AP processes; run under your chosen service
   manager for an always-on host. If you forcibly kill the bot, inspect and stop orphan AP processes
   before starting it again. Interrupted generation becomes failed; inspect the seed's private
   `generator.log`, fix installation/configuration, and form a new seed rather than editing SQLite
   state to replay the job. A server crash is restarted up to three times with the same port,
   password and save path, then reported failed. At seed end the room stops. Fourteen days later,
   its files, YAML rows, credentials and job state are purged with the channel. `/leave` after
   generation stops and deletes the whole local room and its channel to erase combined player
   data, including the bot's posted archive/credentials. Back up the
   database and files privately while the bot is stopped, and apply retention to backups too.

### Upload to archipelago.gg — disabled, Ceryce's decision

The upload path exists but is **off by default and untested against the live site**. Selecting
`hosting_mode = "upload"` without `upload_enabled = true` is rejected. Neither a live upload nor
any contact with archipelago.gg was performed during implementation. Do not enable it as part of
routine setup; Ceryce decides whether sharing player data with a third-party service is acceptable.

Opting in uploads the generated archive including spoiler, creates a room via the site's web UI,
and posts its room-page link. The upstream 0.6.8 UI contract can change. Site ownership cookies
are not persisted, remote end/deletion is not automated, and site retention applies independently
of local cleanup or `/leave`. Confirm an acceptable owner/recovery/deletion procedure and tell
players about this limitation before opting in. Self-host supervision applies only to local rooms.

## Local alpha measurement

The operator can read the existing bot database without starting Discord or AP:

```sh
uv run philotes-bot metrics --db philotes-bot.sqlite3 --out summary.csv
uv run philotes-bot metrics --db philotes-bot.sqlite3 --out summary.json
```

Use the actual configured database path; the command never creates a missing database.
Moderators can use `/mod metrics` for the same private aggregate report. See
[phase1-bot.md](phase1-bot.md#slice-5-alpha-measurement) for sample sizes, retention,
A1–A8 applicability and the success test's limits. Reports do not expose identities or marks,
and do not establish graduation or a complete alpha pass while tests remain n/a.
