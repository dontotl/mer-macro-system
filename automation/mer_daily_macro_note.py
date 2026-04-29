from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager, rcParams


FRED_CSV_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}'


def configure_korean_font() -> None:
    candidates = ['Apple SD Gothic Neo', 'NanumGothic', 'AppleGothic', 'Malgun Gothic']
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            rcParams['font.family'] = name
            break
    rcParams['axes.unicode_minus'] = False


def fetch_fred_series(series_id: str, years: int = 3) -> pd.Series:
    start = (datetime.now() - timedelta(days=365 * years + 10)).strftime('%Y-%m-%d')
    url = FRED_CSV_URL.format(series_id=series_id)
    df = pd.read_csv(url)
    date_col = 'DATE' if 'DATE' in df.columns else 'observation_date'
    if date_col not in df.columns or series_id not in df.columns:
        raise ValueError(f'FRED 응답 형식 이상: {series_id}')

    s = pd.to_numeric(df[series_id], errors='coerce')
    idx = pd.to_datetime(df[date_col], errors='coerce')
    out = pd.Series(s.values, index=idx).dropna()
    out = out[out.index >= pd.to_datetime(start)]
    return out.sort_index()


def to_trillion_from_billions(s: pd.Series) -> pd.Series:
    # FRED 잔액 계열(WTREGEN/RRPONTSYD/WRESBAL)은 대체로 "백만 달러" 단위.
    # 1조 달러(T)로 표기하려면 1,000,000으로 나눔.
    return s / 1_000_000.0


def yoy_percent(s: pd.Series) -> pd.Series:
    return s.pct_change(12) * 100.0


def trend_text(s: pd.Series, lookback: int = 12) -> str:
    s = s.dropna()
    if len(s) < max(lookback, 3):
        return '중립'
    recent = s.tail(lookback)
    slope = (recent.iloc[-1] - recent.iloc[0]) / max(len(recent) - 1, 1)
    std = recent.std() if recent.std() and not pd.isna(recent.std()) else 1.0
    z = slope / std
    if z > 0.05:
        return '상승 흐름'
    if z < -0.05:
        return '하락 흐름'
    return '횡보 흐름'


def metric_summary(s: pd.Series, unit: str, decimals: int = 2) -> dict[str, float | str]:
    s = s.dropna()
    current = float(s.iloc[-1])
    avg = float(s.mean())
    min_value = float(s.min())
    max_value = float(s.max())
    range_span = max_value - min_value
    percentile = 50.0
    if range_span > 0:
        percentile = ((current - min_value) / range_span) * 100.0
    return {
        'current': current,
        'avg': avg,
        'min': min_value,
        'max': max_value,
        'percentile': percentile,
        'trend': trend_text(s),
        'unit': unit,
        'decimals': decimals,
    }


def format_value_with_unit(value: float, unit: str, decimals: int = 2) -> str:
    if unit == 'T':
        if abs(value) < 0.01:
            return f"{value * 1000:.2f}B"
        return f"{value:.{decimals}f}T"
    return f"{value:.{decimals}f}{unit}"


def format_delta_with_unit(delta: float, unit: str, decimals: int = 2) -> str:
    if unit == 'T':
        if abs(delta) < 0.01:
            return f"{delta * 1000:+.2f}B"
        return f"{delta:+.{decimals}f}T"
    return f"{delta:+.{decimals}f}{unit}"


def fmt_metric(name: str, m: dict[str, float | str]) -> str:
    d = int(m['decimals'])
    unit = str(m['unit'])
    current = format_value_with_unit(float(m['current']), unit, d)
    avg = format_value_with_unit(float(m['avg']), unit, d)
    return f"- {name}: 현재 {current} | 평균 {avg} | {m['trend']}"


