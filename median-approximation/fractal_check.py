import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import config
from t_tech.invest import Client
from t_tech.invest.schemas import CandleInterval


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <figi> <power ceiling>")
        sys.exit(1)

    figi = sys.argv[1]
    power_ceiling = int(sys.argv[2])

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

    deltas_series = []
    for i in range(1, power_ceiling + 1):
        deltas_series.append(series.resample(f"{2**i}min").sum())

    std_devs = []
    for i, deltas in enumerate(deltas_series):
        std = deltas.std()
        print(f"std of {i + 1}min deltas: {std}")
        std_devs.append(std)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Graph of Sigma vs Delta t
    time_intervals = [2**i for i in range(1, power_ceiling + 1)]

    ax1.plot(time_intervals, std_devs, marker="o", color="skyblue")
    ax1.set_title("σ(Δt) vs Δt")
    ax1.set_xlabel("Δt (min)")
    ax1.set_ylabel("σ(Δt)")
    ax1.grid(True)

    # Graph of Sigma vs Delta t (Log scale)
    ax2.loglog(time_intervals, std_devs, marker="o", color="skyblue", label="Data")

    # Linear approximation
    log_x = np.log(time_intervals)
    log_y = np.log(std_devs)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    y_fit = np.exp(intercept + slope * log_x)
    print(f"Herst koeff: {slope}")

    ax2.loglog(time_intervals, y_fit, "r--", label=f"Linear Approx (slope={slope:.2f})")
    ax2.legend()

    ax2.set_title("σ(Δt) vs Δt (Log-Log scale)")
    ax2.set_xlabel("Δt (min)")
    ax2.set_ylabel("σ(Δt)")
    ax2.set_xticks(time_intervals)
    ax2.set_xticklabels(time_intervals)
    ax2.grid(True, which="both", linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
