import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
from config import config
from tinkoff.invest import Client
from tinkoff.invest.schemas import CandleInterval


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <figi> <window_size>")
        sys.exit(1)

    figi = sys.argv[1]
    window_size = int(sys.argv[2])

    with Client(config.TINVEST_TOKEN) as client:
        response = client.market_data.get_candles(
            figi=figi,
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
            from_=datetime.now() - timedelta(days=1),
            to=datetime.now(),
        )

    deltas = []
    timestamps = []

    for candle in response.candles:
        close_price = candle.close.units + candle.close.nano / 1e9
        open_price = candle.open.units + candle.open.nano / 1e9
        deltas.append(abs(close_price - open_price))
        timestamps.append(candle.time)

    series = pd.Series(data=deltas, index=timestamps)

    rolling = series.rolling(window=window_size, min_periods=1)
    mean = rolling.mean()
    std = rolling.std()
    median = rolling.median()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Rolling Window Analysis
    ax1.plot(series.index, series, label="Delta (Close - Open)", alpha=0.3)
    ax1.plot(series.index, mean, label="Rolling Mean")
    ax1.plot(series.index, median, label="Rolling Median")
    ax1.plot(series.index, std, label="Rolling Std Dev", linestyle="--")

    ax1.set_title(f"Rolling Window Analysis (Window Size: {window_size})")
    ax1.legend()
    ax1.grid(True)

    # Histogram of Deltas
    ax2.hist(series, bins=50, color="skyblue", edgecolor="black", alpha=0.7, log=True)
    ax2.set_title("Distribution of Deltas (Log Scale)")
    ax2.set_xlabel("Delta Value")
    ax2.set_ylabel("Frequency")
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