METRIC_DEFINITIONS: dict[str, str] = {
    'TGA': '미 재무부 일반계정(TGA) 잔액, 높아지면 시중 유동성 흡수 압력이 커집니다.',
    'RRP': '역레포(RRP) 잔액, 낮아질수록 시장으로 유동성이 되돌아온 상태를 뜻합니다.',
    'Reserve Balances': '은행 지급준비금, 시스템 유동성 완충 여력의 핵심 지표입니다.',
    'CPI YoY': '소비자물가(CPI) 전년동월비, 체감 물가 압력의 대표 지표입니다.',
    'Core CPI YoY': '식품/에너지를 제외한 근원 CPI 전년동월비, 기조 물가 흐름을 보여줍니다.',
    'PCE YoY': '개인소비지출물가(PCE) 전년동월비, 연준이 중시하는 물가 지표입니다.',
    'Core PCE YoY': '근원 PCE 전년동월비, 정책 판단에 더 직접적인 기조 물가 지표입니다.',
    'HY OAS': '하이일드 스프레드(HY OAS), 신용시장 스트레스와 리스크 프리미엄을 반영합니다.',
}


def relative_position_text(current: float, avg: float, unit: str, decimals: int) -> str:
    delta = current - avg
    direction = '상회' if delta > 0 else '하회' if delta < 0 else '동일'
    return f"평균 대비 {format_delta_with_unit(delta, unit, decimals)} ({direction})"


def trend_interpretation(name: str, trend: str) -> str:
    if name in {'TGA', 'CPI YoY', 'Core CPI YoY', 'PCE YoY', 'Core PCE YoY', 'HY OAS'}:
        if '상승' in trend:
            return '방향성: 상승 흐름은 금융여건/자산가격에 부담 신호로 해석합니다.'
        if '하락' in trend:
            return '방향성: 하락 흐름은 부담 완화(디스인플레이션/크레딧 안정) 신호입니다.'
        return '방향성: 횡보 흐름은 뚜렷한 추세 전환 신호가 약한 구간입니다.'
    if name in {'RRP', 'Reserve Balances'}:
        if '상승' in trend:
            return '방향성: 상승 흐름은 유동성 완충 여력 개선 신호입니다.'
        if '하락' in trend:
            return '방향성: 하락 흐름은 유동성 완충 여력 둔화/소진 신호입니다.'
        return '방향성: 횡보 흐름은 유동성 체력이 대체로 유지되는 구간입니다.'
    return f'방향성: {trend}'


def metric_detail_lines(name: str, m: dict[str, float | str], indent: str = '  ') -> list[str]:
    current = float(m['current'])
    avg = float(m['avg'])
    unit = str(m['unit'])
    decimals = int(m['decimals'])
    trend = str(m['trend'])
    definition = METRIC_DEFINITIONS.get(name, f'{name} 지표입니다.')
    return [
        fmt_metric(name, m),
        f"{indent}· 정의: {definition}",
        f"{indent}· 현재 위치: {relative_position_text(current, avg, unit, decimals)}",
        f"{indent}· {trend_interpretation(name, trend)}",
    ]


def metrics_block(names: list[str], summaries: dict[str, dict[str, float | str]], indent: str = '  ') -> str:
    lines: list[str] = []
    for n in names:
        lines.extend(metric_detail_lines(n, summaries[n], indent=indent))
    return '\n'.join(lines)


def delta_text(current: float, avg: float, unit: str, decimals: int) -> str:
    delta = current - avg
    return format_delta_with_unit(delta, unit, decimals)


def trend_arrow(trend: str) -> str:
    if '상승' in trend:
        return '↗ 상승'
    if '하락' in trend:
        return '↘ 하락'
    return '→ 횡보'


def draw_series_with_avg_current(
    ax,
    s: pd.Series,
    title: str,
    color: str,
    unit: str,
    reserve_line: float | None = None,
    scale: float = 1.0,
):
    s = s.dropna()
    ax.set_facecolor('#fcfcfd')
    avg = s.mean()
    current = float(s.iloc[-1])
    trend = trend_text(s)

    ax.plot(s.index, s.values, color=color, linewidth=3.0 * scale, alpha=0.95)
    ax.fill_between(s.index, s.values, avg, color=color, alpha=0.08)
    ax.axhline(avg, linestyle='--', linewidth=1.8 * scale, color='#6b7280', label=f"평균 {format_value_with_unit(float(avg), unit, 2)}")
    ax.scatter([s.index[-1]], [current], color=color, s=78 * scale, zorder=5, edgecolor='white', linewidth=1.0 * scale)

    info = (
        f"현재 {format_value_with_unit(current, unit, 2)} ({delta_text(current, float(avg), unit, 2)})\n"
        f"평균 {format_value_with_unit(float(avg), unit, 2)}  |  {trend_arrow(trend)}"
    )
    ax.text(
        0.025,
        0.955,
        info,
        transform=ax.transAxes,
        va='top',
        ha='left',
        fontsize=18 * scale,
        fontweight='bold',
        color='#111827',
        linespacing=1.5,
        bbox={'boxstyle': 'round,pad=0.55', 'fc': 'white', 'ec': '#d1d5db', 'alpha': 0.97},
    )

    if reserve_line is not None:
        ax.axhline(reserve_line, linestyle=':', linewidth=2.2 * scale, color='#dc2626', label=f'{reserve_line:.1f}{unit} 가이드')
    ax.set_title(title, fontsize=22 * scale, loc='left', pad=12 * scale, fontweight='bold')
    ax.grid(alpha=0.24, linestyle='--')
    ax.tick_params(axis='both', labelsize=16 * scale)
    ax.legend(loc='best', fontsize=15 * scale)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)


