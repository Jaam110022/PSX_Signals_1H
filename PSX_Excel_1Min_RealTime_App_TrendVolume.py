# PSX_Excel_1Min_RealTime_App_TrendVolume.py
"""
PSX Signals 1H — Trend + Volume based signals + ATR TP/SL + Alerts
- Reads psx.xlsx (Tickers column)
- Adds '.KA' suffix automatically if missing
- Fetches 1-hour bars via yfinance (fallback)
- Strategy:
    * Trend filter: EMA 20 / EMA 50 crossover
    * Volume filter: Volume > Volume_MA(20) * VOL_MULT (default 1.6) => indicates interest
    * RSI optional filter (avoid overbought/oversold)
    * Require both crossover and volume spike to generate BUY/SELL
- ATR-based TP/SL (SL = 1*ATR, TP = 2*ATR)
- Auto-refresh every 60 seconds
- Saves latest snapshot to psx_signals_latest_trendvol.csv
- Popup + beep on new BUY/SELL
"""

import sys, os, time, threading, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from PyQt5 import QtWidgets, QtCore

EXCEL_PATH = "psx.xlsx"   # when building with GitHub Actions keep in repo root; bundled into exe via --add-data
OUTPUT_CSV = "psx_signals_latest_trendvol.csv"
STATE_FILE = "psx_last_signals_state.json"
POLL_SECONDS = 60
LOOKBACK = "90d"
INTERVAL = "60m"
EMA_FAST = 20
EMA_SLOW = 50
VOL_MA = 20
VOL_MULT = 1.6
RSI_PERIOD = 14
ATR_PERIOD = 14
MAX_WORKERS = 6

def load_tickers_from_excel(path=EXCEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found: {path}")
    df = pd.read_excel(path, sheet_name=0)
    if 'Tickers' not in df.columns:
        raise ValueError("Excel must contain a 'Tickers' column")
    syms = df['Tickers'].dropna().astype(str).unique().tolist()
    syms = [s if '.' in s else s + '.KA' for s in syms]
    return syms

def fetch_1h_yf(symbol, period=LOOKBACK, interval=INTERVAL):
    try:
        tk = yf.Ticker(symbol)
        df = tk.history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return None
        df = df.loc[:, ['Open','High','Low','Close','Volume']].rename(columns={'Close':'close','Open':'open','High':'high','Low':'low','Volume':'volume'})
        return df
    except Exception:
        return None

def compute_indicators(df):
    df = df.copy()
    # EMAs
    df['ema_fast'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()
    # Volume MA
    df['vol_ma'] = df['volume'].rolling(window=VOL_MA, min_periods=1).mean()
    # RSI (EWMA version)
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    roll_down = down.ewm(alpha=1/RSI_PERIOD, adjust=False).mean().replace(0,1e-10)
    rs = roll_up / roll_down
    df['rsi'] = 100 - (100 / (1 + rs))
    # TR & ATR
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['close'].shift(1)).abs()
    df['tr3'] = (df['low'] - df['close'].shift(1)).abs()
    df['tr'] = df[['tr1','tr2','tr3']].max(axis=1)
    df['atr'] = df['tr'].ewm(span=ATR_PERIOD, adjust=False).mean()
    return df

def generate_signal_trend_volume(df):
    # Return (signal, meta) where meta includes entry,tp,sl,atr,rsi,time
    if df is None or len(df) < max(ATR_PERIOD, EMA_SLOW, VOL_MA) + 2:
        return 'NoData', None
    df = compute_indicators(df)
    a = df.iloc[-2]
    b = df.iloc[-1]
    signal = 'Neutral'
    try:
        # detect EMA crossover
        cross_up = (a['ema_fast'] <= a['ema_slow']) and (b['ema_fast'] > b['ema_slow'])
        cross_down = (a['ema_fast'] >= a['ema_slow']) and (b['ema_fast'] < b['ema_slow'])
        # volume spike condition
        vol_spike = (b['volume'] > (b['vol_ma'] * VOL_MULT))
        # RSI filters (avoid extreme)
        rsi_ok_buy = (b['rsi'] < 80)
        rsi_ok_sell = (b['rsi'] > 20)
        if cross_up and vol_spike and rsi_ok_buy:
            signal = 'BUY'
        elif cross_down and vol_spike and rsi_ok_sell:
            signal = 'SELL'
        else:
            # label trend
            if b['ema_fast'] > b['ema_slow']:
                signal = 'Bullish'
            elif b['ema_fast'] < b['ema_slow']:
                signal = 'Bearish'
            else:
                signal = 'Neutral'
    except Exception:
        signal = 'Error'
    entry = None if pd.isna(b['close']) else float(b['close'])
    atr = None if pd.isna(b['atr']) else float(b['atr'])
    tp = sl = None
    if entry is not None and atr is not None:
        if signal == 'BUY':
            sl = entry - atr * 1.0
            tp = entry + atr * 2.0
        elif signal == 'SELL':
            sl = entry + atr * 1.0
            tp = entry - atr * 2.0
    meta = {
        'entry': None if entry is None else round(entry,4),
        'tp': None if tp is None else round(tp,4),
        'sl': None if sl is None else round(sl,4),
        'atr': None if atr is None else round(atr,4),
        'rsi': None if pd.isna(b['rsi']) else round(float(b['rsi']),2),
        'vol': None if pd.isna(b['volume']) else int(b['volume']),
        'vol_ma': None if pd.isna(b['vol_ma']) else int(round(b['vol_ma'])),
        'time': str(b.name)
    }
    return signal, meta

def worker_fetch(symbols, out_list):
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_1h_yf, s): s for s in symbols}
        for fut in as_completed(futures):
            s = futures[fut]
            try:
                df = fut.result()
                sig, meta = generate_signal_trend_volume(df)
                row = {
                    'symbol': s,
                    'signal': sig,
                    'entry': meta['entry'] if meta else '-',
                    'tp': meta['tp'] if meta else '-',
                    'sl': meta['sl'] if meta else '-',
                    'atr': meta['atr'] if meta else '-',
                    'rsi': meta['rsi'] if meta else '-',
                    'vol': meta['vol'] if meta else '-',
                    'vol_ma': meta['vol_ma'] if meta else '-',
                    'time': meta['time'] if meta else '-'
                }
            except Exception:
                row = {'symbol': s, 'signal': 'Error', 'entry':'-','tp':'-','sl':'-','atr':'-','rsi':'-','vol':'-','vol_ma':'-','time':'-'}
            results.append(row)
    out_list.extend(results)

