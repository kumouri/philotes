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
    the moderators see the post. Try `/mod reports` and `/mod resolve`. Restart the process and
    try an old card button again. Test a member with DMs closed and use `/status`/`/recent` instead.
17. For a quick card/cleanup trial, use a separate disposable test database and shorten
    `[window] goal_days` in that test configuration, keeping one value per goal. Restore defaults
    before the host community trial. Do not shorten retention in a community database.
18. Use one bot process per database. Keep `.env` and the database private, and back up the database
    while the bot is stopped. Review [hosting options](phase1-bot.md#hosting-options-for-ceryce-14-6-remains-her-decision)
    before choosing an always-on host; §14 #6 remains Ceryce's decision. No application, invite,
    token or hosted service was created during implementation.