def build_weekly_delta_series(s: pd.Series, periods: int = 5) -> float:
    s = s.dropna()
    if len(s) < periods + 1:
        return float('nan')
    return float(s.iloc[-1] - s.iloc[-(periods + 1)])


def generate_weekly_chart(report_date: str, metrics: dict[str, dict[str, float | str]]) -> Path:
    charts_dir = Path('invest/notes/daily-macro/charts')
    charts_dir.mkdir(parents=True, exist_ok=True)
    weekly_path = charts_dir / f'{report_date}-weekly-key-changes.png'

    labels = ['TGA', 'RRP', 'Reserves', 'CPI', 'Core CPI', 'PCE', 'Core PCE', 'HY OAS']
    values = [
        metrics['weekly_delta']['TGA'],
        metrics['weekly_delta']['RRP'],
        metrics['weekly_delta']['Reserve Balances'],
        metrics['weekly_delta']['CPI YoY'],
        metrics['weekly_delta']['Core CPI YoY'],
        metrics['weekly_delta']['PCE YoY'],
        metrics['weekly_delta']['Core PCE YoY'],
        metrics['weekly_delta']['HY OAS'],
    ]
    units = ['T', 'T', 'T', '%p', '%p', '%p', '%p', 'bp']

    fig, ax = plt.subplots(figsize=(15, 8.5))
    y = np.arange(len(labels))
    colors = ['#16a34a' if v <= 0 else '#dc2626' for v in values]
    bars = ax.barh(y, values, color=colors, alpha=0.9)
    ax.axvline(0, color='#6b7280', linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_title(f'Weekly Macro Key Changes (1W) - {report_date}', loc='left', fontsize=24, fontweight='bold')
    ax.grid(axis='x', alpha=0.18, linestyle='--')
    ax.set_facecolor('#fcfcfd')
    for i, (bar, unit) in enumerate(zip(bars, units, strict=False)):
        v = values[i]
        label = format_delta_with_unit(float(v), unit, 2)
        ax.text(v + (0.01 if v >= 0 else -0.01), bar.get_y() + bar.get_height() / 2, label, va='center', ha='left' if v >= 0 else 'right', fontsize=16, fontweight='bold')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis='both', labelsize=16)
    fig.tight_layout()
    fig.savefig(weekly_path, dpi=200)
    plt.close(fig)
    return weekly_path


