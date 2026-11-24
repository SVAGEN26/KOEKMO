# Methodology

How the model computes a municipality's finances. Updated 2026-11-24. The
library has two models with the same assumptions and outputs. The site runs
`Kommunekonomi.Continuous.Economy` by default: money and population are stocks
with flows in continuous time, and only annual rules are events. The yearly
model, `Kommunekonomi.Annual`, takes one step a year and can be chosen on the
site ("Tid i modellen"). The sections from Structure to Finance describe
`Annual`, whose rules are the simplest to state; [Continuous time](#continuous-time)
says what the default model does differently and what that changes. The
equations are read from `modelica/Kommunekonomi.mo`; the Modelica documentation
of each component says the same in Swedish.

Scope: the municipality's own accounts (kommunen), not the group. Money is
nominal mnkr, population is persons, time is the calendar year. The start is the
base year's closing accounts (31 December); each step computes one year, and the
default horizon is eight years. The model is built for 8–10 years, like SKR's
forecasts. The site allows up to 100; after SKR's last year (2033) its growth
rates are held and Sweden's population keeps SCB's last projected growth after
2070, so such years are arithmetic, not a forecast. Every amount has its base-year value from the
accounts: Motala's annual reports for Motala, SCB's municipal accounts (TAB6777,
TAB6779, TAB6782) for the others.

The model is a scenario tool. It shows how decisions and assumptions move the
result, cash and debt. It is not shown to forecast better than SKR or the
municipality; see [Validation](#validation).

## Structure

Six components, connected in this order each year:

1. **Scenario** picks the year's values out of the annual paths: migration,
   births, wage and price growth, pensions, SKR's reference for tax and grants,
   investment and the interest rate. Decisions and outside assumptions enter here.
2. **Demography** gives the population at year end.
3. **Services** turns population into demand and capacity per sector.
4. **OperatingAccounts** gives payroll, pensions, other costs, fees and net cost.
5. **Revenue** gives tax and general grants.
6. **Capital** and **Finance** give depreciation, result, cash flow, debt,
   cash and interest. **WorkingCapital** is optional.

`Continuous.Economy`, the site's default, has the same components, assumptions
and outputs in continuous time; see [Continuous time](#continuous-time).

## Demography

Two choices, both with a population balance checked every year
(Δ population = births − deaths + migration).

**Five age groups** (0–6, 7–15, 16–18, 19–64, 65+), the site's default.
Survivors are last year's population times one minus the death rate. A uniform
share of each group ages into the next: 1/7, 1/9, 1/3 and 1/46. Births enter 0–6
and scale with the 19–64 population relative to the base year. Death rates under
65 are illustrative; the 65+ rate is set so base-year deaths match the accounts.
Residual migration per group is the average observed change minus the natural
change over the two latest years. It holds statistical adjustments as well as
migration. A scenario change in net migration is spread over the groups with
fixed weights. The 65+ group is split into 65–79, 80–89 and 90+ in fixed shares
from SCB.

**Single years of age** (`CohortDemography`): ages 0–100+ by sex, as in SCB's
projections. Deaths follow Sweden's life table scaled to the municipality's
level (five years of data), with the national trend (ten years). Births follow a
total fertility rate (default 1.41; or SCB's national projection, or the
five-group rule) with SCB's age profile. Residual flows are calibrated by age on
three years up to the base year, or taken from observed migration (SCB TAB1212).

The amounts in the accounts and in SCB's age tables can differ by a few persons;
the groups are scaled to the published total (`Data.reconcile`).

## Services

Demand indices, base year = 1:

- education: the 0–6, 7–15 and 16–18 groups, weighted by the base year's net
  cost per group (Kolada);
- elderly care: 65–79, 80–89 and 90+ weighted by care cost per inhabitant
  (Kolada). For Motala 2023–2025 a person 80+ costs 7.1 times a person 65–79.
  Kolada has no split of 80+, so 90+ gets the 80–89 weight;
- other services: total population.

Capacity follows demand with a lag, and a fixed share does not follow:

    capacity = capacity_prev + adjustment · (fixedShare + (1 − fixedShare) · demand − capacity_prev)

Defaults 0.5 and 0.25, the same in all sectors; both are illustrative. Service
volume is capacity weighted by the base year's sector costs (Kolada).

## Operating accounts

    standard         = previous · (1 + costDrift)
    wages            = wages_0 · wageIndex · volume · standard / productivity
    employer contr.  = same scaling, or wages · rate when a rate path is given
    other costs      = other_0 · priceIndex · volume · standard
    operating revenue = revenue_0 · revenueIndex · population / population_0
    net cost         = payroll + pension expense + other costs − operating revenue + rounding

Indices compound the year's growth. Productivity lowers payroll only.

`costDrift` is cost growth beyond demography and prices: higher standards, new
tasks, anything that is neither volume nor price. Its default is 0. Its history
comes from `scripts/cost_residual.py`, measured on the basis the model applies it
to: the drift on gross payroll and other costs that makes the model's net cost grow
as SCB's did (TAB6777, without depreciation), with SKR's price index for municipal
activities (PKV outcomes), the model's service volume (fixed share 0.25, half the
gap closed each year) and operating revenue following prices and population.
Over 2011–2025 the mean lies between −0.3 and 0.4 % a year in the 13
municipalities (Linköping 0.31, Motala 0.20), with single years off by 2–3 % (the
standard deviation). Norrköping's 2022 and 2023 are left out: the Ostlänken
provision is not split between operating and financial items. The mean known in
each base year (`knownBy`) uses the weights known then. Used as a forecast it made
costs too high eight years ahead (see Validation), so the default stays 0 and the
site offers it as a scenario. Pension
expense and pension payments are separate annual paths: the expense hits the
result, the payment hits cash. Without a source the payments equal the expense.
The rounding term reconciles the base year's rounded components to the reported
net cost.

## Tax and general grants

Tax and grants start from a reference path: SKR's forecast for the
municipality when imported, otherwise the base year's amounts grown at
`taxGrowth` and `grantGrowth`. National growth includes Sweden's population
growth, so the municipality's share is scaled by its population relative to
Sweden's:

    popFactor = (pop_{t−1} / pop_ref) / (Sweden_{t−1} / Sweden_ref)

where pop_ref is the population at the end of the year before the base year,
since the base year's tax rests on the population of 1 November that year. Tax
and most grants are per inhabitant: at Motala's 2025 amounts each inhabitant is
worth about 77,000 kr a year in tax and grants.

    tax = (reference tax · popFactor + age deviation) · taxRate_t / baseTaxRate

The age deviation is the tax effect of a changed share aged 19–64. Without
component grants, grants = reference grants · popFactor − 0.95 · age deviation,
a simplified equalisation. A changed tax rate changes only tax.

**Grants by component** (`grantsByComponent`): income equalisation, cost
equalisation, the regulation grant and LSS equalisation as kronor per inhabitant
times last year's population; property fee and other grants in mnkr. Next
year's amounts are SCB's published values (TAB1981, TAB4011); later years hold
the per-inhabitant amounts, with income equalisation following Sweden's tax
capacity. Income equalisation follows the law (2004:773): the municipality
receives 95 % of a tax rate times the gap between 115 % of Sweden's mean tax
capacity and its own, and pays 85 % when above (`Data.equalisationShare`). A
changed share in working age changes its own tax capacity. The hindcasts use
this mode; the site does not, because it has SKR's path.

**Imported SKR path** (`importedRevenue`), three modes:

- 0, proportional: the path scaled by the model's population against SKR's;
- 1, published: SKR's amounts as they are;
- 2, per component (the site's default): tax before settlement, income
  equalisation and the regulation item each adjusted for population and tax
  rate; with age weighting of taxable income (SCB TAB744, Motala only, on by
  default), income equalisation takes back the age effect at the county rate.
  Cost and LSS equalisation, the property fee and other grants follow SKR's path.

SKR's path is SKR's own calculation of the equalisation law for the
municipality (Modellverktyget Skatter och bidrag). The model only adjusts it
for its own population; it does not compute cost or LSS equalisation.

`revenueFromReference` takes a path as given, for example a budget's amounts.

**The state's grant increases.** SKR's path holds what the budget bill has
decided; the site's rule `holdRegulation` keeps the regulation grant per
inhabitant after that year. A user can add a further increase, `grantIncrease`
billion kronor more nationally for every year from the second forecast year,
spread equally per inhabitant like the regulation grant. The model
(`Components.Revenue`, all revenue modes, Annual and Continuous) adds it to the
grants after the population scaling; with grants by component it goes into the
regulation grant:

    stateIncrease_t = grantIncrease · 1e3 · (t − 1) · pop_{t−1} / Sweden_{t−1}   (mnkr)

with pop_ref,t SKR's population for the year, or without SKR's path the
population and Sweden's population of the year before the base year. Nationally
general grants and equalisation rose from 130.8 to 146.1 billion kronor 2021–2025
(SCB TAB6777), about 3.8 billion a year.

## Capital

A share of each year's investment (`constructionShare`) waits in work in
progress for `constructionYears` before it is put in use; the rest is put in
use the same year. A named project can be paid and opened in a given year, with
its places in use from then.

    depreciation = (assets_prev + 0.5 · commissioned) / life
    assets       = assets_prev + commissioned − depreciation

`life` is the base year's assets over its depreciation, a blended life (Motala
2025: 2,997 / 180 mnkr). This is a declining stock, not component depreciation.

## Finance

    result = tax + grants − net cost − depreciation + financial income − interest − other financial costs
    operating cash = result + depreciation + pension expense − pension payments + working-capital effect

If operating cash does not cover investment, the municipality borrows the gap;
a surplus repays debt, and what remains goes to cash. With `liquidityPolicy`,
cash above a chosen reserve is used before borrowing, and a share of the first
year's investment can be deferred and prefinanced.

Interest is opening debt times the year's rate on it. Without a fixed-rate
period (`rateFixingYears = 0`) that is the year's rate. With one, the rate path
is the market rate for new and refixed loans, and the average rate moves toward
it by the share 1 − exp(−1/τ) of the debt each year; new loans pay the market
rate. `rateShock` raises the market rate from a date, counted for the rest of
that year. The default rate is the base year's reported average rate when the
annual report gives one, otherwise interest expense over opening debt.

Extra inflation (`inflationShockPath`) reaches prices the same year, wages and
the tax base the year after, pensions the same year and the market rate by
`inflationRateResponse` per point; grants stay fixed in kronor unless
`inflationGrantCompensation` is set. The shares are illustrative.

Key ratios: result as a share of tax and grants (`resultShare`, the usual
financial target), interest as a share of tax and grants, and cumulative
interest. Guarantees, leases, asset sales and pension-liability valuation are
not modelled.

**WorkingCapital** (optional): receivables as days of operating revenue,
payables as days of other costs, and prepaid grants. Only the change in balances
reaches cash. Inventories and land for development are not included.

## Continuous time

`Kommunekonomi.Continuous.Economy` has the same assumptions, parameters and
outputs as `Annual`. What changes gradually is a stock with flows; only rules
that are annual by law or practice are events.

Continuous:

- **Money.** Cash, debt, assets in use, work in progress, receivables,
  payables, pension provision and grant advances are stocks. Liabilities have
  negative levels, so the sum of stocks changes only by the result
  (`equityBalance`, checked at every year end). Interest accrues on the current
  debt; a deficit is borrowed when it arises.
- **Population** (`Continuous.Demography`, five groups). Births, deaths, ageing
  and migration are flows in persons per year. Births follow the 19–64 group as
  in `Annual`. Deaths are a death rate times the group: deaths per mean
  population, as SCB defines it (`Data.deathRatesPerYear`). Ageing out of a
  group is its size over its width in years (7, 9, 3, 46), the rate at which a
  uniform group crosses its upper bound. Migration is the calibrated residual
  plus the scenario's change, spread evenly. The residual is calibrated for these
  flows (`Data.calibratedMigrationRates`): the even inflow that takes each group
  from one year end to the next in the two latest years.
- **Single years** (`Continuous.CohortDemography`, used by
  `Motala.Examples.ContinuousCohort`). Stocks are birth cohorts by sex, labelled
  by age at year end as in SCB's statistics. Births, deaths and migration are
  flows; a death risk q becomes the rate −ln(1 − q), so a closed cohort survives
  a year as in `Annual`. Age now is computed with birthdays spread evenly over
  the year, so the age groups move smoothly.
- **Wage, price, fee, productivity and cost-standard levels**
  (`OperatingAccounts`) grow as `der(level) = rate · level`. A path's annual
  growth (SKR's hourly wage and PKV, or the site's percentages) is growth of the
  annual mean. The rate moves linearly between the turns of the year, and the
  rates there are chosen so that the annual mean grows by exactly the path's
  growth (`Data.meanPreservingRates`: a tridiagonal system, with the base year
  and the time after the last year growing at the nearest rate). The annual
  wage and price indices therefore equal `Annual`'s, to a millionth in the
  tests, also when growth changes between years. The price of that is the
  shape within the year: when annual growth swings, the rate swings more
  (3 and 5 % in alternate years give rates between about 1 and 7 %).
- Capacity, costs, working capital and depreciation, as before.

Events:

- **Year end, 31 December** (`clock`): flows are summed to the year's amounts
  and stocks are read. Every balance is checked.
- **1 January** (`calendar`): decisions for the year. The tax rate, the year's
  tax and general grants and the employer contribution rate are set. Tax and
  grants are paid as one twelfth a month, so they flow evenly and the year's
  total is the decided amount (`revenueBalance`); with a given path (`revenueFromReference`) the
  totals equal the path. Annual paths (investment, pensions, migration, the
  interest-rate path) are read and flow evenly.
- **1 November**: the population that day is the basis for next year's tax and
  grants (revenue mode 2). `Annual` interpolates it between year ends.
- **Single years only**: the birth cohorts are relabelled at the turn of the
  year. No one moves; the population is unchanged.

Not modelled within the year: the final tax settlement (slutavräkning) and wage
agreements' revision dates. Outside revenue mode 2, tax and grants use the
population at the previous year end, as in `Annual`. Pension expense and
investment are annual amounts spread evenly.

`tests/test_continuous.py` (native OpenModelica) checks the balances, the tax
and grant totals against a given path, the annual indices with constant and
with changing growth, the population against `Annual` (within 0.1 %) and that
no age group jumps at a year end. `tests/jit-continuous.test.mjs` runs the
model the way the site does; see [Browser engine](#browser-engine).

**What differs from `Annual`.** With the same inputs, the wage and price
indices and (with SCB's projection) the population at each year end are the
same, and so are tax and grants; with adjustment per component they are within
2 mnkr for Motala, since the 1 November population is read from the stock
instead of interpolated. Three things differ, and they are timing within the
year:

- Capacity follows demand continuously, and costs are counted through the
  year. Both models close the share `adjustment` (default 0.5) of a constant gap
  between demand and capacity in a year. Under a steady trend they differ: the
  continuous capacity is 1/ln 2 = 1.4 years behind demand and its costs are the
  year's average, while `Annual`'s capacity is one year behind and its costs use
  the year-end value. The continuous model's costs are therefore about a year
  further behind a trend in demand. Where demand for schooling falls and total
  cost with it, costs are higher: the service volume is 0.1 % higher for Motala
  and 0.3 % for Linköping by 2033. Where demand rises they are lower (Mjölby in
  the hindcast). Fees and other operating revenue follow the population during
  the year instead of at its end.
- Interest accrues on the debt as it grows, not on the opening debt: 1–2 mnkr
  more a year for Motala.
- Depreciation starts when an investment is paid, not with half a year's
  delay on the year's total. The difference is 0.1 mnkr a year for Motala.

For Motala from the 2025 accounts with the site's defaults the result is 5–11
mnkr lower than `Annual`'s each year 2026–2033 (151 against 159 mnkr in 2033)
and the debt 65 mnkr higher in 2033 (1 576 against 1 511 mnkr). For Linköping
the result is 21–42 mnkr lower a year (0.3 % of net cost) and the debt 291 mnkr
higher in 2033. The adjustment speed is an illustrative assumption in both
models, not an estimate, so neither is shown to be closer to what will happen.

**Against outcomes.** Hindcast from SKR's December circulars 2020–2024
(`HINDCAST_MODEL=Continuous python3 scripts/hindcast_vintages.py`,
`scripts/compare_hindcasts.py`) and eight years from the 2017–2019 accounts
(`HINDCAST_MODEL=Continuous python3 scripts/hindcast_long.py`).
From the circulars, the result's mean absolute error after 1/2/3 years is
40/60/60 mnkr for Motala against `Annual`'s 40/59/58, 39/77/59 against 38/76/59
for Finspång and 42/67/126 against 41/65/116 for Mjölby. Tax and grants are
within 0.6 mnkr of `Annual` and population within 4 persons. Mjölby grows, so
costs that trail the population by more are 3–10 mnkr lower, and the model's
net cost was already too low there. In the
eight-year test (hindsight set, 13 municipalities) the result's mean absolute
error is 1.8/2.3/2.6/3.4/3.0/2.2 % of tax and grants in years 1/2/3/4/6/8
against `Annual`'s 1.7/2.2/2.4/3.3/2.9/2.2, and its mean error
0.2/0.3/−0.1/−0.2/−0.2/0.7 % against 0.0/−0.2/−0.7/−0.8/−0.8/−0.2: the result
is about half a per cent of tax and grants higher, because the model's
population grows too fast in that test and costs now follow it about a year
later. Debt is 36 % too low after eight years against 32 %. The continuous model
is not more accurate than `Annual`; the differences are within what the few
cases can tell apart.

**In the browser.** The staged wasm compiler runs the continuous model with
`euler`, `rungekutta`, `dassl`, `ida` and `gbode`; `heun`, `impeuler`,
`trapezoid`, `rungekuttaSsc`, `imprungekutta` and `irksco` fail at start. The
site uses `rungekutta` with 12 steps a year, which matches native DASSL to
0.01 mnkr; one Euler step a year is off by 40 mnkr in the result and 236 mnkr in
debt after eight years. When the cash flow changes sign inside a step (a year
that turns from borrowing to repaying), the fixed-step solver finds that moment
by linear interpolation and every stock moves by up to 0.001 %: 0.03 mnkr in
Motala's net cost in the test, against 0.00 with DASSL. Twelve explicit steps are too few for flows with time
constants of days to weeks: payment terms in working capital, refilling the
cash reserve and taking a project into use. Scenarios with those run with the
implicit solver `ida` (with single-year ages its matrix-free linear solver,
`-idaLS=spgmr`, since the 202 age stocks make the Jacobian cost 20 s a run).

## Validation

**Identities and parity.** Every year the model asserts population balance,
asset, debt and cash balances and non-negative debt. `npm test` and
`npm run validate:modelica` check native OpenModelica and the browser build
against the independent JavaScript reference (`site/src/engine.js`).
`npm run check:units` runs OpenModelica's unit checker on the library with the
money units written as SI units it knows; see [modelica/README.md](../modelica/README.md)
for what it covers.

**Hindcast.** `scripts/hindcast_vintages.py` starts from each set of accounts
2020–2024 with only what SKR's December circular of that year assumed, and runs
up to three years, not past 2025. Outcomes are Motala's annual reports
(`research/data/annual-ledgers.json`) and SCB for the others. Results are in
`data/vintage-hindcast.json`; the README has a summary. One year ahead the
model's result is off by 40 mnkr on average for Motala, the municipality's
budget by 24 and keeping the base year's result (persistence) by 59. The
"components" set adds the state's grant decisions in the circular. With hindsight
values for prices, the tax base and the state's grants per component (as booked),
tax, grants and net cost come within about 10–20 mnkr, but the result's mean
absolute error is 43/57/39 mnkr after 1/2/3 years, no better than SKR's
assumptions (40/59/58). With SKR's assumptions the small three-year result error
comes from errors that cancel.

**Eight years.** `scripts/hindcast_long.py` runs all 13 municipalities from SCB's
accounts of 2017, 2018 and 2019 to 2025, 39 runs, with hindsight for prices, the
tax base, the state's grants and Sweden's population. Norrköping 2022 and 2023
are not scored (the Ostlänken provision). The benchmark keeps the base year's
result as a share of tax and grants. The model's mean absolute error is 1.7, 2.2
and 2.4 % of tax and grants in years 1–3 against 2.4, 3.7 and 3.4 for the
benchmark; from year 4 the benchmark does as well or better (year 8: 2.2 both).
The result is too low by 0.7–0.8 % in years 3–6. With the standard rates instead
of hindsight the model loses to the benchmark at every horizon. The population is
6 % too high after eight years (migration calibrated on 2015–2017), which raises
costs and grants together, and debt is a third too low because investment is held
at the base year's level. The historical cost residual known in the base year, as
`costDrift`, makes it worse (net cost +11.5 % after eight years), so its default
is 0. Results in `data/long-hindcast.json`. Base years 2017–2019 use SCB's older
series (`scripts/fetch_history.py`); Linköping and Vadstena get a 2 % interest
rate there, since SCB's debt gives none. Boxholm's care weights for 2017 and 2018
are the 2019 ones.

**Responses.** `scripts/response_test.py` tests the model's rules one at a time
against the accounts of the 13 municipalities, with outcomes for the drivers on
purpose: the question is what follows from a given population or investment. For
each rule the observed change is regressed on the change the rule gives, with a
common effect per year removed, so the slope is identified from differences
between municipalities. A slope of 1 is the model's response. Intervals are 95 %
from resampling municipalities with their years (cluster bootstrap). Results in
`data/response-test.json`.

- *Costs.* Real gross operating cost (TAB6777 item 022, deflated with PKV)
  against the service volume from the observed population, 2012–2025. `Annual`:
  0.82, 1.07, 1.03 and 0.80 over 1, 3, 5 and 10 years (five years: 0.54 to 1.64).
  `Continuous.Economy`: 0.71, 0.88, 0.93 and 0.77. With the need taken a year
  late the one-year slope is 0.47 (−0.25 to 1.11). The need itself, without fixed
  share or delay, gives 0.74 over five years, which is what a fixed share of
  about a quarter implies. A least-squares fit of the two parameters gives
  adjustment 1.0 (0.2 to 1.0) and fixed share 0.25 (0 to 0.6); the squared error
  is 0.147 against 0.155 at the defaults and 0.179 with no volume at all. The
  defaults are not rejected and not confirmed.
- *Revenue.* Tax and general grants (items 040 and 050) against the population
  the year before: 0.78, 0.69, 0.65 and 0.44 over 1, 3, 5 and 10 years (one year:
  0.49 to 1.10; ten: 0.10 to 0.90). The site's default scales 0.94 of tax and
  grants with the population, the proportional mode all of it. Against the same
  year's population the one-year slope is 0.12, so the model's lag is right.
- *Financing.* The change of each group of balance sheet items (TAB6779) against
  the financing need, 2018–2025, in shares of tax and grants. Bank loans 0.42,
  less lending 0.24, less cash 0.04, other long-term liabilities 0.11, provisions
  0.04, short-term liabilities 0.03, receivables 0.05, securities −0.24, and 0.31
  not found in these items (disposals, revaluations, and differences between
  SCB's investment survey and the balance sheet). Bank debt less lending and
  cash: 0.71 (0.20 to 1.02); with the need computed from the balance sheet's own
  change of fixed assets, 0.53 (0.17 to 0.95). On investment alone 0.76 (0.28 to
  1.11); on the result and depreciation alone −0.27 (−1.00 to 0.45) where the
  model has −1. Summed over 2, 3, 5 and 8 years the slope is 0.83, 0.85, 0.85 and
  0.88 (five years: 0.58 to 1.09), and with the need from the balance sheet 0.64,
  0.64, 0.78 and 1.02. The one-year shortfall is other forms of borrowing: on the
  balance-sheet need, other long-term liabilities (leasing, loans within the
  group, investment grants) take 0.45 (0.09 to 0.76). The model's rule, all of
  the need to debt, is therefore right over the horizons the site shows and too
  strong for a single year. Connection fees and public investment grants (SCB
  TAB4201 items 210 and 560) were 0.2 to 4.5 % of investment expenditure
  2018–2025 (median 1.6 %), so they are not what is missing.
- *Depreciation.* The model's rule with observed investments: 1.07, 0.89 and
  0.87 over 1, 3 and 5 years (three years: 0.39 to 1.56).
- *Prices.* Nominal cost growth beyond the service volume against PKV, one point
  per year 2012–2025: 0.84 (−0.10 to 1.34), and 0.21 % a year more than PKV on
  average.

The test's Python copy of the capacity rule is checked against `Finspang.Annual`
(to 1e-9) and `Finspang.Continuous` (to 5e-5) in `tests/test_response.py`. Not
tested: the interest rate's pass-through, the tax rate, pension costs and the
inflation scenario's pass-through. The 2020 reform of the cost equalisation falls
in the period and moved grants towards shrinking municipalities, so the low
ten-year revenue slope is not evidence of a weaker response to population.
`data/cost-residual.json` took the need a year late until 2026-11-24; it now
follows the model's timing.

**Population.** `scripts/hindcast_county_ages.py` runs the demography for all 13
municipalities from 2022–2024 to 2025; results in
`research/data/age-group-hindcast.json`.

Limits: against SKR's circulars few cases (five base years, fewer at longer
horizons) and at most three years; the eight-year test has no forecasts of its time
and covers one period whose runs overlap, so its cases are not independent. SKR's
own historical forecasts for the municipalities are no longer available to compare
with. The forecast sets use only data known at the base year (the closing accounts
and Kolada figures of the base year, published the following spring, included);
the hindsight and prices sets use outcomes on purpose.

## Browser engine

The site compiles `Kommunekonomi.mo`, the municipality's package and
`MotalaBrowser.mo` with OpenModelica's web compiler (`wasm-jit`), and re-runs the
compiled model with `-override` for every scenario. `MotalaBrowser.mo` holds two
wrappers without equations of their own: `MotalaBrowserContinuous` around
`Motala.Continuous` (the default) and `MotalaBrowser` around `Motala.Annual`.
Inputs are validated in JavaScript, and the model asserts the same limits. The
compiler revision and file hashes are in `omc-web/manifest.json` on the site. No
resident-level data are used or stored.

For the continuous model the page computes the death rates and the residual
flow in JavaScript (`calibrateContinuous` and `inflowBetween` in
`site/src/scenario-inputs.js`), the same way as `Data.deathRatesPerYear` and
`Data.calibratedMigrationRates`. With SCB's projection the residual flow is the
even inflow that takes the five groups from one projected year end to the next,
births included, so the model's population at each year end is the projection's.

`tests/jit-continuous.test.mjs` runs the staged compiler in Node and checks that
the page's inputs give `Motala.Continuous` as written (to 1e-8), that the
population is SCB's projection at every year end, that tax and grants equal
`Annual`'s, that wages and prices rise by the stated growth also through a
3 → 9 → 0 % shock, that every option keeps the balance checks, that `ida` agrees
with DASSL, that the exported `Scenario.mo` reproduces the page's run, that all
13 municipalities run from the 2024 and 2025 accounts, and that twelve
Runge-Kutta steps a year give native OpenModelica's DASSL within 0.01 mnkr.
`tests/jit-parity.test.mjs` checks the yearly model against the independent
JavaScript reference (`site/src/engine.js`), which covers `Annual` only.

A run takes about 0.1 s in either model, 0.2 s with `ida`, and 0.4 s with
single-year ages in continuous time (0.1 s in `Annual`; 1.5 s with `ida`). A
page update runs about ten scenarios.
