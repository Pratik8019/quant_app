import pandas as pd
import json

def load_ticks(uploaded_file):
    rows = []
    content = uploaded_file.read().decode("utf-8")

    for line in content.splitlines():
        if line.strip():
            rows.append(json.loads(line))

    df = pd.DataFrame(rows)

    for col in ["timestamp", "ts", "E", "T"]:
        if col in df.columns:
            ts_col = col
            break
    else:
        raise ValueError("No timestamp column found")

    df["timestamp"] = pd.to_datetime(
        df[ts_col],
        utc=True,
        errors="coerce"
    )

    df = df.dropna(subset=["timestamp"])
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    if "price" not in df.columns and "p" in df.columns:
        df["price"] = df["p"]

    if "symbol" not in df.columns and "s" in df.columns:
        df["symbol"] = df["s"]

    df["price"] = df["price"].astype(float)

    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df
