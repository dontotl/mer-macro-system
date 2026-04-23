---
name: mer-macro-system
description: Generate and operate Mer-style macro reports from the OpenClaw workspace, including daily markdown notes, weekly summaries, Telegram-ready digest text, liquidity charts, repo/policy summaries, and reusable report automation. Use when asked to run, maintain, improve, package, or reuse the 메르 매크로 리포트 자동화, especially for daily/weekly macro collection, chart generation, Telegram delivery formatting, or skill-based reuse by other agents.
---

# Mer Macro System

메르 블로그식 매크로 프레임을 기준으로,
**수집 → 해석 → 리포트 → 텔레그램 → 차트 → 재사용 가능한 스킬화**까지 이어주는 운영 스킬이다.

이 스킬은 단순히 숫자를 가져오는 것이 아니라,
지표에 메르식 의미를 붙이고 사람 읽기 좋은 문서/메시지로 바꾸는 데 목적이 있다.

## 핵심 역할

이 스킬이 담당하는 일:
- 일간 매크로 리포트 생성
- 주간 매크로 리포트 생성
- 텔레그램 전송용 짧은 요약문 생성
- Liquidity 차트 생성
- Repo / Policy 요약 포함
- 다른 에이전트도 재사용할 수 있도록 동일 포맷 유지

## 실행 기본 흐름

1. `scripts/run_mer_macro_reports.py` 실행
2. `invest/notes/daily-macro/` 아래 결과물 확인
3. 필요하면 텔레그램용 txt 파일 사용 또는 전송 테스트 실행
4. 지표/해석 규칙 바뀌면 `automation/mer_daily_macro_note.py`와 문서 같이 갱신

## 주요 명령

### 일간 생성
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date YYYY-MM-DD
```

### 일간 + 주간 생성
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date YYYY-MM-DD --weekly
```

### 텔레그램 테스트 포함
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py \
  --date YYYY-MM-DD \
  --weekly \
  --send-telegram-test \
  --telegram-target <chat_id>
```

## 반드시 확인할 출력물

일간:
- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`

주간:
- `invest/notes/daily-macro/weekly/YYYY-Www.md`
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`

## 운영 규칙

- 비밀정보는 파일/커밋에 남기지 말 것
- `.env`, 토큰, secret 파일은 git ignore 유지
- 지표 로직은 가능하면 `automation/mer_daily_macro_note.py`에 통합 유지
- md와 telegram 요약의 핵심 판정은 서로 어긋나지 않게 유지
- 한줄 결론은 쉽게, 본문 해석은 깊게 유지

## 문서 참고

상세 설명은 아래 문서를 우선 읽으면 된다.

- 전체 개요: `README.md`
- 설치: `docs/INSTALL.md`
- 활용: `docs/USAGE.md`
- 출력물 규칙/예시: `references/outputs.md`

## 언제 이 스킬을 확장해야 하나

아래 상황이면 이 스킬을 고치거나 확장해야 한다.

- 새 거시지표를 추가할 때
- 차트 종류를 늘릴 때
- Repo / Policy 로직을 고도화할 때
- Telegram 포맷을 손볼 때
- 주간/월간 요약 구조를 늘릴 때
- 다른 에이전트에서 재사용 가능한 운영 문서가 더 필요할 때

## 한 줄 요약

이 스킬은 메르식 매크로 리포트를
**자동 생성하고, 설명하고, 보내고, 다른 에이전트에도 붙일 수 있게 만드는 운영 스킬**이다.
