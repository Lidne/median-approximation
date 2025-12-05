import json
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
from config import config
from matplotlib.widgets import CheckButtons
from tinkoff.invest import Client
from tinkoff.invest.schemas import CandleInterval


def main():
    instruments = []

    # specific path handling to locate the config file relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "configs", "figis.json")

    with open(config_path, "r") as f:
        instruments = json.load(f)

    all_deltas = []
    labels = []

    with Client(config.TINVEST_TOKEN) as client:
        for instrument in instruments:
            print(f"Fetching data for {instrument['ticker']}...")
            try:
                response = client.market_data.get_candles(
                    figi=instrument["figi"],
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                    from_=datetime.now() - timedelta(days=1),
                    to=datetime.now(),
                )

                deltas = []
                for candle in response.candles:
                    close_price = candle.close.units + candle.close.nano / 1e9
                    open_price = candle.open.units + candle.open.nano / 1e9
                    deltas.append(abs(close_price - open_price))

                if deltas:
                    all_deltas.append(pd.Series(data=deltas))
                    labels.append(instrument["ticker"])
            except Exception as e:
                print(f"Error fetching {instrument['ticker']}: {e}")

    if not all_deltas:
        print("No data collected.")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    plt.subplots_adjust(right=0.8)

    # Histogram of Deltas
    _, _, patches1 = ax1.hist(all_deltas, bins=50, label=labels, alpha=0.7)
    ax1.set_title("Distribution of Deltas")
    ax1.set_xlabel("Delta Value")
    ax1.set_ylabel("Frequency")
    ax1.legend(loc="upper right")
    ax1.grid(True)

    # Log histogram of Deltas
    _, _, patches2 = ax2.hist(all_deltas, bins=50, label=labels, alpha=0.7, log=True)
    ax2.set_title("Distribution of Deltas (Log Scale)")
    ax2.set_xlabel("Delta Value")
    ax2.set_ylabel("Frequency")
    ax2.legend(loc="upper right")
    ax2.grid(True)

    # CheckButtons for visibility
    rax = plt.axes((0.82, 0.1, 0.15, 0.8))  # [left, bottom, width, height]
    check = CheckButtons(rax, labels, [True] * len(labels))

    def func(label):
        index = labels.index(label)
        # Toggle visibility for both plots
        # patches1[index] is a BarContainer, we iterate over its patches
        for patch in patches1[index]:
            patch.set_visible(not patch.get_visible())
        for patch in patches2[index]:
            patch.set_visible(not patch.get_visible())
        plt.draw()

    check.on_clicked(func)

    plt.show()


if __name__ == "__main__":
    main()
