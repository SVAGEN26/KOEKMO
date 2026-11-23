# Motala ekonomilabb

A scenario lab for a Swedish municipality's finances, for the people who make
the decisions. Pick a municipality and a start year, change tax rate,
investments, wages, migration, interest or inflation, and see the result, cash
and debt year by year. The model is written in Modelica and runs in the
visitor's browser. Motala (0583) is the main case; all 13 municipalities in
Östergötland run from their own accounts.

The model covers the municipality's own accounts (kommunen, not the group):
population by age, service demand and capacity, payroll, pensions and other
costs, tax and general grants (with income equalisation as the law computes it),
investment, depreciation, working capital, cash, debt and interest. All money is
nominal mnkr. The equations are in [docs/methodology.md](docs/methodology.md).

It is not a better forecast than SKR's. Run from SKR's December circulars
2020–2024, Motala's result one year ahead is off by 40 mnkr on average; the
municipality's own budget was off by 24. See [Accuracy](#accuracy).

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
  each control explains it and where the default comes from. Further options:
  a dated building project, working capital, a cash policy, SKR's revenue path
  as published, proportionally adjusted or adjusted per component, and five age
  groups (default) or single years of age.
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
- **Modellen.** A flow diagram of the six components with their equations and
  Modelica code.
- **Export.** Scenario as JSON or as `Scenario.mo` for OpenModelica, and a PDF
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
year. For Motala from the 2025 accounts the average rate goes from 2.2 % to
3.0 % in 2026 and 4.7 % in 2029; interest from 23 to 32 mnkr in 2026 and from 33
to 71 mnkr in 2029. The hindcast does not use actual rates as inputs.

### Higher inflation

Extra inflation above the price path (`inflationShock`, `inflationPersistence`,
or `inflationShockPath` year by year) reaches prices the same year, wages and the
tax base the year after, pension cost the same year, and the market rate by
`inflationRateResponse` points per point. General grants stay fixed in kronor
unless `inflationGrantCompensation` is set. The pass-through shares are
illustrative assumptions, not estimates.

**Högre inflation** (3 points the first year, half left each year after): for
Motala from the 2025 accounts the result is 49 mnkr below the base path in 2026
and 107 mnkr below in 2033.

The new rate and inflation controls are checked with native OpenModelica
(`-override` on `MotalaBrowser`); a run in the browser has not been checked yet.

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
seconds and is cached. The site is not connected to the server.

## The models

| Model | Where | Used by |
| --- | --- | --- |
| `Kommunekonomi.Annual` | `modelica/Kommunekonomi.mo` | The site, the MCP server, the hindcasts |
| `Kommunekonomi.Continuous.Economy` | same | The MCP server (optional), the hindcasts |
| `Motala.Annual`, `Motala.Continuous`, examples | `modelica/Motala.mo` | Motala's base years 2020–2025 |
| One package per municipality | `modelica/municipalities/*.mo` | Generated from SCB and Kolada |
| M1, M2 (research) | `research/` | Nothing on the site; see [research/M2.md](research/M2.md) |

`Continuous.Economy` has the same assumptions and outputs as `Annual`, with
money moving between stocks through connectors and time continuous within the
year. It gives the same population, tax and grants; interest is 2–5 mnkr and net
cost 5–25 mnkr a year higher, because interest accrues on the current debt and
costs follow the year's average population. It is no more accurate. The site
does not run it: the browser build takes one Euler step per year.

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
still checked against what happened, using only what was known at the start.

`scripts/hindcast_vintages.py` starts from each set of accounts 2020–2024 with
the assumptions in SKR's December circular of that year and runs up to three
years, not past 2025. Motala, mean error (model minus outcome) after 1/2/3 years,
mnkr, from `data/vintage-hindcast.json`:

| Line | 1 year | 2 years | 3 years |
| --- | --- | --- | --- |
| Result | −38 | −47 | +18 |
| Tax | −35 | −51 | −71 |
| General grants | −23 | −61 | −104 |
| Payroll | −10 | −24 | −103 |
| Debt | +57 | +94 | +22 |

Cases: 5, 4 and 3. One year ahead the mean absolute error of the result is
40 mnkr; the municipality's budget had 24 and last year's outcome 59. With hindsight
values for prices and the tax base the tax error drops to −10/−11/−14, so most
of the error comes from the forecasts the model is given, and for grants from
the state's decisions. SKR's own Motala forecasts from those dates are no longer
on SKR's site, so they cannot be compared. `scripts/compare_hindcasts.py CODE`
prints every line for `Annual` and `Continuous` side by side.

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
runs `buildModel` with the `wasm-jit` target (about a second). Each scenario
re-runs the compiled model with `-override`, in 20–90 ms. `MotalaBrowser` adds no
equations: it fixes the array capacity at 100 years and makes every input a free
parameter with a literal default (OpenModelica folds defaults that depend on the
base year at compile time, out of `-override`'s reach). No cross-origin isolation
is needed.

`site/src/engine.js` is an independent JavaScript reference used only by the
tests; the site does not ship it. `tests/jit-parity.test.mjs` runs the staged
compiler in Node against it (skipped when no compiler is staged).

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
- `scripts/`: data fetching and preparation, hindcasts, build, MCP server.
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
