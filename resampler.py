import pandas as pd

MAP = {
    "1s": "1S",
    "1m": "1min",
    "5m": "5min"
}

def resample_ticks(df, timeframe):
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Index must be DatetimeIndex")

    freq = MAP[timeframe]
    ohlc = df["price"].resample(freq).ohlc()

    return ohlc.dropna()
