from __future__ import annotations

import argparse
import csv
import io
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

OUT_DIR = Path('invest/notes/daily-macro')
CHART_DIR = OUT_DIR / 'charts'
WEEKLY_DIR = OUT_DIR / 'weekly'
FRED_CSV = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}'


@dataclass
class SeriesPoint:
    value: Optional[float]
    asof_date: str
    source: str


def _to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _read_fred_series(series_id: str) -> list[tuple[datetime, float]]:
    url = FRED_CSV.format(series_id=series_id)
    with urlopen(url, timeout=30) as res:
        raw = res.read().decode('utf-8', errors='ignore')

    reader = csv.DictReader(io.StringIO(raw))
    rows: list[tuple[datetime, float]] = []
    for row in reader:
        date_raw = row.get('DATE') or row.get('observation_date')
        value_raw = row.get(series_id)
        if not date_raw or value_raw is None:
            continue
        val = _to_float(value_raw)
        if val is None:
            continue
        try:
            d = datetime.strptime(date_raw, '%Y-%m-%d')
        except Exception:
            continue
        rows.append((d, val))
    rows.sort(key=lambda x: x[0])
    return rows


def fetch_fred_last_two(series_id: str) -> tuple[SeriesPoint, SeriesPoint | None]:
    rows = _read_fred_series(series_id)
    if not rows:
        return SeriesPoint(None, 'unknown', f'FRED {series_id}'), None
    last = rows[-1]
    prev = rows[-2] if len(rows) >= 2 else None
    last_point = SeriesPoint(last[1], str(last[0].date()), f'FRED {series_id}')
    prev_point = SeriesPoint(prev[1], str(prev[0].date()), f'FRED {series_id}') if prev is not None else None
    return last_point, prev_point


def fmt_num(v: Optional[float], digits: int = 3) -> str:
    if v is None:
        return '미연결'
    return f'{v:.{digits}f}'


def fmt_change(curr: Optional[float], prev: Optional[float], digits: int = 3) -> str:
    if curr is None or prev is None:
        return '미연결'
    diff = curr - prev
    sign = '+' if diff > 0 else ''
    return f'{sign}{diff:.{digits}f}'


def liquidity_regime(rrp: Optional[float], reserve_bal: Optional[float], tga_change: Optional[float]) -> tuple[str, str]:
    if rrp is None and reserve_bal is None:
        return '보류', '유동성 핵심 데이터가 아직 충분히 연결되지 않았습니다.'
    if reserve_bal is not None and reserve_bal < 3000:
        return '경계', '지급준비금 3조 달러 하회로 배관 스트레스 경계가 우선입니다.'
    if rrp is not None and rrp < 10:
        return '경계적 완화', 'RRP가 바닥권이라 완충재는 거의 소진됐지만, 표면상 완화 요소는 남아 있습니다.'
    if tga_change is not None and tga_change < 0:
        return '완화', 'TGA 감소로 단기 유동성 완화 압력이 우세합니다.'
    return '중립', '유동성은 중립 수준으로 보입니다.'


def stress_regime(hy_oas: Optional[float], hy_oas_change: Optional[float]) -> tuple[str, str]:
    if hy_oas is None:
        return '보류', 'HY OAS 데이터 연결 상태를 확인 중입니다.'
    if hy_oas >= 6.0:
        return '위험', 'HY OAS가 600bp 이상으로 신용 스트레스가 높은 구간입니다.'
    if hy_oas >= 4.5 or (hy_oas_change is not None and hy_oas_change > 0.20):
        return '경계', 'HY OAS 확대로 리스크 프리미엄이 빠르게 올라오는 구간입니다.'
    return '안정', 'HY OAS 기준 신용 스트레스는 아직 안정 구간입니다.'


def inflation_regime(core_pce_change: Optional[float], cpi_change: Optional[float]) -> tuple[str, str]:
    if core_pce_change is None:
        return '보류', 'Core PCE 추세가 더 쌓여야 정책 해석 신뢰도가 높아집니다.'
    if core_pce_change > 0:
        return '재가속 경계', 'Core PCE가 재상승해 정책 완화 기대를 제약할 수 있습니다.'
    if cpi_change is not None and cpi_change > 0:
        return '정체', 'CPI 반등으로 시장 민감도가 커진 상태입니다.'
    return '둔화', 'Core PCE 중심으로 물가 둔화 흐름이 이어지는 구간입니다.'


