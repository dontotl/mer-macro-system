# PRD - 메르 데일리 매크로 노트

- 작성일: 2026-04-23
- 상태: in-progress (v1 자동연결 구현 완료)
- 목적: 메르 블로그에서 추출한 핵심 지표를 매일 Markdown 노트로 기록하고, 숫자 변화와 매크로 해석을 함께 누적하는 운영 체계를 만든다.

## 1. 왜 대시보드보다 데일리 노트인가

기존 구상은 지표를 바로 수집해 대시보드로 보는 방식이었다. 하지만 메르식 해석의 핵심은 단순 시각화보다:

- 숫자의 절대 수준
- 직전 대비 변화
- 임계값 통과 여부
- 정책/유동성/스트레스 맥락 해석

이 네 가지를 함께 읽는 데 있다.

따라서 1단계는 대시보드보다 **데일리 Markdown 노트**를 중심으로 설계한다.

대시보드는 2단계 산출물이다.

---

## 2. 핵심 목표

1. 매일 핵심 매크로 지표를 자동 수집한다.
2. 전일/전주/전월 대비 변화를 계산한다.
3. 메르식 해석 규칙으로 상태를 분류한다.
4. 결과를 날짜별 Markdown 파일로 저장한다.
5. 노트가 누적되면 이후 대시보드/알림/백테스트로 확장한다.

---

## 3. 산출물

### 필수
- `automation/mer-daily-macro-note-prd.md`
- `automation/mer_daily_macro_note.py`
- `invest/notes/daily-macro/YYYY-MM-DD.md`

### 선택
- `automation/data/macro/*.parquet`
- `automation/data/macro/*.csv`
- `invest/notes/daily-macro/_index.md`

---

## 4. 1차 대상 모듈

### 4.1 Liquidity Composite (최우선)
핵심 지표:
- TGA
- RRP
- 지급준비금 (Reserve Balances)
- Repo usage (가능 시)
- 연준 총자산 또는 정책 이벤트 보조축

메르식 핵심 해석:
- TGA 증가 = 민간 유동성 흡수
- TGA 감소 = 재정지출 경유 유동성 완화
- RRP 감소 = 유동성 완충 작동
- RRP 고갈 = 이후 충격 완충 약화
- 지급준비금 3조 달러 하회 = 스트레스 경계선
- 레포 급증 = 배관 막힘 신호

### 4.2 Stress Early Warning
초기 후보:
- 보험 해약률 / 효력상실 해지율
- 신용스프레드/HY OAS (대체 또는 병행)
- 은행/단기자금시장 스트레스 보조지표

### 4.3 Inflation Policy Lens
초기 후보:
- CPI
- Core CPI
- PCE
- Core PCE
- 기대인플레이션 또는 유가 보조지표

### 4.4 Money Scale
초기 후보:
- M2
- GDP
- M2/GDP

### 4.5 Policy Sequence Tracker
초기 후보:
- QT 진행 여부
- RMP/QE성 오퍼레이션
- 금리인하 기대가 아니라 실제 정책 코멘트 변화

---

## 5. 필수 출력 규칙

모든 데일리 Markdown 노트는 아래 규칙을 항상 만족해야 한다.

### 5.1 표 형식 우선
각 모듈은 반드시 **표(table)** 로 시작한다.
표에는 최소 아래 열이 포함되어야 한다.
- 지표
- 값
- 변화
- 메르 해석 포인트
- 현재 판정
- 데이터 출처
- 기준일

### 5.2 숫자와 설명 동시 제공
각 모듈은 반드시 아래 순서를 따른다.
1. 수치 표
2. 메르식 해석
3. 지금 상태

### 5.3 메르식 해석 분리
단순 숫자 해석이 아니라, **메르가 이 지표를 왜 중요하게 보는지**를 따로 적는다.
예:
- TGA 감소는 왜 완화로 보는가
- RRP 바닥은 왜 취약한 완충재 소진으로 보는가
- CPI와 PCE를 왜 다르게 읽는가

### 5.4 현재 상태 명시
각 모듈 마지막에는 반드시 **지금 상태**를 한두 줄로 쓴다.
예:
- "지금은 완화지만 취약한 완화"
- "지금은 인플레 둔화라기보다 재가속 경계"
- "지금은 즉시 위기보다 잠재 스트레스 누적 구간"

### 5.5 데이터 출처와 추출 일자 명시
노트 상단 또는 각 표 내부에 반드시 아래 정보를 남긴다.
- 데이터 출처
- 데이터 기준일(as-of)
- 추출일/생성일(extracted at)

