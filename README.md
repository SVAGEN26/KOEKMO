# Motala ekonomilabb

A scenario lab for a Swedish municipality's finances, for the people who make
the decisions. Pick a municipality and a start year, change tax rate,
investments, wages, migration, interest or inflation, and see the result, cash
and debt year by year. The model is written in Modelica and runs in the
visitor's browser, by default in continuous time: money and people are stocks
that change every day, and only what is decided once a year is a yearly step.
Motala (0583) is the main case; all 13 municipalities in Östergötland run from
their own accounts.

The model covers the municipality's own accounts (kommunen, not the group):
population by age, service demand and capacity, payroll, pensions and other
costs, tax and general grants (SKR's calculation for the municipality, adjusted
per component for the model's population), investment, depreciation, working
capital, cash, debt and interest. All money is nominal mnkr; the library declares
units (`Kommunekonomi.Units`: `MSEK`, `MSEK/a`, `SEK` per inhabitant, persons per
year, years); `npm run check:units` checks the equations, not the annual rules in
algorithm sections (see [modelica/README.md](modelica/README.md)). The equations are in [docs/methodology.md](docs/methodology.md).

It is not a forecast to trust over simpler ones. Run from SKR's December circulars
2020–2024, Motala's result one year ahead is off by 40 mnkr on average; the
municipality's own budget was off by 24. Run eight years from the 2017–2019 accounts
of all 13 municipalities, even with what actually happened to prices, the tax base
and the state's grants, the model beats "the base year's result share kept" only in
the first three years. Its use is to show how a decision moves the result, cash and
debt, not to say what the result will be. Those responses are tested against the 13
municipalities' accounts: costs, depreciation and, over five years or more, debt
have moved about as the model's rules say, and tax and grants somewhat less, all
with wide margins. See [Accuracy](#accuracy).

## Run it

```sh
npm run stage:omc -- /path/to/build-web/install_cmake/share/omc/web   # once per compiler build
npm start                     # builds and serves http://127.0.0.1:8000
npm test
npm run validate:modelica     # native OpenModelica against the JavaScript reference
```

Python 3 and Node 18+; no npm packages. Native validation, the hindcasts and
the MCP server need OpenModelica (set `OMC` if `omc` is not on PATH). If port
8000 is taken, `npm start -- --port 8001`. Building the web compiler is
described under [Browser engine](#browser-engine).

Open a municipality and start year directly, for example
[Linköping from 2025](http://127.0.0.1:8000/?kommun=0580&start=2025). The first
forecast year is 2025 (from the 2024 accounts) or 2026 (from the 2025 accounts);
Motala also has a run from 2022. The end year can be set up to 100 years ahead, but
the model is built for 8–10 years, like SKR's forecasts. After SKR's last year
(2033) its growth rates are held, so later years are arithmetic, not a forecast.

## What the site does

- **Start view.** The root address shows the 13 municipalities as cards with
  population, the latest result and tax rate; a card opens the lab. The address
  `?kommun=CODE` opens a municipality directly.
- **Scenario controls.** Assumptions in five groups that open on demand
  (population, revenue, costs, investment and loans, rate and inflation shocks),
  each showing how many values are changed and with its own reset. A `?` next to
  each control explains it and where the default comes from. Two controls set
  what the model otherwise leaves out: cost growth beyond demography and prices
  (default 0; history −0.3 to 0.4 % a year) and the state's further increase of
  the general grants beyond SKR's path, in billion kronor nationally per year
  (`grantIncrease` in the Modelica model, so the MCP server has it too). Further options:
  a dated building project, working capital, a cash policy, SKR's revenue path
  as published, proportionally adjusted or adjusted per component, five age
  groups (default) or single years of age, and the model's time: continuous
  (default) or one step a year.
- **Prepared scenarios** as buttons: Higher interest, Higher inflation, a weaker
  economy, more migration and lower investment. See [Scenarios](#scenarios).
- **Balance requirement.** Years with a deficit are shaded in the result chart.
  An optional result target (% of tax and grants) draws a line and lists the
  years below it.
- **Shareable address.** The address always describes the scenario on screen:
  municipality, period, changed assumptions and options (`s=`). "Kopiera länk"
  copies it. An imported SKR file is not part of the link.
- **Comparison.** Save named runs in the browser and compare them; "Varför
  skiljer sig banorna?" splits the difference into revenue and costs per year.
  The comparison tab shows the latest accounts and SKR 26:28 for the
  municipality.
- **Modellen.** A flow diagram of the six components with the equations and
  Modelica code of the model that is running, continuous or yearly.
- **Export.** Scenario as JSON or as `Scenario.mo` for OpenModelica (extending
  the municipality's `Continuous` or `Annual` model, whichever ran), and a PDF
  report (A4 landscape, through the browser's print dialog).

## Scenarios

### Higher interest

A rise in the market rate reaches the interest cost as loans are refixed or
newly taken. `rateFixingYears` is the average fixed-rate period (loans and
derivatives) from the annual report: for Motala 3.77, 3.5 and 3.19 years at the
end of 2023, 2024 and 2025 (annual reports 2023 p. 41, 2024 p. 21, 2025 p. 21;
`data/rate-fixing.json`). Other municipalities assume 3 years. `rateShock`
raises the market rate from `rateShockTime` (decimal year, 2026.5 = 1 July 2026).
With `rateFixingYears = 0` the whole debt pays the year's rate, as before.

**Högre ränta** adds 3 percentage points from 1 January of the first forecast
year. For Motala from the 2025 accounts interest goes from 25 to 32 mnkr in 2026
and from 32 to 69 mnkr in 2029; as a share of the year's mean debt that is from
2.2 % to 2.9 % in 2026 and 4.5 % in 2029. The hindcast does not use actual rates
as inputs.

### Higher inflation

Extra inflation above the price path (`inflationShock`, `inflationPersistence`,
or `inflationShockPath` year by year) reaches prices the same year, wages and the
tax base the year after, pension cost the same year, and the market rate by
`inflationRateResponse` points per point. General grants stay fixed in kronor
unless `inflationGrantCompensation` is set. The pass-through shares are
illustrative assumptions, not estimates.

**Högre inflation** (3 points the first year, half left each year after): for
Motala from the 2025 accounts the result is 49 mnkr below the base path in 2026
and 105 mnkr below in 2033.

These numbers are the site's, read from the page in headless Chromium on
2026-11-24 with the continuous model. The rate and inflation controls are also
run in the staged compiler by `tests/jit-continuous.test.mjs`.

## Connect an AI to the page

An AI assistant can work in the page you have open, the way it works in OMEdit:
read the assumptions and the series, try scenarios and change the page while you
watch. A page cannot listen for connections, so a small local bridge sits between
the assistant (MCP) and the page:

```sh
node mcp/bridge.ts            # prints the page address, a token and http://127.0.0.1:8765/mcp
node mcp/bridge.ts --stdio    # MCP over stdin/stdout, for clients that start the bridge
```

In the page, open "Koppla till AI (lokalt)" under the assumptions, give the
address and token, and press Koppla. The assistant connects to
`http://127.0.0.1:8765/mcp` with `Authorization: Bearer <token>`, or starts the
bridge with `--stdio` (give it a fixed `--token` so you can type it in the page).
For Claude Code:
`claude mcp add --transport http ekonomilabb http://127.0.0.1:8765/mcp --header "Authorization: Bearer <token>"`.

| Tool | What it does |
| --- | --- |
| `get_state`, `list_municipalities` | What the page shows; the municipalities and start years |
| `list_assumptions` | Every control: unit, range, current value, default, and what it means |
| `preview_scenario` | Try values without changing the page; results and the difference year by year |
| `set_assumptions`, `reset_assumptions` | Change the page, with a reason shown in the page's log |
| `select_municipality` | Change municipality and start year |
| `get_results` | The page's scenario year by year |
| `list_series`, `get_series` | Accounts per municipality (SCB), cost growth, SKR 26:28, PKV, Sweden's population, the hindcast |

It is all opt-in and local. The link is off until you connect. The bridge listens
on 127.0.0.1 only, makes no outgoing requests, holds no API keys, and needs the
token from both the page and HTTP clients. The page sends only to the address you
give, and warns when that is not this computer. The page runs every tool with its
own OpenModelica build and the same validation as the controls; the assistant
sends values, never model text. The tools are in `site/src/ai-tools.js`, the page
side in `site/src/ai-link.js`. Chrome asks before the published https site may
reach a port on this computer; served locally (`npm start`) it does not.

## Local MCP server: let an AI run the budget

`scripts/mcp_server.py` lets an AI assistant run the model year by year over the
Model Context Protocol, with the project's own tools. Standard library and native
OpenModelica only; nothing leaves the machine.

```sh
python3 scripts/mcp_server.py               # stdio
python3 scripts/mcp_server.py --http 3001   # http://127.0.0.1:3001/mcp
```

Claude Code picks up `.mcp.json` in the project root. Other local clients can
start the stdio command or connect to the HTTP address, which binds to 127.0.0.1
and refuses other browser origins.

| Tool | What it does |
| --- | --- |
| `list_municipalities`, `list_parameters` | The 13 municipalities, base years 2020–2025, and the decisions that can be set |
| `start_session` | Start from a base year's accounts, with `Annual` or `Continuous` |
| `set_decisions` | This year's decisions (tax rate, investment, interest, wages, migration ...) with a reason |
| `advance` | Simulate the next year; return accounts, balance checks and SKR's tax and grants |
| `get_results`, `run_scenario` | Any output variable; a whole scenario at once (`higherInterest`, `higherInflation`) |
| `reference` | SKR 26:28 (cited) and SCB's accounts 2020–2025 |
| `save_session` | Decisions, reasons and results as JSON, plus a Modelica model for OMEdit |

The prompt `budget_round` asks the assistant to act as the finance committee.
Only parameters of `Kommunekonomi.Assumptions` can be set; no client text
reaches the compiler. Sessions go to `build/mcp/sessions/`. A run takes 2–3
seconds and is cached. It runs native OpenModelica, not the page; for the page,
see [Connect an AI to the page](#connect-an-ai-to-the-page).

## The models

| Model | Where | Used by |
| --- | --- | --- |
| `Kommunekonomi.Continuous.Economy` | `modelica/Kommunekonomi.mo` | The site (default), the MCP server (optional), the hindcasts |
| `Kommunekonomi.Annual` | same | The site ("Tid i modellen: Årssteg"), the MCP server, the hindcasts |
| `Motala.Annual`, `Motala.Continuous`, examples | `modelica/Motala.mo` | Motala's base years 2020–2025 |
| One package per municipality | `modelica/municipalities/*.mo` | Generated from SCB and Kolada |
| M1, M2 (research) | `research/` | Nothing on the site; see [research/M2.md](research/M2.md) |

`Continuous.Economy` has the same assumptions and outputs as `Annual` in
continuous time. Money and population are stocks with flows: births, deaths,
ageing and migration, costs, and wage and price levels that grow within the
year. Only annual rules are events: the year-end close, decisions from
1 January (tax rate, tax and grants, paid evenly), the 1 November population
count and reading the annual paths. The site runs it by default; `Annual` takes
one step a year and is a choice under "Pröva modellvarianter".

With the same inputs the two give the same wage and price indices, the same
population at each year end (with SCB's projection) and the same tax and grants
(within 2 mnkr with adjustment per component, where the continuous model reads
the population on 1 November instead of interpolating it). They differ in
timing: capacity follows demand continuously and trails a steady trend by 1.4
years where `Annual`'s trails by one, costs are counted through the year
instead of at its end, interest accrues on the debt as it grows, and
depreciation starts when an investment is paid. Where demand for schooling
falls, costs are therefore higher than in `Annual`: for Motala from the 2025
accounts the result is 5–11 mnkr lower each year (151 against 159 mnkr in 2033)
and the debt 65 mnkr higher in 2033 (1 576 against 1 511); for Linköping the
result is 21–42 mnkr lower a year. The adjustment speed is an illustrative
assumption in both. The continuous model is no more accurate against outcomes
than `Annual`; see [Accuracy](#accuracy) and
[docs/methodology.md](docs/methodology.md#continuous-time).

In OMEdit, load `Kommunekonomi.mo` first, then `Motala.mo`, and open
`Motala.Annual` or `Motala.Continuous` in Diagram view. Defaults are
illustrative; download `Scenario.mo` from the site to reproduce a scenario with
the planning inputs. See [modelica/README.md](modelica/README.md).

## Data

All inputs are archived with source, query, licence, time and SHA-256 under
`data/downloads/<timestamp>/manifest.json`. Only manifests and READMEs of new
archives are in git. SCB data are CC BY 4.0. SKR's workbooks are not in the
repository; the municipal extracts (`skr-revenue-path.json` and per municipality)
are published with source and terms in their `source` block.

| Input | Source | Prepared by |
| --- | --- | --- |
| Base-year accounts | Motala's annual reports; SCB TAB6777/6779/6782 for others | `scripts/prepare_municipality.py` |
| Population by single year of age, births, deaths, migration | SCB | `scripts/prepare_demography.py`, `write_demography_modelica.py` |
| Sweden's population and life tables | SCB | `scripts/fetch_national_population.py`, `fetch_mortality_data.py` |
| Care cost by age (65–79, 80–89) and sector cost weights | Kolada | `scripts/prepare_care.py`, `fetch_sector_costs.py` |
| Tax capacity | SCB OE0101 SkatteKraft | `scripts/fetch_tax_capacity.py` |
| Equalisation per component | SCB TAB1981, TAB4011 | `scripts/fetch_equalisation.py` |
| Tax, grants and November population 2026–2033 | SKR 26:28, recalculated per municipality | `scripts/recalculate_skr.py` |
| Tax-base growth and cost indices | SKR circulars and PKV | `scripts/prepare_planning_inputs.py` |
| Fixed-rate period | Annual reports | `data/rate-fixing.json` |

To add a municipality: `scripts/fetch_municipality.py CODE`,
`scripts/fetch_care_data.py CODE`, `scripts/prepare_care.py ARCHIVE --output
data/municipalities/CODE/care-weights.json`, `scripts/fetch_sector_costs.py CODE`,
`scripts/prepare_municipality.py CODE Package "Name" ARCHIVE --modelica`, then
`scripts/prepare_web_municipality.py CODE 2025` (and 2024). Test it with
`scripts/hindcast_vintages.py CODE Package`.

`scripts/import_skr.py` reads cached values from SKR's XLSX/XLSM with an explicit
cell map and never runs macros; see `data/skr-motala/README.md`.
`scripts/strip_pdf_images.py <archive>` blanks the pictures in archived PDFs
(photos can carry third-party rights) and records the original hash.

## Accuracy

The goal is a tool for decisions, not a better forecast than SKR's. The model is
still checked against what happened. The forecast sets use only what was known at
the start; the "hindsight" sets use outcomes on purpose, to separate errors in the
inputs from errors in the model.

**Up to three years against SKR's circulars.** `scripts/hindcast_vintages.py`
starts from each set of accounts 2020–2024 and runs up to three years, not past
2025. Motala, mean error (model minus outcome) after 1/2/3 years, mnkr, with 5, 4
and 3 cases, from `data/vintage-hindcast.json`. "SKR" uses only the assumptions in
SKR's December circular of the start year, with grants growing 2 % a year;
"components" adds the state's grant decisions in that circular (grants per
component); "hindsight" uses the outcomes for prices, the tax base and the state's
grants per component (a diagnosis, not a forecast):

| Line | SKR | Components | Hindsight |
| --- | --- | --- | --- |
| Result | −38 / −47 / +18 | −11 / −17 / +37 | −18 / −20 / +2 |
| Tax | −35 / −51 / −71 | −35 / −51 / −71 | −10 / −11 / −14 |
| General grants | −23 / −61 / −104 | +4 / −33 / −84 | 0 / +9 / +16 |
| Net cost | −20 / −64 / −187 | −20 / −64 / −187 | +8 / +21 / +5 |

Read it this way. With SKR's assumptions the three-year result error is small only
because two large errors cancel: net cost too low by 187 and tax and grants too low
by 175. With what actually happened to prices, the tax base and the state's grants,
tax, grants and net cost come close, but the result's mean absolute error is still
43 / 57 / 39 mnkr against 40 / 59 / 58 with SKR's assumptions. Keeping the base
year's result ("persistence") misses by 59 / 76 / 41. One year ahead the
municipality's budget missed by 24. Mjölby and Finspång, the same way (mean
absolute error of the result, mnkr):

| | SKR | Hindsight | Persistence |
| --- | --- | --- | --- |
| Motala | 40 / 59 / 58 | 43 / 57 / 39 | 59 / 76 / 41 |
| Mjölby | 41 / 65 / 116 | 28 / 40 / 59 | 44 / 82 / 91 |
| Finspång | 38 / 76 / 59 | 24 / 43 / 13 | 38 / 52 / 38 |

These tables are for the yearly model. The continuous model, the site's
default, gives 40 / 60 / 60 for Motala, 42 / 67 / 126 for Mjölby and
39 / 77 / 59 for Finspång with SKR's assumptions (`HINDCAST_MODEL=Continuous`,
`data/vintage-hindcast-continuous.json`): the same accuracy.

Five, four and three cases per horizon, from one period, are too few to rank the
sets (`scripts/compare_hindcasts.py CODE [skr|components|hold|prices|hindsight|standard]`).

SKR's own forecasts for the municipalities from those dates are no longer on SKR's
site. Four of the workbooks were recovered from the Internet Archive
(`data/skr-historical/`: circulars 21:35, 22:28, 23:56 and 24:56); so far only
21:35, of September 2021, is read out for Motala. Its tax and general grants for
2022–2025 were 63, 155, 177 and 197 mnkr below the outcome. The model's own
forecast from the 2021 accounts, with its standard growth rates and no SKR path,
was 75, 162 and 198 mnkr below for 2022–2024. Both missed the inflation years by
about the same amount. One vintage and one municipality; the other three
workbooks are not yet compared.

**Eight years, 13 municipalities.** `scripts/hindcast_long.py` starts from SCB's
accounts of 2017, 2018 and 2019 and runs to 2025 (8, 7 and 6 years) for all 13
municipalities, 39 runs, against SCB's outcomes. No forecasts from those years are
collected, so "hindsight" uses the outcomes for prices, the tax base, the state's
grants and Sweden's population; the municipality's population, costs, debt and
result are the model's. Norrköping 2022 and 2023 are left out: the outcome holds the
Ostlänken provision (−3 281 and −80 mnkr), not split into operating and financial
items. Mean error / mean absolute error in percent of tax and grants (population:
percent), from `data/long-hindcast.json` (the yearly model; the row "continuous
model" is the site's default, from `data/long-hindcast-continuous.json`):

| Years ahead (cases) | 1 (39) | 2 (39) | 3 (38) | 4 (37) | 6 (38) | 8 (13) |
| --- | --- | --- | --- | --- | --- | --- |
| Result | 0.0 / 1.7 | −0.2 / 2.2 | −0.7 / 2.4 | −0.8 / 3.3 | −0.8 / 2.9 | −0.2 / 2.2 |
| Result, continuous model | 0.2 / 1.8 | 0.3 / 2.3 | −0.1 / 2.6 | −0.2 / 3.4 | −0.2 / 3.0 | 0.7 / 2.2 |
| Result, persistence | −0.5 / 2.4 | −1.8 / 3.7 | −3.1 / 3.4 | −2.1 / 3.0 | −0.3 / 2.3 | −0.5 / 2.2 |
| Result, standard rates | −1.1 / 2.5 | −3.0 / 4.1 | −4.7 / 5.1 | −4.1 / 4.9 | −2.8 / 3.4 | −3.4 / 4.0 |
| Net cost | −0.2 / 1.9 | −0.1 / 2.1 | 1.1 / 2.3 | 1.4 / 2.9 | 3.1 / 4.0 | 5.1 / 5.7 |
| Tax | 0.0 / 0.9 | −0.2 / 1.2 | −0.2 / 1.5 | −0.5 / 1.7 | 0.1 / 2.3 | 1.6 / 2.8 |
| General grants | 0.0 / 0.0 | 0.4 / 0.4 | 0.8 / 0.8 | 1.1 / 1.1 | 1.9 / 1.9 | 3.1 / 3.1 |
| Population | 0.4 / 0.6 | 0.9 / 1.2 | 1.4 / 1.7 | 1.9 / 2.4 | 3.3 / 3.7 | 6.0 / 6.1 |
| Debt | −0.3 / 4.9 | −1.7 / 8.7 | −1.5 / 12.4 | −0.9 / 15.6 | −11.7 / 28.5 | −32.4 / 34.0 |

The model with hindsight beats persistence in years 1–3 only; from year 4 the base
year's result share does as well or better. The continuous model's result is
about half a per cent of tax and grants higher than the yearly model's, since
its costs trail the population by about a year more and the population grows too
fast in this test; its errors are as large. With the model's standard rates instead
of hindsight it is worse than persistence at every horizon. The result is too low by
0.7–0.8 % of tax and grants in years 3–6, about a third of a usual result target of
2 %. The population grows too fast (6 % after eight years: migration calibrated on
2015–2017, the years of high refugee immigration), which raises costs and grants
together, so part of the result error cancels. Debt comes out too low because
investment stays at the base year's amount. With costs growing by each
municipality's historical residual up to the base year (set "drift",
`data/cost-residual.json`, measured on the model's basis), net cost is 11.5 % too
high and the result 6.9 % too low after eight years, so cost growth is 0 by default
and a scenario control on the site. The test covers one period, 2017–2025, and its
runs overlap, so the 39 cases are not independent.

**Does history move as the model says?** The tests above score levels. The site
is used to see how much the result moves when something changes, so
`scripts/response_test.py` tests the model's rules one at a time against the 13
municipalities' accounts. For each rule it takes the observed driver, computes
the change the rule gives, and regresses the observed change on it, with what was
common to all municipalities in a year removed. A slope of 1 means history moved
as the model says; 0.5 means half as much. The interval is 95 %, from resampling
municipalities. From `data/response-test.json`:

| Rule | Model | History: slope (interval) | Cases |
| --- | --- | --- | --- |
| Need from the population → real operating cost, 5 years | 1 | 1.03 (0.54 to 1.64) yearly model; 0.93 (0.42 to 1.54) continuous | 126 |
| The same, 1 year | 1 | 0.82 (0.30 to 1.30); 0.71 (0.09 to 1.31) | 180 |
| Population the year before → tax and grants, 1 year | 0.94 | 0.78 (0.49 to 1.10) | 189 |
| The same, 10 years | 0.94 | 0.44 (0.10 to 0.90) | 74 |
| Financing need → bank debt less lending and cash, 1 year | 1 | 0.71 (0.20 to 1.02); 0.53 (0.17 to 0.95) with the need from the balance sheet | 99 |
| The same, summed over 5 years | 1 | 0.85 (0.58 to 1.09); 0.78 (0.29 to 1.09) | 45 |
| Investment → depreciation, 3 years | 1 | 0.89 (0.39 to 1.56) | 75 |
| SKR's price index → cost beyond volume | 1 | 0.84 (−0.10 to 1.34) | 14 years |

- **Costs** have followed the need from the population about as the model says,
  2012–2025. The data cannot tell the yearly and the continuous model apart, nor
  pin down the adjustment speed (best fit 1.0, interval 0.2 to 1.0) or the fixed
  share (0.25, interval 0 to 0.6). Demography explains little of the differences
  between municipalities (R² 0.17 over five years).
- **Tax and grants** follow the population a year later, as in the model: against
  the same year's population the one-year slope is 0.12. The size is somewhat
  below the model's 0.94 and clearly below over ten years. The 2020 reform of the
  cost equalisation moved grants towards municipalities that shrink, in the same
  period, so a weaker response to population is not shown.
- **Debt.** The model borrows the whole financing need (investment less the
  result and depreciation). Within one year 0.5 to 0.7 of it became bank debt net
  of lending and cash; the rest was covered for the time being by other
  liabilities, such as leasing and loans within the group. Summed over five
  years it is 0.8 to 0.85, and over eight years 0.9 to 1.0 (11 municipalities),
  with 1 inside the interval. So the rule holds over the horizons the site
  shows, and a single year's debt can be off. A quarter of the yearly change of
  bank debt is lending to the municipality's own companies, which the model does
  not have. Connection fees and investment grants paid only 0.2 to 4.5 % of the
  investments 2018–2025 (SCB TAB4201), too little to matter.
- **Depreciation** follows the model's rule within the margins.
- **Not tested:** the interest rate's pass-through, the tax rate, pension costs
  and the inflation scenario's pass-through shares.

Thirteen municipalities in one county are few; every interval is wide.
`tests/test_response.py` checks that the test's copy of the capacity rule is the
Modelica model's.

Population: `scripts/hindcast_county_ages.py` runs the demography for all 13
municipalities from 2022–2024 to 2025 (78 cases per variant). One year ahead,
five age groups miss total population by 93 persons on average, single years of
age by 115–125; single years of age are far better for 80–89 (14 against 84).
Details and the history of earlier attempts are in
[docs/project-memory.md](docs/project-memory.md).

## Browser engine

The site has one engine: OpenModelica's compiler built for WebAssembly. A worker
(`site/src/omc-worker.js`) fetches the compiler (about 100 MB, cached afterwards),
loads `Kommunekonomi.mo`, the municipality's package and `MotalaBrowser.mo`, and
runs `buildModel` with the `wasm-jit` target (two to three seconds; nine with
single-year ages). Each scenario re-runs the compiled model with `-override`, in
about 0.1 s. `MotalaBrowser.mo` holds two wrappers that add no equations,
`MotalaBrowserContinuous` (the default) and `MotalaBrowser` (the yearly model):
they fix the array capacity at 100 years and make every input a free parameter
with a literal default (OpenModelica folds defaults that depend on the base year
at compile time, out of `-override`'s reach). No cross-origin isolation is
needed.

The continuous model is integrated with Runge-Kutta, twelve steps a year, which
gives native OpenModelica's DASSL within 0.01 mnkr (0.03 mnkr in a year where the
cash flow changes sign; see [docs/methodology.md](docs/methodology.md#continuous-time)). Scenarios with working
capital, a cash reserve or the project have flows with time constants of days
to weeks and run with the implicit solver IDA instead (0.2 s). Single-year ages
in continuous time take 0.4 s a run, and 1.5 s with IDA; a page update runs
about ten scenarios, so that combination is slow.

`site/src/engine.js` is an independent JavaScript reference for the yearly model,
used only by the tests; the site does not ship it. `tests/jit-parity.test.mjs`
runs the staged compiler in Node against it. The continuous model has no
JavaScript reference: `tests/jit-continuous.test.mjs` checks it against
`Motala.Continuous` as written, against SCB's and SKR's inputs, against the
yearly model where the two must agree, and against native OpenModelica. Both
are skipped when no compiler is staged.

Build the compiler once (Ubuntu 24.04):

```sh
sudo apt install rustup lld wasi-libc libclang-rt-18-dev-wasm32 libclang-rt-dev-wasm32 libstdc++-14-dev
rustup toolchain install nightly-2026-05-31 --profile minimal \
  --component rustc-codegen-cranelift-preview --target wasm32-unknown-unknown
cmake -S /path/to/OpenModelica -B /path/to/build-web -G Ninja \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DOM_OMC_WASM=ON \
  -DRUST_OMC_WASM_MODE=web-release -DRUST_OMC_CI=ON -DOM_USE_CCACHE=OFF \
  -DWASM_OPT_EXECUTABLE=$PWD/.local/emsdk/emsdk-4.0.20/upstream/bin/wasm-opt
cmake --build /path/to/build-web --target install
npm run stage:omc -- /path/to/build-web/install_cmake/share/omc/web
```

`wasm-opt` must be binaryen 120 or newer; Ubuntu 24.04's (108) fails at the last
step. `stage:omc` copies the compiler and OpenModelica's licence into
`site/omc-web/` (not in git) and records the revision and SHA-256 of every file;
`npm run build` refuses a staged compiler that does not match.

## Publish

`.github/workflows/site.yml` builds the web compiler from OpenModelica's public
repository, runs the tests and builds `site/dist`. A push to `main` only builds
and tests. Publishing is manual: `gh workflow run site.yml --ref main`. The
deploy job runs only in a public repository. By hand,
`scripts/deploy_pages.py <remote>` pushes `site/dist` as a single commit to
`gh-pages`.

## Repository

- `modelica/`: the models the site runs. See [modelica/README.md](modelica/README.md).
- `site/src/`: the web app. `omc-worker.js`, `omc-session.js`, `jit-engine.js` are the engine; `pdf-report.js` the report.
- `scripts/`: data fetching and preparation, hindcasts, the response test, build, MCP server.
- `data/`: prepared inputs, hindcast results, per-municipality data in `data/municipalities/CODE/`, archive manifests in `data/downloads/`.
- `tests/`: `npm test` (JavaScript and Python).
- `docs/methodology.md`: equations and limits. `docs/project-memory.md`: dated project log and open items (Swedish).
- `research/`: M1 and M2, frozen reference models, replays and reviews. Kept so earlier results can be reproduced; see [research/README.txt](research/README.txt) and [research/M2.md](research/M2.md). `python3 scripts/download_research.py` fetches the papers listed in `research/papers/sources.json`.

Git ignores `site/dist/`, `build/`, `research/runs/`, raw downloads and staged
compilers.

## Licence

The project's own work, including the Modelica models, is MIT-licensed; see
`LICENSE`. The published site bundles OpenModelica's web compiler under OSMC-PL
1.8 or GNU AGPL 3, with the licence text and source revision in `omc-web/`.
Source documents and data keep their publishers' terms.
