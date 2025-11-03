import pandas as pd
import numpy as np
import time
import datetime
import os

# -------------------------------
# PSX Signals 1H App (Usman Build)
# -------------------------------

# فائل لوڈ کریں (psx.xlsx یا API سے)
data_file = "psx.xlsx"

def load_data():
    if os.path.exists(data_file):
        df = pd.read_excel(data_file)
    else:
        df = pd.DataFrame({
            "Symbol": ["OGDC", "HBL", "ENGRO", "PSO", "TRG", "LUCK"],
            "Open": np.random.uniform(80, 600, 6),
            "High": np.random.uniform(100, 620, 6),
            "Low": np.random.uniform(70, 580, 6),
            "Close": np.random.uniform(80, 600, 6)
        })
    return df

def generate_signals(df):
    signals = []
    for i in range(len(df)):
        row = df.iloc[i]
        avg_price = (row["High"] + row["Low"]) / 2
        direction = "BUY" if row["Close"] > avg_price else "SELL"

        tp = row["Close"] * (1.02 if direction == "BUY" else 0.98)
        sl = row["Close"] * (0.98 if direction == "BUY" else 1.02)

        signals.append({
            "Symbol": row["Symbol"],
            "Signal": direction,
            "Price": round(row["Close"], 2),
            "TakeProfit": round(tp, 2),
            "StopLoss": round(sl, 2),
            "TimeFrame": "1H"
        })
    return pd.DataFrame(signals)

def display_signals(df):
    print("\n🟩 PSX BUY/SELL SIGNALS (1 Hour Frame)\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    while True:
        data = load_data()
        signals = generate_signals(data)
        os.system('cls' if os.name == 'nt' else 'clear')
        display_signals(signals)
        print("\nUpdated:", datetime.datetime.now().strftime("%H:%M:%S"))
        time.sleep(60 * 60)  # ہر گھنٹے بعد اپڈیٹ
