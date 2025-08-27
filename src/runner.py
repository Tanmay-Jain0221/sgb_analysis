import sys
import subprocess
from pathlib import Path
import os

# Repo root = parent of this file's directory
REPO_ROOT = Path(__file__).resolve().parents[1]

# making it work with .venv
PY = sys.executable

# Commands (in order)
CMDS = [
    [PY, str(REPO_ROOT / "src" / "download_nse_sgb.py")],
    [PY, str(REPO_ROOT / "src" / "collect_nse_csv.py"), "--deep"],
    [PY, str(REPO_ROOT / "src" / "download_bse_bhavcopy.py")],
]

def run_cmd(cmd):
    print(f"\n Running: {' '.join(cmd)}")
    # Stream output live; more helpful than capture_output for debugging
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        text=True
    )
    if proc.returncode != 0:
        raise SystemExit(f" Command failed ({proc.returncode}): {' '.join(cmd)}")

def main():
    print(f"[runner] repo root: {REPO_ROOT}")
    print(f"[runner] python   : {PY}")
    for cmd in CMDS:
        run_cmd(cmd)
    print("\n All done.")

if __name__ == "__main__":
    main()
