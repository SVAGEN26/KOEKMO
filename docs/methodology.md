# Methodology

How the model computes a municipality's finances. Updated 2026-11-25. The model
is `Kommunekonomi.Continuous.Economy`: money and population are stocks with flows
in continuous time, and only annual rules are events. Until November 2026 the
library also had a yearly model, `Kommunekonomi.Annual`, with one step a year; it
was removed so that one model in a system-dynamics form remains. The sections from
Structure to Finance state the rules per year, the way they are simplest to read
(and the way the removed yearly model ran them); [Continuous time](#continuous-time)
says how the model runs them as flows. Comparisons with `Annual` below are the
record of how the continuous model was checked while both existed. The
equations are read from `modelica/Kommunekonomi/package.mo`; the Modelica documentation
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

**Five age groups** (0–6, 7–15, 16–18, 19–64, 65+), the site's default. They are
seven stocks: the four groups under 65, and within 65+ an ageing chain 65–79 →
80–89 → 90+ whose sum is the group. Births enter 0–6 and scale with the 19–64
population relative to the base year.

Who crosses a group's upper age in a given year is known from the base year's
single years of age: those who turn 65 in the first forecast year are the base
year's 64-year-olds, the year after the 63-year-olds. `Data.ageProfile` lets the
base year's population (`BaseYear.ages`, SCB) age one year at a time, with
Sweden's death risks falling along the national trend and the base year's births,
and reads off for every year

- the share of each stock that crosses its upper age: the year's flow out of the
  stock is that share times the stock;
- the death rates of 65–79, 80–89 and 90+ relative to the 65+ rate in the base
  year: the model multiplies them with the municipality's calibrated 65+ rate
  (base-year deaths over the mean population), so more very old people mean more
  deaths, and mortality falls about 1.7 % a year;
- the split of 65+ at the start of the year.

**Where the migration comes from.** `migrationGroupWeight` (0.5 by default: half of each gave the lowest error in the
migration hindcast) swaps a share of the municipality's own net
migration for that of its group in SKR's Kommungruppsindelning 2023:

    residual flow_g = calibrated flow_g + weight · (group rate_g − own rate_g) · p0_g

with both rates the net migration (domestic and foreign) per inhabitant of age group g, the mean of the base year and
the year before (`BaseYear.groupMigration`, `BaseYear.ownMigration`; SCB via `scripts/fetch_migration_groups.py`). The
group rate pools all the group's municipalities. Only the migration is swapped: the rest of the calibrated residual
(statistical adjustments, what the ageing rule misses) stays the municipality's own. The single-years model and years in
which a projection is followed are not affected. `scripts/hindcast_migration.py` compares weights 0, 0.5 and 1.

Death rates under 65 are illustrative. Residual migration per group is the even
flow that, with the two latest years' ageing and deaths, reproduces their change;
since ageing follows the real cohorts it is mostly migration and statistical
adjustments. A scenario change in net migration is spread over the groups with
fixed weights; flows to 65+ enter the chain in the base year's proportions.

Until November 2026 a uniform share of each group aged into the next (1/7, 1/9,
1/3, 1/46) and 65+ was one stock split in the base year's shares. For Motala that
gave 500 people a year turning 65 against 576 due, and 80+ growing 6 % to 2033
against 28 % now (SCB's projection 28 %, single years of age 29 %). In the long
hindcast the fixed transitions made the result 2.6 % of tax and grants too low
after eight years; with the age profile it is 0.9 %.

**Single years of age** (`CohortDemography`): ages 0–100+ by sex, as in SCB's
projections. Deaths follow Sweden's life table scaled to the municipality's
level (five years of data), with the national trend (ten years). Births follow a
total fertility rate with SCB's age profile. The default level is Sweden's in the
base year times the municipality's relation to Sweden over five years (Motala
2025: 1.42 · 1.634/1.498 = 1.55); SCB's national projection or the five-group rule
can be chosen. In the demography hindcast from 2020–2024 every rule that knows
only the base year overshoots births (+36 to +91 a year for this one), because
fertility fell 15 % nationally. The oldest group is a mix of those who were 99
and those already 100 or older, each with its own risk. Residual flows are calibrated by age on
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
- other services: total population, except the part that is roads
  (`infrastructureShare`, 4–10 %: Kolada's net cost of roads, railways and parking
  over the sector's net cost, `data/roads.json`). That part follows the road
  network, a stock that only grows with `networkGrowth`: the municipal network is
  nearly constant (Motala 405 km in 2015, 411 km in 2025) and stays when the
  population falls.

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
site offers it as a scenario. The pension
cost follows the payroll (wages, volume and productivity); `pensionGrowth` is its
growth beyond that, 0 by default. A given path in mnkr (`pensionExpensePath` with
`pensionFollowsPayroll = false`) replaces the rule; the hindcasts use one that
follows SKR's labour-cost index. The expense hits the result, the payment hits
cash; without a source the payments equal the expense. Operating revenue takes
`inflationRevenuePassThrough` (0.3) of a year's extra inflation: in 2022–2025 the
median across the 13 municipalities was 5–50 % with a wide spread, so it is an
assumption.
The rounding term reconciles the base year's rounded components to the reported
net cost.

## Tax and general grants

Tax and grants start from a reference path: SKR's forecast for the
municipality when imported, otherwise the base year's amounts grown at
`taxGrowth` and `grantGrowth`. National growth includes Sweden's population
growth, so the municipality's share is scaled by its population relative to
Sweden's (SCB: outcomes, then the projection; from a base year before the last
outcome the default keeps the last known year's growth, so that a run from an
old base year does not see later outcomes):

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
year's amounts are SCB's published values (TAB1981, TAB4011). After that income
equalisation and the regulation grant follow Sweden's tax base per inhabitant
(the state's frame, below), and cost and LSS equalisation hold their amounts per
inhabitant. Income equalisation follows the law (2004:773): the municipality
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
municipality (Modellverktyget Skatter och bidrag). The model adjusts it for its
own population, replaces the regulation grant after the decided years and
continues the path after its last year (both below); it does not compute cost
or LSS equalisation.

`revenueFromReference` takes a path as given, for example a budget's amounts.

**The state's frame.** The income equalisation is the law's formula, but the
money comes from a national pot: the state's frame for the equalisation. What is
left of the frame when the income equalisation is paid is shared equally per
inhabitant in the whole country, as the regulation grant (a fee when the frame
does not suffice). With F the frame, N Sweden's population, m the nation's mean
tax capacity (tax base per inhabitant) and c the state's net cost of the income
equalisation as a share of m (about 15 % of the county rate, since the guarantee
is 115 % of the mean):

    regulation per inhabitant_t = F_t / N_t − c · m_t

The frame is the state's decision, so years not yet decided need a rule. SKR
keeps F fixed in kronor: c · m grows with the tax base, so the regulation grant
shrinks every year (Motala: 110 mnkr 2027, 15 mnkr 2033). The model lets F follow
the nation's tax base (`stateFrameFollowsTaxBase`, the site's checkbox). Then
F/N and c · m both grow with m, and so does what is left:

    regulation per inhabitant_t = regulation per inhabitant_d · m_t / m_d

from the last decided year d: the year after the base year with grants by
component (SCB's published amount), the year after SKR's workbook on the site
(the budget bill). c is not needed. `scripts/hindcast_regulation.py` tries three
rules against the regulation grant 2005–2026 (SCB TAB1981), from every start year
2011–2025 (`data/regulation-hindcast.json`, `tests/test_regulation_hindcast.py`).
Mean error / mean absolute error, kronor per inhabitant:

| Years ahead | Frame fixed in kronor (SKR) | Grant per inhabitant held | Frame follows the tax base |
|---|---|---|---|
| 2 | −881 / 898 | −280 / 635 | −167 / 662 |
| 4 | −1 908 / 1 928 | −719 / 1 129 | −542 / 1 235 |
| 8 | −4 221 / 4 221 | −2 002 / 2 082 | −1 900 / 2 075 |

Every rule is too low: the state raised the frame beyond all of them in
2019–2021 and 2024. The fixed frame is the worst at every horizon. Holding the
grant per inhabitant and following the tax base cannot be told apart on the
absolute error; following the tax base is less biased, and it is the only one of
the two that makes sense over decades, where an amount held in kronor erodes to
nothing. It is an assumption about the state, not a forecast of it: in 2021–2025
general grants and equalisation rose 12 % nationally (SCB TAB6777) while the tax
base rose 19 %.

**After the path's last year.** `Data.sourcedRevenue` computes the path the model
uses from SKR's rows, in Modelica; the site sends the rows as they stand. After
the last row (2033) every part keeps its last yearly change: tax and income
equalisation with the tax base, the grants other than the regulation grant at the
rate SKR's path itself had in its last year (3.0 % for Motala: income equalisation
with the tax base, cost and LSS equalisation and the property fee held), and the
regulation grant follows the state's frame. Until November 2026 the site extended
the sum of the grants at its last rate, 1.2 %, which SKR's shrinking regulation
grant had pulled down; with a falling population the grants then stood still in
kronor. Without the frame rule SKR's own regulation grant keeps its yearly change
in kronor and turns into a fee. `Report.referenceRevenue` is the path's tax and
grants for the year.

**The state's grant increases.** A user can add a further increase, `grantIncrease`
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

Investment is a yearly path. By default it is the base year's amount. Where the
municipality's budget with plan is recorded (`data/investment-plans.json`, nine
municipalities), the page multiplies the base year's amount by the plan for each
year over the budget for the base year; after the plan the base year's amount
returns. This carries the base year's share of the budget carried out forward
(55 to 95 % in 2025) and keeps SCB's definition of investment, which differs from
the municipalities' own (Linköping 2025: 952 against 606 mnkr). A municipality is
taken in when it carried out between half and all of its 2025 budget by its own
figures; Ödeshög, Ydre, Boxholm and Åtvidaberg are not, for reasons stated in the
data file.
Motala's annual reports show the share carried out between 42 and 71 % in
2021–2025, so a single year's share is uncertain.

