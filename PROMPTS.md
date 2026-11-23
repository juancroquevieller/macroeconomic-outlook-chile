# Design prompts and decisions

This is a concise record of the user instructions and implementation decisions, not a verbatim transcript.

1. Build a Chile dashboard for International Finance: macroeconomic conditions and goods retail, useful for recruiting and professional use. Prefer Banco Central's API; identify original INE/BLS producers where applicable.
2. Macro panels: real GDP split into mining/non-mining with a single EEE activity expectation; inflation/expectations/target/TPM; nominal and real FX; labor.
3. Retail panels: consumer demand, real retail categories and nominal scale, online/in-store dynamics, and retail channel comparisons. Avoid crowded charts and use selections where appropriate.
4. Update automatically on the 1st and 16th, replacing the initial monthly schedule.
5. Make FX references self-contained. Show a simple range from two historical anchor periods. If 2019 is included, stop before October because of the estallido social.
6. Use GitHub repository juancroquevieller/macroeconomic-outlook-chile and Streamlit for deployment. Keep credentials in GitHub Actions Secrets.
7. Implementation: English, complete calendar quarters plus monthly signals, official direct mining, standalone eight-indicator assignment view, raw-observation downloads, source-date transparency, and explicit uncertainty/coverage limits.
8. Validation: independently compare published observations to API values, test missing-period and aggregation behavior, evaluate forecast errors against precisely matched targets and simple baselines, and preserve refresh evidence.

Scope choices: indirect mining postponed; no fabricated channel CLP totals; online measures retain BCCh experimental-series definitions; FX anchors are historical sensitivity rather than fair-value predictions.

9. User requested autonomous visual inspection and improvement without having to send screenshots. Implemented Chromium screenshot capture in GitHub Actions, then inspected source-version and live Streamlit desktop/mobile PNGs and revised the interface. Retained Streamlit after proving that direct visual review works.
