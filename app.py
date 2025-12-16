import streamlit as st
import plotly.express as px
import pandas as pd

from storage import load_ticks
from resampler import resample_ticks
from analytics import (
    safe_hedge_ratio, zscore,
    rolling_corr, adf_test,
    mean_reversion_backtest
)
from alerts import check_alert

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Quant Trading Analytics Dashboard",
    page_icon="📈",
    layout="wide"
)

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ Controls")

st.sidebar.markdown("### 📂 Data Input")
file = st.sidebar.file_uploader("Upload NDJSON Tick File")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Resampling")
timeframe = st.sidebar.selectbox(
    "Timeframe", ["1s", "1m", "5m"], index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧮 Model Parameters")
window = st.sidebar.slider(
    "Rolling Window",
    min_value=10,
    max_value=100,
    value=30,
    step=5
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚨 Alerts")
threshold = st.sidebar.slider(
    "Z-Score Threshold",
    1.0, 3.0, 2.0, 0.1
)

# ---------------- Main ----------------
if file:
    df = load_ticks(file)

    st.markdown("## 📊 Quant Trading Analytics Dashboard")
    st.caption(
        "Statistical pair analysis with hedge ratios, spreads, z-scores, "
        "correlations, stationarity diagnostics, and alerts"
    )

    # -------- Symbol Selection --------
    st.markdown("### 🔀 Symbol Selection")
    col_sym1, col_sym2 = st.columns(2)
    with col_sym1:
        symbol_a = st.selectbox("Symbol A", df.symbol.unique())
    with col_sym2:
        symbol_b = st.selectbox("Symbol B", df.symbol.unique())

    if symbol_a == symbol_b:
        st.warning("Please select two different symbols.")
        st.stop()

    df_a = df[df.symbol == symbol_a]
    df_b = df[df.symbol == symbol_b]

    # -------- Resampling --------
    ohlc_a = resample_ticks(df_a, timeframe)
    ohlc_b = resample_ticks(df_b, timeframe)

    if ohlc_a.empty or ohlc_b.empty:
        st.error("No OHLC data available for selected timeframe.")
        st.stop()

    # -------- Normalize Prices --------
    a = ohlc_a["close"] / ohlc_a["close"].iloc[0]
    b = ohlc_b["close"] / ohlc_b["close"].iloc[0]

    # -------- Returns --------
    ret = pd.concat([a.pct_change(), b.pct_change()], axis=1)
    ret.columns = ["a", "b"]
    ret = ret.replace([float("inf"), float("-inf")], pd.NA).dropna()

    use_returns = len(ret) >= 5

    # -------- Hedge & Spread --------
    if use_returns:
        beta, mode = safe_hedge_ratio(ret["a"], ret["b"])
        spread = ret["a"] - beta * ret["b"]
        base_a, base_b = ret["a"], ret["b"]
    else:
        beta, mode = safe_hedge_ratio(a, b)
        spread = a - beta * b
        base_a, base_b = a, b

    if pd.isna(beta):
        st.warning("Hedge ratio unstable due to limited data.")
        spread = a - a.mean()
        mode = "fallback"

    # -------- Adaptive Rolling Window --------
    effective_window = min(window, max(5, len(spread) // 2))

    z = zscore(spread, effective_window)
    corr = rolling_corr(base_a, base_b, effective_window)

    # -------- Status Banner --------
    st.info(
        f"**Timeframe:** {timeframe}  |  "
        f"**Mode:** {'Returns' if use_returns else 'Prices'}  |  "
        f"**Hedge Method:** {mode.upper()}  |  "
        f"**Data Points:** {len(spread)}"
    )

    if len(spread) < 5:
        st.warning(
            "Very few data points at this timeframe. "
            "Rolling analytics may be unavailable."
        )

    # -------- Metrics --------
    st.markdown("### 📌 Key Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Hedge Ratio (β)", f"{beta:.4f}" if pd.notna(beta) else "N/A")
    m2.metric("Spread Mean", f"{spread.mean():.6f}")
    m3.metric("Spread Std Dev", f"{spread.std():.6f}")

    # -------- Alerts --------
    if not z.dropna().empty and check_alert(z, threshold):
        st.error("🚨 Z-score breach detected — potential trading signal")
    else:
        st.success("✅ Z-score within statistical bounds")

    # -------- Tabs --------
    tabs = st.tabs([
        "📈 Prices",
        "📉 Returns",
        "🔀 Spread",
        "📊 Z-Score",
        "🔗 Correlation",
        "🧪 ADF Test",
        "💰 Backtest",
        "📥 Data Export"
    ])

    # -------- Prices --------
    with tabs[0]:
        st.plotly_chart(
            px.line(
                pd.DataFrame({symbol_a: a, symbol_b: b}),
                title="Normalized Prices"
            ),
            use_container_width=True
        )

    # -------- Returns --------
    with tabs[1]:
        if use_returns:
            st.plotly_chart(
                px.line(ret, title="Asset Returns"),
                use_container_width=True
            )
        else:
            st.info("Returns unavailable at this timeframe.")

    # -------- Spread --------
    with tabs[2]:
        st.plotly_chart(
            px.line(spread, title="Spread"),
            use_container_width=True
        )

    # -------- Z-Score --------
    with tabs[3]:
        if z.dropna().empty:
            st.info("Not enough data points to compute Z-score.")
        else:
            st.plotly_chart(
                px.line(z, title="Rolling Z-Score"),
                use_container_width=True
            )

    # -------- Correlation --------
    with tabs[4]:
        if corr.dropna().empty:
            st.info("Not enough data points to compute correlation.")
        else:
            st.plotly_chart(
                px.line(corr, title="Rolling Correlation"),
                use_container_width=True
            )

    # -------- ADF Test --------
    with tabs[5]:
        if spread.dropna().shape[0] < 10:
            st.info("Insufficient data for ADF test.")
        else:
            if st.button("Run ADF Test"):
                st.json(adf_test(spread))

    # -------- Backtest --------
    with tabs[6]:
        if z.dropna().empty:
            st.info("Not enough data points to run backtest.")
        else:
            pos = mean_reversion_backtest(z)
            pnl = (pos.shift(1) * spread).cumsum()
            st.plotly_chart(
                px.line(pnl, title="Cumulative Strategy PnL"),
                use_container_width=True
            )

    # -------- Data Export --------
    with tabs[7]:
        st.markdown("### 📥 Download Analytics as CSV")

        st.download_button(
            "⬇️ Download Spread",
            spread.to_csv().encode("utf-8"),
            file_name="spread.csv",
            mime="text/csv"
        )

        if not z.dropna().empty:
            st.download_button(
                "⬇️ Download Z-Score",
                z.to_csv().encode("utf-8"),
                file_name="zscore.csv",
                mime="text/csv"
            )
        else:
            st.info("Z-score not available for this timeframe.")

        if not corr.dropna().empty:
            st.download_button(
                "⬇️ Download Correlation",
                corr.to_csv().encode("utf-8"),
                file_name="correlation.csv",
                mime="text/csv"
            )
        else:
            st.info("Correlation not available for this timeframe.")

        if not z.dropna().empty:
            pnl = (mean_reversion_backtest(z).shift(1) * spread).cumsum()
            st.download_button(
                "⬇️ Download Backtest PnL",
                pnl.to_csv().encode("utf-8"),
                file_name="backtest_pnl.csv",
                mime="text/csv"
            )
        else:
            st.info("Backtest not available for this timeframe.")