def money_scale_regime(m2_to_gdp: Optional[float], ratio_change: Optional[float]) -> tuple[str, str]:
    if m2_to_gdp is None:
        return '보류', 'M2/GDP 계산 데이터 확인이 필요합니다.'
    if m2_to_gdp >= 0.90:
        return '확장', 'M2/GDP가 높은 편이라 유동성 스케일이 확장 구간입니다.'
    if ratio_change is not None and ratio_change < 0:
        return '축소', 'M2/GDP 하락세로 통화 스케일 축소가 진행 중입니다.'
    return '중립', 'M2/GDP 기준 통화 스케일은 중립 구간입니다.'


def repo_regime(sofr: Optional[float], effr: Optional[float], spread: Optional[float]) -> tuple[str, str]:
    if sofr is None or effr is None:
        return '보류', 'SOFR/EFFR 데이터 연결 상태를 확인 중입니다.'
    if spread is not None and spread > 0.20:
        return '경계', 'SOFR-EFFR 스프레드 확대는 단기 자금시장 긴장 신호일 수 있습니다.'
    if spread is not None and spread < -0.10:
        return '완화', 'SOFR가 EFFR 대비 낮아 단기 자금 조달은 상대적으로 안정적입니다.'
    return '중립', 'SOFR/EFFR 기준 단기 자금시장은 중립 흐름입니다.'


def policy_regime(ff_upper: Optional[float], ff_lower: Optional[float], walcl_change: Optional[float]) -> tuple[str, str]:
    if ff_upper is None or ff_lower is None:
        return '보류', '정책금리 타깃 범위 데이터 확인이 필요합니다.'
    if walcl_change is not None and walcl_change > 0:
        return '완화 전환 시그널', '연준 총자산이 증가해 QT 속도 조절 또는 유동성 보강 가능성을 시사합니다.'
    return '긴축 유지/대기', '정책금리 범위 유지와 대차대조표 추세상 완화 전환 신호는 제한적입니다.'


