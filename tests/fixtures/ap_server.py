"""Fake MultiServer that records starts and crashes on a host-created flag; no sockets."""

import argparse
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("multidata")
for name in ("host", "port", "password", "savefile", "auto_shutdown"):
    parser.add_argument("--" + name, required=True)
args = parser.parse_args()
folder = Path(args.multidata).parent
assert Path(args.multidata).read_bytes() == b"fake multidata"
assert args.password and args.auto_shutdown == "0"
with (folder / "starts.txt").open("a") as f:
    f.write(args.port + "\n")
while True:
    flag = folder / "crash"
    if flag.exists():
        flag.unlink()
        raise SystemExit(3)
    time.sleep(0.02)
