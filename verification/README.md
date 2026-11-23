# Verification record

The current dashboard passes **17 automated tests** and **38 independent published-source comparisons**. The source check covers every retrieved series, including total, mining and commerce IMACEC, at a common observation date with rounding and display-unit scaling accounted for.

## Data and computation

- Authenticated full-history refresh succeeded: https://github.com/juancroquevieller/macroeconomic-outlook-chile/actions/runs/45094832655
- Full available BCCh series are requested from 1900, replacing the previous 2009 cutoff. The selected source definitions determine actual coverage: FX starts in August 1982, GDP/IMACEC in 1996, and retail activity in 2005.
- Tests cover quarterly aggregation, missing calendar periods, sales-weighted penetration, reference-period cutoffs, forecast target alignment, failed-fetch preservation, and successful unchanged-data refreshes.
- New tests cover monthly same-calendar-month YoY comparisons, rejection of monthly GDP upsampling, derived monthly participation/in-store sales, both UI frequencies, quarterly-only consumption panels and a historical end-date assertion on plotted timestamps.
- See `source_checks.json` and `test-output.txt`. Run `python -m unittest -v` and `python verify_sources.py` to reproduce. The rendering tests require no API secret.

## Direct visual review

Final successful browser run: https://github.com/juancroquevieller/macroeconomic-outlook-chile/actions/runs/45095507575

Chromium rendered both the source version and the actual public Streamlit deployment. The assistant directly inspected the resulting PNGs, not another agent's descriptions. Both `browser/checks.json` and `browser/live/checks.json` report no Streamlit exceptions.

The browser exercised monthly and quarterly modes, full and five-year history, both FX/labor measures, activity/consumption/sentiment demand views, real and nominal retail measures, online penetration/growth/sales mix, channel detail and mobile layout. The source-commit field in live metadata is the version requested for review, not an independently queried deployment hash; the deployed features were also checked visually.

Current screenshots:

- [Monthly macro](browser/live/macro-monthly-top.png)
- [FX references and employment](browser/live/macro-monthly-bottom.png)
- [Quarterly macro](browser/live/macro-quarterly-top.png)
- [Monthly retail](browser/live/retail-monthly-top.png)
- [Online trend and channel table](browser/live/retail-monthly-bottom.png)
- [Quarterly goods consumption with monthly nominal retail](browser/live/retail-consumption-nominal.png)
- [Retail expectations](browser/live/retail-expectations.png)
- [Online/in-store growth](browser/live/retail-online-growth.png)
- [Channel history](browser/live/retail-channel-detail.png)
- [Full history](browser/live/macro-full-history.png)
- [Mobile](browser/live/mobile-macro.png)

Visual findings corrected: the oversized introduction and signal strip were removed; date controls were separated to avoid clipping; forecasts were separated from observed series; FX references moved into the main view; policy rates use steps; nominal sales compare year over year; online share has a readable trend view; channel rows use a common date. GDP/consumption panels are explicitly quarterly even in monthly mode, and labor rolling-window semantics are disclosed.

The captures verify the tested viewports and modes, not every possible browser or screen size. Data remains revised official history, not a real-time-vintage archive. Credentials stay solely in GitHub Secrets.
