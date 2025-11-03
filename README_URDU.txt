PSX Signals 1H - GitHub Actions کے ذریعے Windows .exe بنانے کا آسان طریقہ (اردو)

تیار پیکیج میں شامل فائلز:
- PSX_Excel_1Min_RealTime_App_TrendVolume.py   -> Main app (signals + TP/SL + alerts)
- psx.xlsx                                     -> آپ کی tickers فائل (Sheet1 میں 'Tickers' column ہونا چاہیے)
- .github/workflows/build-windows.yml          -> GitHub Actions workflow جو exe بنائے گا
- README_URDU.txt                              -> یہی فائل

گائیڈ (Step-by-step):
1) GitHub پر لاگ ان کریں اور نیا repository بنائیں:
   - نام کچھ بھی رکھ سکتے ہیں (مثلاً: psx-signals-1h)
   - public یا private دونوں ٹھیک ہیں

2) ZIP کے اندر موجود تمام فائلز اپنے repository میں upload کریں:
   - .github فولڈر سمیت سبھی فائلز رکھیں۔ (GitHub ویب UI سے یا git push سے)

3) Repository میں جائیں → "Actions" tab کھولیں
   - یہاں آپ کو "Build PSX Signals 1H (Windows)" workflow نظر آئے گا
   - workflow کو manually چلانے کے لیے "Run workflow" یا simply main برانچ پر push کریں

4) جب workflow چل جائے تو Windows runner پر build ہوگا
   - Build ختم ہونے کے بعد Actions → (run) → "Artifacts" میں جائیں
   - وہاں 'PSX-Signals-1H-exe' artifact ملے گا — اسے download کریں

5) exe چلائیں:
   - جو exe آپ نے ڈاؤنلوڈ کیا، اسے اپنے Windows پر رکھیں اور double-click کریں
   - پہلی بار exe تھوڑا وقت لے سکتا ہے، پھر UI کھلے گا اور ہر 60 سیکنڈ پر خود بخود refresh ہوگا
   - جب BUY یا SELL آئے گا تو popup + beep آ جائے گا
   - Latest snapshot کی CSV اسی فولڈر میں بن سکتی ہے (نام: psx_signals_latest_trendvol.csv)

نوٹس و Troubleshooting:
- اگر build fail ہو اور PyInstaller missing-module error دے تو Actions کی log یہاں copy/paste کریں — میں فوراً حل دوں گا
- yfinance بعض PSX tickers پر intraday data مہیا نہ کرے — ایسی صورت میں signal 'NoData' یا 'Error' آسکتا ہے
- حقیقی real-time licensed feed کے لیے آپ کو PSX یا paid data vendor کی API درکار ہوگی — میں وہ integrate کر سکتا ہوں اگر آپ credentials دیں

اگر آپ چاہیں تو میں آپ کے لیے یہ repo GitHub پر بنا کر workflow بھی run کر دوں — اگر آپ اپنا GitHub username اور repo name بتا دیں تو میں مزید رہنمائی دوں گا۔

اب ZIP download کریں: PSX_Signals_1H_Ready.zip
