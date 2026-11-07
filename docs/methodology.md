# Motala economic scenario model

This is a reproducible first prototype for municipality 0583, covering the municipality's own accounts (kommunen), excluding the consolidated group. It does not yet demonstrate forecasting superiority. Modelica describes the annual stocks and flows, and the browser runs that Modelica model: OpenModelica's web compiler compiles it in the browser (wasm-jit). A JavaScript reference implementation (`site/src/engine.js`) is kept only for parity tests. All money is nominal SEK million, and all population values are persons. Baseline: 31 December 2025; forecast years: 2026–2033. Source access date: 13 October 2026.

## Activated planning mode (6 November 2026)

The dashboard loads `planning-inputs.json` by default; the source toggle removes
it for the earlier illustrative calculation. Annual residual migration is chosen
so a neutral scenario follows the anchored external cohort path. This residual
includes all differences from the simple birth/death/ageing assumptions and must
not be interpreted as observed migration. User changes to births or migration
still act on the evolving scenario and preserve population conservation.

The source provides five-year ages. Assume a uniform distribution when splitting
5–9, 15–19 at boundaries 7, 16 and 19. For each model cohort, multiply the existing
2025 account value by its source-cohort ratio to 2025; then proportionally scale
all cohorts so total population follows the source's total growth from the
account baseline. This retains the existing account opening state and makes the
43132 source / 43131 accounts difference explicit. No causal or statistical
precision is claimed for this approximation. Source older groups are shown
separately but care costs still use the aggregate 65+ index.

SKR input cells `Blad 2 Indata!C9:J9`, `C100:J100`, `C101:J101` supply annual
national tax-base, labour-cost and other-consumption growth, respectively, with
years verified against `C99:J99`. Percentage-point scenario offsets are added
to every year's rate before compounding. Labour costs are a proxy applied only
to payroll excluding pensions; pensions retain their separately labelled path.
When no municipal revenue path is selected, tax-base growth is compounded from
observed tax revenue and passed through the existing approximate local
population/composition equations. It is not the
municipal SKR revenue model and does not reproduce settlements or equalisation.

The original `Prognosunderlag!B1` is empty. A separate copy now selects Motala
(583) and was recalculated with LibreOffice 24.2.7.2 after VBA removal; macros
were disabled. The dashboard activates `skr-revenue-path.json` by default.
Output row 38 includes tax settlements and row 40 includes general grants,
equalisation, LSS and property fees. Convert tkr to mnkr by 0.001. Input row 29
provides 1 November population of the preceding year. Tax plus grants reconciles
to output row 36 in every forecast year. The original workbook remains unchanged.

Imported values are reference amounts. The existing local population/composition,
tax-rate and approximate equalisation equations can change scenario amounts,
even in the neutral population scenario because its population base differs from
SKR's November reference. The raw reference is therefore displayed separately.
No new official SKR forecast or improvement in accuracy is claimed. Kolada data are displayed with definitions and units, and
budget PDFs are downloadable references. These inputs do not automatically
calibrate sector budgets or activate investment amounts. The historical backtest
remains a test of the earlier population model, not this new future-source path.

## Evidence and benchmarks

