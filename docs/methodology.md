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

`Continuous.Economy` uses the same assumptions and outputs with time continuous
within the year; see the last section.

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
comes from `scripts/cost_residual.py`:
SCB's net cost excluding depreciation (TAB6777), deflated with SKR's price index
for municipal activities (PKV outcomes), minus the demographic need weighted like
the model's sectors. Over 2010–2025 the mean lies between −0.1 and 0.6 % a year
in the 13 municipalities (Linköping 0.34, Motala 0.30), with single years off by
several percent. Norrköping's 2022 and 2023 are left out: the Ostlänken provision
is not split between operating and financial items. The need weights are the 2025
ones for every year. Used as a forecast, the mean up to the base year made costs
too high eight years ahead (see Validation), so the default stays 0 and the site
offers it as a scenario. Pension
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
changed share in working age changes its own tax capacity.

**Imported SKR path** (`importedRevenue`), three modes:

- 0, proportional: the path scaled by the model's population against SKR's;
- 1, published: SKR's amounts as they are;
- 2, per component: tax before settlement, income equalisation and the
  regulation item each adjusted for population and tax rate; optional age
  weighting of taxable income (SCB TAB744), with income equalisation taking back
  the age effect at the county rate.

`revenueFromReference` takes a path as given, for example a budget's amounts.

**The state's grant increases.** SKR's path holds what the budget bill has
decided; the site's rule `holdRegulation` keeps the regulation grant per
inhabitant after that year. A user can add a further increase, `grantIncrease`
billion kronor more nationally for every year from the second forecast year,
spread equally per inhabitant like the regulation grant. The site adds it to the
reference path before the model scales it by population:

    extra_t = grantIncrease · 1e3 · (t − 1) · pop_ref,t / Sweden_{t−1}   (mnkr)

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

`Kommunekonomi.Continuous.Economy` keeps the annual rules (tax and grants,
wage and price levels, the demography) but moves money between stocks within
the year: cash, debt, assets, work in progress, receivables, payables, pension
provision and grant advances. Liabilities have negative levels, so the sum of
stocks changes only by the result, which the model checks (`equityBalance`).
Interest accrues on the current debt and costs follow the year's average
population. Population, tax and grants are identical to `Annual`;
`tests/test_continuous.py` checks that.

## Validation

**Identities and parity.** Every year the model asserts population balance,
asset, debt and cash balances and non-negative debt. `npm test` and
`npm run validate:modelica` check native OpenModelica and the browser build
against the independent JavaScript reference (`site/src/engine.js`).

**Hindcast.** `scripts/hindcast_vintages.py` starts from each set of accounts
2020–2024 with only what SKR's December circular of that year assumed, and runs
up to three years, not past 2025. Outcomes are Motala's annual reports
(`research/data/annual-ledgers.json`) and SCB for the others. Results are in
`data/vintage-hindcast.json`; the README has a summary. One year ahead the
model's result is off by 40 mnkr on average for Motala, the municipality's
budget by 24. The "components" set adds the state's grant decisions in the
circular. With hindsight values for prices, the tax base and the state's grants per
component (as booked), tax, grants and net cost come within about 10–20 mnkr and
the result's mean absolute error is 43/58/39 mnkr after 1/2/3 years. With SKR's
assumptions the small three-year result error comes from errors that cancel.

**Eight years.** `scripts/hindcast_long.py` runs all 13 municipalities from SCB's
accounts of 2017, 2018 and 2019 to 2025, 39 runs, with hindsight for prices, the
tax base, the state's grants and Sweden's population. The result has no bias at
any horizon; its mean absolute error is 1.7–4.0 % of tax and grants. The population
is 6 % too high after eight years (migration calibrated on 2015–2017), which raises
costs and revenue together, and debt is a third too low because investment is held
at the base year's level. A historical cost residual as `costDrift` makes it worse
(net cost +11.5 % after eight years), so its default is 0. Results in
`data/long-hindcast.json`. Base years 2017–2019 use SCB's older series
(`scripts/fetch_history.py`); Linköping and Vadstena get a 2 % interest rate there,
since SCB's debt gives none.

**Population.** `scripts/hindcast_county_ages.py` runs the demography for all 13
municipalities from 2022–2024 to 2025; results in
`research/data/age-group-hindcast.json`.

Limits: against SKR's circulars few cases (five base years, fewer at longer
horizons) and at most three years; the eight-year test has no forecasts of its time
and so tests the structure, not a forecast. SKR's own historical Motala forecasts
are no longer available to compare with. The hindcast uses only data known at the
base year; later outcomes are the answer, not inputs.

## Browser engine

The site compiles `Kommunekonomi.mo`, the municipality's package and
`MotalaBrowser.mo` with OpenModelica's web compiler (`wasm-jit`), and re-runs the
compiled model with `-override` for every scenario. Inputs are validated in
JavaScript, and the model asserts the same limits. The compiler revision and file
hashes are in `omc-web/manifest.json` on the site. No resident-level data are
used or stored.
