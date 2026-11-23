# Chile Economy & Retail
Implementation in progress. Panels with unverified inputs explicitly report unavailable data; no demo observations are represented as real data.

## Run
Python 3.12. Install requirements, then run:
```
python -m unittest -v
python refresh.py
streamlit run app.py
```
Set BCCH_API_TOKEN as an environment variable for local refreshes or as a GitHub Actions repository secret. Never commit credentials.

## Deployment
Create a GitHub repository containing this directory, then select main / app.py in Streamlit Community Cloud. The scheduled workflow runs at 08:17 America/Chicago on the 1st and 16th; it also supports manual dispatch. Scheduling is not active until this workflow is pushed to GitHub.

## Outstanding validation
BCCh credentials and authenticated catalog inspection are required. Registry entries are candidates pending source validation. GDP, labor, goods consumption, TCR, retail monetary totals, online/channel mappings and US CPI ingestion remain to be connected. Historical EEE evaluation, visual QA and original-source verification are not yet complete. Do not submit this initial implementation as a verified dashboard.

## FX references
January 2010–December 2014 and January 2015–September 2019. Exclude October 2019 onward from the second anchor. Calculate medians of monthly bilateral real exchange rates, then translate each anchor using current relative CPIs. This is historical sensitivity, not a confidence interval.