## Finance

    result = tax + grants − net cost − depreciation + financial income − interest − other financial costs
    operating cash = result + depreciation + pension expense − pension payments + working-capital effect

If operating cash does not cover investment, the municipality borrows the gap;
a surplus repays debt, and what remains goes to cash. With `liquidityPolicy`,
cash above a chosen reserve is used before borrowing, and a share of the first
year's investment can be deferred and prefinanced.

Interest is charged on the debt as it stands (opening debt times the year's rate in the yearly statement of the rule). Without a fixed-rate
period (`rateFixingYears = 0`) that is the year's rate. With one, the rate path
is the market rate for new and refixed loans, and the average rate moves toward
it by the share 1 − exp(−1/τ) of the debt each year; new loans pay the market
rate. `oneOffCost` is a one-off operating cost in the base year's prices, a flow
from the date `oneOffCostTime` for `oneOffCostDuration` (half a year); the site's
cloudburst scenario sets it in kronor per inhabitant. `rateShock` raises the market rate from a date, counted for the rest of
that year. The default rate is the base year's reported average rate when the
annual report gives one, otherwise interest expense over the year's mean debt
(opening and closing). Cash above the base year's earns the market rate less
`depositSpread` (0.5 points, an assumption); the base year's financial income
covers the base year's cash. Without that a liquidity reserve would be borrowed at
the full rate with no return.

Rate stress paths (`rateEpisode` in the page's assumptions, `data/rate-stress.json`)
replace the flat rate path: the market rate in forecast year i is the scenario's
rate plus the change in the 3-month treasury bill rate (Riksbank, yearly average)
from the year before an episode to its year i, never below 0, with the last
change held after the episode. The treasury bill is the closest published rate to
what a municipality pays on new and refixed loans with short fixing; the
municipality's margin is in its own rate and is assumed to stay. The episodes are
chosen by hand to cover a fast rise (2022–2025), a rise from a high level followed
by a fall (1989–1996), a moderate rise and fall (2006–2013) and a long fall
(2013–2020). Changes taken from a level of 10 % are applied at today's level of
about 2 %, which is a choice, not an estimate of how rates move at low levels.

Debt is the municipality's own. Some municipalities borrow for their companies
through an internal bank; the companies are not in the model. The base year's debt
is therefore the borrowing less the loans passed on to the municipality's own
companies (SCB TAB6779: bank loans, bonds and the short-term part, 081 + 082 + 136
+ 134, less long-term receivables from the companies, 034). Interest on the
passed-on part is taken out of both interest expense and financial income: the
year's interest times the passed-on share of the mean borrowing, never more than
the interest income booked (TAB6782, 260). The result does not change, and the
rate on the municipality's own debt is the rate it pays on all its borrowing.
What the municipality earns above that rate stays in financial income, held at
the base year's amount. Finspång's borrowing is the annual reports' figure;
Linköping's own loans from 2024 and Norrköping's for all years come from their
reports, because SCB's items do not separate them
(`data/municipalities/<code>/annual-report-inputs.json`: `externalBankDebt`,
`ownDebt`, `onLending`, with page references). Check: Finspång's annual report
2025 says the municipality borrowed 131 mnkr, passed on 138 and reduced its own
loans by 7; the rule gives 296 and 290 mnkr for 2024 and 2025. Linköping's
finance report for 31 December 2025 gives 16 616 mnkr borrowed, 15 516 passed on,
a gross interest cost of 338 mnkr and 324 on the lending; the rule gives 23 mnkr
on the municipality's own 1 100. Three figures exist for Linköping's borrowing at
the end of 2024 (16 071, 16 270 and 16 583 mnkr in two reports); its own loans
are 1 000 in all of them.

Extra inflation s (`inflationShockPath`) reaches the prices of other costs the
same year. Everything that is set afterwards follows the delayed inflation
d[t] = (s[t−1] + s[t−2])/2: wage growth rises by `inflationWagePassThrough`·d
(0.4) and the tax base with it, pension cost is its path times
1 + `inflationPensionPassThrough`·d (8; back on the path when d is zero), and
the market rate rises by `inflationRateResponse`·d (0.5). Grants stay fixed in
kronor unless `inflationGrantCompensation` is set (the share of the year
before's extra inflation the state adds). The shares are set after 2022–2025,
see Validation.

Key ratios: result as a share of tax and grants (`resultShare`, the usual
financial target), interest as a share of tax and grants, and cumulative
interest. Guarantees, leases, asset sales and pension-liability valuation are
not modelled.

**WorkingCapital** (optional): receivables as days of operating revenue,
payables as days of other costs, and prepaid grants. Only the change in balances
reaches cash. Inventories and land for development are not included.

## Continuous time

`Kommunekonomi.Continuous.Economy` had the same assumptions, parameters and
outputs as the removed `Annual`. What changes gradually is a stock with flows; only rules
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
  stock is the year's share from the base year's single years of age times the
  stock (`Data.ageProfile`, see Demography). Migration is the calibrated residual
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
the result is 21–46 mnkr lower a year (0.3 % of net cost) and the debt 173 mnkr
higher in 2030 (430 against 257 mnkr); both have repaid it by 2031. The adjustment speed is an illustrative assumption in both
models, not an estimate, so neither is shown to be closer to what will happen.

**Against outcomes.** Hindcast from SKR's December circulars 2020–2024
(`python3 scripts/hindcast_vintages.py`) and eight years from the 2017–2019 accounts
(`python3 scripts/hindcast_long.py`).
From the circulars, the result's mean absolute error after 1/2/3 years is
40/60/60 mnkr for Motala against `Annual`'s 40/59/58, 37/76/59 against 37/75/59
for Finspång and 42/67/126 against 41/65/116 for Mjölby. Tax and grants are
within 0.6 mnkr of `Annual` and population within 4 persons. Mjölby grows, so
costs that trail the population by more are 3–10 mnkr lower, and the model's
net cost was already too low there. In the
eight-year test (hindsight set, 13 municipalities) the result's mean absolute
error is 1.8/2.3/2.5/3.4/3.0/2.1 % of tax and grants in years 1/2/3/4/6/8
against `Annual`'s 1.7/2.2/2.3/3.2/2.9/2.1, and its mean error
0.3/0.3/−0.1/−0.2/−0.2/0.9 % against 0.1/−0.1/−0.7/−0.8/−0.8/0.0: the result
is about half a per cent of tax and grants higher, because the model's
population grows too fast in that test and costs now follow it about a year
later. Debt is too low by 24 % of tax and grants after eight years against 20 %. The continuous model
is not more accurate than `Annual`; the differences are within what the few
cases can tell apart.

**In the browser.** The site runs the continuous model with the implicit solver
`ida` and stores twelve values a year. It matches native DASSL to 0.01 mnkr, with
and without the flows that have time constants of days to weeks (payment terms in
working capital, refilling the cash reserve, taking a project into use). With
single-year ages it uses IDA's matrix-free linear solver (`-idaLS=spgmr`), since
the 202 age stocks make the Jacobian cost 20 s a run; that takes 1.3 s. One Euler
step a year is off by 40 mnkr in the result and 236 mnkr in debt after eight
years. Which solvers start depends on the compiler. In the web compiler built
from OpenModelica of 22 September 2026 (cc09fe3f5b), `euler`, `rungekutta`,
`dassl`, `ida`, `cvode`, `gbode` and `qss` start; in the one from 23 November 2026
(d3ca67ddd) `rungekutta`, `gbode` and `qss` fail at start with "in-wasm
initialization failed", also for `der(x) = -x`. `heun`, `impeuler`, `trapezoid`,
`rungekuttaSsc`, `imprungekutta`, `irksco` and `symSolver` fail in both. Until
24 November 2026 the site used `rungekutta` with 12 steps a year, about twice as
fast as `ida` (a scenario change took 0.6 s on the page, now 1.0 s); `dassl`
gives the same values but takes 20 s a run with single-year ages.

## Validation

**Identities and parity.** Every year the model asserts population balance,
asset, debt and cash balances and non-negative debt. `npm test` checks the browser
build against `Motala.Continuous` as written and against native OpenModelica. The
JavaScript reference of the yearly model (`site/src/engine.js`) was removed with it.
`npm run check:units` runs OpenModelica's unit checker on the library with the
money units written as SI units it knows; see [modelica/README.md](../modelica/README.md)
for what it covers.

**Hindcast.** `scripts/hindcast_vintages.py` starts from each set of accounts
2020–2024 with only what SKR's December circular of that year assumed, and runs
up to three years, not past 2025. Outcomes are Motala's annual reports
(`research/data/annual-ledgers.json`) and SCB for the others. Results are in
`data/vintage-hindcast-continuous.json`; the README has a summary (its tables were
made with the yearly model and are to be redone). One year ahead the
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
and 2.3 % of tax and grants in years 1–3 against 2.4, 3.7 and 3.4 for the
benchmark; from year 4 the benchmark does as well or better (year 8: 2.1 against 2.2).
The result is too low by 0.7–0.8 % in years 3–6. With the standard rates instead
of hindsight the model loses to the benchmark at every horizon. The population is
6 % too high after eight years (migration calibrated on 2015–2017), which raises
costs and grants together, and debt is too low by 20 % of tax and grants because
investment is held at the base year's level. The historical cost residual known in the base year, as
`costDrift`, makes it worse (net cost +11.5 % after eight years), so its default
is 0. Results in `data/long-hindcast-continuous.json`. Base years 2017–2019 use SCB's older
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

The test's Python copy of the capacity rule is checked against `Finspang.Continuous`
(to 5e-5) in `tests/test_response.py`. Not
tested: the interest rate's pass-through, the tax rate and pension costs. The
inflation scenario's shares are compared with 2022–2025 under "Explaining an
outcome" below. The 2020 reform of the cost equalisation falls
in the period and moved grants towards shrinking municipalities, so the low
ten-year revenue slope is not evidence of a weaker response to population.
`data/cost-residual.json` took the need a year late until 2026-11-24; it now
follows the model's timing.

**Explaining an outcome.** `scripts/explain_outcome.py [code Package]` treats the
closing accounts as the facts and asks what explains them. It runs
`Continuous.Economy` from the 2021 accounts to 2025, first as things were believed
(the `skr` set: SKR's December circular for the tax base, wages and prices; years
beyond the circular keep its last rate), then with one more input set to its
outcome in each run, cumulatively:

| Step | Parameter | Outcome from |
| --- | --- | --- |
| wages | `wageGrowthPath` | SKR's labour-cost index (PKV) |
| prices | `priceGrowthPath` | SKR's price index for other costs |
| pensions | `pensionExpensePath` | the accounts |
| tax base | `referenceTax` | SCB, the national tax base |
| grants | the component paths with `grantsByComponent` | the accounts, per component |
| interest | `interestRatePath` | interest expense over the mean debt of the year |
| investment | `investmentPath` | the accounts |

No equation changes. What is left after the last step is what these inputs do not
carry: the municipality's decisions on volume and savings, one-off items, financial
items other than interest (constant in the model), the municipality's population
(the model's projection throughout) and model error. The order is fixed; where
causes interact (debt and rate, wages and volume) a step's share depends on it. The
labour index includes the employer's pension surcharge, while payroll in the model
excludes pensions, so the wage step is somewhat too strong in 2023–2024 and too weak
in 2025.

Results for the 13 municipalities (`data/outcome-explanation-summary.json`, medians):
payroll is 2 to 7 % too low as believed and within about 2 % with the wage index
set in. Other costs are 2 to 6 % too low as believed and 5 to 9 % too high from 2023
with the price index set in: 85 % of the price surprise reached them in 2022, 20 to
50 % by 2023–2025. The model has no rule that cuts purchases when the result falls;
the balance requirement works through decisions, which are the user's to set. The
result's level is therefore not reliably closer to the accounts with the outcomes
set in: 3.4, 2.3, 4.2 and 2.9 % of tax and grants in 2022–2025, against 1.6, 4.3,
5.4 and 2.9 % as believed, where too-low revenue and too-low costs cancelled in
2022. The 2023 median is fragile: the gaps fall in two groups, around 2 % and
around 5 %, and one municipality moves it between 2.3 and 4.1. Its change from the
year before is closer in 2023 and 2025 (1.4 and 1.3 % against 3.7 and 2.0 %), not
in 2022 (3.4 against 1.6). One period, 13 municipalities.

The inflation scenario is tested in the same script: the believed run with
`inflationShockPath` set to the price surprise (SKR's index for other costs, outcome
minus circular: 7.8, 2.5, 0.6, 0.3 points) and nothing else. Medians, model minus
accounts: tax −2.9, −3.2, −0.1, 0.4 %; payroll −2.1, −3.4, −3.0, −2.8 %; pension cost
9.2, −2.0, −8.7, −2.3 %; interest −20, −13, 11, −53 % (no fixed-rate period in the
run). The result's change from the believed run, percent of tax and grants: −3.5,
−6.6, −7.4, −5.4, and with `inflationGrantCompensation = 1` −3.5, −4.6, −4.7, −2.5,
against −0.5, −4.3, −4.6, −1.2 in the accounts. The shares come from the same
period, so this is a fit, not an independent test: labour-cost index 5.0 points and
tax base 3.7 points above the circular over four years against 10.5 points of
delayed inflation; pension cost 34, 55 and 15 % above its believed path in
2023–2025 (the 2023 pension agreement not separated); the paid rate 1.8 and 2.1
points above 2021 in 2023–2024. Before 2026-11-24 wages and the tax base took all
of the year before's inflation, pension cost rose one for one the same year and
stayed, and the rate rose the same year; that put the hit a year early and kept it.

**SKR's old forecasts.** `scripts/read_skr_vintages.py` selects each municipality in
a macro-free copy of the four recovered workbooks (21:35, 22:28, 23:56, 24:56),
recalculates it in LibreOffice with macros disabled, and reads tax (Blad 1 row 38)
and general grants (row 40) after checking the municipality's name, the circular,
the years and the sums. Motala's 2021 figures equal the copy recalculated by hand
earlier, and every forecast for the year under way is within 3 % of the outcome
(`tests/test_explain_outcome.py`). Mean error for tax and grants against SCB, 13
municipalities: SKR 21:35 −2.8, −4.8, −5.6 and −5.3 % for 2022–2025; SKR 22:28
−3.0, −2.8 and −1.9 % for 2023–2025; the model from the 2021 accounts −2.2, −3.8,
−4.9 and −5.1 %. The model's run has later information than SKR 21:35 (the closing
accounts and the December circular), so the two are not a ranking. With its own
standard rates instead of the circular (run `standard`: tax base 3.5 %, wages 3 %,
prices 2 % a year) the model gives −2.2, −3.9, −5.0 and −5.1 %: the circular expected
3.4–3.7 % a year, so the model's default happened to be SKR's view then. Sweden's
population in that run is still the circular's.

**The band around tax and grants.** `scripts/prepare_revenue_uncertainty.py` sorts
the same errors of SKR's four workbooks by years ahead of the year the workbook was
published and writes `data/revenue-uncertainty.json`: mean absolute error 0.8 % in
the forecast's own year, then 1.9, 2.9, 3.9 and 5.3 % one to four years ahead, from
4, 4, 3, 2 and 1 workbooks. The page draws it as a band around the scenario's tax
and grants and holds the last value after four years. With an imported SKR path the
years count from the path's vintage, otherwise from the base year. The mean errors
are negative at every horizon (−0.8 to −5.3 %): the forecasts were too low through
the inflation of 2022–2023. The band is symmetric anyway, since one period gives no
ground for expecting the same sign again. It is the size of the errors in that
period, not a probability, and it is not carried over to the result: the inflation
that raised the tax base raised wages and prices too.

**SKR beside the government and ESV.** Each December circular has a table of the
latest forecasts of Sweden's tax base: SKR's, SKR's previous, the government's
(the budget proposition) and ESV's. They are read from the five circulars 2020–2024
(`research/data/tax-base-forecasters.json`, with page and table), and
`scripts/compare_tax_base_forecasters.py` compares them with the outcome through
2024 (`data/tax-base-forecasters.json`, `tests/test_tax_base_forecasters.py`). One
year ahead, four cases, every forecast was too low: mean error of the growth SKR
−1.8, ESV −1.5 and the government −1.5 percentage points. Two years ahead, three
cases, the mean absolute error is 1.3, 1.2 and 1.4. The level three years after
December 2020 was 4.9 % too low with SKR, 5.9 % with ESV and 5.8 % with the
government; after December 2021 3.3, 3.3 and 4.4 %. Nobody stood out. The miss of
2021 was the recovery after the pandemic (forecasts 1.9–2.5 %, outcome 5.3 %), that
of 2022 wages and prices (3.5–3.8 % against 5.8 %). The forecasts are not from the
same day (the government's is up to three months older, and its first two years
are fixed factors), the cases are few and share one period. Konjunkturinstitutet
publishes the wage sum, not the tax base; it is recorded in the same file and not
compared.

**Population.** `scripts/hindcast_county_ages.py` runs the demography for all 13
municipalities from 2022–2024 to 2025; results in
`research/data/age-group-hindcast.json`.

Limits: against SKR's circulars few cases (five base years, fewer at longer
horizons) and at most three years; the eight-year test has no forecasts of its time
and covers one period whose runs overlap, so its cases are not independent. SKR's
own historical forecasts for the municipalities are no longer on SKR's site; four
workbooks were recovered from the Internet Archive and are compared below. The
forecast sets use only data known at the base year (the closing accounts
and Kolada figures of the base year, published the following spring, included);
the hindsight and prices sets use outcomes on purpose.

## Browser engine

The site compiles `Kommunekonomi.mo`, the municipality's package and
`Browser.mo` with OpenModelica's web compiler (`wasm-jit`), and re-runs the
compiled model with `-override` for every scenario. `Browser.mo` holds the
wrapper `BrowserContinuous` around
`Kommunekonomi.Municipalities.Motala.Continuous`, without equations of
its own.
Inputs are validated in JavaScript, and the model asserts the same limits. The
compiler revision and file hashes are in `omc-web/manifest.json` on the site. No
resident-level data are used or stored.

The population calibration is computed in Modelica, in the wrapper: the page sends
the three years of history and, where loaded, SCB's projection (`historyCohorts`,
`projectedCohorts`, `followProjection`), and the model computes the death rates
(`Data.deathRatesPerYear`), the residual flow (`Data.calibratedMigrationRates`) and,
with the projection, the flow per year (`Data.projectionResiduals`) when it starts.
`-override` reaches them because they are computed from the inputs at
initialization. With SCB's projection the residual flow is the even inflow that
takes the five groups from one projected year end to the next through the ageing
chain, births included, so the model's population at each year end is the
projection's. Until November 2026 the page computed these in JavaScript, a copy
of the Modelica functions.

`tests/jit-continuous.test.mjs` runs the staged compiler in Node and checks that
the page's inputs give `Motala.Continuous` as written (to 1e-8), that the
population is SCB's projection at every year end, that wages and prices rise by the stated growth also through a
3 → 9 → 0 % shock, that every option keeps the balance checks, that `ida` agrees
with DASSL, that the exported `Scenario.mo` reproduces the page's run, that all
13 municipalities run from the 2024 and 2025 accounts, and that the page's
solver gives native OpenModelica's DASSL within 0.01 mnkr.
`tests/jit-model.test.mjs` checks the base years, Finspång, the migration profiles,
the single-year ages for every municipality and properties such as a tax rate
change not being cancelled by equalisation.

A run takes about 0.2 s with `ida`, and 1.5 s with single-year ages. A
page update runs about ten scenarios.
