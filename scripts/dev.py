#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_HOST = "127.0.0.1"
DEFAULT_FRONTEND_PORT = 5173
DEFAULT_POLL_INTERVAL_SECONDS = 0.8
WATCH_DIRS = ("backend", "config")
WATCH_FILES = (".env", ".env.example")
WATCH_EXTENSIONS = {".py", ".json"}
IGNORED_PARTS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class FileFingerprint:
    size: int
    mtime_ns: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local development stack with backend auto-restart and optional Vite HMR.",
    )
    parser.add_argument("--backend-host", default=DEFAULT_BACKEND_HOST, help="Backend host.")
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT, help="Backend port.")
    parser.add_argument("--frontend-host", default=DEFAULT_FRONTEND_HOST, help="Frontend dev-server host.")
    parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT, help="Frontend dev-server port.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between backend file checks.",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Only run the backend watcher and skip the Vite dev server.",
    )
    parser.add_argument(
        "backend_args",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to `python -m backend.api.minimal_api`. Prefix with `--`.",
    )
    return parser.parse_args()


def format_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def iter_watch_paths() -> list[Path]:
    paths: list[Path] = []
    for relative_dir in WATCH_DIRS:
        root = PROJECT_ROOT / relative_dir
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative_parts = path.relative_to(PROJECT_ROOT).parts
            if any(part in IGNORED_PARTS for part in relative_parts):
                continue
            if path.suffix.lower() not in WATCH_EXTENSIONS:
                continue
            paths.append(path)

    for relative_file in WATCH_FILES:
        path = PROJECT_ROOT / relative_file
        if path.exists() and path.is_file():
            paths.append(path)

    return sorted(set(paths))


def take_snapshot() -> dict[str, FileFingerprint]:
    snapshot: dict[str, FileFingerprint] = {}
    for path in iter_watch_paths():
        stat = path.stat()
        snapshot[str(path.relative_to(PROJECT_ROOT))] = FileFingerprint(size=stat.st_size, mtime_ns=stat.st_mtime_ns)
    return snapshot


def summarize_snapshot_changes(
    previous: dict[str, FileFingerprint],
    current: dict[str, FileFingerprint],
    *,
    limit: int = 6,
) -> list[str]:
    messages: list[str] = []

    added = sorted(set(current) - set(previous))
    removed = sorted(set(previous) - set(current))
    changed = sorted(path for path in (set(previous) & set(current)) if previous[path] != current[path])

    for path in added[:limit]:
        messages.append(f"added {path}")
    remaining = limit - len(messages)

    if remaining > 0:
        for path in changed[:remaining]:
            messages.append(f"changed {path}")
    remaining = limit - len(messages)

    if remaining > 0:
        for path in removed[:remaining]:
            messages.append(f"removed {path}")

    total = len(added) + len(changed) + len(removed)
    if total > len(messages):
        messages.append(f"... and {total - len(messages)} more change(s)")

    return messages or ["detected backend/config change"]


def build_backend_command(args: argparse.Namespace, backend_args: list[str]) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "backend.api.minimal_api",
        "--host",
        args.backend_host,
        "--port",
        str(args.backend_port),
    ]
    command.extend(backend_args)
    return command


def find_npm_command() -> str:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm", "npm.cmd"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise SystemExit("npm was not found. Install Node.js first, then rerun `python scripts/dev.py`.")


def build_frontend_command(args: argparse.Namespace, npm_command: str) -> list[str]:
    return [
        npm_command,
        "run",
        "dev",
        "--",
        "--host",
        args.frontend_host,
        "--port",
        str(args.frontend_port),
    ]


def start_process(label: str, command: list[str], cwd: Path) -> subprocess.Popen[Any]:
    print(f"[dev] starting {label}: {format_command(command)}")
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(command, cwd=str(cwd), env=env)


def stop_process(label: str, process: subprocess.Popen[Any] | None, timeout_seconds: float = 5.0) -> None:
    if process is None or process.poll() is not None:
        return

    print(f"[dev] stopping {label}")
    process.terminate()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(f"[dev] force killing {label}")
        process.kill()
        process.wait(timeout=timeout_seconds)


def main() -> None:
    args = parse_args()
    backend_args = list(args.backend_args)
    if backend_args[:1] == ["--"]:
        backend_args = backend_args[1:]

    if not args.backend_only and not FRONTEND_DIR.exists():
        raise SystemExit(f"Missing frontend directory: {FRONTEND_DIR}")

    npm_command = None if args.backend_only else find_npm_command()
    snapshot = take_snapshot()
    backend_command = build_backend_command(args, backend_args)
    frontend_command = build_frontend_command(args, npm_command) if npm_command else None

    print(f"[dev] project root: {PROJECT_ROOT}")
    print(f"[dev] backend url: http://{args.backend_host}:{args.backend_port}/")
    if frontend_command:
        print(f"[dev] frontend url: http://{args.frontend_host}:{args.frontend_port}/")
        print("[dev] frontend code uses Vite HMR; backend/config edits trigger automatic backend restarts.")
    else:
        print("[dev] running in backend-only mode")

    backend_process: subprocess.Popen[Any] | None = None
    frontend_process: subprocess.Popen[Any] | None = None

    try:
        backend_process = start_process("backend", backend_command, PROJECT_ROOT)
        if frontend_command:
            frontend_process = start_process("frontend", frontend_command, FRONTEND_DIR)

        while True:
            time.sleep(args.poll_interval)

            if frontend_process is not None and frontend_process.poll() is not None:
                raise SystemExit(f"Frontend dev server exited with code {frontend_process.returncode}.")

            current_snapshot = take_snapshot()
            backend_needs_restart = current_snapshot != snapshot

            if backend_process is not None and backend_process.poll() is not None:
                print(f"[dev] backend exited with code {backend_process.returncode}; restarting")
                backend_needs_restart = True

            if not backend_needs_restart:
                continue

            for message in summarize_snapshot_changes(snapshot, current_snapshot):
                print(f"[dev] {message}")

            stop_process("backend", backend_process)
            backend_process = start_process("backend", backend_command, PROJECT_ROOT)
            snapshot = current_snapshot
    except KeyboardInterrupt:
        print("[dev] received Ctrl+C, shutting down")
    finally:
        stop_process("frontend", frontend_process)
        stop_process("backend", backend_process)


if __name__ == "__main__":
    main()
