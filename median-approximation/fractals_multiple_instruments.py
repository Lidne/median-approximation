import json
import os
import random
import sys
from datetime import datetime, timedelta
from string import ascii_letters, digits

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import config
from matplotlib.widgets import CheckButtons
from tinkoff.invest import Client
from tinkoff.invest.schemas import CandleInterval

ALLOWED_SYMBOLS = ascii_letters + digits


def calculate_fractal_stats(figi, power_ceiling, client):
    """
    Calculates the std dev series for a given figi.
    """
    response = client.market_data.get_candles(
        figi=figi,
        interval=CandleInterval.CANDLE_INTERVAL_5_SEC,
        from_=datetime.now() - timedelta(minutes=199),
        to=datetime.now(),
    )

    deltas = []
    timestamps = []

    for candle in response.candles:
        close_price = candle.close.units + candle.close.nano / 1e9
        open_price = candle.open.units + candle.open.nano / 1e9
        deltas.append(abs(close_price - open_price))
        timestamps.append(candle.time)

    if not deltas:
        return None, None

    series = pd.Series(data=deltas, index=timestamps)

    deltas_series = []
    for i in range(1, power_ceiling + 1):
        deltas_series.append(series.resample(f"{i}min").sum())

    std_devs = []
    for deltas in deltas_series:
        std = deltas.std()
        std_devs.append(std)

    return std_devs, [i for i in range(1, power_ceiling + 1)]


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <power ceiling>")
        sys.exit(1)

    power_ceiling = int(sys.argv[1])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "configs", "figis.json")

    with open(config_path, "r") as f:
        instruments = json.load(f)

    plot_data = {}  # Store plot data for toggling: {label: {'lines': [], 'color': color}}
    slope_data = {}

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    plt.subplots_adjust(right=0.8)

    colors = plt.cm.get_cmap("tab10")(np.linspace(0, 1, len(instruments)))

    with Client(config.TINVEST_TOKEN) as client:
        for idx, instrument in enumerate(instruments):
            ticker = instrument["ticker"]
            print(f"Processing {ticker}...")

            try:
                std_devs, time_intervals = calculate_fractal_stats(instrument["figi"], power_ceiling, client)

                if std_devs is None:
                    print(f"No data for {ticker}")
                    continue

                color = colors[idx]

                # Plot 1: Sigma vs Delta t
                (line1,) = ax1.plot(time_intervals, std_devs, marker="o", color=color, label=ticker)

                # Plot 2: Log-Log Sigma vs Delta t
                (line2,) = ax2.loglog(time_intervals, std_devs, marker="o", color=color, label=ticker)

                # Linear approximation
                log_x = np.log(np.array(time_intervals))
                log_y = np.log(np.array(std_devs))
                slope, intercept = np.polyfit(log_x, log_y, 1)
                slope_data[ticker] = slope
                y_fit = np.exp(intercept + slope * log_x)

                (line3,) = ax2.loglog(
                    time_intervals, y_fit, linestyle="--", color=color, alpha=0.7, label=f"{ticker} (slope={slope:.2f})"
                )

                plot_data[ticker] = [line1, line2, line3]

            except Exception as e:
                print(f"Error processing {ticker}: {e}")

    # Setup Axes 1
    ax1.set_title("σ(Δt) vs Δt")
    ax1.set_xlabel("Δt (min)")
    ax1.set_ylabel("σ(Δt)")
    ax1.grid(True)
    # ax1.legend(loc="upper left", bbox_to_anchor=(1, 1))

    # Setup Axes 2
    ax2.set_title("σ(Δt) vs Δt (Log-Log scale)")
    ax2.set_xlabel("Δt (min)")
    ax2.set_ylabel("σ(Δt)")

    # CheckButtons
    labels = list(plot_data.keys())

    # Set xticks based on the last computed time_intervals (assuming all are same)
    if labels and plot_data:
        # Extract time intervals from the first plot data
        first_ticker = labels[0]
        # line1 data (x-axis)
        time_intervals_data = plot_data[first_ticker][0].get_xdata()
        ax2.set_xticks(time_intervals_data)
        ax2.set_xticklabels(time_intervals_data)

    result_file = os.path.join(script_dir, "results", f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    with open(result_file, mode="x") as results:
        json.dump(slope_data, results)

    ax2.grid(True, which="both", linestyle="--", alpha=0.7)
    # ax2.legend(loc="upper left", bbox_to_anchor=(1, 1))

    rax = plt.axes((0.82, 0.1, 0.15, 0.8))
    check = CheckButtons(rax, labels, [True] * len(labels))

    def func(label):
        lines = plot_data[label]
        for line in lines:
            line.set_visible(not line.get_visible())
        plt.draw()

    check.on_clicked(func)

    plt.show()


if __name__ == "__main__":
    main()
