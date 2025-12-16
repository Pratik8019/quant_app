import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


def safe_hedge_ratio(series_a, series_b):
    """
    Robust hedge ratio estimation:
    1. OLS if possible
    2. Fallback to ratio hedge if variance too low
    """

    df = pd.concat(
        [series_a.rename("a"), series_b.rename("b")],
        axis=1
    )

    df = df.replace([float("inf"), float("-inf")], pd.NA).dropna()

    # -------- Check variance --------
    if df["a"].std() < 1e-8 or df["b"].std() < 1e-8:
        # Ratio hedge fallback
        ratio = df["a"].mean() / df["b"].mean()
        return ratio, "ratio"

    if len(df) < 5:
        return float("nan"), "insufficient"

    X = sm.add_constant(df["b"])
    y = df["a"]

    try:
        beta = sm.OLS(y, X).fit().params["b"]
        return beta, "ols"
    except Exception:
        ratio = df["a"].mean() / df["b"].mean()
        return ratio, "ratio"


def zscore(series, window=30):
    return (series - series.rolling(window).mean()) / series.rolling(window).std()


def rolling_corr(series_a, series_b, window=30):
    return series_a.rolling(window).corr(series_b)


def adf_test(series):
    series = series.replace([float("inf"), float("-inf")], pd.NA).dropna()
    result = adfuller(series)
    return {
        "ADF Statistic": result[0],
        "p-value": result[1],
        "Used Lags": result[2],
        "Observations": result[3]
    }


def mean_reversion_backtest(z, entry=2.0, exit=0.0):
    pos = 0
    positions = []

    z = z.dropna()

    for val in z:
        if val > entry:
            pos = -1
        elif val < -entry:
            pos = 1
        elif abs(val) < exit:
            pos = 0
        positions.append(pos)

    return pd.Series(positions, index=z.index)
