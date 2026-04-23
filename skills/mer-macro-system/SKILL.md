---
name: mer-macro-system
description: Generate and operate Mer macro reporting outputs from OpenClaw workspace, including daily macro note, Telegram digest, liquidity chart, repo summary, policy summary, and weekly summary files. Use when asked to run/update/package the 메르 매크로 노트 자동화, produce md+telegram outputs, or maintain related scripts/docs.
---

# Mer Macro System

## Quick workflow

1. Run `scripts/run_mer_macro_reports.py` to generate outputs.
2. Check files under `invest/notes/daily-macro/`.
3. If requested, send the Telegram text file contents via delivery pipeline.
4. Update PRD/docs when report format or indicators change.

## Commands

- Daily only:
  - `python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date YYYY-MM-DD`
- Daily + weekly:
  - `python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date YYYY-MM-DD --weekly`
- Include Telegram test send:
  - `python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date YYYY-MM-DD --weekly --send-telegram-test --telegram-target <chat_id>`

## Output contract

Always verify these files after generation:

- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png` (optional if matplotlib missing)
- `invest/notes/daily-macro/weekly/YYYY-Www.md` (when `--weekly`)
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt` (when `--weekly`)

## Maintenance rules

- Keep secrets out of files and commits.
- Use environment variables for credentials.
- Keep `.env*`, tokens, API key files ignored by git.
- Prefer extending `automation/mer_daily_macro_note.py` for indicator logic.
- Keep report sections aligned between markdown and Telegram summaries.
