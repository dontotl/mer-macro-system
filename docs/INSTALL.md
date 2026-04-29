# INSTALL

이 문서는 `mer-macro-system` 스킬을 설치하고 실제로 실행 가능한 상태로 만드는 방법을 설명합니다.

---

## 1. 기본 전제

이 스킬은 OpenClaw 워크스페이스 기준으로 아래 구조를 전제로 합니다.

- 워크스페이스 루트: `~/.openclaw/workspace`
- 주요 생성기:
  - `automation/mer_daily_macro_note.py`
- 스킬 실행 래퍼:
  - `scripts/run_mer_macro_reports.py`

---

## 2. Python 환경

권장 Python 실행 경로:

```bash
./.venv-mer-dashboard/bin/python
```

이유:
- 기존 매크로/백테스트/시그널 자동화와 같은 운영 환경 공유
- pandas/matplotlib 등 의존성 관리 일관성 유지

### 권장 확인
```bash
./.venv-mer-dashboard/bin/python --version
```

---

## 3. 필수/권장 패키지

### 최소 동작
- 표 기반 md 리포트 생성
- 텔레그램용 txt 생성
- 주요 FRED 시리즈 수집

### 권장 패키지
- `matplotlib`
  - 차트 PNG 생성용

설치 예시:
```bash
./.venv-mer-dashboard/bin/pip install matplotlib
```

확인 예시:
```bash
./.venv-mer-dashboard/bin/python -c "import matplotlib; print(matplotlib.__version__)"
```

---

## 4. Git/GitHub 운영

이 스킬은 결과물과 코드가 함께 관리되므로, 아래를 권장합니다.

### 권장 사항
- git 저장소에서 운영
- GitHub 원격 저장소 연결
- 토큰은 파일이 아니라 환경변수 또는 `gh auth login`으로 관리

### 절대 하지 말 것
- PAT를 채팅에 남기기
- `.env` 파일을 그대로 커밋하기
- 토큰 문자열을 문서/스크립트에 하드코딩하기

---

## 5. .gitignore 보안 규칙

다음 항목은 반드시 git ignore 상태를 유지하세요.

- `.env`
- `.env.*`
- `*.env`
- `*token*`
- `*secret*`
- `secrets/`

즉, 인증정보는 항상 **환경변수/키체인/gh 인증 저장소**로만 다루는 것이 좋습니다.

---

## 6. OpenClaw와 연결

이 스킬은 OpenClaw에서 아래 방식으로 연결할 수 있습니다.

### 직접 실행
```bash
./.venv-mer-dashboard/bin/python scripts/run_mer_macro_reports.py --date 2026-04-23
```

### 일간 + 주간 동시 생성
```bash
./.venv-mer-dashboard/bin/python scripts/run_mer_macro_reports.py --date 2026-04-23 --weekly
```

### 텔레그램 테스트 포함
```bash
./.venv-mer-dashboard/bin/python scripts/run_mer_macro_reports.py \
  --date 2026-04-23 \
  --weekly \
  --send-telegram-test \
  --telegram-target 5294188460
```

---

## 7. 설치 후 확인 체크리스트

설치가 끝나면 아래를 확인하세요.

### 필수 확인
1. md 파일 생성됨
2. telegram txt 생성됨
3. 차트 png 생성됨
4. 내용에 표/메르 설명/현재 상태 포함됨

### 확인 경로
- `invest/notes/daily-macro/YYYY-MM-DD.md`
- `invest/notes/daily-macro/YYYY-MM-DD.telegram.txt`
- `invest/notes/daily-macro/charts/YYYY-MM-DD-liquidity.png`
- `invest/notes/daily-macro/weekly/YYYY-Www.md`
- `invest/notes/daily-macro/weekly/YYYY-Www.telegram.txt`

---

## 8. 자동화 추천

권장 운영 방식:
- 매일 오전 8시: 일간 리포트 + 텔레그램 발송
- 주말 또는 월요일 아침: 주간 요약 생성/전송

즉, 이 스킬은 단발 실행보다는 **정기 자동화**로 붙였을 때 가치가 커집니다.

---

## 9. 설치 한 줄 요약

- Python 환경 준비
- `matplotlib` 설치
- 보안 파일 git 제외
- 스크립트 실행 확인
- 텔레그램 전송 확인
- 크론 연결

이렇게 하면 운영 가능한 상태입니다.
