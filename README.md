# mer-macro-system

메르 블로그식 매크로 해석 프레임을 바탕으로, **일간/주간 매크로 리포트, 텔레그램 전송용 요약문, 유동성 차트 이미지**를 자동 생성하는 OpenClaw용 스킬입니다.

이 스킬의 목적은 단순히 숫자를 수집하는 것이 아니라, 아래 흐름을 하나의 운영 체계로 묶는 것입니다.

- 핵심 거시지표 자동 수집
- 메르식 경제적 의미 부여
- Markdown 리포트 생성
- 텔레그램 전송용 짧은 요약 생성
- 차트 이미지 생성
- OpenClaw 자동화/크론 연결

---

## 이 스킬이 해결하는 문제

기존에는 메르 블로그에서 중요하게 보는 지표를 사람이 직접 확인하고, 따로 해석하고, 따로 메신저로 옮겨야 했습니다.

이 스킬은 그 과정을 다음처럼 줄여줍니다.

1. 지표 수집
2. 상태 판정
3. 메르식 해석 문장 생성
4. 일간/주간 리포트 저장
5. 텔레그램 전송용 요약 생성
6. 차트 첨부까지 자동화

즉, **숫자 수집 도구**가 아니라 **메르식 매크로 운영 시스템**에 가깝습니다.

---

## 현재 포함된 주요 기능

### 1) 일간 리포트
생성 파일:
- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`

포함 내용:
- Summary 표
- Liquidity / Stress / Inflation / Money Scale / Policy 요약
- 메르의 설명
- 지금 상태
- Final Take

### 2) 주간 리포트
생성 파일:
- `invest/notes/daily-macro/weekly/YYYY-Www.md`
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`

포함 내용:
- 한 주 동안 핵심 변화
- 메르식 주간 해석
- 다음 주 체크포인트

### 3) 차트 이미지
현재 지원:
- Liquidity 차트
  - TGA
  - RRP
  - Reserve Balances
  - 3조 달러 기준선 표시

생성 파일:
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`

### 4) 텔레그램 전송 포맷
모바일에서 읽기 쉽게:
- 한줄 결론
- 핵심 수치
- 판정 메모
- 차트 경로

---

## 현재 연결된 주요 지표

### Liquidity
- TGA (`WTREGEN`)
- RRP (`RRPONTSYD`)
- Reserve Balances (`WRESBAL`)

### Stress
- HY OAS (`BAMLH0A0HYM2`)

### Inflation
- CPI (`CPIAUCSL`)
- Core CPI (`CPILFESL`)
- PCE (`PCEPI`)
- Core PCE (`PCEPILFE`)

### Money Scale
- M2 (`M2SL`)
- GDP (`GDP`)
- M2/GDP (파생 계산)

### Repo / Policy
- Repo 축:
  - SOFR
  - EFFR/DFF
  - SOFR-EFFR spread
- Policy 축:
  - `DFEDTARU`
  - `DFEDTARL`
  - `WALCL`

---

## 누구에게 유용한가

이 스킬은 특히 아래 경우에 잘 맞습니다.

- 메르 블로그식 매크로 프레임을 운영에 붙이고 싶은 사람
- 매일 아침 매크로 숫자를 빠르게 보고 싶은 사람
- 차트와 해석을 함께 텔레그램으로 받고 싶은 사람
- OpenClaw를 이용해 리포트 자동화까지 연결하고 싶은 사람
- 다른 에이전트에도 같은 매크로 프레임을 재사용하고 싶은 사람

---

## 사용 구조

실제 운영은 보통 아래처럼 갑니다.

### 일간 운영
1. 아침에 스크립트 실행
2. Markdown 리포트 생성
3. Telegram 요약 생성
4. 차트 생성
5. 필요 시 자동 전송

### 주간 운영
1. 주간 옵션 포함 실행
2. 주간 리포트 생성
3. 주간 요약 메시지 생성
4. 다음 주 체크포인트 정리

---

## 권장 활용 방식

### 활용안 1: 개인 매크로 브리핑
- 매일 오전 8시 텔레그램 발송
- 핵심 수치와 한줄 해석만 빠르게 확인

### 활용안 2: 리서치 기록 축적
- `invest/notes/daily-macro/` 아래 md 파일 누적
- 나중에 특정 시기 회고나 전략 판단에 활용

### 활용안 3: 에이전트 공통 스킬
- 다른 OpenClaw 에이전트에도 같은 스킬 적용
- 같은 규칙/같은 포맷으로 리포트 생성 가능

### 활용안 4: 대시보드 전 단계
- 먼저 md/telegram 방식으로 운영
- 충분히 검증된 뒤 시각 대시보드로 확장

---

## 관련 문서
더 자세한 설치와 운영은 아래 문서를 보세요.

- 설치: `docs/INSTALL.md`
- 활용: `docs/USAGE.md`

---

## 한 줄 요약
이 스킬은 메르식 매크로 해석을
**수집 → 해석 → 리포트 → 텔레그램 → 차트**
까지 이어주는 운영 패키지입니다.
