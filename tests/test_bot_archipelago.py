import json
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from philotes_bot.archipelago import upload_room, validate_yaml
from philotes_bot.config import Archipelago, validate
from philotes_bot.core import Bot, Invocation
from philotes_bot.store import Store
from tests.test_bot_core import GUILD, world


def player_yaml(name="Player", game="Test Game"):
    return f"name: {name}\ngame: {game}\n{game}: {{}}\n".encode()


def wait_for(condition, w=None):
    end = time.monotonic() + 8
    while time.monotonic() < end:
        if w:
            w.bot.tick()
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("fake subprocess did not reach expected state")


def submit(w, uid, content=None):
    return w.run(uid, "submit_yaml", seed=1, file=content or player_yaml(f"Player{uid}"))


def all_in(w):
    for uid in (1, 2, 3):
        assert submit(w, uid).ok


def job(w):
    return w.bot.archipelago.job(1)


def test_safe_validation_accepts_plain_and_bom():
    data = validate_yaml(b"\xef\xbb\xbf" + player_yaml(), 65536, {"Test Game"})
    assert data["game"] == "Test Game"


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"x" * 65537,
        b"\xff",
        b"[]",
        b"name: p",
        b"game: Test Game",
        player_yaml(game="Unknown"),
        b"name: p\ngame: Test Game\nTest Game: []",
        b"name: !!python/object/apply:os.system ['echo bad']",
        b"name: &x p\ngame: Test Game\nTest Game: {x: *x}",
        player_yaml() + b"---\nname: other",
        player_yaml() + b"quantity: 2",
        player_yaml() + b"linked_options: []",
        player_yaml() + b"triggers: []",
        player_yaml() + b"date: 2026-10-07",
        player_yaml(name="{player}"),
        player_yaml(name="abcdefghijklmnopq"),
        b"name: [Player]\ngame: Test Game\nTest Game: {}",
        b"name: p\ngame: {Test Game: 1}\nTest Game: {}",
        player_yaml() + b"deep: " + b"[" * 40 + b"1" + b"]" * 40,
    ],
    ids=lambda content: f"{len(content)}-bytes",
)
def test_rejects_yaml(content):
    with pytest.raises(ValueError):
        validate_yaml(content, 65536, {"Test Game"})


def test_collection_authorization_replacement_export_and_reminder(automated):
    w = automated()
    assert not w.bot.submit_yaml(Invocation(1, GUILD + 1), 1, player_yaml()).ok
    assert not submit(w, 999).ok
    assert not submit(w, 1, b"[]").ok
    assert submit(w, 1).ok
    assert submit(w, 1, player_yaml("Replaced")).ok
    assert not submit(w, 2, player_yaml("replaced")).ok
    export = w.run(1, "mydata").text
    assert "Replaced" in export and "your_archipelago_yamls" in export
    assert "Replaced" not in w.run(2, "mydata").text
    assert "submitted" in w.run(1, "status").text
    w.advance(1)
    messages = w.t.channels[w.store.seed(1).channel_id].messages
    assert sum("YAML reminder" in m.text for m in messages) == 1
    w.bot.tick()
    assert sum("YAML reminder" in m.text for m in messages) == 1
    assert all(len(w.t.dms_to(u)) == 1 for u in (1, 2, 3))
    assert job(w)["status"] == "collecting"


def test_all_in_generates_archive_spoiler_and_room(automated):
    w = automated()
    all_in(w)
    assert job(w)["status"] == "generating"
    assert not submit(w, 1).ok
    wait_for(lambda: job(w)["status"] == "hosting", w)
    folder = w.bot.archipelago.folder(1)
    wait_for(lambda: (folder / "starts.txt").exists())
    assert (folder / "spoiler.txt").read_text() == "fake spoiler"
    assert (folder / "generator.log").read_text().strip() == "fake generation"
    assert len(list((folder / "players").glob("*.yaml"))) == 3
    messages = w.t.channels[w.store.seed(1).channel_id].messages
    assert any(m.files and m.files[0].name == "AP_fake.zip" for m in messages)
    assert any("localhost:38281" in m.text and job(w)["password"] in m.text for m in messages)
    assert any("generation succeeded" in m.text for m in w.t.mod_posts)
    assert all(job(w)["password"] not in m.text and not m.files for m in w.t.mod_posts)


def test_deadline_uses_only_submitters_and_rejects_late(automated):
    w = automated()
    assert submit(w, 2).ok
    w.advance(2)
    assert job(w)["status"] == "generating"
    assert not submit(w, 3).ok
    wait_for(lambda: job(w)["status"] == "hosting", w)
    folder = w.bot.archipelago.folder(1)
    assert [p.name for p in (folder / "players").glob("*.yaml")] == ["2.yaml"]
    args = json.loads((folder / "output" / "invocation.json").read_text())
    assert args["multi"] == "1"


