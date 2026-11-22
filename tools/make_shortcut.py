#!/usr/bin/env python3
"""Create the desktop shortcut for the dashboard (run once on each computer).

    python tools/make_shortcut.py

The shortcut points at 启动面板.bat in this project folder, wherever the folder is.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "启动面板.bat"
NAME = "研究团队面板.lnk"


def main() -> int:
    if not TARGET.is_file():
        print(f"Not found: {TARGET}")
        return 1
    script = (
        "$d = [Environment]::GetFolderPath('Desktop'); "
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d '%s')); "
        "$s.TargetPath = '%s'; $s.WorkingDirectory = '%s'; $s.WindowStyle = 7; "
        "$s.IconLocation = \"$env:SystemRoot\\System32\\imageres.dll,109\"; $s.Save(); "
        "Write-Output (Join-Path $d '%s')"
    ) % (NAME, str(TARGET).replace("'", "''"), str(ROOT).replace("'", "''"), NAME)
    p = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    if p.returncode != 0:
        print("Could not create the shortcut:\n" + (p.stderr or p.stdout))
        return 1
    print("Shortcut created on the desktop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
