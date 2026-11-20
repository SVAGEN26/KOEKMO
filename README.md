# Motala ekonomilabb

A whole-budget Modelica scenario model for **Motala**, with an interactive Swedish dashboard. Includes traceable 2025 accounts, five demographic cohorts, separate payroll/pension/other operating costs with adaptation delays, approximate tax/equalisation responses, investment, assets, cash and debt. Dated SKR cost forecasts improve the Motala retrospective comparison at short horizons; three-year accuracy remains weak. Forecast superiority beyond these development comparisons is unproven.

Motala's historical results and local planning needs are the primary evaluation.
Tests on other municipalities are supplementary checks of transferability and
overfitting. Their results remain visible, but do not replace the Motala evaluation
or automatically justify adding mechanisms specific to another municipality.

The web app runs the Modelica model itself. OpenModelica's compiler, built for
WebAssembly, compiles `modelica/Kommunekonomi.mo` with the selected municipality’s package in the visitor's browser (`wasm-jit`)
and simulates every scenario there. Nothing is sent to a server, so the site is
plain static files and can be hosted on GitHub Pages. See
[Browser engine](#browser-engine-openmodelica-wasm-jit).

```sh
npm run stage:omc -- /path/to/build-web/install_cmake/share/omc/web   # once per compiler build
npm run build
npm test
npm run backtest
npm run validate:modelica
npm start
```

Open http://127.0.0.1:8000. No npm installation is required. Python 3, Node 18+ and (for native validation) OpenModelica are used. Set `OMC` to an omc executable if it is not on PATH. Native validation auto-detects the existing local installation.

`npm start` also builds the static files, so it works from a fresh checkout.
If port 8000 is occupied, use `npm start -- --port 8001`.

Select any of **Östergötland’s 13 municipalities** in the scenario controls. For example, open [Linköping from 2025](http://127.0.0.1:8000/?kommun=0580&start=2025). Each municipality can start its forecast in 2025 or 2026. The comparison view includes the 2025 accounts and the local SKR 26:28 reference. See [project memory](docs/project-memory.md#alla-13-kommuner-i-östergötland) for sources and regeneration commands.

- `modelica/`: the model the site runs, and nothing else. `Kommunekonomi.mo` is a library of reusable components for a
  Swedish municipality's annual finances (record types, Sweden-wide SCB data, components, the partial model `Annual`).
  `Motala.mo` holds Motala's data and examples; `Motala.Annual` extends `Kommunekonomi.Annual` with Motala's base year.
  `MotalaBrowser.mo` is the wrapper the browser compiles, `validate.py` the native parity check. Load the library first.
  `modelica/municipalities/` holds packages for other municipalities, generated from SCB and Kolada (including the Finspång web pilot and the Mjölby transferability check). To add one: `scripts/fetch_municipality.py CODE`, `scripts/fetch_care_data.py CODE` and
  `scripts/prepare_care.py ARCHIVE --output data/municipalities/CODE/care-weights.json`, `scripts/fetch_sector_costs.py CODE`,
  then `scripts/prepare_municipality.py CODE Package "Name" ARCHIVE --modelica`, and test it against the SKR circulars with
  `scripts/hindcast_vintages.py CODE Package`. For Motala the SCB route reproduces the annual reports within 2-3 mnkr from 2023.
- `research/`: experiments that are not part of the site: the M1 and M2 models (`MotalaResearch`,
  `MotalaDynamics`), frozen model versions in `research/reference/`, historical replays, their data,
  reviews and tests. Kept so the results quoted in this README and on the site can be reproduced.
- `site/src/omc-worker.js`, `omc-session.js`, `jit-engine.js`: the browser engine. A worker loads OpenModelica, compiles a model per municipality, start year and demographic mode, then re-runs it with `-override` per scenario.
- `site/src/engine.js`: independent JavaScript reference used only by the tests (`tests/jit-parity.test.mjs`, native parity). The site does not ship it. Other editable dashboard assets are also in `site/src/`.
- `data/baseline.json`, `data/history.json`, `data/sources.json`: facts, provenance and explicit assumptions.
- `data/operating-accounts-history.json`: sourced 2024–2025 expenditure/revenue components and reconciliation.
- `data/municipal-benchmarks.json`: recorded 2025 budget/April/August result forecasts, with provenance and missing release dates identified.
- `docs/methodology.md`: equations, approximations, acceptance criteria and validation limits.
- `scripts/import_skr.py`: dependency-free XLSX/XLSM inspection and explicit cell-map extraction. Reads cached values, never runs macros.
- `scripts/backtest.mjs`: retrospective population comparison; writes `data/backtest.json` and browser results.

## Active planning inputs (2026-11-06)

The dashboard now starts with `data/planning-inputs.json` active. A checkbox
switches to the earlier illustrative assumptions. The prepared inputs use:

- Motala population projections from the regional PxWeb database, 2026–2033.
  Five-year age bins are split uniformly at the model's age boundaries. Cohort
  growth is anchored to the existing 2025 accounts, then reconciled to the source
  total growth. Source 2025 total is 43,132 versus 43,131 in the accounts.
- National SKR annual tax-base growth and labour/other-consumption indices read
  from cached input cells in the user-supplied 26:28 workbook. Sliders become
  percentage-point deviations from these paths. The labour index is a proxy for
  payroll excluding pensions; it does not replace the pension-cost assumptions.
- Twenty Kolada indicators as visible comparison data, plus six original budget
  and accounts PDFs as downloadable references. Neither is automatically treated
  as calibrated cost weights or an imported investment plan.

The original workbook's `Prognosunderlag!B1` is empty. A separate working copy
now selects Motala (583), and its formulas have been recalculated with a local
LibreOffice 24.2.7.2 runtime. VBA was removed before recalculation and macros
were disabled. `data/skr-revenue-path.json` is active by default in the dashboard.
Tax uses output row 38 including settlements; grants use row 40 including
property fees, LSS and equalisation. Values convert tkr to mnkr. Reference
population is 1 November of the preceding year, from input row 29. Components
reconcile to output row 36 in all eight forecast years.

The raw reference is shown separately from locally adjusted scenario revenue.
The original file is unchanged. The recalculated workbook, explicit cell map,
source hashes and reconciliation receipt are under `data/skr-motala/`.
See that directory's README for local recalculation instructions.

Recreate the prepared inputs offline with:

```sh
python3 scripts/prepare_planning_inputs.py
npm run build
npm test
npm run validate:modelica
```

This requires the archived originals at `data/downloads/20261106T090534Z/` and the
user-supplied workbook in `data/`. Preparation verifies the source hashes.
`export_reference.mjs` loads the same active inputs and municipal revenue reference for native parity checks.
A standalone `Motala.Annual` in OMEdit retains its illustrative defaults; export
`Scenario.mo` from the dashboard to reproduce the activated scenario.

The historical population backtest still evaluates the earlier model, not the
new externally supplied future path. Input activation is not evidence of improved
forecast accuracy. See `docs/project-memory.md` for status and remaining work.

## PDF scenario report

Use **Exportera PDF** beside the view tabs, then choose **Save as PDF** in the
browser print dialog. The report opens in a separate tab and snapshots the
current scenario, including graphs from all views. Five graph sections show
their relevant settings and annual effective inputs; a sixth section compares
the imported SKR revenue reference with the locally adjusted scenario and gives
source/version information. Output is designed for A4 landscape. The report
keeps the existing small-logo dashboard layout unchanged.

The client-side implementation is `site/src/pdf-report.js`; it requires no
external PDF service or runtime dependency. `npm test` covers current parameter
values, source-off mode, missing graph fallback and escaping imported text.
Actual Firefox export was checked with a changed interest rate and a six-page
PDF. This is an export of scenario calculations, not a validated forecast.

## Demography: single years of age (SCB)

`Motala.Components.CohortDemography` is the cohort-component method SCB uses: single years of
age 0–100+ by sex, deaths from the national life table scaled to Motala's level, births from a
selectable fertility model, and calibrated residual flows. `Examples.AnnualCohort` runs the whole
model with it; `Annual` keeps the five-cohort demography, which the site uses.

- Data: SCB (CC BY 4.0), archived in `data/downloads/20261108T124756Z/` by
  `scripts/fetch_mortality_data.py`, prepared by `scripts/prepare_demography.py` into
  `data/demography-inputs.json`, written into `Motala.Data.SCB` by `scripts/write_demography_modelica.py`.
- Each base year 2020–2025 has its own calibration from data up to that year: Motala's mortality
  relative to Sweden (five years), the national mortality trend (ten years, by age band), and residual
  flows by age (three transitions).
- Birth models (`Components.Fertility`): `Constant` (default 1.41 children per woman), `Projected`
  (SCB's national projection), `Legacy` (the five-cohort rule).
- `scripts/hindcast_demography.py` starts from each base year 2020–2024 and compares births, deaths
  and population with SCB's outcome up to 2025 (`data/demography-hindcast.json`). Fertility 1.41
  gave the smallest birth errors (mean absolute error 11–34 births a year); deaths were within
  12–40 a year. Population errors, 96–302 persons, are mostly migration.
- From base year 2024, 2025 came out at 327 births, 455 deaths and 43 395 inhabitants. SCB's regional
  projection said 356, 466 and 43 575; the outcome was 337, 459 and 43 113. One year is not evidence
  of a better projection.

## Care demand by age (Kolada)

Care demand weights 65–79, 80–89 and 90+ by elderly-care cost per inhabitant: home-care and
residential-care users per inhabitant in each group, times the cost per user. Kolada data for Motala
(`data/downloads/20261108T131731Z/`, `scripts/fetch_care_data.py`, `scripts/prepare_care.py` →
`data/care-weights.json`), three-year mean per base year. For 2023–2025 a person 80+ costs 7.1 times
as much as a person 65–79 (166 483 against 23 331 kr a year); the ratio was about 10 in 2018–2020.
Kolada has no split of 80+, so 90+ gets the 80–89 weight unless `oldestRelativeCare` is set.

With single-year ages (`Examples.AnnualCohort`), care demand grows 22 % by 2033 instead of the 10 %
that counting everyone 65+ gives, which lowers the 2033 result by about 80 mnkr with the model's default assumptions. The five-cohort model
splits 65+ in fixed shares, so its care index and the site's results are unchanged.

## Revenue relative to Sweden

Reference growth for tax and grants (`taxGrowth`, `grantGrowth`, SKR's national tax-base growth) is national.
Motala's share therefore follows its population relative to Sweden's, comparing the end of the previous year with
the end of the year before the base year (the 1 November population behind the base year's tax). Sweden's
population, outcome to 2025 and SCB's projection after, is archived by `scripts/fetch_national_population.py`
in `data/national-population.json` and `Motala.Data.SCB.nationalPopulation`. An imported SKR path for Motala is
already Motala's own and is scaled only by the model's population against SKR's.

## Inspect the models in OMEdit

| Model | Open | Inspect or simulate |
| --- | --- | --- |
| Annual dashboard model (the site) | `modelica/Kommunekonomi.mo`, `modelica/Motala.mo` | Load both, then open `Motala.Annual` in Diagram view, or simulate it. Time is the calendar year: start 2025 (the 2025 accounts), stop 2033; with another base year, start in that year. Its defaults are illustrative; download `Scenario.mo` from the site to reproduce a scenario with the planning inputs. Descriptions and documentation are in Swedish. |
| Stock-flow model, continuous within the year | `modelica/Kommunekonomi.mo`, `modelica/Motala.mo` | Open `Motala.Continuous` and simulate it from 2025 to 2033; the experiment saves twelve points a year. Same assumptions and annual outputs as `Motala.Annual`. Open `Kommunekonomi.Continuous.Capital`, `Payments` or `Finance` in Diagram view to see the stocks and flows. `Motala.Examples.ContinuousCohort` uses single years of age. Every generated municipality package has a `Continuous` model too. |
| Continuous scenarios (M2, research) | `research/MotalaDynamics/package.mo` | Open `Continuous` in Diagram view to see the five components. Simulate `Examples.Base` or another example. In an example, double-click `plant` to inspect the model. |
| Annual statistical candidate (M1, research) | `research/MotalaResearch/package.mo` | Open `Annual` in Diagram view. Simulation requires a fitted `Scenario.mo`, generated by the M1 runner documented in `research/README.txt`. |

The models have component icons, placements and labelled schematic arrows.
Arrows describe the existing equation bindings; they are graphical annotations,
not connector ports. Edit input bindings in the Modelica text and parameters in
the parameter dialog. Double-click a component for its detail diagram or equations.
M2 uses seconds internally: its eight-year experiment stops at 252460800 seconds;
`plant.modelYear` gives elapsed years in the examples. The annual models use years.
Annotations do not change the model equations. The browser compiles and runs the
annual model `Motala.Annual` (through `MotalaBrowser`); M2 produces separate reports.

## Stocks and flows in continuous time

`Kommunekonomi.Continuous` runs the same municipality with time continuous within
the year. Money moves as flows between stocks through connectors: a `Stock` is an
account, a `Transfer` moves money between two accounts, and `Inflow`/`Outflow`
cross the boundary as income or expense. Cash, debt, fixed assets, work in
progress, receivables, payables, the change in pension provisions and grant
advances are stocks. Liabilities have negative levels, so the sum of all stocks
changes only by the year's result, and the model checks that every year
(`equityBalance`). Each flow sums its own annual amount at 31 December.

Rules that are annual in reality are evaluated when the year starts: tax and
grants (based on the population on 1 November of the previous year), wage and
price levels, and the demography's year-end. The calendar therefore fires at the
start of each year, and a separate clock closes the accounts at the end. During
the year the population moves linearly, capacity follows demand continuously,
interest accrues on the current debt, deficits are borrowed when they arise, and
a project can be taken into use in a given month (`projectOpeningTime`).

With the default assumptions the continuous model gives the same population,
tax, grants and depreciation as `Annual`. Interest is about 2 mnkr higher in 2026
and 5 mnkr higher in 2033, because it accrues on the debt during the year. Net cost
is 5 to 25 mnkr higher, because the annual model charges the whole year at the
lower year-end population. Against Motala's annual reports from the five December
circulars 2020–2024, mean result errors are within about 2 mnkr of the annual
model's at one to three years (`HINDCAST_MODEL=Continuous python3 scripts/hindcast_vintages.py`
writes `data/vintage-hindcast-continuous.json`; `python3 scripts/compare_hindcasts.py [code]`
prints both models per account line). The continuous model is no more
accurate; it shows what happens within the year. `tests/test_continuous.py` checks
the identities and balances. The site still runs `Annual`.

## Local MCP server: let an AI run the budget

`scripts/mcp_server.py` lets an AI assistant run the model year by year over the
Model Context Protocol, much like OMEdit's MCP server, but with the project's own
tools instead of generic editing. It uses only the Python standard library and
native OpenModelica (set `OMC` if `omc` is not on PATH). Nothing leaves the
machine.

```sh
python3 scripts/mcp_server.py               # stdio
python3 scripts/mcp_server.py --http 3001   # http://127.0.0.1:3001/mcp
```

Claude Code picks up `.mcp.json` in the project root and offers to start the server.
Other local clients (LM Studio, Claude Desktop, Open WebUI or an Ollama MCP client)
can start the stdio command or connect to the HTTP address. The HTTP transport binds
to 127.0.0.1 and refuses requests from other browser origins.

| Tool | What it does |
| --- | --- |
| `list_municipalities`, `list_parameters` | The 13 municipalities, their base years 2020–2025, and the decisions that can be set, with descriptions |
| `start_session` | Start from a base year's closing accounts, with `Annual` or `Continuous` |
| `set_decisions` | Set this year's decisions (tax rate, investments, interest, wages, migration ...) with a reason |
| `advance` | Simulate the next year and return the accounts, balance checks and SKR's tax and grants for that year |
| `get_results`, `run_scenario` | Any output variable; a whole scenario at once |
| `reference` | SKR 26:28 (cited) and SCB's accounts 2020–2025 |
| `save_session` | Decisions, reasons and results as JSON, plus a Modelica model that reproduces the run in OMEdit |

The prompt `budget_round` asks the assistant to act as the finance committee.
Decisions for a year that has been simulated are fixed. Only parameters of
`Kommunekonomi.Assumptions` can be set, with numbers or booleans of the declared
size; no client text reaches the compiler. Sessions are saved under
`build/mcp/sessions/`. Each run takes about 2–3 seconds and is cached.
`tests/test_mcp_server.py` covers both transports.

## Repository contents and generated files

Keep the Modelica/Python/JavaScript sources, tests, documentation, reviewed JSON
inputs, research catalogues and `research/reference/` under version control.
The reference directories are frozen, hash-checked inputs used by the comparison
tests, rather than disposable copies of the active models.

Git ignores the generated `site/dist/` and `build/` directories, Python caches,
local environments, `research/runs/`, raw downloads, downloaded research PDFs and
local tool/hosting metadata. Existing simulation runs stay available locally.
Research originals belong in `research/papers/`, with the filenames listed in
`sources.json`; `python3 scripts/download_research.py` retrieves them separately.
The build only writes static assets and does not modify hosting metadata.

The dated report links below refer to local generated runs and will be absent
from a fresh clone. The accompanying source inputs, protocols and review notes
are versioned; run the documented commands to create new reports. Later replay
and audit stages require their earlier run archives, supplied with `--parent-run`
or `--run` where supported. These archives can be distributed separately from
the source repository. Do not edit the frozen reference files to update diagrams.

Run the dashboard and data-import checks with `npm test`. Run the model research
checks from the project root with:

```sh
PYTHONPATH=research python3 -m unittest discover -s research/tests -p 'test_*.py'
python3 -m unittest discover -s research/benchmark -p 'test_*.py'
```

The model research suite needs NumPy and OpenModelica. Basic dashboard checks
and the build have no third-party package dependencies.

## Continuous Modelica scenarios (M2)

`research/MotalaDynamics` implements the derived continuous equations for population,
staffing, service capacity, construction, costs, tax/grants, assets, debt and cash.
Staffing and facilities adjust separately; lower staffing can produce purchased
service costs or unmet demand. Debt affects interest expense. See the
[equations and research evidence](docs/dynamics-equations.md).

Run from the project root with Python 3.9+ and OpenModelica:

```sh
python3 research/run_dynamics.py --scenario base
python3 research/run_dynamics.py --scenario school-decline
python3 research/run_dynamics.py --scenario fast-adjustment
python3 research/run_dynamics.py --scenario base --parameters research/data/dynamics-example-parameters.json
python3 research/run_dynamics.py --scenario supply-constraint
python3 research/run_dynamics.py --parameters research/data/extra-cost-example.json
python3 research/run_experiments.py research/data/dynamics-sensitivity.json
```

Each command prints the path to a local HTML report, with annual CSV/JSON, native
results, frozen sources and balance checks. Fixed assumptions are ordinary Modelica
parameters in [Parameters.mo](research/MotalaDynamics/Parameters.mo). Override them
with a JSON object; time-dependent decisions are input bindings in
[Examples.mo](research/MotalaDynamics/Examples.mo). Open `MotalaDynamics/package.mo`
in OMEdit and simulate `Examples.Base` or another example.

Additional operating costs can be supplied as ordinary parameters. For example,
`{"extraCostPath": [0, 50, 0]}` adds 50 mnkr in 2027 when starting after the 2025
accounts. Each entry is the nominal amount for one simulation year; the cost is
zero after the array ends. Payments default to the same path. Set
`"extraCostPaymentPath": [0, 20, 30]` to pay 20 mnkr in 2027 and 30 in 2028.
The report shows expense, payments and the remaining accrual separately. These
are additions to the operating costs already modelled; investments use the
investment inputs. No automatic inflation is applied to these nominal amounts.

The experiment runner produces paired policy comparisons across chosen wage,
construction, facility-cost and transition-cost assumptions, plus a joint stress
scenario. Ranges are sensitivity scenarios, not confidence intervals. Failed cases
remain visible. V2 supports separate sector allocations, bounded staffing changes,
limited outside service and transition costs; opening work in progress now uses
the observed 99 mnkr. Compiler-resolved parameters and their evidence are exported.

This is a tested mechanism model with illustrative, unestimated service parameters.
It is not yet connected to the dashboard. The separate M1 statistical experiments
and SKR comparison workflow remain documented in [research/README.txt](research/README.txt).

V3 corrects the conversion from previous annual totals to continuous opening rates.
At constant quantities, 3% annual growth now produces exactly 3% growth in the next
integrated annual amount. Historical replay (also requires NumPy for M1) is available:

```sh
python3 research/run_historical.py --out research/runs/my-historical-check
PYTHONPATH=research python3 -m unittest discover -s research/tests -p 'test_*.py'
```

The output directory must be new. The report includes common-target comparisons,
component errors, uncertain construction-stock scenarios, frozen native sources,
resolved opening parameters and source/version conflicts. The first five-target
comparison gave result MAE **61.93 mnkr for M2 versus 58.92 for persistence**.
This is retrospective development evidence. See the
[original protocol](research/data/historical-protocol.json) and
[annual ledgers](research/data/annual-ledgers.json).

A subsequent fixed protocol uses dated December SKR cost forecasts for every origin:

```sh
python3 research/run_historical.py --protocol research/data/historical-protocol-pkv.json --out research/runs/my-pkv-check
```

The [PKV replay report](research/runs/historical-v3-20261015-pkv/report.html) gives:

| Result MAE, mnkr | One year (5 targets) | Two years (4 targets) | Three years (3 targets) |
| --- | ---: | ---: | ---: |
| M2, fixed price assumptions | 61.93 | 81.69 | 56.05 |
| M2 with dated SKR PKV costs | 25.21 | 49.20 | 83.02 |
| Simple accounting with the same PKV costs | 24.25 | 39.73 | 96.82 |
| Previous result unchanged | 58.92 | 76.28 | 40.87 |
| Expanding historical mean | 51.47 | 54.09 | 32.43 |

The short-horizon gain comes chiefly from external cost information; an incremental
forecasting gain from M2 dynamics is not established. Three-year accuracy deteriorates.
Motala's component errors also matter: M2-PKV underestimates tax and general grants
in all five one-year cases, while cost errors sometimes offset income errors.
The subsequent reconsideration prioritised a longer observed Motala series and
a small, theory-based test of lagged budget adjustment. That series is now
prepared and tested below. Historical local KPA/SKR forecast paths are
optional inputs to an independent model, not a prerequisite for modelling.
They are needed to compare against those forecasters' actual historical
predictions. The [independent reconsideration](research/reviews/full-goal-reconsideration-20261015.txt)
supersedes the earlier recommendation to wait for those forecast paths, while
retaining the finding that full forecast precision is unproven.
The [research and data catalogue](research/data/municipal-economics-research.json)
records Swedish municipal-economics research and SCB outcome tables covering
1998–2025 for results and 2011–2025 for cost/revenue components. The archived
2026-10-16 download contains Motala values for the result table and two component
tables. The result table has now been reviewed and used in the locked aggregate
experiment below. The proposed equation is documented in
[the modelling notes](docs/dynamics-equations.md). A lower total-result error
alone does not establish accurate components or policy effects.

Fetch the four SCB accounts tables for **Motala (0583)** with Python's standard library:

```sh
python3 research/fetch_scb_accounts.py
```

The script requests all published items for 1998–2025 in the result table and
2011–2025 in the three component tables. It saves raw JSON-stat responses,
metadata, exact queries, hashes and CSV files under `research/data/raw/scb-accounts/`.
It checks the returned municipality, years and dimensions, and preserves negative
values, zeroes, missing observations and unit metadata. It does not change model
inputs. Use `--table TAB6777` to fetch only the result table. Retrieval attempts
early on 2026-10-16 and again on 2026-10-23 failed at DNS resolution in this environment. The six
offline tests and an independent synthetic end-to-end check passed; see the
[independent review](research/reviews/scb-accounts-fetch-20261016.txt).
The [latest acquisition and evaluation status](research/data/history-extension-status.json)
preserves the failed requests and corrects the earlier conclusion that data were
absent: a later 2026-10-16 download had already succeeded for three tables.
The reviewed result-table source packet is preserved under
`research/reference/scb-accounts-20261016/`, with original responses, query and
receipts. Its file hashes have been verified. A fresh network transfer still
fails here; the aggregate experiment can now run entirely offline.

The reduced annual budget-response experiment is now implemented separately
from Modelica, with a [locked protocol](research/data/budget-response-protocol.json):

```sh
python3 research/run_budget_response.py --out research/runs/my-budget-response-check
```

It uses the existing annual ledgers by default. Those contain full accounts for
2020–2025 and do not satisfy the required older training sample: the original
[coverage report](research/runs/budget-response-20261016-final-coverage/report.json)
contains no fitted parameter or forecast score. Exit code 2 means no evaluable
cases. The minimum is eight earlier transitions, each with five consecutive
years for its base forecast; it is not relaxed to accommodate short data.
The parameter is frozen before 2020 for the existing 2020–2024 forecast origins.
The 2026-10-23 short-series coverage rerun confirmed the same status, with zero fitted origins
and zero scored predictions. For those later origins, the required eight training
transitions need at least a consecutive 2007–2019 accounts series; the declared
earlier origins require earlier data. The locked protocol has not changed.

A reconciled longer series can be supplied with `--format aggregate --accounts
PATH`. Its JSON declares `municipality: "0583"`, `scope: "kommunen"`,
`moneyUnit: "mnkr_current_prices"`, `seriesTreatment: "reported_unadjusted"`,
`sources` keyed by source ID (each with `url`), and chronological `rows` with
`year`, `taxAndGrants`, `netCost`, `financeNet`, `result`, `sourceId` and `locator`.
Net cost is positive and includes depreciation; original reported result is
retained even when rounded components do not sum exactly. SCB CSV files require
an explicit reviewed definition/unit mapping before this step. The experiment
compares one bounded coefficient with the identical zero-response base and two
simple result baselines. It reports component errors and retains missing cases.
Technical tests use synthetic accounts and establish no Motala accuracy gain.
The [independent technical review](research/reviews/budget-response-20261016.txt)
passed all 13 focused tests, checked the equations independently and reproduced
the frozen CLI outside the repository. That technical review did not score
long-series observed forecasts; the new SCB experiment below now does so.

The separate [reviewed SCB input](research/data/scb-budget-response-accounts.json)
now supplies all 28 observed years, 1998–2025. Rebuild and evaluate it offline:

```sh
python3 research/prepare_scb_accounts.py --out /tmp/motala-scb-accounts.json
python3 research/run_budget_response.py --format aggregate --accounts /tmp/motala-scb-accounts.json --out /tmp/motala-budget-response-scb
```

Both output paths must be new. The [explicit mapping](research/data/scb-budget-response-mapping.json)
converts signed tkr to mnkr, includes the separately reported pension interest
through 2010, and preserves extraordinary items in reported result. Every year's
result after finance and reported-result bridge reconcile exactly at source
precision. Missing cells in superseded column layouts remain missing. The input
also records differences from all six overlapping annual-report ledgers, including
about 19.5 mnkr in 2021 grants and net cost. No source series is spliced or replaced.

The [new report](research/runs/budget-response-20261023-scb/report.json) evaluates
42 origin/horizon cases from 15 origins, with four models per case and no skips.
The coefficient for origins 2020–2024 is 0.8813, estimated using 17 transitions
ending by 2019. The locked protocol and forecast rules are unchanged.

| Result MAE, mnkr, all origins | One year (15 cases) | Two years (14 cases) | Three years (13 cases) |
| --- | ---: | ---: | ---: |
| Budget response | 47.82 | 51.77 | 46.71 |
| Identical base, zero response | 44.64 | 64.71 | 55.32 |
| Previous reported result | 43.71 | 62.72 | 47.35 |
| Expanding historical mean | 39.47 | 40.39 | 38.05 |

Response improves on its identical base at two and three years, but worsens
one-year MAE and does not beat the historical mean at any horizon. Source revisions,
reporting changes and offsetting component errors remain material. This is
retrospective development evidence; no candidate is promoted. Matched comparisons
with frozen M2 remain necessary before promotion. The versioned status file
retains component scores, period summaries and the full source/evaluation hashes.

All targets were already examined during development; original publication dates of
the municipal accounts remain unverified. These are not blind tests or a comparison
against SKR's municipal tax-and-grant model. National PKV is an approximation for
local personnel costs, and only the combined payroll/pension forecast is evaluated.
The [source file](research/data/skr-pkv-vintages.json) retains every vintage and definition.

A further fixed Motala experiment separates charges explicitly listed in note 10
from the recurring cost base, retaining every observed result and closing stock:

```sh
python3 research/run_historical.py --protocol research/data/historical-protocol-events.json --out research/runs/my-notes-check
```

The [note-separation report](research/runs/historical-v4-20261015-notes/report.html)
shows result MAE of **16.03 / 57.61 / 104.24 mnkr** at one/two/three years for M2
with the note 10 cost base. The corresponding simple accounting comparison gives
21.80 / 48.13 / 117.63. One-year error improves, but longer horizons deteriorate;
income and cost errors still partly cancel. These are development results, not
independent validation. A mandatory separate sensitivity also removes temporary
note 10 receipts without replacement financing: its M2 MAE is 35.01 / 90.87 / 86.52.
Both scenarios and the original PKV results remain in the report. The
[itemised source ledger](research/data/motala-noted-events.json) identifies scope,
signs and ambiguities. This is not a full adjustment of all exceptional items or
a forecast of future provision payments. Extra cost paths remain zero in this
experiment; their scenario support is tested separately.

A subsequent locked **tax-only diagnostic** uses the same five December SKR
circulars for national nominal tax-base growth:

```sh
python3 research/run_historical.py --protocol research/data/historical-protocol-tax.json --out research/runs/my-tax-check
```

The [tax diagnostic report](research/runs/historical-v5-20261015-tax/report.html)
retains all 12 targets, both note scenarios, WIP sensitivities and prior comparisons.
All previous predictions are unchanged. The new variants assume a constant local
share of the national tax base and keep each parent's grant path unchanged.
Thus the experiment changes both the growth information and the demographic tax
mapping; it does not isolate the value of the growth forecast alone.

| Result MAE, mnkr | One year (5 targets) | Two years (4 targets) | Three years (3 targets) |
| --- | ---: | ---: | ---: |
| M2, note 10 cost base | 16.03 | 57.61 | 104.24 |
| Same cost base, tax-only sensitivity | 20.94 | 55.63 | 93.47 |
| M2, no-repeat receipts sensitivity | 35.01 | 90.87 | 86.52 |
| Same no-repeat scenario, tax-only sensitivity | 47.01 | 88.90 | 74.70 |

Tax MAE worsens at every horizon: 27.48/55.19/49.19 becomes
30.94/62.37/57.03 mnkr. The main systematic income shortfall is in grants and
equalisation, whose unchanged biases are −29.51/−74.76/−120.44 mnkr.
Net-cost biases remain −35.89/−78.35/−199.19; lower result error at some horizons
still depends on offsetting component errors. The diagnostic is not promoted to
a validated forecast. National tax growth applied to reported opening tax also
retains tax settlements and omits compensating grant changes. The
[dated inputs](research/data/skr-tax-vintages.json) and
[local-source catalog](research/data/local-forecast-catalog.json) preserve these
limits and the missing original local finance plans. A grant-component and tax-settlement
reconciliation is the next source-based revenue task. Later outcomes must not be
used to choose its parameters.

As a supplementary test, the simple PKV accounting rule was frozen and tested on a predeclared external
panel of Vadstena, Mjölby and Norrköping, origins 2022–2024 and targets through 2025:

```sh
python3 research/run_external_pkv.py --out research/runs/my-external-pkv-check
```

This uses only Python's standard library. The
[external report](research/runs/external-pkv-v1-20261015-audited/report.html)
retains all 18 cases; 15 can currently be scored. The exact Norrköping 2025 annual
result is unavailable in accessible primary tables, and the superseded preliminary
result is deliberately not used. Data gaps are visible, including all three affected
horizons. Later comparative columns are identified in the
[source ledger](research/data/external-pkv-ledgers.json).

One-year result MAE in mnkr is 4.26 / 13.77 / 12.34 in Vadstena, 46.01 / 54.17 /
68.46 in Mjölby, and 1942.71 / 1680.50 / 727.62 in Norrköping, in the order
PKV / persistence / historical mean. Norrköping has only two scored one-year targets.
The frozen rule carries the 2022 Ostlänken exceptional expense forward as recurring
cost; this is a structural forecasting failure, retained without adjustment. These
results do not justify general use of the rule as an automatic municipal forecast.
The successful municipalities must not be selected after the fact as a new test set.

The run saves the candidate, protocol, data, evaluator and tests. To reproduce an
archive independently, run `python3 <archive>/sources/run_external_pkv.py --out <new-directory>`.
Ledger identities are checked against explicit source rounding precision before
forecasting. The Modelica mechanism model remains useful for conditional scenarios;
its incremental predictive accuracy is still unestablished.

## Pension scenarios

Modelica accepts independent annual `pensionExpensePath` and `pensionCashPaymentsPath` arrays in mnkr. In the JavaScript interface these are assumption overrides of the same names. Supply one value per forecast year. The growth-rate fallback is illustrative, and the fallback cash-payment path equals expense; no future KPA values are implied. A noncash pension expense reduces result while leaving operating cash unchanged when payments are held fixed. Productivity affects payroll only.

The dashboard exposes pension growth, operating-revenue growth, component ledgers and the municipality's recorded 2025 forecast benchmarks. Original forecast cutoffs still need to be collected before comparing predictive accuracy.

## SKR data

The latest identified workbook is linked in `data/baseline.json` and `data/sources.json`. Download it on a network-enabled machine and inspect the worksheets:

```sh
python3 scripts/import_skr.py workbook.xlsm --inspect
python3 scripts/import_skr.py workbook.xlsm --map data/my-skr-map.json --output data/skr-motala.json
```

Use `data/skr-map.example.json` as the mapping schema, selecting the cells explicitly after inspection. Formula caches can be absent or stale, so check the extraction against Excel's Motala output. Load the resulting JSON in the dashboard. The reference population must match SKR's timing for each income year. Extraction includes workbook SHA256 and cell provenance. A macro-driven selection must be calculated and saved by an authorised workbook user before importing; this script does not select Motala by running VBA.

Both the mapping's expected municipality and the workbook cell must identify Motala.
The importer accepts the name (ignoring case and surrounding whitespace), text
codes `0583`, `583`, `583.0`, and Excel numeric code 583. A matching name for another
municipality is rejected rather than labelled as Motala.

## Browser engine: OpenModelica wasm-jit

The dashboard has one forecast engine: OpenModelica's compiler built for the web.
On page load a worker (`site/src/omc-worker.js`) fetches the compiler (about 100 MB,
cached by the browser afterwards), loads `Kommunekonomi.mo`, `Motala.mo` and `MotalaBrowser.mo`, and runs
`buildModel(MotalaBrowser)` with the `wasm-jit` target (about one second). Each scenario
then re-runs the compiled model with `-override` for every annual input, in 20–90 ms.
A view needs up to eight scenarios (yours, the baseline, two stress paths, four
sensitivities); they go to the worker as one batch. `MotalaBrowser` adds no equations:
it fixes the array capacity at 30 years and makes every input a free parameter.

No cross-origin isolation is needed for compiling and simulating, so GitHub Pages and
`npm start` serve the site without special headers.

Build the compiler once (Ubuntu 24.04 shown):

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

`wasm-opt` must be binaryen 120 or newer; Ubuntu 24.04's package (108) fails at the
last build step. Any recent emsdk ships a new enough one. `stage:omc` copies the
compiler, its wasm side modules and OpenModelica's licence into `site/omc-web/`
(not versioned) and records the compiler revision and SHA-256 of every file in
`site/omc-web/manifest.json`. `npm run build` refuses a staged compiler that does not
match its manifest.

`tests/jit-parity.test.mjs` runs the staged compiler in Node and checks every annual
output for 14 scenarios against `engine.js`, plus the model's own input assertions.
It is skipped when no compiler is staged.

OpenModelica is distributed under OSMC-PL 1.8 or GNU AGPL 3. The site ships the licence
and names the exact compiler revision. Publish only a compiler built from a commit
that is available in a public OpenModelica repository.

## Source documents and SKR workbooks

`scripts/fetch_planning_data.py` archives municipal PDFs, SCB and Kolada data. Run
`python3 scripts/strip_pdf_images.py <archive>` afterwards: it replaces every picture in
the PDFs with a blank image labelled "Bild borttagen" (photos can carry third-party
rights), keeps text and vector graphics, and records the original SHA-256 in the
manifest. SKR's workbooks are not in the repository or on the site; see
`data/skr-motala/README.md` for the link to SKR's original and the expected hash.

## Publish on GitHub Pages

`.github/workflows/site.yml` does it all in CI: it builds the web compiler from
OpenModelica's public repository (`master`, or the ref given when run by hand),
runs the tests against it, builds `site/dist` and deploys it with GitHub Pages'
Actions source. The staged compiler is cached per OpenModelica commit. A push to
`main` only builds and tests. Publishing is manual: run the workflow by hand on
`main` (Actions → Site → Run workflow, or `gh workflow run site.yml --ref main`).
The deploy job runs only in a public repository.

By hand: `site/dist` is the complete site. `scripts/deploy_pages.py <remote>` builds it and
pushes it as a single commit to the `gh-pages` branch of that remote; set the
repository's Pages source to that branch. The compiler stays out of the main
branch's history, and each deployment replaces the previous one.

## Download research papers

```sh
python3 scripts/download_research.py
```

Uses Python 3's standard library and the catalogue in `research/papers/sources.json`.
PDFs and dated download receipts go into `research/papers/`. Existing files are
preserved; transient network failures are retried and HTML error pages are rejected.
Use `--list` to inspect the sources, `--only cellier-2008` to select a paper, or
`--output /path/to/papers` to change the destination. `--timeout 30 --retries 2`
are the defaults. Run from a machine with internet access.

Four papers have direct PDF links. The optional Lund thesis requires a manual
download; the script prints its repository link and expected filename. Exit code
1 means at least one paper remains unavailable, including manual downloads.
See `research/papers/README.txt` for the reading order and research context.

## Research findings

SKR offers both a tax/grant model and a broader demographic service-price budget model. Motala publishes plans and periodic forecasts, but the available material does not establish the exact internal forecasting software or algorithms. Useful improvements to test are age-specific care intensity, cost adjustment lags, pension forecasts, correlated macro scenarios and explicit investment financing. More Modelica equations do not guarantee more accurate predictions.

There is no GitHub contribution or commit in this workspace. A private Site was registered as `appgprj_6ace353435b08191b78da94df7920761`, but remains unpublished: source synchronization failed because the environment cannot resolve `git.chatgpt-team.site`. No live website URL is claimed. The local preview server is also blocked by the environment's socket restrictions. Static application assets and a source archive are available locally.

## Licence

The project's own work, including the Modelica models, is MIT-licensed; see
`LICENSE`. The published site also bundles OpenModelica's web compiler under its own
licence (OSMC-PL 1.8 or GNU AGPL 3), with the licence text and the exact source
revision in `omc-web/`. Source documents and data in `data/` keep their publishers'
terms.