def test_deadline_without_yamls_fails_once(automated):
    w = automated()
    w.advance(2)
    assert job(w)["status"] == "failed"
    n = len(w.t.mod_posts)
    w.bot.tick()
    assert len(w.t.mod_posts) == n == 1
    assert "No YAMLs" in w.t.mod_posts[0].text
    assert not w.bot.archipelago.children


@pytest.mark.parametrize("mode", ["failure", "missing", "no-spoiler"])
def test_generation_failure_and_invalid_artifacts(automated, mode):
    w = automated(mode)
    all_in(w)
    wait_for(lambda: job(w)["status"] == "failed", w)
    assert any("failed" in m.text for m in w.t.mod_posts)
    assert any("failed" in m.text for m in w.t.channels[w.store.seed(1).channel_id].messages)
    assert not w.bot.archipelago.children


def test_generation_timeout_kills_process(automated):
    w = automated("timeout", generation_timeout_seconds=0.1)
    all_in(w)
    child = w.bot.archipelago.children[1].process
    wait_for(lambda: job(w)["status"] == "failed", w)
    assert child.poll() is not None
    assert "timed out" in w.t.mod_posts[-1].text


def test_room_restart_stop_retention_and_bot_restart(automated):
    w = automated()
    all_in(w)
    wait_for(lambda: job(w)["status"] == "hosting", w)
    folder = w.bot.archipelago.folder(1)
    wait_for(lambda: (folder / "starts.txt").exists())
    password, port = job(w)["password"], job(w)["port"]
    first = w.bot.archipelago.children[1].process
    (folder / "crash").touch()
    wait_for(lambda: first.poll() is not None)
    w.bot.tick()
    assert job(w)["status"] == "ready"
    w.clock.t += 60
    w.bot.tick()
    wait_for(lambda: len((folder / "starts.txt").read_text().splitlines()) == 2)
    assert job(w)["restarts"] == 1 and job(w)["password"] == password
    second = w.bot.archipelago.children[1].process
    w.bot.archipelago.close()
    assert second.poll() is not None
    w.bot = Bot(w.bot.cfg, w.store, w.t, w.clock)
    w.clock.t += 60
    w.bot.tick()
    assert job(w)["status"] == "hosting" and job(w)["port"] == port
    third = w.bot.archipelago.children[1].process
    w.clock.t = w.store.seed(1).ends_at
    w.bot.tick()
    assert third.poll() is not None and job(w)["status"] == "stopped"
    assert folder.exists()
    w.advance(14)
    assert not folder.exists() and job(w) is None
    assert not w.store._all("SELECT * FROM ap_yamls")
    # The original fixture bot and replacement share the database; avoid double close.
    w.bot.archipelago.close()


def test_restart_limit(automated):
    w = automated(max_restarts=0)
    all_in(w)
    wait_for(lambda: job(w)["status"] == "hosting", w)
    first = w.bot.archipelago.children[1].process
    w.bot.archipelago.folder(1).joinpath("crash").touch()
    wait_for(lambda: first.poll() is not None)
    w.clock.t += 60
    w.bot.tick()
    assert job(w)["status"] == "ready"
    w.clock.t += 60
    w.bot.tick()
    assert job(w)["status"] == "failed"
    assert "restart limit" in w.t.mod_posts[-1].text


def test_leave_removes_yaml_and_generated_personal_data(automated):
    collecting = automated()
    assert submit(collecting, 1).ok
    collecting.run(1, "leave", confirm=True)
    assert not collecting.store._all("SELECT * FROM ap_yamls")
    hosted = automated()
    all_in(hosted)
    wait_for(lambda: job(hosted)["status"] == "hosting", hosted)
    process = hosted.bot.archipelago.children[1].process
    channel = hosted.store.seed(1).channel_id
    hosted.run(1, "leave", confirm=True)
    assert process.poll() is not None and job(hosted) is None
    assert not hosted.bot.archipelago.folder(1).exists()
    assert hosted.t.channels[channel].deleted
    assert hosted.store.seed(1).channel_closed


def test_manifest_version_must_match(automated, tmp_path):
    w = automated()
    manifest = Path(w.bot.cfg.archipelago.games_manifest)
    manifest.write_text(json.dumps({"version": "wrong", "games": ["Test Game"]}))
    with pytest.raises(ValueError, match="version"):
        Bot(w.bot.cfg, w.store, w.t, w.clock)


def test_upload_disabled_and_mock_contract(tmp_path, monkeypatch):
    archive = tmp_path / "seed.zip"
    archive.write_bytes(b"fake zip")
    opener = MagicMock()
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: opener)
    with pytest.raises(ValueError, match="disabled"):
        upload_room(archive, False)
    opener.open.assert_not_called()
    seed_response, room_response = MagicMock(), MagicMock()
    seed_response.__enter__.return_value.geturl.return_value = "https://archipelago.gg/seed/abc"
    room_response.__enter__.return_value.geturl.return_value = "https://archipelago.gg/room/def"
    opener.open.side_effect = [seed_response, room_response]
    assert upload_room(archive, True) == "https://archipelago.gg/room/def"
    request = opener.open.call_args_list[0].args[0]
    assert request.full_url == "https://archipelago.gg/uploads"
    assert b'name="file"' in request.data and b"fake zip" in request.data
    assert opener.open.call_args_list[1].args[0] == "https://archipelago.gg/new_room/abc"