### 5.6 미연결 데이터도 숨기지 않기
아직 자동 연결되지 않은 지표는 비워두지 않고 아래처럼 표시한다.
- 값: `미연결`
- 현재 판정: `보류`
- 데이터 출처: `연결 예정`

---

## 6. 운영 원칙

### 6.1 숫자 나열 금지
노트는 단순 데이터 덤프가 아니라 아래 4요소를 반드시 포함한다.
- 숫자
- 변화
- 해석
- 상태 레이블

### 6.2 상태 분류 우선
처음부터 예측모델을 만들지 않는다.
먼저 상태 분류기를 만든다.

예:
- Liquidity: 확장 / 중립 / 축소 / 경계적 완화
- Stress: 안정 / 경계 / 위험
- Inflation: 둔화 / 정체 / 재가속
- Policy: 완화적 / 대기 / 긴축적

### 6.3 메르식 문장 생성
숫자만 보여주지 않고, 규칙 기반 해석 문장을 함께 만든다.

예:
- "TGA가 주간 기준 큰 폭 감소해 단기 유동성 완화 압력이 생겼다."
- "RRP 잔고가 낮은 상태라 이후 충격 완충력은 예전보다 제한적이다."
- "지급준비금이 3조 달러 경계선 아래면 QT 지속 가능성보다 스트레스 관리가 더 중요해진다."

---

## 7. Markdown 출력 포맷 v2

예시 경로:
- `invest/notes/daily-macro/2026-04-23.md`

핵심 구조:
1. Summary 표
2. 모듈별 수치 표
3. 메르식 해석
4. 지금 상태
5. Final Take

---

## 8. 1차 로직 설계

### 8.1 Liquidity 룰 초안
- TGA WoW < 0 이면 완화 점수 +1
- RRP WoW < 0 이면 완화 점수 +1
- Reserve Balances < 3.0T 이면 스트레스 점수 +2
- Repo usage 급증 시 스트레스 점수 +2
- 합산 점수로 `확장 / 중립 / 축소 / 경계완화` 구간 분류

### 8.2 Inflation 룰 초안
- Core PCE YoY 하락 추세면 둔화 점수 +1
- Core CPI는 시장 반응용 보조축
- CPI 둔화 + Core PCE 정체면 `시장완화/정책경계` 태그

### 8.3 Stress 룰 초안
- 보험 해약률 상승 추세면 가계 스트레스 경보
- 단기 구현이 어렵다면 HY OAS 등 대체 지표로 임시 시작

---

## 9. 구현 단계

### 단계 1. 문서 중심 PoC
- 템플릿 설계
- 수동/반자동으로 1~3일치 작성
- 해석 문장 품질 확인

### 단계 2. 자동 생성
- 데이터 수집 스크립트 작성
- 규칙 기반 해석 자동 생성
- Markdown 파일 자동 저장

### 단계 3. 운영화
- 매일 특정 시각 cron 실행
- 필요시 Telegram/Signal 전달
- 누적 노트 인덱스 생성

### 단계 4. 대시보드화
- 자주 보는 지표만 차트화
- 이미 검증된 규칙만 위젯화

---

## 10. 지금 바로 할 일

1. Liquidity Composite용 입력 데이터 소스 확정
2. Daily Macro Note 템플릿 고정
3. 해석 규칙 초안 작성
4. 1호 파일 샘플 생성
5. 자동 생성 스크립트에 출력 규칙 강제 적용

---

## 11. 제니 메모
이 프로젝트의 핵심은 예쁜 화면이 아니라,
**메르의 숫자 읽는 방식을 매일 재현 가능한 문서 시스템으로 바꾸는 것**이다.

---

## 12. Telegram 전송형 메시지 포맷 v1

목표: 표 중심 노트를 그대로 보내지 않고, 모바일에서 15초 내 핵심을 읽을 수 있는 요약 포맷을 고정한다.

필수 블록(순서 고정):
1. 제목: `📌 메르 데일리 매크로 (YYYY-MM-DD)`
2. 한줄 결론 3개 (Liquidity / Inflation / Stress·Policy)
3. 핵심 수치 4개 (TGA / RRP / Reserve / Core PCE)
4. 판정 메모 2줄
5. 차트 경로 1줄 + 생성시각 + 태그

형식 원칙:
- 표 금지, 불릿만 사용
- 한 줄 55자 내외 유지
- 숫자는 원본 노트와 동일값 사용
- 차트가 없으면 `생성 실패(환경 확인 필요)`로 명시