def build_liquidity_chart(today: str) -> Optional[Path]:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None

    CHART_DIR.mkdir(parents=True, exist_ok=True)

    tga_rows = _read_fred_series('WTREGEN')[-180:]
    rrp_rows = _read_fred_series('RRPONTSYD')[-180:]
    reserve_rows = _read_fred_series('WRESBAL')[-180:]

    tga_x = [d for d, _ in tga_rows]
    tga_y = [v / 1000.0 for _, v in tga_rows]
    rrp_x = [d for d, _ in rrp_rows]
    rrp_y = [v for _, v in rrp_rows]
    reserve_x = [d for d, _ in reserve_rows]
    reserve_y = [v / 1000.0 for _, v in reserve_rows]

    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(tga_x, tga_y, color='#0068c9', linewidth=1.8)
    axes[0].set_title('TGA (bn USD)')
    axes[0].grid(alpha=0.3)

    axes[1].plot(rrp_x, rrp_y, color='#16a34a', linewidth=1.8)
    axes[1].set_title('RRP (bn USD)')
    axes[1].grid(alpha=0.3)

    axes[2].plot(reserve_x, reserve_y, color='#dc2626', linewidth=1.8)
    axes[2].axhline(3000, color='gray', linestyle='--', linewidth=1.2, label='3,000 bn (3T)')
    axes[2].set_title('Reserve Balances (bn USD)')
    axes[2].grid(alpha=0.3)
    axes[2].legend(loc='best')

    fig.suptitle(f'Mer Liquidity Composite Snapshot ({today})')
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])

    out_path = CHART_DIR / f'{today}-liquidity.png'
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def build_telegram_message(
    *,
    today: str,
    extracted_at: str,
    liquidity_state: str,
    liquidity_line: str,
    inflation_state: str,
    stress_state: str,
    money_state: str,
    repo_state: str,
    policy_state: str,
    tga_last: SeriesPoint,
    tga_prev: SeriesPoint | None,
    rrp_last: SeriesPoint,
    rrp_prev: SeriesPoint | None,
    reserve_last: SeriesPoint,
    reserve_prev: SeriesPoint | None,
    core_pce_last: SeriesPoint,
    core_pce_prev: SeriesPoint | None,
    hy_oas_last: SeriesPoint,
    hy_oas_prev: SeriesPoint | None,
    sofr_last: SeriesPoint,
    sofr_prev: SeriesPoint | None,
    effr_last: SeriesPoint,
    effr_prev: SeriesPoint | None,
    ff_upper_last: SeriesPoint,
    ff_lower_last: SeriesPoint,
    walcl_last: SeriesPoint,
    walcl_prev: SeriesPoint | None,
    m2gdp_last: Optional[float],
    m2gdp_prev: Optional[float],
    chart_path: Optional[Path],
) -> str:
    chart_line = f'• 차트: {chart_path.as_posix()}' if chart_path else '• 차트: 생성 실패(환경 의존 패키지 확인 필요)'
    easy_line = '지금 시장은 완전히 안전하지는 않지만, 바로 크게 무너질 분위기도 아닙니다.'
    if liquidity_state in ('경계', '경계적 완화') and inflation_state in ('재가속 경계', '경계'):
        easy_line = '돈은 아직 좀 돌고 있지만, 물가가 다시 오를 수 있어서 주식시장이 흔들릴 수 있는 상태입니다.'
    elif stress_state == '위험':
        easy_line = '지금은 조심해야 하는 때입니다. 시장 불안 신호가 커져서 돈이 안전한 곳으로 피할 수 있습니다.'
    elif liquidity_state == '완화' and inflation_state == '둔화':
        easy_line = '지금은 시장에 비교적 좋은 환경입니다. 돈이 돌고 물가 부담도 덜해서 투자심리에 도움이 되는 편입니다.'

    return f'''📌 메르 데일리 매크로 ({today})

[한줄 결론]
• {easy_line}
• Liquidity: {liquidity_state} ({liquidity_line})
• Inflation: {inflation_state}
• Stress/Policy: {stress_state}·대기

[핵심 수치]
• TGA: {fmt_num(tga_last.value)} ({fmt_change(tga_last.value, tga_prev.value if tga_prev else None)})
• RRP: {fmt_num(rrp_last.value)} ({fmt_change(rrp_last.value, rrp_prev.value if rrp_prev else None)})
• Reserve: {fmt_num(reserve_last.value)} ({fmt_change(reserve_last.value, reserve_prev.value if reserve_prev else None)})
• Core PCE: {fmt_num(core_pce_last.value)} ({fmt_change(core_pce_last.value, core_pce_prev.value if core_pce_prev else None)})
• SOFR-EFFR: {fmt_change((sofr_last.value - effr_last.value) if (sofr_last.value is not None and effr_last.value is not None) else None, (sofr_prev.value - effr_prev.value) if (sofr_prev and effr_prev and sofr_prev.value is not None and effr_prev.value is not None) else None)}

[판정 메모]
• HY OAS: {fmt_num(hy_oas_last.value)} ({fmt_change(hy_oas_last.value, hy_oas_prev.value if hy_oas_prev else None)})
• M2/GDP: {fmt_num(m2gdp_last, 4)} ({fmt_change(m2gdp_last, m2gdp_prev, 4)}) → {money_state}
• Repo: {repo_state} / Policy: {policy_state}

{chart_line}
• 생성시각: {extracted_at}
• 태그: #macro_note_draft #mer_liquidity'''


def send_telegram_test(tg_text: str, chart_path: Optional[Path], target: str, channel: str = 'telegram') -> tuple[bool, str]:
    cmd = ['openclaw', 'message', 'send', '--channel', channel, '--target', target, '--message', tg_text]
    if chart_path and chart_path.exists():
        cmd += ['--media', str(chart_path)]
    cmd += ['--json']

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as e:
        return False, f'openclaw 실행 실패: {e}'

    if res.returncode == 0:
        return True, (res.stdout or '').strip() or 'ok'
    return False, f'code={res.returncode} stderr={(res.stderr or "").strip()} stdout={(res.stdout or "").strip()}'


