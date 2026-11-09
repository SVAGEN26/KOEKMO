"""Native regression checks: python3 modelica/validate.py (requires omc and Node).

Builds in /tmp, leaving the application and its generated assets untouched.
Reference parity checks preserve the original scenarios; independent checks
exercise accounting identities, horizon handling and the new scenario inputs.
"""

import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OMC = os.environ.get("OMC") or shutil.which("omc")
if not OMC:
    candidate = Path("/home/johti17/OpenModelicaWork/om-install/bin/omc")
    if candidate.exists():
        OMC = str(candidate)
if not OMC:
    raise SystemExit("Set OMC to an OpenModelica compiler executable")

BUILD = Path(tempfile.mkdtemp(prefix="motala-validation-"))
START = 2025  # simulation time is the calendar year; Motala.Annual starts at the 2025 accounts
OUTPUTS = [
    "population", "tax", "grants", "cost", "depreciation", "interest",
    "result", "debt", "cash", "assets", "educationIndex", "careIndex",
    "payroll", "pensionExpense", "pensionCashPayments", "otherOperatingExpense",
    "operatingRevenue", "operatingCash",
]


def check(condition, message="Validation check failed"):
    # Not `assert`: python -O strips asserts and the script would print PASS unchecked.
    if not condition:
        raise AssertionError(message)


def close(actual, expected, label):
    check(math.isfinite(actual) and math.isclose(
        actual, expected, rel_tol=1e-10, abs_tol=1e-5
    ), f"{label}: {actual} != {expected}")


def simulate(name, source, stop=10, error=None):
    directory = BUILD / name
    directory.mkdir()
    (directory / "Scenario.mo").write_text(source)
    (directory / "run.mos").write_text(
        f"loadFile({json.dumps(str(HERE / 'Kommunekonomi.mo'))});\n"
        f"loadFile({json.dumps(str(HERE / 'Motala.mo'))});\n"
        'loadFile("Scenario.mo");\ncheckModel(Scenario);\ngetErrorString();\n'
        f'simulate(Scenario,startTime={START},stopTime={START + stop},numberOfIntervals={stop},outputFormat="csv");\n'
        "getErrorString();\n"
    )
    process = subprocess.run(
        [OMC, "run.mos"], cwd=directory, capture_output=True, text=True, timeout=120
    )
    log = process.stdout + process.stderr
    (directory / "omc.log").write_text(log)
    # This compiler can print LOG_SUCCESS after an assertion at the final event.
    # An error-level assertion always invalidates the simulation, even then.
    assertion_error = re.search(r"LOG_ASSERT\s*\|\s*error", log)
    if error:
        check(error in log and (assertion_error or "The simulation finished successfully" not in log), log)
        return
    check(process.returncode == 0 and not assertion_error and "The simulation finished successfully" in log, log)
    with (directory / "Scenario_res.csv").open() as file:
        raw = list(csv.DictReader(file))
    # Keep post-event values. Multiple rows at an annual boundary are expected.
    rows = []
    for year in range(stop + 1):
        matching = [r for r in raw if math.isclose(float(r["time"]), START + year, abs_tol=1e-8)]
        check(matching, f"Missing year {year} in {name}")
        rows.append({k: float(v) for k, v in matching[-1].items() if k})
    return rows


def scenario(modifiers):
    return f"within ; model Scenario extends Motala.Annual({modifiers}); end Scenario;"


def balances(rows, horizon):
    for year in range(1, horizon + 1):
        before, now = rows[year - 1], rows[year]
        close(now["yearIndex"], year, "yearIndex")
        close(now["population"] - before["population"],
              now["births"] - now["deaths"] + now["migration"], "population conservation")
        close(now["assets"] - before["assets"],
              now["annualInvestment"] - now["depreciation"], "asset roll-forward")
        close(now["debt"] - before["debt"], now["borrowing"] - now["repayment"], "debt roll-forward")
        close(now["cash"] - before["cash"], now["operatingCash"] - now["annualInvestment"]
              + now["borrowing"] - now["repayment"], "cash roll-forward")
        close(now["operatingCash"], now["result"] + now["depreciation"]
              + now["pensionExpense"] - now["pensionCashPayments"], "pension cash bridge")
        close(now["result"], now["tax"] + now["grants"] - now["cost"]
              - now["depreciation"] + 15 - now["interest"] - 4, "income statement")
        close(now["interest"], before["debt"] * now["annualInterestRate"], "opening-debt interest")
        check(now["debt"] >= 0 and now["repayment"] <= before["debt"], "Debt waterfall violated")
        check(now["borrowing"] * now["repayment"] == 0, "Borrowing and repayment in the same year")
        for residual in ("populationBalance", "assetBalance", "debtBalance", "cashBalance"):
            close(now[residual], 0, residual)
    for row in rows[horizon + 1:]:
        # Every exported variable, including internal state, must stay frozen.
        for key, value in rows[horizon].items():
            if key not in ("time", "calendar.tick"):
                close(row[key], value, f"frozen after horizon: {key}")


