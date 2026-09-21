"""
src/kale/tools/watch.py
File-watching daemon for Kale projects with automatic rebuild/recheck on file change.
"""

import sys
import os
import time
import subprocess
from typing import Dict, Optional


def _get_mtimes(root_dir: str) -> Dict[str, float]:
    mtimes = {}
    for root, dirs, files in os.walk(root_dir):
        # Skip git, cache, build dirs
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "bin", "dist")]
        for file in files:
            if file.endswith(".kl") or file == "kale.toml":
                full_p = os.path.join(root, file)
                try:
                    mtimes[full_p] = os.path.getmtime(full_p)
                except OSError:
                    pass
    return mtimes


def watch_project(
    target_path: str = ".",
    action: str = "check",
    poll_interval: float = 0.5,
    max_loops: Optional[int] = None
) -> int:
    target_path = os.path.abspath(target_path)
    print(f"Kale Watch: Monitoring '{target_path}' for changes (Action: {action})...")
    print("Press Ctrl+C to stop.")

    last_mtimes = _get_mtimes(target_path)
    loops = 0

    try:
        while True:
            time.sleep(poll_interval)
            loops += 1
            if max_loops is not None and loops >= max_loops:
                break

            current_mtimes = _get_mtimes(target_path)
            changed_files = []

            for path, mtime in current_mtimes.items():
                if path not in last_mtimes or mtime > last_mtimes[path]:
                    changed_files.append(path)

            if changed_files:
                rel_names = [os.path.relpath(p, target_path) for p in changed_files]
                timestamp = time.strftime("%H:%M:%S")
                print(f"\n[{timestamp}] Changed: {', '.join(rel_names[:3])} -> Triggering {action}...")

                cmd = [sys.executable, "-m", "kale.cli", action]
                if action in ("check", "build") and len(changed_files) == 1 and changed_files[0].endswith(".kl"):
                    cmd.append(changed_files[0])

                subprocess.run(cmd)
                last_mtimes = current_mtimes

    except KeyboardInterrupt:
        print("\nKale Watch stopped.")
        return 0

    return 0


def run_watch(args) -> int:
    target = getattr(args, "target", ".") or "."
    action = getattr(args, "action", "check") or "check"
    interval = getattr(args, "interval", 0.5) or 0.5
    return watch_project(target_path=target, action=action, poll_interval=interval)
