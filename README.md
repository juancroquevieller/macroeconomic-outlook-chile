# Chile Economy & Retail

[Open the live dashboard](https://macroeconomic-outlook-chile-2nx6g2qvukrcaexz7ycssk.streamlit.app/)

A personal and professional dashboard of Chile's macroeconomic backdrop and goods retail activity, built with Streamlit and official statistics. Three views: Macroeconomic outlook, Retail outlook, and Sources & methodology.

## Deploy

In [Streamlit Community Cloud](https://share.streamlit.io), create an app from this GitHub repository:

- Repository: `juancroquevieller/macroeconomic-outlook-chile`
- Branch: `main`
- Entrypoint: `app.py`
- Python: `3.12` (Advanced settings)

No Streamlit secret is required: the app reads the committed snapshot. Only GitHub Actions needs the repository secret `BCCH_API_TOKEN`. Follow the [official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Local use

```sh
pip install -r requirements.txt
python -m unittest -v
streamlit run app.py
```

To refresh locally, set `BCCH_API_TOKEN` in the process environment, then run `python refresh.py`. Never add the token to source code or a committed file.

## Refresh and recovery

GitHub Actions retrieves the official series at 08:17 America/Chicago on the **1st and 16th** of every month. Scheduling can be delayed by GitHub. Use Actions > Refresh official data > Run workflow for an immediate attempt. Commits containing new snapshots trigger Streamlit's deployment update. GitHub may disable scheduled workflows after prolonged repository inactivity; check Actions if the last-attempt timestamp stops advancing.

The app distinguishes successful-refresh time, attempt time, retrieval time per series, and observation dates. A successful fetch advances the success timestamp even if the source data is unchanged. Failed series retain their last valid data, show a partial-refresh warning, and fail the Actions run. Never interpret retrieval time as the release date. Token expiry or revocation requires replacing the same GitHub secret. US CPI is retrieved from BLS and cross-checked with the Federal Reserve's FRED republication. The freshest validated full history is used; BCCh is a last-resort fallback subject to the same freshness and history checks.

## Timeframes and calculations

Monthly, Quarterly and Annual are available above the dashboard and independently inside each expanded chart. From/To selectors use year plus month or quarter; Annual uses year only. Submission mode caps dates at December 2026 and hides expectations from charts, sources and downloads. The refresh pipeline retains expectations for later work.

| Measure | Monthly | Quarterly | Annual |
| --- | --- | --- | --- |
| Economic activity | IMACEC YoY | Real GDP YoY | Four quarterly real GDP flows summed, then growth vs prior year |
| INE retail volume | Index YoY | Mean of three index levels, then YoY | Mean of twelve index levels, then YoY |
| Nominal retail turnover | CLP billions per month | Sum of three months | Sum of twelve months |
| Online sales growth | Nominal index YoY | Aggregated index YoY | Aggregated index YoY |
| Online penetration | Published monthly share | Sales-weighted share | Sales-weighted share over twelve months |
| IPC inflation | Twelve-month change | Quarter-end month's twelve-month change | December-to-December change |
| Monetary policy rate | Month-end | Quarter-end | Year-end |
| FX and real FX index | Monthly mean | Mean of three monthly levels | Mean of twelve monthly levels |
| Employment | Rolling three-month estimates | March/June/September/December estimates | October-December estimate, explicitly labeled; not annual-average employment |

Annual views are calculated from the connected source histories, not fetched as separate official annual releases. Incomplete calendar years remain blank. Growth is calculated after aggregation, never by averaging growth rates. Daily FX is averaged within each month first, so an annual mean may differ slightly from an official daily-weighted annual average. No interpolation, missing-month replacement or monthly GDP fabrication is used.

Online shares use sum(online index) / sum(online index / share). In-store relative sales are online index times (1 - share) / share within the same statistical universe. Rounded shares introduce approximation. Independently based channel indices cannot establish channel peso totals, company market shares or marketplace GMV.

## Sources and comparability

Every chart identifies its source in the subtitle; original series links, units, coverage and calculation details remain in Sources & definitions.

- **INE (via BCCh):** inflation-adjusted retail volume, durables and non-durables. INE also produces IPC and employment statistics.
- **BCCh (IVE):** nominal retail turnover in current pesos; no matching durable/non-durable peso split is connected.
- **BCCh (IVOCM):** experimental nominal online sales and online shares, with implied in-store growth. See the [official IVOCM methodology](https://www.bcentral.cl/es/web/banco-central/areas/estadisticas/estadisticas-experimentales/ivocm).
- **BCCh:** GDP, IMACEC, monetary policy and exchange rates.
- **BLS / FRED:** the same US all-items CPI-U, not seasonally adjusted, 1982-84=100, used in FX references.

INE real retail growth is not directly comparable with BCCh nominal online/in-store growth: price basis, coverage and methods differ. Their rates should not be weighted together or reconciled simply by subtracting headline inflation. IVE monetary totals are also not multiplied by IVOCM shares to invent monetary channel splits.

Direct mining and non-mining GDP use official chained-volume series; growth rates are not additive. IMACEC approximates GDP evolution; it is not monthly GDP. [BCCh IMACEC](https://www.bcentral.cl/es/web/banco-central/areas/estadisticas/imacec) and [INE employment definitions](https://www.ine.gob.cl/estadisticas-por-tema/mercado-laboral/ocupacion-y-desocupacion) describe the underlying measures.

## Exchange-rate references

For nominal CLP/USD S, calculate monthly bilateral real exchange rate q = S * US CPI / Chile CPI. Take median q over **January 2010-December 2014** and **January 2015-September 2019**, excluding October 2019's social unrest from the second reference. Translate each anchor into nominal CLP/USD using each historical month's relative CPIs.

These are retrospective sensitivity references, not forecasts, fair-value estimates or confidence intervals. They differ from BCCh's multilateral real FX index. Both start visible. Quarterly references require three common months; Annual requires twelve. No extrapolation: the genuine October 2025 US CPI gap prevents a complete 2025 annual reference; incomplete 2026 is not an annual observation. Monthly and quarterly references still use the available 2026 inputs.

US CPI retrieval reads BLS CUUR0000SA0 and FRED CPIAUCNS every refresh. Missing BLS values such as October 2025's dash remain gaps. Complete history is selected from the freshest validated source, never spliced across series. Overlapping observations are cross-checked. A feed more than two calendar months behind, a regressed endpoint, incomplete anchor history or inconsistent values fails the refresh. BCCh is a last-resort fallback subject to the same freshness guard.

## Interface

Three views: Macroeconomic outlook, Retail outlook, Sources & methodology. Compact source subtitles and latest values remain visible; explanations are collapsed. Refresh time and newest available period sit beside the top controls. Quarterly labels use Q1 2026; Annual uses 2026.

Retail shows real volume growth, nominal turnover bars, online versus in-store, and channel trends. Sales growth is the first/default online view; Online penetration is a 100% stacked bar chart. Channel views offer Online sales growth and Online penetration, with legend toggles.

Palette order: navy #014169, green #37968C, cyan #00C1D5, purple #78365F, grey #72777D. Economic activity orders total, non-mining, mining; mining starts hidden. Inflation, policy rates, employment rates, shares and nominal turnover include zero by default without hiding negative observations. The 3% inflation target appears in the legend. Dual axes have explicit units.

Expand / customize sits beside each title and supports independent frequency, variables, dates, axes, zoom, CSV and PNG export. Narrowed axes warn about clipped observations. Historical selections use today's revised data, not real-time vintages; earlier source history remains available for valid growth and reference calculations.

## Verification and visual review

`registry.json` records API IDs, producers, units, source links and transformations. `data/raw` retains source responses and `data/snapshot.json` drives the app. `verify_sources.py` compares observations with public source tables. Tests cover growth alignment, annual completeness, weighted shares, year-end measures, CPI retrieval, and dashboard/workspace behavior.

The `Browser visual review` GitHub Action uses Chromium/Playwright to exercise Monthly, Quarterly and Annual, expanded controls, retail modes, long history, and mobile layouts. It captures both the exact source version and the deployed Streamlit app. Images are saved in `verification/browser/` and `verification/browser/live/`; inspect job step outcomes and `checks.json` for live-site verification. The workflow supports manual dispatch.

See [verification](verification/README.md), [source checks](verification/source_checks.json), and [design prompts](PROMPTS.md).
