def check_alert(z, threshold):
    z = z.dropna()
    if len(z) == 0:
        return False
    return abs(z.iloc[-1]) > threshold
