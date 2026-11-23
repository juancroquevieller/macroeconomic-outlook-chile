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

The app distinguishes successful-refresh time, attempt time, retrieval time per series, and observation dates. A successful fetch advances the success timestamp even if the source data is unchanged. Failed series retain their last valid data, show a partial-refresh warning, and fail the Actions run. Never interpret retrieval time as the release date. Token expiry or revocation requires replacing the same GitHub secret. The BLS endpoint is attempted first for US CPI; BCCh's republication of that series is the fallback, replacing the entire CPI history to avoid splicing bases.

## Economic choices

- **Monthly by default, with a Monthly / Quarterly switch.** Monthly activity uses total, mining and non-mining IMACEC; quarterly activity uses official GDP. Every panel containing a quarterly-only series stays quarterly for all its inputs. Monetary flows are summed; indices and monthly FX are averaged; CPI and TPM are period-end. Daily FX is averaged within each month first. Monthly labor observations are overlapping rolling quarters; quarterly mode selects March/June/September/December endpoints. No interpolation or monthly GDP fabrication.
- **Official direct mining/non-mining GDP** in chained volume terms. Growth rates are not additive. Indirect mining estimates would require assumptions and input-output vintages that make an automated historical comparison less robust.
- **EEE forecasts retain explicit target dates** in callouts and diamond markers within the selected window. Quarterly GDP forecasts are never plotted as monthly IMACEC forecasts. Non-mining current-quarter growth provides the relevant forward-looking activity measure; the inflation forecast targets 11 months after the survey. Historical errors are separated by survey month, with matched-sample naive benchmarks. Selection emphasizes relevance, a clear horizon and usable history; it is not a claim of optimal predictive performance. Revised actuals are used, not real-time vintages.
- **Inflation** is year-over-year CPI with a 3% target and TPM. **Labor** includes unemployment, participation and workforce size.
- **Retail** distinguishes real INE retail activity, nominal IVE sales, household durable/non-durable goods consumption, and experimental online retail measures. These populations are not interchangeable.
- Quarterly online share is sales weighted: sum(online index) / sum(online index / share). In-store growth is implied within that same series population. Rounded source shares introduce approximation. We do not multiply IVE sales by IVOCM shares to invent monetary channel totals. Independently based category indices cannot establish channel market size, company shares or marketplace GMV.

## Exchange-rate reference range

This section is self-contained. For nominal CLP/USD S, calculate monthly bilateral real exchange rate q = S * US CPI / Chile CPI. Take median q over two historical periods: **January 2010–December 2014** and **January 2015–September 2019**. Convert each anchor back into nominal CLP/USD using contemporaneous relative CPIs. October 2019 and subsequent social unrest are excluded from the second reference period.

The two lines provide sensitivity to historical anchors, not a confidence interval, fair-value estimate or prediction. They are distinct from BCCh's multilateral real exchange-rate index. A higher CLP/USD means a weaker peso. Only months with all three inputs are used; displayed quarterly references require three months.

## Reproducibility and evidence

`registry.json` records verified API IDs, units, original producers, source links and transformations. `data/raw` contains BCCh responses; `data/snapshot.json` is the rendering input. `verify_sources.py` independently discovers public BDE table links and compares one published observation for each series with the API, respecting displayed rounding and unit scaling.

See [verification](verification/README.md), [source checks](verification/source_checks.json), and [design prompts](PROMPTS.md). Automated Streamlit checks exercise the populated views; the public deployment URL is recorded above. Desktop and mobile layouts have also been reviewed directly from Chromium screenshots of the live deployment.


## Visual review workflow

The `Browser visual review` GitHub Action runs Chromium using Playwright. It renders the checked-out source, changes the history filter, navigates between macro and retail views, and captures desktop (1440px) and mobile (390px) images. It also repeats the capture against the public Streamlit URL, locating the application inside its hosting iframe.

Screenshots are saved under `verification/browser/`, with live-site images in `verification/browser/live/`. An assistant can pull these image files and inspect them directly; the user does not need to supply screenshots. The workflow runs after app or browser-script edits and supports manual dispatch. Its source checks and live-host checks are distinct; review step outcomes and `checks.json`, not just overall workflow status.

The visual pass shortened labels, distinguished online sales from online share, replaced repetitive metadata with source expanders, added current values above charts, separated labor-rate views, made the channel table fit, removed the introductory hero and signal cards, and kept compact titles for each view. The default five-year view emphasizes recent developments; longer history remains selectable.


## Historical range controls

Choose **From** and **To** months or quarters independently at the top of the app. The source retrieval requests full available BCCh histories, replacing the previous 2009 cutoff. Selected series include FX from August 1982, GDP/IMACEC from 1996, and INE retail activity from 2005. Growth begins only when a prior-year observation exists.

Dates filter observation period-ends. Source history outside the displayed range remains available for valid YoY calculations and fixed FX anchors. Short series retain their true coverage; no backfilling or splicing is used. Historical views use revised data, not historical publication vintages. EEE callouts use surveys available by the chosen end month and show their target period explicitly.

## Chart review decisions

- Policy rates use step lines; CPI retains the 3% target.
- FX displays both historical reference lines with observed CLP/USD by default; the separate TCR view retains its own units.
- Retail demand separates broad commerce activity from quarterly household goods consumption and survey expectations. The sentiment view includes a neutral 50 line.
- Online penetration defaults to a readable line chart; growth and 100% sales-mix views remain available.
- Channel tables use one common date across all rows, one decimal place, and YoY percentage-point changes in online share.
- Nominal retail sales are compared with the same period one year earlier, not interpreted from unadjusted month-to-month changes.
- Missing calendar periods remain gaps in charts; dates, units, and source definitions remain attached to each panel.

[BCCh describes IMACEC as an approximation of GDP evolution](https://www.bcentral.cl/es/web/banco-central/areas/estadisticas/imacec). [INE publishes labor estimates for rolling quarters](https://www.ine.gob.cl/estadisticas-por-tema/mercado-laboral/ocupacion-y-desocupacion).


### Compact dashboard and chart workspace
Three views: Macroeconomic, Retail, Sources & methodology. Navigation, frequency and month/quarter selectors sit above the dashboard. The end selector extends at most twelve months ahead; EEE points retain explicit target dates. Each plot offers Expand / customize beside its title, with an independent Monthly / Quarterly switch plus period, variable and axis controls, clipped-observation warnings, CSV and PNG downloads. Mining and the two historical FX anchors are available but hidden initially. FX and labor use labeled dual axes. Refresh time and newest available period appear beside the top filters; individual releases may lag.

Chart latest values and observation periods remain visible; explanations live in Sources & definitions. Quarterly axes, hover labels and readouts use Q1 2026 notation. Quarterly-only consumption panels retain quarterly frequency in the chart workspace.
