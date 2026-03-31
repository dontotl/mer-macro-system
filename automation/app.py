from __future__ import annotations

import streamlit as st

from automation.run_backtest import run

st.set_page_config(page_title="KRX RS Trend App", layout="wide")
st.title("KRX RS 추세추종 백테스트")
st.caption("PyKRX 기반 · RS 상위 · 신고가 · 정배열 · 유닛 피라미딩 전략")

if st.button("10년 백테스트 실행"):
    with st.spinner("백테스트 실행 중..."):
        equity_curve, trades, summary = run()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Return", f"{summary.total_return:.2%}")
    c2.metric("CAGR", f"{summary.cagr:.2%}")
    c3.metric("MDD", f"{summary.mdd:.2%}")
    c4.metric("Sharpe", f"{summary.sharpe:.2f}")

    st.line_chart(equity_curve)
    st.dataframe(trades)
