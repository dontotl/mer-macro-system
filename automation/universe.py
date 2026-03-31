from __future__ import annotations

from typing import Dict, List


MANUAL_UNIVERSE: Dict[str, str] = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "012330": "현대모비스",
    "068270": "셀트리온",
    "105560": "KB금융",
    "055550": "신한지주",
    "051910": "LG화학",
    "006400": "삼성SDI",
    "207940": "삼성바이오로직스",
    "096770": "SK이노베이션",
    "066570": "LG전자",
    "035720": "카카오",
    "028260": "삼성물산",
    "034730": "SK",
    "086790": "하나금융지주",
    "323410": "카카오뱅크",
    "000270": "기아",
    "036570": "엔씨소프트",
}

MANUAL_MARKET_CAP: Dict[str, int] = {ticker: 1_500_000_000_000 for ticker in MANUAL_UNIVERSE}


def get_manual_universe() -> List[str]:
    return list(MANUAL_UNIVERSE.keys())