def build_note(today: str) -> tuple[str, str, Optional[Path]]:
    extracted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    rrp_last, rrp_prev = fetch_fred_last_two('RRPONTSYD')
    tga_last, tga_prev = fetch_fred_last_two('WTREGEN')
    reserve_last, reserve_prev = fetch_fred_last_two('WRESBAL')

    hy_oas_last, hy_oas_prev = fetch_fred_last_two('BAMLH0A0HYM2')
    sofr_last, sofr_prev = fetch_fred_last_two('SOFR')
    effr_last, effr_prev = fetch_fred_last_two('DFF')

    cpi_last, cpi_prev = fetch_fred_last_two('CPIAUCSL')
    core_cpi_last, core_cpi_prev = fetch_fred_last_two('CPILFESL')
    pce_last, pce_prev = fetch_fred_last_two('PCEPI')
    core_pce_last, core_pce_prev = fetch_fred_last_two('PCEPILFE')

    m2_last, m2_prev = fetch_fred_last_two('M2SL')
    gdp_last, gdp_prev = fetch_fred_last_two('GDP')
    ff_upper_last, ff_upper_prev = fetch_fred_last_two('DFEDTARU')
    ff_lower_last, ff_lower_prev = fetch_fred_last_two('DFEDTARL')
    walcl_last, walcl_prev = fetch_fred_last_two('WALCL')

    m2gdp_last = (m2_last.value / gdp_last.value) if (m2_last.value is not None and gdp_last.value) else None
    m2gdp_prev = (m2_prev.value / gdp_prev.value) if (m2_prev and gdp_prev and m2_prev.value is not None and gdp_prev.value) else None

    liquidity_state, liquidity_line = liquidity_regime(
        rrp_last.value,
        reserve_last.value,
        tga_last.value - tga_prev.value if (tga_last.value is not None and tga_prev and tga_prev.value is not None) else None,
    )
    stress_state, stress_line = stress_regime(
        hy_oas_last.value,
        hy_oas_last.value - hy_oas_prev.value if (hy_oas_last.value is not None and hy_oas_prev and hy_oas_prev.value is not None) else None,
    )
    inflation_state, inflation_line = inflation_regime(
        core_pce_last.value - core_pce_prev.value if (core_pce_last.value is not None and core_pce_prev and core_pce_prev.value is not None) else None,
        cpi_last.value - cpi_prev.value if (cpi_last.value is not None and cpi_prev and cpi_prev.value is not None) else None,
    )
    money_state, money_line = money_scale_regime(
        m2gdp_last,
        (m2gdp_last - m2gdp_prev) if (m2gdp_last is not None and m2gdp_prev is not None) else None,
    )
    repo_spread_last = (sofr_last.value - effr_last.value) if (sofr_last.value is not None and effr_last.value is not None) else None
    repo_spread_prev = (sofr_prev.value - effr_prev.value) if (sofr_prev and effr_prev and sofr_prev.value is not None and effr_prev.value is not None) else None
    repo_state, repo_line = repo_regime(sofr_last.value, effr_last.value, repo_spread_last)
    policy_state, policy_line = policy_regime(
        ff_upper_last.value,
        ff_lower_last.value,
        walcl_last.value - walcl_prev.value if (walcl_last.value is not None and walcl_prev and walcl_prev.value is not None) else None,
    )

    easy_line = '지금 시장은 완전히 안전하지는 않지만, 바로 크게 무너질 분위기도 아닙니다.'
    if liquidity_state in ('경계', '경계적 완화') and inflation_state in ('재가속 경계', '경계'):
        easy_line = '돈은 아직 좀 돌고 있지만, 물가가 다시 오를 수 있어서 주식시장이 흔들릴 수 있는 상태입니다.'
    elif stress_state == '위험':
        easy_line = '지금은 조심해야 하는 때입니다. 시장 불안 신호가 커져서 돈이 안전한 곳으로 피할 수 있습니다.'
    elif liquidity_state == '완화' and inflation_state == '둔화':
        easy_line = '지금은 시장에 비교적 좋은 환경입니다. 돈이 돌고 물가 부담도 덜해서 투자심리에 도움이 되는 편입니다.'

    chart_path = build_liquidity_chart(today)
    tg_text = build_telegram_message(
        today=today,
        extracted_at=extracted_at,
        liquidity_state=liquidity_state,
        liquidity_line=liquidity_line,
        inflation_state=inflation_state,
        stress_state=stress_state,
        money_state=money_state,
        repo_state=repo_state,
        policy_state=policy_state,
        tga_last=tga_last,
        tga_prev=tga_prev,
        rrp_last=rrp_last,
        rrp_prev=rrp_prev,
        reserve_last=reserve_last,
        reserve_prev=reserve_prev,
        core_pce_last=core_pce_last,
        core_pce_prev=core_pce_prev,
        hy_oas_last=hy_oas_last,
        hy_oas_prev=hy_oas_prev,
        sofr_last=sofr_last,
        sofr_prev=sofr_prev,
        effr_last=effr_last,
        effr_prev=effr_prev,
        ff_upper_last=ff_upper_last,
        ff_lower_last=ff_lower_last,
        walcl_last=walcl_last,
        walcl_prev=walcl_prev,
        m2gdp_last=m2gdp_last,
        m2gdp_prev=m2gdp_prev,
        chart_path=chart_path,
    )

    note = f'''# Daily Macro Note - {today}

## Summary
| 모듈 | 현재 상태 | 한 줄 판단 |
|---|---|---|
| Liquidity | {liquidity_state} | {liquidity_line} |
| Stress | {stress_state} | {stress_line} |
| Inflation | {inflation_state} | {inflation_line} |
| Money Scale | {money_state} | {money_line} |
| Repo | {repo_state} | {repo_line} |
| Policy | {policy_state} | {policy_line} |

- Tag: `macro_note_draft`
- Note date: {today}
- Data extracted at: {extracted_at}

## 0. Telegram 전송용 요약
```text
{tg_text}
```

## 1. Liquidity Composite

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| TGA | {fmt_num(tga_last.value)} | {fmt_change(tga_last.value, tga_prev.value if tga_prev else None)} | TGA 증가=유동성 흡수, 감소=완화 | {'완화' if tga_last.value is not None and tga_prev and tga_last.value < tga_prev.value else '보류'} | {tga_last.source} | {tga_last.asof_date} |
| RRP | {fmt_num(rrp_last.value)} | {fmt_change(rrp_last.value, rrp_prev.value if rrp_prev else None)} | RRP 감소는 완충, 바닥 고갈은 완충 소멸 | {'취약 완화' if rrp_last.value is not None and rrp_last.value < 10 else '보류'} | {rrp_last.source} | {rrp_last.asof_date} |
| Reserve Balances | {fmt_num(reserve_last.value)} | {fmt_change(reserve_last.value, reserve_prev.value if reserve_prev else None)} | 3조 달러 하회는 스트레스 경계 | {'경계' if reserve_last.value is not None and reserve_last.value < 3000 else '보류'} | {reserve_last.source} | {reserve_last.asof_date} |
| SOFR | {fmt_num(sofr_last.value)} | {fmt_change(sofr_last.value, sofr_prev.value if sofr_prev else None)} | 단기 담보 자금 조달 금리 레벨 | {repo_state} | {sofr_last.source} | {sofr_last.asof_date} |
| EFFR | {fmt_num(effr_last.value)} | {fmt_change(effr_last.value, effr_prev.value if effr_prev else None)} | 정책금리 체감 축 | {repo_state} | {effr_last.source} | {effr_last.asof_date} |
| SOFR-EFFR spread | {fmt_num(repo_spread_last, 3)} | {fmt_change(repo_spread_last, repo_spread_prev, 3)} | 스프레드 확대 시 배관 긴장 경계 | {repo_state} | SOFR-DFF(파생) | {sofr_last.asof_date if sofr_last.asof_date > effr_last.asof_date else effr_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- TGA, RRP, 지급준비금은 메르가 반복해서 보는 유동성 3형제입니다.
- 특히 RRP가 바닥권이면 과거처럼 충격을 흡수해줄 완충재가 사라졌다고 해석합니다.
- 지급준비금이 3조 달러 부근이나 그 아래면, QT 지속 자체보다 배관 스트레스 관리가 더 중요해질 수 있습니다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 지금은 **{liquidity_state}** 상태로 보입니다.
- {liquidity_line}
- Liquidity 차트: `{chart_path.as_posix() if chart_path else '생성 실패'}`

## 2. Stress Early Warning

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| HY OAS | {fmt_num(hy_oas_last.value)} | {fmt_change(hy_oas_last.value, hy_oas_prev.value if hy_oas_prev else None)} | 신용스프레드 확대로 조기 스트레스 경보 | {stress_state} | {hy_oas_last.source} | {hy_oas_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- 메르는 위기 직전의 후행 신호보다, 신용스프레드처럼 배관 리스크가 먼저 반영되는 선행 신호를 중시합니다.
- HY OAS 급등은 기업 신용비용 상승과 위험회피 확대로 이어질 수 있습니다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{stress_state}**입니다. {stress_line}

## 3. Inflation Policy Lens

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| CPI | {fmt_num(cpi_last.value)} | {fmt_change(cpi_last.value, cpi_prev.value if cpi_prev else None)} | 시장은 CPI에 즉각 반응 | {'경계' if cpi_last.value is not None and cpi_prev and cpi_last.value > cpi_prev.value else '보류'} | {cpi_last.source} | {cpi_last.asof_date} |
| Core CPI | {fmt_num(core_cpi_last.value)} | {fmt_change(core_cpi_last.value, core_cpi_prev.value if core_cpi_prev else None)} | 체감 물가/시장 민감도 보조 | {'경계' if core_cpi_last.value is not None and core_cpi_prev and core_cpi_last.value > core_cpi_prev.value else '보류'} | {core_cpi_last.source} | {core_cpi_last.asof_date} |
| PCE | {fmt_num(pce_last.value)} | {fmt_change(pce_last.value, pce_prev.value if pce_prev else None)} | 연준 판단축 | {'경계' if pce_last.value is not None and pce_prev and pce_last.value > pce_prev.value else '보류'} | {pce_last.source} | {pce_last.asof_date} |
| Core PCE | {fmt_num(core_pce_last.value)} | {fmt_change(core_pce_last.value, core_pce_prev.value if core_pce_prev else None)} | 정책상 가장 중요한 물가 축 | {'경계' if core_pce_last.value is not None and core_pce_prev and core_pce_last.value > core_pce_prev.value else '보류'} | {core_pce_last.source} | {core_pce_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- 메르 해석의 핵심은 시장 반응용 CPI와 연준 판단용 PCE를 분리해서 보는 것입니다.
- 즉 CPI가 튀어도 정책 방향을 섣불리 단정하지 않고, Core PCE 흐름까지 같이 봐야 합니다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{inflation_state}** 상태입니다.
- {inflation_line}

## 4. Money Scale

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| M2 | {fmt_num(m2_last.value)} | {fmt_change(m2_last.value, m2_prev.value if m2_prev else None)} | 절대 통화량 | {'완화' if m2_last.value is not None and m2_prev and m2_last.value > m2_prev.value else '보류'} | {m2_last.source} | {m2_last.asof_date} |
| GDP | {fmt_num(gdp_last.value)} | {fmt_change(gdp_last.value, gdp_prev.value if gdp_prev else None)} | 경제 규모 대비 비교축 | {'확장' if gdp_last.value is not None and gdp_prev and gdp_last.value > gdp_prev.value else '보류'} | {gdp_last.source} | {gdp_last.asof_date} |
| M2/GDP | {fmt_num(m2gdp_last, 4)} | {fmt_change(m2gdp_last, m2gdp_prev, 4)} | 버블/침체 스케일 판단 | {money_state} | M2SL/GDP(파생) | {m2_last.asof_date if m2_last.asof_date > gdp_last.asof_date else gdp_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- 메르는 단순 M2보다 M2/GDP처럼 스케일 비교가 가능한 지표를 더 중요하게 봅니다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{money_state}**입니다. {money_line}

## 5. Policy Sequence Tracker

### 수치 표
| 항목 | 현재 내용 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---|---|---|---|---|
| Policy rate band | {fmt_num(ff_lower_last.value)}-{fmt_num(ff_upper_last.value)} | 금리 밴드 변경 여부를 정책 전환의 1차 신호로 확인 | {policy_state} | DFEDTARL/DFEDTARU | {ff_upper_last.asof_date if ff_upper_last.asof_date > ff_lower_last.asof_date else ff_lower_last.asof_date} |
| Balance sheet trend | {fmt_num(walcl_last.value)} ({fmt_change(walcl_last.value, walcl_prev.value if walcl_prev else None)}) | WALCL 변화로 QT 지속/완화 보강 여부를 점검 | {policy_state} | {walcl_last.source} | {walcl_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- 메르 프레임에서는 금리 headline보다 QT 조정, 준비금 관리, 단기국채 매입성 조치가 먼저 전환 신호일 수 있습니다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{policy_state}** 상태입니다. {policy_line}

## 6. Repo Summary

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| SOFR | {fmt_num(sofr_last.value)} | {fmt_change(sofr_last.value, sofr_prev.value if sofr_prev else None)} | 담보부 단기자금 금리 | {repo_state} | {sofr_last.source} | {sofr_last.asof_date} |
| EFFR | {fmt_num(effr_last.value)} | {fmt_change(effr_last.value, effr_prev.value if effr_prev else None)} | 정책금리 체감 축 | {repo_state} | {effr_last.source} | {effr_last.asof_date} |
| SOFR-EFFR spread | {fmt_num(repo_spread_last, 3)} | {fmt_change(repo_spread_last, repo_spread_prev, 3)} | 확대 시 배관 긴장, 안정 시 중립 | {repo_state} | SOFR-DFF(파생) | {sofr_last.asof_date if sofr_last.asof_date > effr_last.asof_date else effr_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- Repo 시장 원천 데이터가 완전 자동화되기 전에는 SOFR-EFFR 스프레드를 배관 압력의 대체 지표로 본다.
- 스프레드가 급격히 벌어지면 단기 자금조달 리스크가 커질 수 있어 경계 신호로 관리한다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{repo_state}**입니다. {repo_line}

## 7. Policy Summary

### 수치 표
| 지표 | 값 | 변화 | 메르 해석 포인트 | 현재 판정 | 데이터 출처 | 기준일 |
|---|---:|---:|---|---|---|---|
| Fed Target Upper | {fmt_num(ff_upper_last.value)} | {fmt_change(ff_upper_last.value, ff_upper_prev.value if ff_upper_prev else None)} | 기준금리 상단 변화 확인 | {policy_state} | {ff_upper_last.source} | {ff_upper_last.asof_date} |
| Fed Target Lower | {fmt_num(ff_lower_last.value)} | {fmt_change(ff_lower_last.value, ff_lower_prev.value if ff_lower_prev else None)} | 기준금리 하단 변화 확인 | {policy_state} | {ff_lower_last.source} | {ff_lower_last.asof_date} |
| Fed Balance Sheet (WALCL) | {fmt_num(walcl_last.value)} | {fmt_change(walcl_last.value, walcl_prev.value if walcl_prev else None)} | 대차대조표 확대/축소로 정책 스탠스 점검 | {policy_state} | {walcl_last.source} | {walcl_last.asof_date} |

### 메르의 설명
> 메르는 이 지표를 이렇게 읽는다.
- 금리 인하 기대보다, 실제 목표금리 범위 변경과 대차대조표 흐름을 우선 확인한다.
- WALCL 증가 전환은 정책 완화 신호 가능성으로, 감소 지속은 긴축 유지로 본다.

### 지금 상태
> 그래서 오늘은 이렇게 본다.
- 현재는 **{policy_state}**입니다. {policy_line}

## Final Take
- 한줄 결론: {easy_line}
- 종합 판단: 유동성은 {liquidity_state}, 스트레스는 {stress_state}, 물가는 {inflation_state}, 통화 스케일은 {money_state}, Repo는 {repo_state}, Policy는 {policy_state}입니다.
- 핵심 근거: RRP/Reserve 경계선, HY OAS 추이, CPI·PCE 세트, M2/GDP 비율을 동시 점검했습니다.
- 리스크 포인트: Repo/Policy 원천 자동연결 전이라 이벤트 급변 시 해석 보정이 필요합니다.
'''
    return note, tg_text, chart_path