def generate_charts(report_date: str, years: int = 3, chart_scale: float = 1.0, suffix: str = '', canvas_scale: float = 1.0, dpi: int = 200) -> tuple[dict[str, Path], dict[str, dict[str, float | str]]]:
    charts_dir = Path('invest/notes/daily-macro/charts')
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Liquidity
    tga = to_trillion_from_billions(fetch_fred_series('WTREGEN', years))
    rrp = to_trillion_from_billions(fetch_fred_series('RRPONTSYD', years))
    reserves = to_trillion_from_billions(fetch_fred_series('WRESBAL', years))

    fig, axes = plt.subplots(3, 1, figsize=(16 * canvas_scale, 14 * canvas_scale), sharex=True)
    draw_series_with_avg_current(axes[0], tga, 'TGA (Treasury General Account)', '#2563eb', 'T', scale=chart_scale)
    draw_series_with_avg_current(axes[1], rrp, 'RRP (Overnight Reverse Repo)', '#f59e0b', 'T', scale=chart_scale)
    draw_series_with_avg_current(axes[2], reserves, 'Reserve Balances', '#16a34a', 'T', reserve_line=3.0, scale=chart_scale)
    fig.suptitle(f'Liquidity Dashboard ({years}Y) - {report_date}', fontsize=26 * chart_scale, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=2.6 * chart_scale)
    liquidity_path = charts_dir / f'{report_date}{suffix}-liquidity-timeseries.png'
    fig.savefig(liquidity_path, dpi=dpi)
    plt.close(fig)

    # Inflation (YoY)
    cpi = yoy_percent(fetch_fred_series('CPIAUCSL', years + 1)).dropna()
    core_cpi = yoy_percent(fetch_fred_series('CPILFESL', years + 1)).dropna()
    pce = yoy_percent(fetch_fred_series('PCEPI', years + 1)).dropna()
    core_pce = yoy_percent(fetch_fred_series('PCEPILFE', years + 1)).dropna()

    fig, axes = plt.subplots(2, 2, figsize=(16 * canvas_scale, 12 * canvas_scale), sharex=True)
    draw_series_with_avg_current(axes[0, 0], cpi, 'CPI YoY', '#1d4ed8', '%', scale=chart_scale)
    draw_series_with_avg_current(axes[0, 1], core_cpi, 'Core CPI YoY', '#2563eb', '%', scale=chart_scale)
    draw_series_with_avg_current(axes[1, 0], pce, 'PCE YoY', '#7c3aed', '%', scale=chart_scale)
    draw_series_with_avg_current(axes[1, 1], core_pce, 'Core PCE YoY', '#a855f7', '%', scale=chart_scale)
    fig.suptitle(f'Inflation Dashboard ({years}Y, YoY) - {report_date}', fontsize=26 * chart_scale, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=2.4 * chart_scale, w_pad=2.2 * chart_scale)
    inflation_path = charts_dir / f'{report_date}{suffix}-inflation-timeseries.png'
    fig.savefig(inflation_path, dpi=dpi)
    plt.close(fig)

    # Stress
    hy_oas = fetch_fred_series('BAMLH0A0HYM2', years) * 100.0
    fig, ax = plt.subplots(1, 1, figsize=(16 * canvas_scale, 7 * canvas_scale))
    draw_series_with_avg_current(ax, hy_oas, 'HY OAS (High Yield Spread)', '#dc2626', 'bp', scale=chart_scale)
    fig.suptitle(f'Stress Dashboard ({years}Y) - {report_date}', fontsize=26 * chart_scale, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=2.0 * chart_scale)
    stress_path = charts_dir / f'{report_date}{suffix}-stress-timeseries.png'
    fig.savefig(stress_path, dpi=dpi)
    plt.close(fig)

    summaries = {
        'TGA': metric_summary(tga, 'T', 2),
        'RRP': metric_summary(rrp, 'T', 2),
        'Reserve Balances': metric_summary(reserves, 'T', 2),
        'CPI YoY': metric_summary(cpi, '%', 1),
        'Core CPI YoY': metric_summary(core_cpi, '%', 1),
        'PCE YoY': metric_summary(pce, '%', 1),
        'Core PCE YoY': metric_summary(core_pce, '%', 1),
        'HY OAS': metric_summary(hy_oas, 'bp', 0),
        'weekly_delta': {
            'TGA': build_weekly_delta_series(tga),
            'RRP': build_weekly_delta_series(rrp),
            'Reserve Balances': build_weekly_delta_series(reserves),
            'CPI YoY': build_weekly_delta_series(cpi),
            'Core CPI YoY': build_weekly_delta_series(core_cpi),
            'PCE YoY': build_weekly_delta_series(pce),
            'Core PCE YoY': build_weekly_delta_series(core_pce),
            'HY OAS': build_weekly_delta_series(hy_oas),
        },
    }

    return {
        'liquidity': liquidity_path,
        'inflation': inflation_path,
        'stress': stress_path,
    }, summaries