def main():
    cases = [
        {},
        {"taxGrowth": 2.5, "wageGrowth": 4, "interestRate": 4, "migrationDelta": -100},
        {"migrationDelta": 300, "investment": 250, "productivity": 0.5, "taxRate": 22.2},
        {"pensionExpensePath": [275, 250, 220, 190, 190, 190, 190, 190],
         "pensionCashPaymentsPath": [190, 195, 200, 200, 200, 200, 200, 200]},
    ]
    for index, overrides in enumerate(cases):
        reference = json.loads(subprocess.check_output(
            ["node", str(ROOT / "scripts/export_reference.mjs"), json.dumps(overrides)], text=True
        ))
        rows = simulate(f"parity-{index}", reference["source"])
        for year, expected in enumerate(reference["run"]["rows"][1:], 1):
            for key in OUTPUTS:
                close(rows[year][key], expected[key], f"scenario {index}, year {year}, {key}")
            for cohort, value in enumerate(expected["cohorts"], 1):
                close(rows[year][f"p[{cohort}]"], value, "cohort parity")
        balances(rows, 8)
    print("PASS: four reference scenarios, 23 outputs per year, balances and horizon freeze")

    rows = simulate("annual-paths", scenario(
        "horizon=3,investmentPath={0,900,50},interestRatePath={0.01,0.04,0.02},"
        "migrationDeltaPath={100,-200,300},birthChangePath={0,0.1,-0.1},"
        "serviceAdjustment={0,1,0.5},serviceFixedShare={0.25,0.1,0.4}"
    ), stop=5)
    balances(rows, 3)
    base_migration = sum((-44.63234187162425, 62.14678281833085,
                          11.894277120084553, -238.86311941128406, 37.964246056899356))
    for year, (investment, rate, migration, birth_change) in enumerate(zip(
        (0, 900, 50), (0.01, 0.04, 0.02), (100, -200, 300), (0, 0.1, -0.1)
    ), 1):
        now = rows[year]
        close(now["annualInvestment"], investment, "investment path timing")
        close(now["annualInterestRate"], rate, "rate path timing")
        close(now["migration"], base_migration + migration, "migration path timing")
        close(now["births"], 334 * rows[year - 1]["p[4]"] / rows[0]["p[4]"]
              * (1 + birth_change), "birth path timing")
        close(now["capacity[1]"], 1, "fixed education capacity")
        close(now["capacity[2]"], 0.1 + 0.9 * now["careIndex"], "immediate care adaptation")
        close(now["capacity[3]"], 0.5 * rows[year - 1]["capacity[3]"]
              + 0.5 * (0.4 + 0.6 * now["population"] / rows[0]["population"]), "other services adaptation")
    print("PASS: independently varying annual inputs and sector adaptation")

    rows = simulate("short-surplus", scenario("horizon=1,debt0=1,investment=0,sectorCosts={1,1,1}"), stop=3)
    balances(rows, 1)
    close(rows[0]["yearIndex"], 0, "no transition at initialization")
    close(rows[0]["cost"], 3023, "initial cost is independent of service weights")
    close(rows[0]["result"], 2330 + 987 - 3023 - 180 + 15 - 21 - 4, "initial result is the observed ledger")
    close(rows[1]["debt"], 0, "surplus clears debt")
    check(rows[1]["cash"] > rows[0]["cash"], "Surplus after repayment must accumulate as cash")
    print("PASS: one-year horizon, consistent initial ledger, debt payoff and excess cash")

    # With no population/composition change, imported paths must be reproduced.
    rows = simulate("imported-revenue", scenario(
        "horizon=1,p0={7,9,3,46,10},deathRates=zeros(5),births0=1,"
        "residualMigration={0,0,0,0,-1},importedRevenue=true,"
        "referenceTax={2500},referenceGrants={1100},referencePopulation={75}"
    ), stop=2)
    balances(rows, 1)
    close(rows[1]["tax"], 2500, "imported tax")
    close(rows[1]["grants"], 1100, "imported grants")
    close(rows[1]["population"], 75, "stationary population")
    print("PASS: imported revenue benchmark with stationary population")

    invalid = [
        ("migrationWeights={1,1,1,1,1}", "migrationWeights måste"),
        ("serviceAdjustment={0,1.1,0}", "serviceAdjustment måste"),
        ("productivityGrowth=-1", "Årliga tillväxttakter måste"),
        ("referencePopulation=fill(0,horizon)", "referencePopulation måste"),
        ("pensionCashPaymentsPath=fill(-1,horizon)", "pensionCashPaymentsPath får inte"),
        ("migrationDelta=-30000", "Scenariot tömmer en åldersgrupp"),
    ]
    for index, (modifiers, message) in enumerate(invalid):
        simulate(f"invalid-{index}", scenario(modifiers), stop=1, error=message)
    print("PASS: five invalid input configurations and one exhausted-cohort scenario rejected")
    print(f"Native validation passed; compiler logs and CSV files: {BUILD}")


if __name__ == "__main__":
    main()
