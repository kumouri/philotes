"""The local console and CLI: runnable with no token and no network."""

from philotes_bot.cli import DEMO_START, main
from philotes_bot.commands import COMMANDS
from philotes_bot.config import BotConfig
from philotes_bot.console import Console, demo_lines
from philotes_bot.core import Bot


def test_every_command_names_a_bot_method_with_matching_options():
    import inspect

    for c in COMMANDS:
        sig = inspect.signature(getattr(Bot, c.method))
        params = [p for p in sig.parameters if p not in ("self", "inv")]
        assert [o.name for o in c.options] == params, c.name


def test_console_parses_commands_clicks_and_errors():
    con = Console(BotConfig(), DEMO_START)
    assert con.run_line("as 1 /join adult=true")[0].startswith("> You're in")
    assert con.run_line("as 1 /signup goals=nope")[0].startswith("! goals")
    assert con.run_line("as 1 /join adult=maybe") == ["! adult must be true or false"]
    assert con.run_line("as 1 /bogus")[0] == "! unknown command /bogus"
    assert con.run_line("as 1 click ph:more:1:2")[0].startswith("!")
    assert con.run_line("as 1 /mod reports")[0] == "! Moderators only."
    assert con.run_line("as 9 mod /mod reports")[0] == "> No open reports."
    assert con.run_line("advance soon") == ["! advance takes e.g. 7d, 12h or 30m"]
    assert con.run_line("# a comment") == []


def test_demo_runs_end_to_end():
    con = Console(BotConfig(), DEMO_START, seed=1)
    out = "\n".join(demo_lines(con))
    assert "CHANNEL #seed-1-short" in out
    assert "MOD CHANNEL: **Report #1**" in out
    assert "Avoids are honoured" in out
    seeds = [con.store.seed_members(s.id) for s in con.store.seeds()]
    assert len(seeds) >= 3  # two weeks of seeds


def test_check_reports_token_absent_without_printing_it(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    args = ["--config", str(tmp_path / "x.toml"), "--env-file", str(tmp_path / "e"), "check"]
    assert main(args) == 0
    assert "DISCORD_TOKEN: absent" in capsys.readouterr().out
    (tmp_path / "e").write_text("DISCORD_TOKEN=s3cret\n", encoding="utf-8")
    main(args)
    out = capsys.readouterr().out
    assert "DISCORD_TOKEN: set" in out and "s3cret" not in out