def build_daily_note(report_date: str, summaries: dict[str, dict[str, float | str]]) -> str:
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'''# Daily Macro Note - {report_date}

## Summary
- Liquidity: RRP/Reserves가 완충, TGA 증감 속도는 부담 요인
- Inflation: 현재값 vs 3년 평균 vs 방향(↗/↘/→)을 함께 체크
- Stress: HY OAS로 신용 스트레스 온도 확인

- Note date: {report_date}
- Data extracted at: {generated_at}

## Liquidity (최근 3년)
{metrics_block(['TGA', 'RRP', 'Reserve Balances'], summaries)}
- 해석: TGA는 유동성 흡수, RRP 하락과 Reserves(3T 가이드선 상단 유지 여부)가 완충 역할.

## Inflation (최근 3년, YoY)
{metrics_block(['CPI YoY', 'Core CPI YoY', 'PCE YoY', 'Core PCE YoY'], summaries)}
- 해석: 평균 대비 현재 위치와 최근 흐름을 같이 보며 디스인플레이션 지속 여부 확인.

## Stress (최근 3년)
{metrics_block(['HY OAS'], summaries)}
- 해석: HY OAS 상승은 리스크오프 압력, 하락은 크레딧 안정 신호.

## Final Take
- 한줄 결론: 유동성 완충은 남아 있으나, 인플레이션 흐름이 꺾이지 않으면 위험자산 변동성은 재확대될 수 있습니다.
'''


def liquidity_position_text(summaries: dict[str, dict[str, float | str]]) -> str:
    tga_p = float(summaries['TGA']['percentile'])
    rrp_p = float(summaries['RRP']['percentile'])
    reserve_current = float(summaries['Reserve Balances']['current'])
    if tga_p >= 75 and rrp_p <= 20 and reserve_current < 3.0:
        return '중간 이하'
    if tga_p <= 40 and rrp_p >= 60 and reserve_current >= 3.0:
        return '중간 이상'
    return '중간'


def inflation_position_text(summaries: dict[str, dict[str, float | str]]) -> str:
    core_pce = float(summaries['Core PCE YoY']['current'])
    core_cpi = float(summaries['Core CPI YoY']['current'])
    if core_pce >= 3.0 or core_cpi >= 3.5:
        return '중간 이상'
    if core_pce <= 2.3 and core_cpi <= 3.0:
        return '낮음'
    return '중간'


def stress_position_text(summaries: dict[str, dict[str, float | str]]) -> str:
    hy_oas = float(summaries['HY OAS']['current'])
    if hy_oas <= 320:
        return '안정'
    if hy_oas <= 450:
        return '경계'
    return '위험'


def liquidity_trend_text(summaries: dict[str, dict[str, float | str]]) -> str:
    tga_trend = str(summaries['TGA']['trend'])
    reserve_trend = str(summaries['Reserve Balances']['trend'])
    rrp_trend = str(summaries['RRP']['trend'])
    if '상승' in tga_trend and ('하락' in reserve_trend or '하락' in rrp_trend):
        return '완만한 약화'
    if '하락' in tga_trend and ('상승' in reserve_trend or '상승' in rrp_trend):
        return '완만한 개선'
    return '혼조'


def inflation_trend_text(summaries: dict[str, dict[str, float | str]]) -> str:
    core_pce_trend = str(summaries['Core PCE YoY']['trend'])
    cpi_trend = str(summaries['CPI YoY']['trend'])
    if '하락' in core_pce_trend and '하락' in cpi_trend:
        return '둔화 지속'
    if '상승' in core_pce_trend or '상승' in cpi_trend:
        return '반등 경계'
    return '혼조'


def stress_trend_text(summaries: dict[str, dict[str, float | str]]) -> str:
    hy_trend = str(summaries['HY OAS']['trend'])
    if '하락' in hy_trend:
        return '안정 유지'
    if '상승' in hy_trend:
        return '긴장 누적'
    return '횡보'


def final_take_text(summaries: dict[str, dict[str, float | str]]) -> str:
    liquidity = liquidity_position_text(summaries)
    inflation = inflation_position_text(summaries)
    stress = stress_position_text(summaries)
    if liquidity == '중간 이하' and inflation == '중간 이상' and stress == '안정':
        return '강하게 추격 매수하기보다, 선별적으로 대응하는 편이 유리한 구간입니다.'
    if stress == '위험':
        return '지금은 방어 우선으로 보고, 위험자산 노출을 빠르게 점검하는 편이 좋습니다.'
    if liquidity == '중간 이상' and inflation in {'낮음', '중간'} and stress == '안정':
        return '유동성과 스트레스 환경은 비교적 우호적이지만, 무리한 낙관보다 분할 접근이 좋습니다.'
    return '완전한 위험장은 아니지만, 강하게 낙관하기엔 아직 부담이 남아 있습니다.'


