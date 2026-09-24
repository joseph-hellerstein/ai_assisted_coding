"""Shared helper for the ad-hoc Playwright acceptance scripts in this
directory: starts a real instance of the app as a subprocess and waits
for it to come up. Not pytest-collected (see pytest.ini)."""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_DIR = ROOT / "src"


def start_server(port: int):
    env = dict(os.environ)
    cmd = (
        "import sys; sys.path.insert(0, r'{src}'); "
        "from app import app; app.run(debug=False, host='127.0.0.1', port={port})"
    ).format(src=SRC_DIR, port=port)
    proc = subprocess.Popen(
        [sys.executable, "-c", cmd],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{url}/_dash-layout", timeout=1)
            return proc
        except Exception:
            time.sleep(0.5)
    out, err = proc.communicate(timeout=2)
    proc.terminate()
    raise RuntimeError(f"Server did not start.\nSTDOUT: {out}\nSTDERR: {err}")


def stop_server(proc):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
