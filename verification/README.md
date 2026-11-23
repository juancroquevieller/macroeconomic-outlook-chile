# Submission verification record

## Source observations

[source_checks.json](source_checks.json) documents 38 published-source comparisons, all passing. Each record identifies the series, source URL, observation period, published value, API value, display scaling and rounding tolerance. This includes backend series that are not currently shown in the submission view. Data retrieval through BCCh preserves the original producers (including INE); US CPI is cross-checked against FRED's BLS republication.

[October 2025 CPI evidence](cpi-gap-2025.json) separately records the BLS shutdown footnote and the blank FRED observation. Monthly data remain missing. The annual FX references use the eleven available months for 2025 only, explicitly labeled; this is a dashboard calculation following BLS's available-month principle, not an official BLS FX series.

## Successful automatic-refresh pipeline

[Successful full refresh and execution log](https://github.com/juancroquevieller/macroeconomic-outlook-chile/actions/runs/45118060827).

The scheduled workflow runs on the 1st and 16th at 08:17 America/Chicago and can also be triggered manually. The successful run demonstrates retrieval and validation; a refresh need not change observation values. The app separates last successful refresh time from observation dates. Failed inputs retain prior data and prevent the full-success timestamp from advancing.

## Calculation and interface checks

37 automated tests passed during final data-method verification. They cover period aggregation, same-calendar-period growth, weighted online penetration, missing observations, the narrowly scoped 2025 reference exception, restoration to twelve months if official data become available, CPI-feed validation, and Streamlit controls. Run `python -m unittest discover -v` to reproduce. Older test-output.txt is retained as historical evidence, not the current test count.

[Final successful source and live-browser review](https://github.com/juancroquevieller/macroeconomic-outlook-chile/actions/runs/45123024514) exercised Monthly, Quarterly and Annual, expanded charts, date selection, retail modes and mobile layout. [Live check results](browser/live/checks.json) report no application exceptions. The deployed screenshots were visually inspected, including the corrected title alignment.

Dashboard examples:

- [Macroeconomic view](browser/live/macro-monthly-top.png)
- [Retail view](browser/live/retail-monthly-top.png)
- [Annual view](browser/live/macro-annual-top.png)
- [Expanded annual FX references](browser/live/expanded-annual-fx.png)

These checks cover the tested modes and viewports; historical observations use the latest revised data, not real-time vintages.