def percentile_line(name: str, summaries: dict[str, dict[str, float | str]]) -> str:
    metric = summaries[name]
    current = format_value_with_unit(float(metric['current']), str(metric['unit']), int(metric['decimals']))
    percentile = round(float(metric['percentile']))
    meaning_map = {
        'TGA': '시장 돈을 빨아들이는 쪽',
        'RRP': '완충재가 거의 소진된 바닥권',
        'Reserve Balances': '아직 버티지만 예전보다 여유는 줄어든 상태',
        'Core PCE YoY': '물가 부담이 완전히 해소된 단계는 아님',
        'HY OAS': '신용시장은 아직 차분한 편',
    }
    label_map = {
        'TGA': 'TGA',
        'RRP': 'RRP',
        'Reserve Balances': 'Reserve',
        'Core PCE YoY': 'Core PCE',
        'HY OAS': 'HY OAS',
    }
    return f"- {label_map[name]}: {current} (최근 3년 {percentile}% 위치) → {meaning_map[name]}"


def build_daily_telegram(report_date: str, summaries: dict[str, dict[str, float | str]]) -> str:
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    liquidity_position = liquidity_position_text(summaries)
    inflation_position = inflation_position_text(summaries)
    stress_position = stress_position_text(summaries)
    liquidity_trend = liquidity_trend_text(summaries)
    inflation_trend = inflation_trend_text(summaries)
    stress_trend = stress_trend_text(summaries)
    final_take = final_take_text(summaries)
    one_line = (
        f'유동성은 {liquidity_position} 구간이고 물가는 {inflation_position} 수준이라, '
        f'시장을 편하게 낙관하긴 아직 이른 자리입니다.'
    )
    return f'''📌 메르 데일리 매크로 ({report_date})

[한줄 결론]
{one_line}

[큰 위치]
- 유동성: {liquidity_position}
- 물가: {inflation_position}
- 스트레스: {stress_position}

[장기추세]
- 유동성: {liquidity_trend}
- 물가: {inflation_trend}
- 스트레스: {stress_trend}

[오늘 해석]
{final_take}

[핵심 숫자]
{percentile_line('TGA', summaries)}
{percentile_line('RRP', summaries)}
{percentile_line('Reserve Balances', summaries)}
{percentile_line('Core PCE YoY', summaries)}
{percentile_line('HY OAS', summaries)}

• 생성시각: {generated_at}
'''


def build_weekly_note(report_date: str, week_label: str, summaries: dict[str, dict[str, float | str]]) -> str:
    d = summaries['weekly_delta']
    return f'''# Weekly Macro Summary - {week_label}

## 이번 주 차트 요약
- 기준일: {report_date}
- 핵심 변화(1주):
  - 유동성: TGA {format_delta_with_unit(float(d['TGA']), 'T', 2)}, RRP {format_delta_with_unit(float(d['RRP']), 'T', 2)}, Reserves {format_delta_with_unit(float(d['Reserve Balances']), 'T', 2)}
  - 물가(YoY): CPI {d['CPI YoY']:+.2f}%p, Core CPI {d['Core CPI YoY']:+.2f}%p, PCE {d['PCE YoY']:+.2f}%p, Core PCE {d['Core PCE YoY']:+.2f}%p
  - 스트레스: HY OAS {d['HY OAS']:+.2f}bp

## 해석
- Liquidity와 Inflation의 동시 방향을 먼저 보고, HY OAS로 리스크온/오프 강도를 확인하세요.
- 첨부한 주간 핵심 변화 차트(가로 막대)로 절대 크기를 한 번에 파악할 수 있습니다.
'''


