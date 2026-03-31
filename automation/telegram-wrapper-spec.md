# 텔레그램 명령 연결용 Wrapper 설계

작성일: 2026-04-01

## 목표
텔레그램 메시지 명령을 `automation/holding.py`, `automation/filled.py` 등의 로컬 스크립트에 연결해 상태관리와 조회를 쉽게 한다.

## 명령 매핑
- `/holding` -> `python3 -m automation.holding`
- `/filled buy <ticker> <price> [name]` -> `python3 -m automation.filled buy <ticker> <price> --name <name>`
- `/filled add <ticker> <price>` -> `python3 -m automation.filled add <ticker> <price>`
- `/filled sell <ticker>` -> `python3 -m automation.filled sell <ticker>`

## 입력 파서 규칙
- 공백 단위 split
- ticker는 6자리 문자열로 정규화
- price는 float 변환
- 종목명은 buy 명령에서 optional

## 에러 처리
- 필수 인자 누락 -> 사용 예시 반환
- 존재하지 않는 ticker -> 에러 메시지 반환
- 3유닛 초과 add -> 에러 메시지 반환
- 이미 보유 중 buy -> 에러 메시지 반환

## 응답 포맷
### 성공
- [체결반영 완료]
- 삼성전자(005930) / 2유닛
- 마지막 유닛 기준 손절가: 111320

### 실패
- [체결반영 실패]
- 사유: 이미 보유 중인 종목
- 예시: /filled add 005930 121000

## 구현 권장
- 얇은 wrapper 함수 1개
- 내부에서 subprocess 또는 직접 함수 호출
- 최종 출력은 텔레그램용 텍스트로 반환
