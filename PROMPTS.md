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

10. User requested a critical review of every graph, monthly data where available, a Monthly / Quarterly switch using IMACEC as the monthly GDP proxy, removal of the hero and latest-signals section, sober view titles, and editable beginning/end dates with full available history. Implemented these choices, preserved quarterly-only comparisons, and expanded the browser review across chart modes.

## Final user-directed revisions (November 2026)

The numbered entries above record the development sequence, including superseded designs. The submitted app follows these final instructions:

- Retain three views: Macroeconomic outlook, Retail outlook, Sources & methodology. Remove the assignment-only view and hide expectations for submission.
- Support Monthly, Quarterly and Annual, including independent frequency and date controls in expanded charts. Monthly activity uses IMACEC; quarterly and annual activity use GDP. Keep selectable dates through December 2026.
- Keep eight chart panels: activity; inflation and monetary policy; exchange rates; employment; real retail growth by durability; nominal retail turnover; online versus in-store; retail channels. Channel comparisons use growth/penetration charts instead of a table.
- Explain real versus nominal values and source coverage. Show compact source labels, units and latest observation dates; put detailed explanations in Sources & definitions.
- Use navy, green, cyan, purple and grey. Put total activity before non-mining and mining; mining starts hidden. Show both historical FX anchors by default.
- Use current BLS CPI, cross-checked with FRED, for the FX references. Retain the genuine October 2025 monthly gap. For the annual 2025 references, use the eleven available months with explicit coverage labels, applying the available-month principle described by BLS.
- Refresh automatically on the 1st and 16th. Preserve data and successful-refresh timestamps appropriately when retrieval fails.
- Add the Chilean flag and constant title Chile at a Glance in the existing navigation row; align navigation and date filters on a shared grid. Inspect actual live-browser screenshots and fix remaining alignment issues.

Selected original user instructions (verbatim excerpts):

> let's do the refresh twice a month better... the 1th and the 16th

> Please check the live app yourself and make sure the title, tabs and filters are now properly aligned and look good... I want it ready to submit!

OpenAI Codex assisted with coding, source integration, testing and visual review. This file is a summarized development record with selected verbatim excerpts, not a full chat transcript.
