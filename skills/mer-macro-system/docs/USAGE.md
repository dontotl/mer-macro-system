# USAGE

## 일간 리포트 생성
```bash
python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date 2026-04-23
```

## 일간 + 주간 동시 생성
```bash
python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date 2026-04-23 --weekly
```

## 텔레그램 테스트 전송 포함
```bash
python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date 2026-04-23 --weekly --send-telegram-test --telegram-target 5294188460
```

## 결과물 경로
- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`
- `invest/notes/daily-macro/weekly/YYYY-Www.md`
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`