def build_weekly_telegram(report_date: str, week_label: str, summaries: dict[str, dict[str, float | str]]) -> str:
    d = summaries['weekly_delta']
    return f'''📌 메르 주간 매크로 ({week_label})

[주간 핵심 변화, 1W]
• Liquidity: TGA {format_delta_with_unit(float(d['TGA']), 'T', 2)} / RRP {format_delta_with_unit(float(d['RRP']), 'T', 2)} / Reserves {format_delta_with_unit(float(d['Reserve Balances']), 'T', 2)}
• Inflation(YoY): CPI {d['CPI YoY']:+.2f}%p, Core CPI {d['Core CPI YoY']:+.2f}%p, PCE {d['PCE YoY']:+.2f}%p, Core PCE {d['Core PCE YoY']:+.2f}%p
• Stress: HY OAS {d['HY OAS']:+.2f}bp

첨부: 주간 핵심 변화 차트(막대) + 데일리 3종 차트
기준일: {report_date}
'''


def write_outputs(report_date: str, weekly: bool = False) -> tuple[Path, Path, dict[str, Path]]:
    base = Path('invest/notes/daily-macro')
    base.mkdir(parents=True, exist_ok=True)
    note_path = base / f'{report_date}.md'
    telegram_path = base / f'{report_date}.telegram.txt'

    charts, summaries = generate_charts(report_date, years=3)
    note_path.write_text(build_daily_note(report_date, summaries), encoding='utf-8')
    telegram_path.write_text(build_daily_telegram(report_date, summaries), encoding='utf-8')

    if weekly:
        weekly_dir = base / 'weekly'
        weekly_dir.mkdir(parents=True, exist_ok=True)
        week_label = datetime.strptime(report_date, '%Y-%m-%d').strftime('%Y-W%V')
        weekly_chart = generate_weekly_chart(report_date, summaries)
        charts['weekly'] = weekly_chart
        (weekly_dir / f'{week_label}.md').write_text(build_weekly_note(report_date, week_label, summaries), encoding='utf-8')
        (weekly_dir / f'{week_label}.telegram.txt').write_text(build_weekly_telegram(report_date, week_label, summaries), encoding='utf-8')

    return note_path, telegram_path, charts


def send_telegram(channel: str, target: str, message: str, charts: dict[str, Path]) -> None:
    msg_cmd = [
        'openclaw',
        'message',
        'send',
        '--channel',
        channel,
        '--target',
        target,
        '--message',
        message,
        '--json',
    ]
    msg_result = subprocess.run(msg_cmd, capture_output=True, text=True, check=False)
    if msg_result.returncode != 0:
        raise RuntimeError(f'Message send failed: {msg_result.stderr or msg_result.stdout}')

    captions = {
        'liquidity': '메르 Liquidity 차트 (TGA/RRP/Reserves, 평균선+현재점+3T 가이드)',
        'inflation': '메르 Inflation 차트 (CPI/Core CPI/PCE/Core PCE, 평균선+현재점)',
        'stress': '메르 Stress 차트 (HY OAS, 평균선+현재점)',
        'weekly': '메르 Weekly 핵심 변화 차트 (1주 증감 막대 요약)',
    }

    media_payloads = {}
    for key in ['liquidity', 'inflation', 'stress', 'weekly']:
        if key not in charts:
            continue
        media_cmd = [
            'openclaw',
            'message',
            'send',
            '--channel',
            channel,
            '--target',
            target,
            '--media',
            str(charts[key]),
            '--message',
            captions[key],
            '--json',
        ]
        media_result = subprocess.run(media_cmd, capture_output=True, text=True, check=False)
        if media_result.returncode != 0:
            raise RuntimeError(f'Chart send failed ({key}): {media_result.stderr or media_result.stdout}')
        media_payloads[key] = media_result.stdout.strip()

    print(json.dumps({'message': msg_result.stdout.strip(), 'charts': media_payloads}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--date', required=True)
    p.add_argument('--weekly', action='store_true')
    p.add_argument('--send-telegram-test', action='store_true')
    p.add_argument('--telegram-target', default='5294188460')
    p.add_argument('--message-channel', default='telegram')
    return p.parse_args()


def main() -> int:
    configure_korean_font()
    args = parse_args()
    note_path, telegram_path, charts = write_outputs(args.date, weekly=args.weekly)
    print(note_path)
    print(telegram_path)
    for k in charts:
        print(charts[k])

    if args.send_telegram_test:
        telegram_text = telegram_path.read_text(encoding='utf-8')
        send_telegram(args.message_channel, args.telegram_target, telegram_text, charts)
        print('메르 데일리 매크로 리포트/차트 발송 완료')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