class ScannerThread(threading.Thread):
    def __init__(self, symbols, update_callback, stop_event):
        super().__init__(daemon=True)
        self.symbols = symbols
        self.update_callback = update_callback
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            start = time.time()
            out = []
            worker_fetch(self.symbols, out)
            out.sort(key=lambda x: x['symbol'])
            df_out = pd.DataFrame(out)
            try:
                df_out.to_csv(OUTPUT_CSV, index=False)
            except Exception:
                pass
            try:
                prev = {}
                if os.path.exists(STATE_FILE):
                    try:
                        with open(STATE_FILE, 'r') as f:
                            prev = json.load(f)
                    except Exception:
                        prev = {}
                alerts = []
                for r in out:
                    sym = r['symbol']
                    sig = r['signal']
                    prev_sig = prev.get(sym)
                    if sig in ('BUY','SELL') and prev_sig != sig:
                        alerts.append((sym, sig))
                    prev[sym] = sig
                try:
                    with open(STATE_FILE, 'w') as f:
                        json.dump(prev, f)
                except Exception:
                    pass
                self.update_callback(out, alerts)
            except Exception:
                pass
            elapsed = time.time() - start
            to_sleep = POLL_SECONDS - elapsed
            if to_sleep > 0:
                for _ in range(int(to_sleep)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, symbols):
        super().__init__()
        self.setWindowTitle('PSX Signals 1H — Trend+Volume (BUY/SELL + TP/SL)')
        self.resize(1200,650)
        self.symbols = symbols

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(['Symbol','Signal','Entry','TP','SL','ATR','RSI','Vol','Vol_MA','Time'])
        self.setCentralWidget(self.table)

        toolbar = self.addToolBar('Main')
        refresh_now = QtWidgets.QAction('Refresh Now', self)
        refresh_now.triggered.connect(self.manual_refresh)
        toolbar.addAction(refresh_now)

        stop_action = QtWidgets.QAction('Stop Auto-refresh', self)
        stop_action.triggered.connect(self.stop_scanner)
        toolbar.addAction(stop_action)

        start_action = QtWidgets.QAction('Start Auto-refresh', self)
        start_action.triggered.connect(self.start_scanner)
        toolbar.addAction(start_action)

        self.status = self.statusBar()

        self.stop_event = threading.Event()
        self.scanner = ScannerThread(self.symbols, self.update_table, self.stop_event)
        self.scanner.start()
        self.status.showMessage('Scanner started — updates every {}s'.format(POLL_SECONDS))

    def update_table(self, rows, alerts):
        QtCore.QMetaObject.invokeMethod(self, '_update_table', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(object, rows), QtCore.Q_ARG(object, alerts))

    @QtCore.pyqtSlot(object, object)
    def _update_table(self, rows, alerts):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r['symbol'], r['signal'], r['entry'], r['tp'], r['sl'], r['atr'], r['rsi'], r['vol'], r['vol_ma'], r['time']]
            for j, val in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(str(val))
                if j == 1:
                    if val == 'BUY':
                        it.setBackground(QtCore.Qt.green)
                    elif val == 'SELL':
                        it.setBackground(QtCore.Qt.red)
                self.table.setItem(i, j, it)
        self.table.resizeColumnsToContents()
        self.status.showMessage('Last update: {} UTC'.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        for sym, sig in alerts:
            try:
                QtWidgets.QApplication.beep()
                title = f"PSX Signal: {sig} — {sym}"
                msg = f"{sig} signal detected for {sym}\nOpen app to view TP/SL and details."
                QtWidgets.QMessageBox.information(self, title, msg)
            except Exception:
                pass

    def manual_refresh(self):
        t = threading.Thread(target=lambda: worker_fetch(self.symbols, []), daemon=True)
        t.start()
        self.status.showMessage('Manual refresh triggered...')

    def stop_scanner(self):
        self.stop_event.set()
        self.status.showMessage('Stopping scanner...')

    def start_scanner(self):
        if not self.scanner.is_alive():
            self.stop_event.clear()
            self.scanner = ScannerThread(self.symbols, self.update_table, self.stop_event)
            self.scanner.start()
            self.status.showMessage('Scanner restarted...')

def main():
    try:
        symbols = load_tickers_from_excel(EXCEL_PATH)
    except Exception as e:
        print('Error loading tickers from Excel:', e)
        return
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow(symbols)
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
