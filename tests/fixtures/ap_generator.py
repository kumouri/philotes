"""Fake AP 0.6.8 CLI: no imports from Archipelago and no network."""

import argparse
import json
import time
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="success")
for name in (
    "player_files_path",
    "outputpath",
    "multi",
    "spoiler",
    "plando",
    "weights_file_path",
    "meta_file_path",
):
    parser.add_argument("--" + name, required=True)
args = parser.parse_args()
print("fake generation", flush=True)
if args.mode == "failure":
    raise SystemExit(2)
if args.mode == "timeout":
    time.sleep(60)
players = list(Path(args.player_files_path).glob("*.yaml"))
assert len(players) == int(args.multi)
assert args.spoiler == "1" and args.plando == "none"
Path(args.outputpath, "invocation.json").write_text(json.dumps(vars(args)))
if args.mode != "missing":
    with zipfile.ZipFile(Path(args.outputpath, "AP_fake.zip"), "w") as z:
        z.writestr("AP_fake.archipelago", b"fake multidata")
        if args.mode != "no-spoiler":
            z.writestr("AP_fake_Spoiler.txt", "fake spoiler")