The [2025 accounts](https://www.motala.se/media/uploads/Arsredovisning-2025.pdf) provide population, financial history and initial states. The [2026 budget](https://www.motala.se/media/uploads/Budget-Mal-och-resursplan-for-2026-med-plan-for-2027-2028.pdf) is identified but its numeric forecasts have not been extracted. [SKR's revenue methodology](https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html) and [service-price budget model](https://skr.se/ekonomiochbudgetplanering/resursfordelningochanalysstod.8273.html) are distinct benchmarks. The 6 October 2026 revenue workbook was identified but could not be downloaded in this environment. The application never calls its illustrative revenue path an official SKR forecast.

The 2025 report reproduces the municipality's budget result of 96 mnkr, April full-year forecast of 89 and August forecast of 83, against the 105 outcome (printed page 43). The corresponding absolute differences are 9, 16 and 22 mnkr. They are stored in `data/municipal-benchmarks.json`. The budget is a planning comparator, distinct from in-year forecasts. Original release dates and contemporaneous inputs are still missing, and no matched Modelica hindcast is claimed.

Motala's public reporting process includes April and August full-year forecasts and December accounts. We have not established what proprietary forecasting software or internal equations Motala uses. Demographics alone are therefore not a demonstrated improvement over its current method.

## Annual equations

The 2025 published age counts sum to 43,139 while the published total is 43,131. The model proportionally reconciles each cohort to the published total. Original values remain in `observedPopulation` and the history file. No specific cause of this discrepancy is assumed. This reconciliation is applied separately at each historical origin using that year's total.

Population uses five cohorts (0–6, 7–15, 16–18, 19–64, 65+). Survivors equal previous population times one minus mortality. Survivors in the first four cohorts advance at rates 1/7, 1/9, 1/3 and 1/46, assuming a uniform distribution inside each group. Births enter 0–6. Cohort migration residuals are the average observed cohort changes minus natural changes in the two latest transitions. Residuals include statistical adjustments and errors from broad cohort aggregation; they are not observed age-specific migration estimates.

Mortality rates for the first four cohorts are illustrative. The senior mortality rate is selected so base-year deaths reconcile with the published total. Births scale with 19–64 population as a rough exposure proxy. A user-specified migration change is distributed across cohorts with explicit weights. Population conservation is checked each year: Δ population = births − deaths + sum of residual migration. Negative cohorts stop a scenario.

Education demand is a weighted average of the first three cohort ratios. Elderly-care demand is the 65+ ratio. Other-service demand is total population ratio. These are demand indices, not pupil numbers or care recipients. Production needs single-year ages, 65–79 / 80–89 / 90+ groups, participation rates, care intensity, and actual capacity constraints.

Operating costs now start from the published gross accounts: payroll excluding pensions 2,288 mnkr, pension expense 190, other operating expenditure 1,297 (derived from total expenditure 3,775), and operating revenue 751. The rounded gross values give net operating cost of 3,024. The reported net cost excluding depreciation is 3,203 − 180 = 3,023; an explicit −1 mnkr rounding adjustment reconciles these series. The legacy JSON name `cashCost` denotes this accrual net operating cost, not an observed cash flow.

Service weights remain illustrative: education 1,250, elderly care 600, and other services 1,173, summing to 3,023. They determine an aggregate service-volume index from gradually adapting capacity. They are not audited functional budgets or separate pension allocations. Actual service weights require Kolada/SCB functional accounts. Wage growth compounds on gross payroll only. Productivity reduces the payroll needed for the same service volume; it does not automatically reduce pensions, purchased goods/services, or revenue. Other expenditure compounds with its own price index and service volume. Operating revenue has a separate growth rate and scales with population. That revenue-volume assumption still needs fee, sales and earmarked-grant components.

Pension expense follows an explicit annual `pensionExpensePath`, or a separately labelled illustrative growth rate from the 190 mnkr base. Pension cash payments follow `pensionCashPaymentsPath` when supplied, otherwise they are assumed equal to expense. Each supplied array must cover exactly the forecast horizon, in mnkr. No future KPA forecast has been imported. These inputs represent operating pension expense and associated payments; financial pension expense remains in the non-interest financial-cost allowance.

The observed 2024–2025 cost bridge is now preserved in `data/operating-accounts-history.json`: payroll +30, pension expense −85, other expenditure +28, lower operating revenue +23, and component rounding −1, giving a net operating-cost change of −5 mnkr before depreciation. This is an accounting explanation of observed outcomes, not a forecast validation. Pension values in the 2023 report explicitly exclude payroll tax, so they are not silently appended to this series.

Tax revenue is a reference tax path multiplied by lagged population and a working-age composition correction, with municipal tax-rate changes applied separately. Grants use the reference grant path and population correction, with an adjustable offset of the local tax-base deviation. The default 95% offset is an illustrative sensitivity, not a statutory implementation. It does not offset a discretionary tax-rate change. Income/cost/LSS equalisation, guarantee levels, national tax capacity, settlement years, property fees and rule changes must be separated for a production revenue model. The population reference is simplified to previous 31 December, not the legally applicable November date.

Default revenue growth is illustrative. An imported annual SKR tax/grant/population path replaces it; the path must cover every forecast year. Population in the import must be the reference population actually used in that forecast year, not the year-end population labelled with the same year. Exact SKR revenue reconciliation requires separating the components and settlement adjustments.

Depreciation uses an inferred blended asset life: 2,997 / 180 years. Annual depreciation is (opening depreciable assets + half annual investment) / life. Assets close at opening assets + investment − depreciation. This is a declining stock proxy, not Motala's straight-line component accounting. Commissioning, work in progress, replacement schedules, disposal and land require separate asset vintages.

Interest equals opening bank debt times the scenario rate. The 2025 note reports interest expense of 21 mnkr within total financial expenses of 25; the model now retains 4 mnkr separately for remaining financial expenses and rounding. The default interest rate is 21/1,040, a closing-debt proxy rather than an observed average portfolio rate. Financial income stays at 15 mnkr. Annual result = tax + grants − net operating cost − depreciation + financial income − interest − other financial expense.

Operating cash = result + depreciation + operating pension expense − pension cash payments. Investment deficits increase debt; surpluses repay debt up to the opening balance, with any remainder held as cash. A noncash pension expense therefore lowers result without automatically increasing borrowing. This is still a simplified cash-flow model: guarantees, leases, working capital, asset sales, other noncash provisions, pension-liability valuation and liquidity policy remain omitted. The base-year published result is 105 while rounded ledger terms produce 104; the 1 mnkr reconciliation difference is retained only in the observed base row. Base-year pension payments are left unknown rather than invented.

Stress curves perturb revenue growth, wage/price growth, net migration, births and interest coherently. They are user-defined scenarios, not calibrated confidence intervals or probabilities. No prediction interval is claimed.

## Validation and the meaning of “better”

Numerical checks cover conservation, fiscal and cash identities, nonnegative debt, tax-rate sensitivity, imported-path completeness, scenario validation and native Modelica/reference parity. Native parity is tested over four scenarios: base, adverse, alternative migration/investment, and a pension path where expense and payments differ. All 23 checked outputs match for eight annual rows. The reference engine rejects future or discontinuous calibration history. The browser's wasm-jit build is checked the same way in `tests/jit-parity.test.mjs`: 25 annual outputs and five cohorts for 14 scenarios agree with the reference within a relative 1e-8 (observed about 1e-12).

The supplied population retrospective evaluation compares a one-year cohort model with persistence and a recent total-population trend, using only preceding rows for each fit. The later annual report supplies all observations, so this is not a genuine real-time vintage backtest. Only three holdouts (2023–2025) are available. Structural population results can fail to outperform the simpler baselines; failures are reported. No fiscal or municipality/SKR superiority result is claimed.

For forecast acceptance, archive every source vintage with release date and information cutoff. Collect at least 10 years of annual accounts and the April/August municipal forecasts, every available SKR vintage and corresponding SCB/Kolada observations. Evaluate 1/2/3-year horizons at rolling origins without future input leakage. Score population by age (MAE), revenue/cost/debt (MAE and bias in mnkr), result (MAE, not percentage errors near zero), and interval coverage/width. Compare with the exact municipality and SKR paths and simple statistical baselines on identical cutoffs. Report shock years separately. Choose additional mechanisms only when they improve held-out performance and retain accounting consistency. Modelica makes the mechanisms explicit; it does not by itself improve forecast accuracy.

## OpenModelica wasm-jit

The browser compiles `Motala.Annual`, through the `MotalaBrowser` wrapper, with OpenModelica's web compiler and the `wasm-jit` target. The compiled model is reused: every scenario re-runs it with `-override` values for all annual inputs, and the horizon is set through `stopTime`. Inputs are validated in JavaScript before they reach the model, and the model asserts the same limits itself. The compiler revision and file hashes are recorded in `omc-web/manifest.json` on the site. Compiler version or API drift can require changes to `site/src/omc-session.js`.

The engine needs no personal resident records. The prototype is aggregate and stores no resident-level data.
