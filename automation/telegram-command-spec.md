# 텔레그램 명령 / 상태관리 상세 설계

작성일: 2026-04-01

## 1. 목표
텔레그램에서 간단한 명령으로 현재 보유종목, 신규 진입 후보, 체결 반영 상태를 관리한다.
실제 주문은 사용자가 MTS에서 수행한다.

## 2. 상태 파일
파일: `automation/state/portfolio_state.json`

### 필드
- `asOf`: 마지막 업데이트 일시
- `totalUnits`: 총 유닛 수 (기본 5)
- `usedUnits`: 사용 중 유닛 수
- `cashUnits`: 남은 유닛 수
- `positions`: 보유 종목 배열

### position 예시
```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "unitsHeld": 2,
  "initialEntry": 112000,
  "add1": 121000,
  "add2": null,
  "lastUnitEntry": 121000,
  "stopPrice": 111320,
  "ma20": 118500,
  "note": "turnover+RS10"
}
```

## 3. 명령 구조
### /holding
현재 보유 종목과 남은 유닛 표시

예시 응답:
- [보유현황]
- 사용 유닛: 3 / 5
- 남은 유닛: 2
- 삼성전자 / 2유닛 / 최초 112000 / 추가1 121000 / 손절 111320
- SK하이닉스 / 1유닛 / 최초 640000 / 손절 588800

### /signal
오늘 종가 기준 신규 진입 후보 요약

예시 응답:
- [오늘 신규진입 후보]
- 삼성전자 / RS 상위 10% / 3개월 신고가 / 거래대금 급증 양봉
- HD현대일렉트릭 / RS 상위 10% / 정배열

### /close
오늘 종가 기준 매도 신호

예시 응답:
- [매도신호]
- NAVER / 20일선 이탈 / 전량매도 검토
- 카카오 / 마지막 유닛 기준 -8% / 전량매도 검토

### /filled buy <ticker> <price>
최초 진입 반영
예:
- `/filled buy 005930 112000`

동작:
- positions에 종목 추가
- unitsHeld = 1
- initialEntry = price
- lastUnitEntry = price
- stopPrice = price * 0.92

### /filled add <ticker> <price>
추매 반영
예:
- `/filled add 005930 121000`

동작:
- unitsHeld += 1
- add1 또는 add2 갱신
- lastUnitEntry = price
- stopPrice = price * 0.92

### /filled sell <ticker> <price>
전량매도 반영
예:
- `/filled sell 005930 118500`

동작:
- positions에서 종목 제거
- usedUnits / cashUnits 재계산

## 4. 유닛 계산 규칙
- 기본 총 유닛 = 5
- 종목당 최대 3유닛
- state 저장 시:
  - `usedUnits = sum(position.unitsHeld)`
  - `cashUnits = totalUnits - usedUnits`

## 5. stopPrice 계산 규칙
- 1유닛 보유: initialEntry * 0.92
- 2유닛 보유: add1 * 0.92
- 3유닛 보유: add2 * 0.92

## 6. 구현 우선순위
1. state 파일 로더/세이버
2. /holding 렌더러
3. /filled buy|add|sell 반영기
4. /signal /close 리포터

## 7. 주의사항
- 체결 반영은 사용자가 직접 수행해야 함
- state 파일은 단일 진실원본(single source of truth)으로 사용
- 여러 기기/세션에서 동시에 수정 시 충돌 방지 필요
