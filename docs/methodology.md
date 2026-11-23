# Methodology

How `Kommunekonomi.Annual` computes a municipality's finances, the model the
site runs. Updated 2026-11-23. The equations below are read from
`modelica/Kommunekonomi.mo`; the Modelica documentation of each component says
the same in Swedish.

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

`Continuous.Economy` uses the same assumptions and outputs in continuous time;
see [Continuous time](#continuous-time).

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
Over 2011–2025 the mean lies between −0.2 and 0.5 % a year in the 13
municipalities (Linköping 0.32, Motala 0.22), with single years off by 2–3 % (the
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
  growth (SKR's hourly wage and PKV) is growth of the annual mean, which belongs
  to the turn of the year between two means. The rate is ln(1 + this year's
  growth) on 1 January and moves linearly to ln(1 + next year's) on
  31 December. With constant growth the annual means equal `Annual`'s exactly.
  When growth changes, the mean grows by about
  (last year's + 4 · this year's + next year's)/6: smoothed, not delayed. The
  level at the base year's end assumes the base year grew like the first
  forecast year.
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

`tests/test_continuous.py` checks the balances, the tax and grant totals
against a given path, the annual indices with constant growth, the smoothing of
a wage jump, the population against `Annual` (within 0.1 %) and that no age
group jumps at a year end.

**Against `Annual` and outcomes.** Hindcast from SKR's December circulars
2020–2024 (`HINDCAST_MODEL=Continuous python3 scripts/hindcast_vintages.py`,
`scripts/compare_hindcasts.py`). Tax and grants are within 0.6 mnkr of `Annual`
and population within 4 persons. Net cost is 2–10 mnkr lower than `Annual` and
the result 2–10 mnkr higher (Mjölby's −3 to −11 in net cost was there before).
What this change added is mostly payroll, up to 5 mnkr a year: the labour index
of the 2022 and 2023 circulars jumps (7.2 % then 4.2 %; 5.7 % then 0.0 %) and is
smoothed. Against the outcome the result's mean absolute error is lower in some
cells and higher in others (after 1/2/3 years: Motala 34/57/59 against
`Annual`'s 40/59/58 mnkr, Mjölby 40/70/126 against 41/65/116, Finspång
35/75/59 against 39/76/59). Where it is lower, net cost's mean error has grown
in the other direction (Motala year 1: −20 to −27 mnkr) while tax and grants
stay too low: errors that cancel. It is not more accurate.

**In the browser.** The staged wasm compiler builds `Motala.Continuous` and
runs it with `euler`, `rungekutta`, `dassl`, `ida` and `gbode`; `heun`,
`impeuler`, `trapezoid`, `rungekuttaSsc`, `imprungekutta` and `irksco` fail at
start. `rungekutta` with 12 steps a year matches native DASSL to 0.01 mnkr and
runs in about 30 ms after a 2 s build. The site's one Euler step a year is off
by 40 mnkr in the result and 236 mnkr in debt after eight years. The site does
not run it.

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
`costDrift`, makes it worse (net cost +12.9 % after eight years), so its default
is 0. Results in `data/long-hindcast.json`. Base years 2017–2019 use SCB's older
series (`scripts/fetch_history.py`); Linköping and Vadstena get a 2 % interest
rate there, since SCB's debt gives none. Boxholm's care weights for 2017 and 2018
are the 2019 ones.

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
compiled model with `-override` for every scenario. Inputs are validated in
JavaScript, and the model asserts the same limits. The compiler revision and file
hashes are in `omc-web/manifest.json` on the site. No resident-level data are
used or stored.