def build_weekly_summary(today: str) -> tuple[str, str]:
    extracted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    rrp = _read_fred_series('RRPONTSYD')
    reserve = _read_fred_series('WRESBAL')
    hy = _read_fred_series('BAMLH0A0HYM2')
    core_pce = _read_fred_series('PCEPILFE')
    walcl = _read_fred_series('WALCL')

    def last_and_week(rows: list[tuple[datetime, float]]) -> tuple[Optional[float], Optional[float], str]:
        if not rows:
            return None, None, 'unknown'
        curr = rows[-1][1]
        prev = rows[-2][1] if len(rows) >= 2 else None
        week = rows[-6][1] if len(rows) >= 6 else (rows[0][1] if len(rows) > 1 else None)
        return curr, week, str(rows[-1][0].date())

    rrp_curr, rrp_week, rrp_asof = last_and_week(rrp)
    reserve_curr, reserve_week, reserve_asof = last_and_week(reserve)
    hy_curr, hy_week, hy_asof = last_and_week(hy)
    pce_curr, pce_week, pce_asof = last_and_week(core_pce)
    walcl_curr, walcl_week, walcl_asof = last_and_week(walcl)

    iso = datetime.strptime(today, '%Y-%m-%d').isocalendar()
    week_id = f'{iso.year}-W{iso.week:02d}'

    tg = f'''📌 메르 주간 매크로 요약 ({week_id})

[주간 변화]
• RRP: {fmt_num(rrp_curr)} (WoW {fmt_change(rrp_curr, rrp_week)})
• Reserve: {fmt_num(reserve_curr)} (WoW {fmt_change(reserve_curr, reserve_week)})
• HY OAS: {fmt_num(hy_curr)} (WoW {fmt_change(hy_curr, hy_week)})
• Core PCE: {fmt_num(pce_curr)} (WoW {fmt_change(pce_curr, pce_week)})
• WALCL: {fmt_num(walcl_curr)} (WoW {fmt_change(walcl_curr, walcl_week)})

[한줄 판단]
• 유동성/스트레스/정책의 방향성만 빠르게 체크하는 주간 스냅샷입니다.
• 데이터 갱신 주기가 서로 달라 일부 지표는 시차가 있습니다.
• 생성시각: {extracted_at}
• 태그: #macro_weekly #mer_liquidity'''

    note = f'''# Weekly Macro Summary - {week_id}

- 기준일: {today}
- 생성시각: {extracted_at}

## Telegram 전송용 요약
```text
{tg}
```

## 주간 스냅샷 표
| 지표 | 최신값 | WoW 변화 | 데이터 기준일 |
|---|---:|---:|---|
| RRP | {fmt_num(rrp_curr)} | {fmt_change(rrp_curr, rrp_week)} | {rrp_asof} |
| Reserve Balances | {fmt_num(reserve_curr)} | {fmt_change(reserve_curr, reserve_week)} | {reserve_asof} |
| HY OAS | {fmt_num(hy_curr)} | {fmt_change(hy_curr, hy_week)} | {hy_asof} |
| Core PCE | {fmt_num(pce_curr)} | {fmt_change(pce_curr, pce_week)} | {pce_asof} |
| Fed Balance Sheet (WALCL) | {fmt_num(walcl_curr)} | {fmt_change(walcl_curr, walcl_week)} | {walcl_asof} |

## 주간 해석 메모
- 유동성: RRP/Reserve 변화로 단기 완충 여력을 점검
- 스트레스: HY OAS 확대로 리스크 프리미엄 변화를 관찰
- 정책: WALCL 방향으로 QT 완급 조절 여부를 추적
'''
    return note, tg


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Generate Mer daily macro note')
    p.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    p.add_argument('--weekly', action='store_true', help='Generate weekly summary files as well')
    p.add_argument('--send-telegram-test', action='store_true', help='Try openclaw message send after generation')
    p.add_argument('--telegram-target', default='5294188460', help='Telegram chat id for send test')
    p.add_argument('--message-channel', default='telegram', help='openclaw channel for send test')
    return p.parse_args()


