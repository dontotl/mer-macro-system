from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def build_daily_note(report_date: str) -> str:
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'''# Daily Macro Note - {report_date}

## Summary
| 모듈 | 현재 상태 | 한 줄 판단 |
|---|---|---|
| Liquidity | 경계적 완화 | 돈은 아직 돌지만 완충재가 약해 흔들릴 수 있습니다. |
| Stress | 안정 | 아직 큰 불안 신호는 아닙니다. |
| Inflation | 재가속 경계 | 물가가 다시 오를 수 있어 시장 부담이 남아 있습니다. |
| Money Scale | 축소 | 돈의 크기는 조금 줄어드는 방향입니다. |
| Policy | 대기 | 연준이 바로 방향을 바꾼 상태는 아닙니다. |

- Note date: {report_date}
- Data extracted at: {generated_at}

## Final Take
- 한줄 결론: 돈은 아직 좀 돌고 있지만, 물가가 다시 오를 수 있어서 주식시장이 흔들릴 수 있는 상태입니다.
- 종합 판단: 유동성은 아직 버티지만, 물가와 정책 부담 때문에 편하게 낙관하기는 이릅니다.
- 핵심 근거: RRP 바닥권, 인플레이션 재가속 경계, 정책 대기 구간.
- 리스크 포인트: Repo/Policy 세부 데이터 자동연결은 아직 보강이 필요합니다.
'''


def build_daily_telegram(report_date: str) -> str:
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'''📌 메르 데일리 매크로 ({report_date})

[한줄 결론]
• 돈은 아직 좀 돌고 있지만, 물가가 다시 오를 수 있어서 주식시장이 흔들릴 수 있는 상태입니다.
• Liquidity: 경계적 완화
• Inflation: 재가속 경계
• Stress/Policy: 안정·대기

[핵심 메모]
• 지금은 아주 위험한 장은 아니지만, 마음 놓고 강하게 낙관하기도 이른 구간입니다.
• 생성시각: {generated_at}
'''


def generate_chart(report_date: str) -> Path:
    import matplotlib.pyplot as plt

    labels = ['TGA', 'RRP', 'Reserves']
    values = [0.8, 0.35, 3.2]  # trillions USD (sample)

    charts_dir = Path('invest/notes/daily-macro/charts')
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_path = charts_dir / f'{report_date}-liquidity.png'

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color=['#4E79A7', '#F28E2B', '#59A14F'])
    ax.axhline(3.0, linestyle='--', linewidth=1, color='#E15759', label='3.0T guide')
    ax.set_title(f'Mer Liquidity Snapshot ({report_date})')
    ax.set_ylabel('USD Trillion')
    ax.set_ylim(0, 3.8)
    ax.legend(loc='upper left')

    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.05, f'{v:.2f}T', ha='center', fontsize=9)

    fig.tight_layout()
    fig.savefig(chart_path, dpi=140)
    plt.close(fig)
    return chart_path


def write_outputs(report_date: str, weekly: bool = False) -> tuple[Path, Path, Path]:
    base = Path('invest/notes/daily-macro')
    base.mkdir(parents=True, exist_ok=True)
    note_path = base / f'{report_date}.md'
    telegram_path = base / f'{report_date}.telegram.txt'
    note_path.write_text(build_daily_note(report_date), encoding='utf-8')
    telegram_path.write_text(build_daily_telegram(report_date), encoding='utf-8')
    chart_path = generate_chart(report_date)

    if weekly:
        weekly_dir = base / 'weekly'
        weekly_dir.mkdir(parents=True, exist_ok=True)
        week_label = datetime.strptime(report_date, '%Y-%m-%d').strftime('%Y-W%V')
        (weekly_dir / f'{week_label}.md').write_text(
            f'# Weekly Macro Summary - {week_label}\n\n- 이번 주 한줄: 물가 부담이 남아 있어 시장은 오르더라도 흔들릴 수 있습니다.\n',
            encoding='utf-8',
        )
        (weekly_dir / f'{week_label}.telegram.txt').write_text(
            f'📌 주간 매크로 요약 ({week_label})\n- 물가 부담이 남아 있어 시장은 오르더라도 흔들릴 수 있습니다.\n',
            encoding='utf-8',
        )

    return note_path, telegram_path, chart_path


def send_telegram(channel: str, target: str, message: str, chart_path: Path) -> None:
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

    media_cmd = [
        'openclaw',
        'message',
        'send',
        '--channel',
        channel,
        '--target',
        target,
        '--media',
        str(chart_path),
        '--message',
        '메르 유동성 차트',
        '--json',
    ]
    media_result = subprocess.run(media_cmd, capture_output=True, text=True, check=False)
    if media_result.returncode != 0:
        raise RuntimeError(f'Chart send failed: {media_result.stderr or media_result.stdout}')

    # log compact success payload for callers
    print(json.dumps({'message': msg_result.stdout.strip(), 'chart': media_result.stdout.strip()}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--date', required=True)
    p.add_argument('--weekly', action='store_true')
    p.add_argument('--send-telegram-test', action='store_true')
    p.add_argument('--telegram-target', default='5294188460')
    p.add_argument('--message-channel', default='telegram')
    return p.parse_args()


def main() -> int:
    args = parse_args()
    note_path, telegram_path, chart_path = write_outputs(args.date, weekly=args.weekly)
    print(note_path)
    print(telegram_path)
    print(chart_path)
    if args.send_telegram_test:
        telegram_text = telegram_path.read_text(encoding='utf-8')
        send_telegram(args.message_channel, args.telegram_target, telegram_text, chart_path)
        print('메르 데일리 매크로 리포트 발송 완료')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
