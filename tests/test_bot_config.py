"""Bot configuration: TOML + untracked env file, token degrades to absent, ruled matcher values."""

import pytest

from philotes_bot.config import BotConfig, load_config, read_env_file


def test_defaults_are_the_ruled_v1_values(tmp_path):
    cfg = load_config(tmp_path / "missing.toml", tmp_path / "missing.env", environ={})
    assert cfg.discord_token is None
    assert cfg.community.guild_id is None  # community-agnostic until Ceryce picks a host
    pol = cfg.policy()
    assert pol.hard_cap == 10  # §14 #8
    assert pol.soft_half_life_days == 7.0  # §14 #9
    assert pol.newcomer_decay_sessions == 0 and not pol.anchors_enabled  # §14 #18
    assert cfg.weights().low_connectivity == 0.0
    assert cfg.shape().kind == "async"


def test_toml_and_env_file(tmp_path):
    (tmp_path / "bot.toml").write_text(
        '[community]\nname = "Test Server"\nguild_id = 42\n\n'
        '[window]\nclose_weekday = 4\ngoals = ["quick", "long"]\ngoal_days = [5, 21]\n',
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("# secret\nDISCORD_TOKEN='abc.def'\n", encoding="utf-8")
    cfg = load_config(tmp_path / "bot.toml", tmp_path / ".env", environ={})
    assert cfg.community.name == "Test Server" and cfg.community.guild_id == 42
    assert cfg.window.goals == ("quick", "long") and cfg.window.goal_days == (5, 21)
    assert cfg.discord_token == "abc.def"
    assert "abc.def" not in repr(cfg)  # never printed


def test_only_env_file_supplies_token(tmp_path):
    (tmp_path / ".env").write_text("DISCORD_TOKEN=file\n", encoding="utf-8")
    cfg = load_config(None, tmp_path / ".env", environ={"DISCORD_TOKEN": "process"})
    assert cfg.discord_token == "file"


def test_bad_config_is_refused(tmp_path):
    (tmp_path / "a.toml").write_text("[community]\nguild = 1\n", encoding="utf-8")
    with pytest.raises(KeyError):
        load_config(tmp_path / "a.toml", environ={})
    (tmp_path / "b.toml").write_text('[window]\ngoals = ["x"]\ngoal_days = [1, 2]\n', "utf-8")
    with pytest.raises(ValueError):
        load_config(tmp_path / "b.toml", environ={})


def test_env_file_parsing(tmp_path):
    p = tmp_path / ".env"
    p.write_text('A=1\n\n# c\nB = "two words"\nnot a pair\n', encoding="utf-8")
    assert read_env_file(p) == {"A": "1", "B": "two words"}
    assert read_env_file(tmp_path / "nope") == {}


def test_example_config_loads():
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / "philotes-bot.example.toml"
    cfg = load_config(example, environ={})
    assert isinstance(cfg, BotConfig)
