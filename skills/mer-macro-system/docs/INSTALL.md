# INSTALL

## 1) 가상환경 준비
- 기본 경로: `./.venv-mer-dashboard/bin/python`
- 필요한 패키지(최소): `matplotlib` (없으면 차트만 스킵)

## 2) 스크립트 위치
- 생성기 본체: `automation/mer_daily_macro_note.py`
- skill 실행 래퍼: `skills/mer-macro-system/scripts/run_mer_macro_reports.py`

## 3) 보안
- 토큰/키는 환경변수로만 사용
- `.env`, `.env.*`, `secrets/`, `*token*` 파일은 git ignore 유지
