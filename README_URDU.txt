PSX Signals — Fixed Build Package ( Urdu )
اس پیکیج میں شامل فائلز:
- PSX_Excel_1Min_RealTime_App_TrendVolume_Fixed.py   -> Fixed main script
- psx.xlsx                                         -> آپ کی tickers فائل
- .github/workflows/build-windows.yml              -> GitHub Actions workflow
- requirements.txt                                 -> Python dependencies list
- icon_light.png                                   -> Placeholder icon

هدایات (Step-by-step):
1) GitHub پر لاگ ان کریں اور نیا repository بنائیں (مثلاً: psx-signals-1h)
2) اس ZIP کو extract کریں اور اندر کی تمام فائلز اپنے repository میں upload کریں (فولڈر .github بھی شامل کریں)
3) Repository میں جائیں -> Actions tab -> 'Build PSX Signals EXE (Windows)' workflow چلائیں (Run workflow)
4) جب build ختم ہو جائے تو Actions -> run -> Artifacts سے 'PSX_Signals_EXE' ڈاؤنلوڈ کریں
5) ZIP کھولیں، 'PSX Signals 1H.exe' کو extract کریں اور double-click کر کے چلائیں

اگر کسی جگہ error آئے تو Actions کی log یہاں paste کریں میں فوراً حل کر دوں گا.
