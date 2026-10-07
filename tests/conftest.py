"""Test-wide guard: no test may open a network connection."""

import socket

import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise RuntimeError("tests must not use the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture
def automated(tmp_path):
    import json
    import sys
    from dataclasses import replace
    from pathlib import Path

    from philotes_bot.config import Archipelago, validate
    from philotes_bot.core import Bot
    from tests.test_bot_core import MOD, join_and_sign, world

    fixtures = Path(__file__).parent / "fixtures"
    bots = []

    def make(mode="success", **overrides):
        w = world()
        manifest = tmp_path / "games.json"
        manifest.write_text(json.dumps({"version": "0.6.8", "games": ["Test Game"]}))
        a = Archipelago(
            enabled=True,
            install_path=str(tmp_path),
            games_manifest=str(manifest),
            data_path=str(tmp_path / f"seeds-{len(bots)}"),
            generator_command=(sys.executable, str(fixtures / "ap_generator.py"), "--mode", mode),
            server_command=(sys.executable, str(fixtures / "ap_server.py")),
            **overrides,
        )
        cfg = replace(w.bot.cfg, archipelago=a)
        validate(cfg)
        w.bot = Bot(cfg, w.store, w.t, w.clock)
        bots.append(w.bot)
        join_and_sign(w, [1, 2, 3], size="3")
        w.run(MOD, "mod_close_window", mod=True)
        return w

    yield make
    for bot in bots:
        bot.close()
