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
        "and stationarity diagnostics"
    )

    # -------- Symbol Selection --------
    with st.container():
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

    # -------- Normalize Prices --------
    a = ohlc_a["close"] / ohlc_a["close"].iloc[0]
    b = ohlc_b["close"] / ohlc_b["close"].iloc[0]

    # -------- Returns --------
    ret = pd.concat([a.pct_change(), b.pct_change()], axis=1)
    ret.columns = ["a", "b"]
    ret = ret.replace([float("inf"), float("-inf")], pd.NA).dropna()

    use_returns = len(ret) >= 5

    if use_returns:
        beta, mode = safe_hedge_ratio(ret["a"], ret["b"])
        spread = ret["a"] - beta * ret["b"]
        base_a, base_b = ret["a"], ret["b"]
    else:
        beta, mode = safe_hedge_ratio(a, b)
        spread = a - beta * b
        base_a, base_b = a, b

    if pd.isna(beta):
        st.error("Hedge ratio cannot be estimated for this dataset.")
        st.stop()

    z = zscore(spread, window)
    corr = rolling_corr(base_a, base_b, window)

    # ---------------- Status Banner ----------------
    st.info(
        f"**Mode:** {'Returns-based' if use_returns else 'Price-based'}  |  "
        f"**Hedge Method:** {mode.upper()}  |  "
        f"**Observations:** {len(spread)}"
    )

    # ---------------- Metrics ----------------
    st.markdown("### 📌 Key Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Hedge Ratio (β)", f"{beta:.4f}")
    m2.metric("Spread Mean", f"{spread.mean():.6f}")
    m3.metric("Spread Std Dev", f"{spread.std():.6f}")

    # ---------------- Alerts ----------------
    if check_alert(z, threshold):
        st.error("🚨 Z-score breach detected — potential trading signal")
    else:
        st.success("✅ Z-score within statistical bounds")

    # ---------------- Tabs ----------------
    tabs = st.tabs([
        "📈 Prices",
        "📉 Returns",
        "🔀 Spread",
        "📊 Z-Score",
        "🔗 Correlation",
        "🧪 ADF Test",
        "💰 Backtest"
    ])

    with tabs[0]:
        st.plotly_chart(
            px.line(
                pd.DataFrame({symbol_a: a, symbol_b: b}),
                title="Normalized Prices"
            ),
            use_container_width=True
        )

    with tabs[1]:
        if use_returns:
            st.plotly_chart(
                px.line(ret, title="Asset Returns"),
                use_container_width=True
            )
        else:
            st.info("Returns unavailable due to low variance in price data.")

    with tabs[2]:
        st.plotly_chart(
            px.line(spread, title="Spread"),
            use_container_width=True
        )

    with tabs[3]:
        st.plotly_chart(
            px.line(z, title="Rolling Z-Score"),
            use_container_width=True
        )

    with tabs[4]:
        st.plotly_chart(
            px.line(corr, title="Rolling Correlation"),
            use_container_width=True
        )

    with tabs[5]:
        st.markdown("### 🧪 Stationarity Test (ADF)")
        if st.button("Run ADF Test"):
            st.json(adf_test(spread))

    with tabs[6]:
        pos = mean_reversion_backtest(z)
        pnl = (pos.shift(1) * spread).cumsum()

        st.plotly_chart(
            px.line(pnl, title="Cumulative Strategy PnL"),
            use_container_width=True
        )
