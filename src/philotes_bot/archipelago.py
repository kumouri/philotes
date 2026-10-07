"""Offline YAML collection and supervised, operator-configured Archipelago subprocesses.

Only upload_room touches the network, behind two explicit configuration switches.
Player content is data, never command arguments, paths, imports or executable code.
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import time
import urllib.request
import zipfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

import yaml
from yaml.tokens import AliasToken, AnchorToken

from .transport import Message


def validate_yaml(content: bytes, limit: int, games: set[str]) -> dict:
    """A single, bounded, plain player document; AP validates detailed game options."""
    if not content or len(content) > limit:
        raise ValueError(f"YAML must be 1–{limit} bytes.")
    try:
        source = content.decode("utf-8-sig")
        # No aliases/anchors: avoids expansion/cycles, including when AP loads it again.
        if any(isinstance(t, (AliasToken, AnchorToken)) for t in yaml.scan(source)):
            raise ValueError("YAML anchors and aliases are not supported.")
        data = yaml.safe_load(source)
    except (UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError("Use one valid UTF-8 YAML document with safe data types.") from exc
    if not isinstance(data, dict):
        raise ValueError("YAML must contain a mapping.")
    for key in ("name", "game"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"Required key {key} must be a nonempty string.")
    if (
        len(data["name"]) > 16
        or data["name"] != data["name"].strip()
        or any(c in data["name"] for c in "{}%\r\n")
        or data["name"] == "Archipelago"
    ):
        raise ValueError("Use a literal player name of at most 16 characters (no placeholders).")
    game = data["game"]
    if game not in games:
        raise ValueError("Game is not in the configured install's supported-games manifest.")
    if not isinstance(data.get(game), dict):
        raise ValueError("Include the game's options mapping, even if empty.")
    if type(data.get("quantity", 1)) is not int or data.get("quantity", 1) != 1:
        raise ValueError("One player slot per member: quantity must be 1.")

    # AP linked options/triggers can replace game, name or quantity after our checks.
    def plain(value, depth=0):
        if depth > 32:
            raise ValueError("YAML nesting exceeds 32 levels.")
        if isinstance(value, dict):
            for k, v in value.items():
                if not isinstance(k, (str, int, float, bool)):
                    raise ValueError("YAML keys must be plain scalars.")
                if k in {"linked_options", "triggers"}:
                    raise ValueError("Linked options and triggers are not supported in this slice.")
                plain(v, depth + 1)
        elif isinstance(value, list):
            for v in value:
                plain(v, depth + 1)
        elif value is not None and type(value) not in (str, int, float, bool):
            raise ValueError("YAML values must be plain data.")

    plain(data)
    return data


def upload_room(archive: Path, enabled: bool) -> str:
    """0.6.8 web UI contract. Mock-tested only; never tested on archipelago.gg.

    Uploads the whole archive including spoiler. Session cookies retain room ownership
    for this request sequence only; deletion/room management on the site is manual.
    """
    if not enabled:
        raise ValueError("Third-party upload is disabled.")
    base = "https://archipelago.gg"
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    boundary = secrets.token_hex(24)
    body = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            'filename="seed.zip"\r\nContent-Type: application/zip\r\n\r\n'
        ).encode()
        + archive.read_bytes()
        + f"\r\n--{boundary}--\r\n".encode()
    )
    request = urllib.request.Request(
        base + "/uploads",
        body,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with opener.open(request, timeout=30) as response:
        seed_url = response.geturl()
    match = re.fullmatch(re.escape(base) + r"/seed/([A-Za-z0-9_-]+)", seed_url)
    if not match:
        raise ValueError("Upload did not return a seed page.")
    with opener.open(base + "/new_room/" + match[1], timeout=30) as response:
        room_url = response.geturl()
    if not re.fullmatch(re.escape(base) + r"/room/[A-Za-z0-9_-]+", room_url):
        raise ValueError("Upload did not return a room page.")
    return room_url


@dataclass
class Child:
    process: subprocess.Popen
    started: float
    kind: str


class Automation:
    def __init__(self, cfg, store, transport):
        self.cfg, self.store, self.transport = cfg, store, transport
        self.a = cfg.archipelago
        self.root = Path(self.a.data_path).resolve()
        self.install = Path(self.a.install_path).resolve()
        self.children: dict[int, Child] = {}
        self.games: set[str] = set()
        if self.a.enabled:
            manifest = json.loads(Path(self.a.games_manifest).read_text(encoding="utf-8-sig"))
            if manifest.get("version") != self.a.version:
                raise ValueError(
                    "Supported-games manifest version differs from configured AP version"
                )
            games = manifest.get("games")
            if (
                not isinstance(games, list)
                or not games
                or any(not isinstance(g, str) or not g for g in games)
            ):
                raise ValueError("Supported-games manifest needs a nonempty list of game names")
            self.games = set(games)

    def job(self, sid):
        row = self.store._one("SELECT * FROM ap_jobs WHERE seed_id = ?", sid)
        if row is None:
            return None
        return dict(
            zip(
                (
                    "seed_id",
                    "deadline",
                    "reminded",
                    "status",
                    "port",
                    "password",
                    "restarts",
                    "retry_at",
                ),
                row,
                strict=True,
            )
        )

    def update(self, sid, **values):
        # Keys are internal constants; never player input.
        self.store._exec(
            "UPDATE ap_jobs SET " + ", ".join(f"{k} = ?" for k in values) + " WHERE seed_id = ?",
            *values.values(),
            sid,
        )

    def folder(self, sid):
        path = self.root / str(sid)
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise ValueError("Seed directory must stay inside data_path")
        return path

    def post(self, sid, wording, *, mods=False, files=()):
        seed = self.store.seed(sid)
        if seed and seed.channel_id:
            self.transport.post_seed(seed.channel_id, Message(wording, files=tuple(files)))
        if mods:
            self.transport.post_mod(Message(wording))

    def formed(self, seed):
        if not self.a.enabled:
            return
        deadline = min(seed.ends_at, seed.formed_at + self.a.submission_hours * 3600)
        self.store._exec(
            "INSERT OR IGNORE INTO ap_jobs (seed_id, deadline) VALUES (?, ?)", seed.id, deadline
        )
        self.post(
            seed.id,
            f"Submit `/yaml seed:{seed.id} file:<attachment>` before "
            f"<t:{int(deadline)}:f>. Everyone in: generate early. At the deadline, "
            "generate with submitted players only (even one); none means no room.",
        )

    def permission(self, sid, uid, now):
        seed, job = self.store.seed(sid), self.job(sid)
        if not self.a.enabled or job is None:
            raise ValueError("Archipelago automation is not enabled for this seed.")
        if seed is None or uid not in self.store.seed_members(sid):
            raise ValueError("Only this seed's members can submit.")
        if job["status"] != "collecting" or now >= job["deadline"] or now >= seed.ends_at:
            raise ValueError("YAML submissions for this seed have closed.")

    def submit(self, sid, uid, content, now):
        self.permission(sid, uid, now)
        data = validate_yaml(content, self.a.max_yaml_bytes, self.games)
        for other, saved in self.store._all(
            "SELECT user_id, content FROM ap_yamls WHERE seed_id = ?", sid
        ):
            if other != uid and yaml.safe_load(saved)["name"].casefold() == data["name"].casefold():
                raise ValueError("Player names must be unique within the seed.")
        # Re-serialize safe plain data: AP never sees custom tags or player file names.
        normalized = yaml.safe_dump(data, sort_keys=False).encode()
        self.store._exec("INSERT OR REPLACE INTO ap_yamls VALUES (?, ?, ?)", sid, uid, normalized)
        self.tick(now)

    def command(self, configured):
        first = Path(configured[0])
        return [str(first if first.is_absolute() else self.install / first), *configured[1:]]

    def spawn(self, sid, kind, command):
        folder = self.folder(sid)
        folder.mkdir(parents=True, exist_ok=True)
        # No shell, no player content in argv. AP's output stays on the host.
        with (folder / f"{kind}.log").open("ab") as log:
            process = subprocess.Popen(
                command,
                cwd=self.install,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                start_new_session=os.name != "nt",
            )
        self.children[sid] = Child(process, time.monotonic(), kind)

    def generate(self, sid):
        rows = self.store._all("SELECT user_id, content FROM ap_yamls WHERE seed_id = ?", sid)
        if not rows:
            self.fail(sid, "No YAMLs submitted by the deadline.")
            return
        folder = self.folder(sid)
        players, output = folder / "players", folder / "output"
        players.mkdir(parents=True, exist_ok=True)
        output.mkdir(parents=True, exist_ok=True)
        for uid, content in rows:
            (players / f"{uid}.yaml").write_bytes(content)
        self.update(sid, status="generating")  # crash leaves an explicit interrupted job
        self.post(sid, f"Seed #{sid}: generating with {len(rows)} submitted player(s).")
        self.spawn(
            sid,
            "generator",
            [
                *self.command(self.a.generator_command),
                "--player_files_path",
                str(players),
                "--outputpath",
                str(output),
                "--multi",
                str(len(rows)),
                "--spoiler",
                "1",
                "--plando",
                "none",
                "--weights_file_path",
                str(folder / "unused-weights.yaml"),
                "--meta_file_path",
                str(folder / "unused-meta.yaml"),
            ],
        )

    def artifacts(self, sid):
        archives = list((self.folder(sid) / "output").glob("*.zip"))
        if len(archives) != 1 or archives[0].stat().st_size > self.a.max_artifact_bytes:
            raise ValueError("Generator must produce one archive within the artifact size limit.")
        archive = archives[0]
        with zipfile.ZipFile(archive) as z:
            selected = [n for n in z.namelist() if n.endswith((".archipelago", "_Spoiler.txt"))]
            for suffix, target in (
                (".archipelago", "room.archipelago"),
                ("_Spoiler.txt", "spoiler.txt"),
            ):
                names = [n for n in selected if n.endswith(suffix)]
                if len(names) != 1 or z.getinfo(names[0]).file_size > self.a.max_artifact_bytes:
                    raise ValueError("Archive must contain one bounded multidata and spoiler log.")
                # Fixed target paths: never extract archive paths or deserialize multidata.
                (self.folder(sid) / target).write_bytes(z.read(names[0]))
        return archive

    def host(self, sid, now):
        job = self.job(sid)
        if job["port"] is None:
            busy = {
                r[0]
                for r in self.store._all(
                    "SELECT port FROM ap_jobs WHERE status IN ('hosting', 'ready')"
                    " AND port IS NOT NULL"
                )
            }
            port = next(
                (p for p in range(self.a.port_start, self.a.port_end + 1) if p not in busy), None
            )
            if port is None:
                raise ValueError("No free configured room port.")
            self.update(sid, port=port, password=secrets.token_urlsafe(18))
            job = self.job(sid)
        self.spawn(
            sid,
            "server",
            [
                *self.command(self.a.server_command),
                str(self.folder(sid) / "room.archipelago"),
                "--host",
                self.a.bind_host,
                "--port",
                str(job["port"]),
                "--password",
                job["password"],
                "--savefile",
                str(self.folder(sid) / "room.apsave"),
                "--auto_shutdown",
                "0",
            ],
        )
        self.update(sid, status="hosting", retry_at=now + self.a.restart_seconds)
        self.post(
            sid,
            f"Seed #{sid}: room process started. Connect to "
            f"{self.a.public_host}:{job['port']} with password `{job['password']}`. "
            "Startup is supervised; reachability must be checked by the host.",
            mods=False,
        )
        self.transport.post_mod(Message(f"Seed #{sid}: self-host room process started."))

    def stop(self, sid):
        child = self.children.get(sid)
        if child and child.process.poll() is None:
            if os.name == "nt":
                # AP generation may create worker children. Kill this exact PID's tree.
                try:
                    subprocess.run(
                        ["taskkill.exe", "/PID", str(child.process.pid), "/T", "/F"],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    child.process.kill()
            else:
                with suppress(ProcessLookupError):
                    os.killpg(child.process.pid, signal.SIGTERM)
            try:
                child.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    child.process.kill()
                else:
                    with suppress(ProcessLookupError):
                        os.killpg(child.process.pid, signal.SIGKILL)
                child.process.wait(timeout=5)
        self.children.pop(sid, None)

    def fail(self, sid, reason):
        self.stop(sid)
        self.update(sid, status="failed")
        self.post(
            sid, f"Seed #{sid}: Archipelago failed. {reason} Host intervention needed.", mods=True
        )

    def erase(self, sid):
        self.stop(sid)
        folder = self.folder(sid)
        if folder.exists():
            shutil.rmtree(folder)
        self.store._exec("DELETE FROM ap_jobs WHERE seed_id = ?", sid)

    def forget(self, uid):
        for (sid,) in self.store._all("SELECT seed_id FROM ap_yamls WHERE user_id = ?", uid):
            job = self.job(sid)
            if job["status"] == "collecting":
                self.store._exec("DELETE FROM ap_yamls WHERE seed_id = ? AND user_id = ?", sid, uid)
            else:
                # Generated data combines players; no safe way to redact an AP archive/save.
                self.erase(sid)
                self.post(
                    sid,
                    f"Seed #{sid}: room stopped and local artifacts deleted for a "
                    "member's data deletion request.",
                    mods=True,
                )
                seed = self.store.seed(sid)
                if seed and seed.channel_id is not None:
                    self.transport.delete_channel(seed.channel_id)
                    self.store.mark_channel_closed(sid)
                    self.store.set_seed_channel(sid, None)

    def tick(self, now):
        # Even disabled configuration stops processes/retains the original cleanup schedule.
        for (sid,) in self.store._all("SELECT seed_id FROM ap_jobs ORDER BY seed_id"):
            seed, job = self.store.seed(sid), self.job(sid)
            if seed is None:
                continue
            retention = min(
                self.cfg.safety.recently_played_days, self.cfg.safety.coplay_retention_days
            )
            if now >= seed.ends_at + retention * 86400:
                self.erase(sid)
                continue
            if now >= seed.ends_at or not self.a.enabled:
                self.stop(sid)
                self.update(sid, status="stopped")
                continue
            try:
                status = job["status"]
                child = self.children.get(sid)
                if status == "collecting":
                    n = self.store._one("SELECT COUNT(*) FROM ap_yamls WHERE seed_id = ?", sid)[0]
                    if now >= job["deadline"] or n == len(self.store.seed_members(sid)):
                        self.generate(sid)
                    elif not job["reminded"] and now >= min(
                        job["deadline"], seed.formed_at + self.a.reminder_hours * 3600
                    ):
                        self.post(
                            sid,
                            f"Seed #{sid}: YAML reminder — {n} submitted. Deadline "
                            f"<t:{int(job['deadline'])}:f>; use `/yaml` before then.",
                        )
                        self.update(sid, reminded=1)
                elif status == "generating":
                    if child is None:
                        self.fail(sid, "Generation was interrupted by a bot restart.")
                    elif child.process.poll() is not None:
                        self.children.pop(sid)
                        if child.process.returncode:
                            self.fail(sid, "Generator exited unsuccessfully; see private host log.")
                            continue
                        archive = self.artifacts(sid)
                        self.post(
                            sid,
                            f"Seed #{sid}: generation succeeded. Archive attached; "
                            "it includes spoilers. Separate spoiler log retained on host.",
                            mods=True,
                            files=(archive,),
                        )
                        if self.a.hosting_mode == "upload":
                            self.update(sid, status="uploading")
                            room = upload_room(archive, self.a.upload_enabled)
                            self.update(sid, status="uploaded")
                            self.post(sid, f"Seed #{sid}: third-party room: {room}", mods=True)
                        else:
                            self.update(sid, status="ready")
                            self.host(sid, now)
                    elif time.monotonic() - child.started >= self.a.generation_timeout_seconds:
                        self.fail(sid, "Generator timed out.")
                elif status == "uploading":
                    self.fail(
                        sid, "Upload was interrupted; check the site manually before retrying."
                    )
                elif status in {"ready", "hosting"}:
                    if child is not None and child.process.poll() is None:
                        continue
                    if child is not None:
                        self.children.pop(sid)
                        self.update(sid, status="ready", retry_at=now + self.a.restart_seconds)
                        self.post(sid, f"Seed #{sid}: room exited; scheduling restart.", mods=True)
                        continue
                    if now >= job["retry_at"]:
                        if job["restarts"] >= self.a.max_restarts:
                            self.fail(sid, "Room restart limit reached.")
                        else:
                            self.update(sid, restarts=job["restarts"] + 1)
                            self.host(sid, now)
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                # Avoid exposing paths, player options, logs or passwords to moderators.
                self.fail(
                    sid, f"Operation failed ({type(exc).__name__}); check private host files."
                )

    def close(self):
        for sid in list(self.children):
            self.stop(sid)
