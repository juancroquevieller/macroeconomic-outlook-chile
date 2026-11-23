# Chile Economy & Retail

A personal and professional dashboard of Chile's macroeconomic backdrop and goods retail activity, built with Streamlit and official statistics. Four views: Macroeconomic outlook, Retail outlook, an eight-indicator Assignment view, and Sources & methodology.

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

- **Quarterly main charts**, complete calendar quarters only, with a separate latest-month signals strip. Publication lags differ across series. Monetary flows are summed; indices and monthly FX are averaged; CPI and TPM are quarter-end. Daily FX is averaged within each month first. Labor uses March/June/September/December rolling-quarter observations, not overlapping-quarter averages.
- **Official direct mining/non-mining GDP** in chained volume terms. Growth rates are not additive. Indirect mining estimates would require assumptions and input-output vintages that make an automated historical comparison less robust.
- **EEE non-mining current-quarter growth** provides the relevant forward-looking activity measure; the inflation forecast targets 11 months after the survey. Historical errors are separated by survey month, with matched-sample naive benchmarks. Selection emphasizes relevance, a clear horizon and usable history; it is not a claim of optimal predictive performance. Revised actuals are used, not real-time vintages.
- **Inflation** is year-over-year CPI with a 3% target and TPM. **Labor** includes unemployment, participation and workforce size.
- **Retail** distinguishes real INE retail activity, nominal IVE sales, household durable/non-durable goods consumption, and experimental online retail measures. These populations are not interchangeable.
- Quarterly online share is sales weighted: sum(online index) / sum(online index / share). In-store growth is implied within that same series population. Rounded source shares introduce approximation. We do not multiply IVE sales by IVOCM shares to invent monetary channel totals. Independently based category indices cannot establish channel market size, company shares or marketplace GMV.

## Exchange-rate reference range

This section is self-contained. For nominal CLP/USD S, calculate monthly bilateral real exchange rate q = S * US CPI / Chile CPI. Take median q over two historical periods: **January 2010–December 2014** and **January 2015–September 2019**. Convert each anchor back into nominal CLP/USD using contemporaneous relative CPIs. October 2019 and subsequent social unrest are excluded from the second reference period.

The two lines provide sensitivity to historical anchors, not a confidence interval, fair-value estimate or prediction. They are distinct from BCCh's multilateral real exchange-rate index. A higher CLP/USD means a weaker peso. Only months with all three inputs are used; displayed quarterly references require three months.

## Reproducibility and evidence

`registry.json` records verified API IDs, units, original producers, source links and transformations. `data/raw` contains BCCh responses; `data/snapshot.json` is the rendering input. `verify_sources.py` independently discovers public BDE table links and compares one published observation for each series with the API, respecting displayed rounding and unit scaling.

See [verification](verification/README.md), [source checks](verification/source_checks.json), and [design prompts](PROMPTS.md). Automated Streamlit checks exercise the populated views; browser layout review and the public deployment URL remain to be recorded after deployment.
