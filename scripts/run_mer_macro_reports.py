#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Run Mer macro report generator')
    p.add_argument('--date', required=True, help='Report date (YYYY-MM-DD)')
    p.add_argument('--weekly', action='store_true', help='Generate weekly summary too')
    p.add_argument('--send-telegram-test', action='store_true')
    p.add_argument('--telegram-target', default='5294188460')
    p.add_argument('--message-channel', default='telegram')
    p.add_argument('--python-bin', default='./.venv-mer-dashboard/bin/python')
    return p.parse_args()


def resolve_python_bin(workspace: Path, requested: str) -> str:
    if requested != './.venv-mer-dashboard/bin/python':
        return requested

    candidates = [
        workspace / '.venv-mer-dashboard' / 'bin' / 'python',
        workspace / '.venv' / 'bin' / 'python',
    ]

    for c in candidates:
        if c.exists():
            return str(c)

    system_python = shutil.which('python3') or shutil.which('python')
    if system_python:
        return system_python

    raise FileNotFoundError('No usable python interpreter found.')


def main() -> int:
    args = parse_args()
    workspace = Path(__file__).resolve().parents[1]
    script = workspace / 'automation' / 'mer_daily_macro_note.py'

    python_bin = resolve_python_bin(workspace, args.python_bin)

    cmd = [python_bin, str(script), '--date', args.date]
    if args.weekly:
        cmd.append('--weekly')
    if args.send_telegram_test:
        cmd += ['--send-telegram-test', '--telegram-target', args.telegram_target, '--message-channel', args.message_channel]

    result = subprocess.run(cmd, cwd=workspace, check=False)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