def test_upload_mode_needs_explicit_opt_in():
    w = world()
    with pytest.raises(ValueError, match="upload_enabled"):
        validate(
            replace(
                w.bot.cfg,
                archipelago=Archipelago(
                    enabled=True, install_path="fake", games_manifest="fake", hosting_mode="upload"
                ),
            )
        )
    w.bot.close()


def test_completed_generator_is_not_timed_out_by_delayed_timer(automated):
    w = automated(generation_timeout_seconds=0.1)
    all_in(w)
    child = w.bot.archipelago.children[1]
    wait_for(lambda: child.process.poll() is not None)
    child.started -= 100
    w.bot.tick()
    assert job(w)["status"] == "hosting"


def test_generation_restart_reports_interruption(automated):
    w = automated("timeout")
    all_in(w)
    w.bot.archipelago.close()
    w.bot = Bot(w.bot.cfg, w.store, w.t, w.clock)
    w.bot.tick()
    assert job(w)["status"] == "failed"
    assert "interrupted" in w.t.mod_posts[-1].text


def test_upload_mode_does_not_start_local_server(automated, monkeypatch):
    w = automated(hosting_mode="upload", upload_enabled=True)
    calls = []

    def fake_upload(path, enabled):
        calls.append((path, enabled))
        return "https://archipelago.gg/room/mock"

    monkeypatch.setattr("philotes_bot.archipelago.upload_room", fake_upload)
    all_in(w)
    wait_for(lambda: job(w)["status"] == "uploaded", w)
    assert len(calls) == 1 and calls[0][1]
    assert not w.bot.archipelago.children
    assert "room/mock" in w.t.mod_posts[-1].text
    w.bot.tick()
    assert len(calls) == 1


def test_rooms_take_distinct_ports(automated):
    from tests.test_bot_core import MOD, join_and_sign

    w = automated()
    join_and_sign(w, [4, 5, 6], size="3")
    w.run(MOD, "mod_close_window", mod=True)
    all_in(w)
    for uid in (4, 5, 6):
        assert w.run(uid, "submit_yaml", seed=2, file=player_yaml(f"Player{uid}")).ok
    wait_for(lambda: all(w.bot.archipelago.job(s)["status"] == "hosting" for s in (1, 2)), w)
    assert {w.bot.archipelago.job(s)["port"] for s in (1, 2)} == {38281, 38282}


def test_disk_state_resumes_room(automated, tmp_path):
    w = automated()
    all_in(w)
    wait_for(lambda: job(w)["status"] == "hosting", w)
    w.bot.archipelago.close()
    path = str(tmp_path / "persistent.db")
    disk = Store(path)
    w.store.db.backup(disk.db)
    disk.close()
    reopened = Store(path)
    bot = Bot(w.bot.cfg, reopened, w.t, w.clock)
    try:
        w.clock.t += 60
        bot.tick()
        assert bot.archipelago.job(1)["status"] == "hosting"
        assert bot.archipelago.job(1)["password"] == job(w)["password"]
        assert bot.archipelago.children[1].process.poll() is None
    finally:
        bot.close()


def test_interrupted_upload_is_not_replayed_or_self_hosted(automated, monkeypatch):
    w = automated(hosting_mode="upload", upload_enabled=True)
    w.bot.archipelago.update(1, status="uploading")
    upload = MagicMock()
    monkeypatch.setattr("philotes_bot.archipelago.upload_room", upload)
    w.bot.tick()
    assert job(w)["status"] == "failed"
    upload.assert_not_called()
    assert not w.bot.archipelago.children


def test_shorter_history_retention_cannot_orphan_files(automated):
    w = automated()
    assert submit(w, 1).ok
    folder = w.bot.archipelago.folder(1)
    folder.mkdir(parents=True)
    folder.joinpath("private.log").write_text("private")
    w.bot.cfg = replace(w.bot.cfg, safety=replace(w.bot.cfg.safety, coplay_retention_days=1))
    w.bot.archipelago.cfg = w.bot.cfg
    w.clock.t = w.store.seed(1).ends_at + 2 * 86400
    w.bot.tick()
    assert not folder.exists() and job(w) is None and not w.store.seeds()


def test_upload_opt_in_must_be_boolean():
    w = world()
    with pytest.raises(ValueError, match="booleans"):
        validate(replace(w.bot.cfg, archipelago=Archipelago(upload_enabled="false")))
    w.bot.close()