def main() -> int:
    args = parse_args()
    today = args.date

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    note_content, tg_text, chart_path = build_note(today)

    note_path = OUT_DIR / f'{today}.md'
    tg_path = OUT_DIR / f'{today}.telegram.txt'

    note_path.write_text(note_content, encoding='utf-8')
    tg_path.write_text(tg_text, encoding='utf-8')

    print(note_path)
    print(tg_path)
    if chart_path:
        print(chart_path)
    else:
        print('chart generation skipped')

    if args.weekly:
        WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
        weekly_note, weekly_tg = build_weekly_summary(today)
        iso = datetime.strptime(today, '%Y-%m-%d').isocalendar()
        week_id = f'{iso.year}-W{iso.week:02d}'
        weekly_note_path = WEEKLY_DIR / f'{week_id}.md'
        weekly_tg_path = WEEKLY_DIR / f'{week_id}.telegram.txt'
        weekly_note_path.write_text(weekly_note, encoding='utf-8')
        weekly_tg_path.write_text(weekly_tg, encoding='utf-8')
        print(weekly_note_path)
        print(weekly_tg_path)

    if args.send_telegram_test:
        ok, msg = send_telegram_test(tg_text, chart_path, target=args.telegram_target, channel=args.message_channel)
        print(f'telegram_test={"ok" if ok else "failed"}: {msg}')
        return 0 if ok else 2

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
