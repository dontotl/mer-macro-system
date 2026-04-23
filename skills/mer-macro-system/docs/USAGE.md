# USAGE

이 문서는 `mer-macro-system` 스킬을 실제로 어떻게 활용하면 좋은지 설명합니다.

---

## 1. 이 스킬을 언제 쓰면 좋은가

아래 같은 요청에 잘 맞습니다.

- 메르 블로그식 매크로 요약을 자동으로 받고 싶다
- 아침마다 매크로 상황을 짧게 브리핑 받고 싶다
- 텔레그램으로 차트까지 같이 받고 싶다
- 일간/주간 리포트를 축적하고 싶다
- 다른 에이전트에서도 같은 방식으로 쓰고 싶다

즉, 이 스킬은 **매크로 데이터 수집 도구**라기보다
**메르식 해석 운영 체계**로 쓰는 게 가장 좋습니다.

---

## 2. 기본 사용법

### 일간 리포트 생성
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date 2026-04-23
```

### 일간 + 주간 동시 생성
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py --date 2026-04-23 --weekly
```

### 텔레그램 테스트 전송 포함
```bash
./.venv-mer-dashboard/bin/python skills/mer-macro-system/scripts/run_mer_macro_reports.py \
  --date 2026-04-23 \
  --weekly \
  --send-telegram-test \
  --telegram-target 5294188460
```

---

## 3. 생성되는 결과물

### 일간 결과물
- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`

### 주간 결과물
- `invest/notes/daily-macro/weekly/YYYY-Www.md`
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`

---

## 4. 리포트는 어떻게 읽으면 되나

### Summary
가장 먼저 보는 곳입니다.
- Liquidity
- Stress
- Inflation
- Money Scale
- Policy
를 한 줄로 요약합니다.

### 수치 표
각 모듈마다 아래가 들어갑니다.
- 값
- 변화
- 메르 해석 포인트
- 현재 판정
- 데이터 출처
- 기준일

즉, 단순 숫자만 보여주는 것이 아니라
**“왜 중요한가”까지 같이 보게 만든 구조**입니다.

### 메르의 설명
이 부분은 단순 데이터 설명이 아니라,
**메르가 이 지표를 왜 중요하게 보는지**를 정리한 부분입니다.

### 지금 상태
오늘 시점에서 시장을 어떻게 읽어야 하는지,
쉽게 풀어 쓴 결론입니다.

---

## 5. 추천 운영 시나리오

### 시나리오 A. 개인 아침 브리핑
- 매일 오전 8시 자동 발송
- 텔레그램에서 한줄 결론 + 핵심 수치 확인
- 필요하면 md 원문 열람

### 시나리오 B. 리서치 노트 축적
- 매일 md 파일 누적
- 나중에 특정 시기(예: 급락 전후)만 모아서 비교
- 전략 판단 기록과 연결

### 시나리오 C. 팀/다중 에이전트 운영
- 같은 스킬을 다른 에이전트에도 붙여서 사용
- 사람이 바뀌어도 같은 포맷으로 리포트 생성 가능

### 시나리오 D. 대시보드 전 단계
- 먼저 md/telegram 체계로 실제 유용성 검증
- 살아남는 지표만 나중에 대시보드로 확장

---

## 6. 다른 에이전트에 붙이는 방법

이 스킬은 단순 문서가 아니라 **재사용 가능한 운영 단위**입니다.

다른 에이전트에 붙일 때는 보통 아래 흐름으로 갑니다.

1. `skills/mer-macro-system/` 폴더 복사 또는 배포
2. `SKILL.md` 기준으로 트리거 연결
3. 래퍼 스크립트 실행
4. 결과물 확인
5. 텔레그램/메신저 자동 발송 연결

즉, 이 스킬 하나로 다른 에이전트도 같은 리포트 체계를 바로 쓸 수 있게 됩니다.

---

## 7. 활용 팁

### 팁 1. 한줄 결론은 쉽게
한줄 결론은 경제를 잘 모르는 사람도 읽히게 두고,
아래 본문에서 메르식 해석을 깊게 설명하는 구조가 좋습니다.

### 팁 2. 차트는 과하지 않게
너무 많은 차트보다,
- Liquidity
- Inflation
- Stress
핵심 1~3장만 유지하는 것이 읽기 좋습니다.

### 팁 3. Telegram은 짧게
모바일에서는 긴 표보다
- 한줄 결론
- 핵심 수치
- 판정 메모
- 차트 1장
구성이 제일 잘 읽힙니다.

### 팁 4. 주간 요약은 맥락용
데일리는 체크용,
주간은 방향성/맥락 해석용으로 쓰는 것이 좋습니다.

---

## 8. 추천 발전 방향

이 스킬은 앞으로 아래 식으로 확장할 수 있습니다.

1. Repo 세부 데이터 고도화
2. Policy 이벤트 자동 감지 강화
3. Inflation 차트 추가
4. Stress 보조지표 확대
5. 월간/분기 요약 추가
6. 전략/자산배분 코멘트 연동

---

## 9. 한 줄 요약

이 스킬은 메르식 매크로 해석을
**매일 읽고, 기록하고, 보내고, 다른 에이전트에도 붙일 수 있게 만든 운영 도구**입니다.