---

## 13. Liquidity 차트 생성 구조 v1

산출물:
- 경로: `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`
- 패널: 3단( TGA / RRP / Reserve )

데이터:
- TGA: `WTREGEN` (FRED)
- RRP: `RRPONTSYD` (FRED)
- Reserve Balances: `WRESBAL` (FRED)
- 기본 표시 구간: 최근 180개 관측치

구현 원칙:
- 데이터 수집은 CSV 직접 파싱(의존성 최소화)
- 차트 라이브러리(`matplotlib`) 없으면 노트/텔레그램은 계속 생성하고 차트만 스킵
- Reserve 패널에 3,000bn(=3T) 경계선 표시

---

## 14. 미구현 지표 우선 연결 계획 (CPI/Core CPI/PCE/HY OAS/M2/GDP/Repo)

우선순위(추천):
1. **HY OAS**: Stress 대체축으로 즉시 연결 가능 (FRED `BAMLH0A0HYM2`)
2. **CPI / Core CPI / PCE**: Inflation 세트 완성 (FRED `CPIAUCSL`, `CPILFESL`, `PCEPI`)
3. **M2 / GDP / M2-GDP**: 구조적 스케일 축 완성 (FRED `M2SL`, `GDP` + 파생계산)
4. **Repo**: 최종 난이도 높음 (NY Fed API/오퍼레이션 데이터 정합 필요)

연결 난이도 메모:
- CPI/Core CPI/PCE/M2/GDP/HY OAS: FRED 직결 가능, 단기 구현 적합
- Repo: FRED 대체 시리즈만으로는 메르식 '배관막힘' 포착이 약해 NY Fed 원천 접근 권장

다음 구현 순서 제안:
1) HY OAS 먼저 연결해 Stress 모듈 즉시 활성화
2) CPI/Core CPI/PCE 동시 연결로 Inflation 판정 정확도 개선
3) M2/GDP 파생 지표 추가해 Money Scale 판정 개시
4) Repo는 별도 수집기(원천 API/파일)로 분리 구축

---

## 15. 구현 현황 업데이트 (2026-04-23)

완료:
- `automation/mer_daily_macro_note.py`에 아래 FRED 자동연결 반영
  - HY OAS (`BAMLH0A0HYM2`)
  - CPI (`CPIAUCSL`), Core CPI (`CPILFESL`), PCE (`PCEPI`), Core PCE (`PCEPILFE`)
  - M2 (`M2SL`), GDP (`GDP`), 파생 M2/GDP
- Liquidity 차트 PNG 생성 동작 확인
- Telegram 전송형 텍스트 + 차트 이미지 전송 테스트 성공 (`openclaw message send`)

실행 명령:
```bash
./.venv-mer-dashboard/bin/python automation/mer_daily_macro_note.py --date 2026-04-23
./.venv-mer-dashboard/bin/python automation/mer_daily_macro_note.py --date 2026-04-23 --send-telegram-test --telegram-target 5294188460 --message-channel telegram
```

검증 산출물:
- `invest/notes/daily-macro/2026-04-23.md`
- `invest/notes/daily-macro/2026-04-23.telegram.txt`
- `invest/notes/daily-macro/charts/2026-04-23-liquidity.png`

---

## 16. 최종 패키지 업데이트 (2026-04-23, v1.1)

추가 완료:
- Repo 요약 자동화 연결
  - SOFR (`SOFR`), EFFR (`DFF`), SOFR-EFFR spread 파생 계산
  - Daily note Summary 및 `Repo Summary` 섹션 반영
- Policy 요약 자동화 연결
  - Fed Target Upper/Lower (`DFEDTARU`, `DFEDTARL`), WALCL (`WALCL`)
  - `Policy Sequence Tracker`/`Policy Summary` 섹션 반영
- 주간 요약 생성 기능 추가
  - Daily 스크립트에 `--weekly` 옵션 추가
  - 산출물:
    - `invest/notes/daily-macro/weekly/YYYY-Www.md`
    - `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`

테스트 실행:
```bash
./.venv-mer-dashboard/bin/python automation/mer_daily_macro_note.py --date 2026-04-23 --weekly
```

확인 산출물:
- `invest/notes/daily-macro/2026-04-23.md`
- `invest/notes/daily-macro/2026-04-23.telegram.txt`
- `invest/notes/daily-macro/charts/2026-04-23-liquidity.png`
- `invest/notes/daily-macro/weekly/2026-W17.md`
- `invest/notes/daily-macro/weekly/2026-W17.telegram.txt`
