"""Compare independently supplied forecasts; never feeds SKR values to Motala.

Usage: python3 modelica/benchmark/compare.py observations.json --output report.json

JSON has forecasts and outcomes arrays. All rows require municipality, scope,
metric, unit, definition, targetYear, value and source. Forecasts additionally
require model (candidate/skr/persistence/trend), forecastDate, informationCutoff,
inputsLatestRelease, modelVersion and usesBenchmarkOutputs (boolean). Outcomes
require publishedAt. Dates are ISO YYYY-MM-DD. Definition is a shared, reviewed
accounting definition identifier, not merely a matching column name.

Missing matches are reported, never scored as zero. Pairwise scores use every matched candidate/comparator case. The common
score uses cases with all four original forecasts and an outcome. This checks declared metadata; provenance
and genuine out-of-sample model selection still require an external audit.
"""

import argparse
from collections import defaultdict
from datetime import date
import json
import math
from pathlib import Path
from statistics import mean


IDENTITY = ("municipality", "scope", "metric", "unit", "definition", "targetYear")
MODELS = ("candidate", "skr", "persistence", "trend")
OPTIONAL_MODELS = ("reference", "municipal")


def identity(row):
    for field in (*IDENTITY[:-1], "source"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"Missing/non-text {field}")
    if type(row.get("targetYear")) is not int:
        raise ValueError("targetYear must be an integer")
    if type(row.get("value")) not in (int, float) or not math.isfinite(row["value"]):
        raise ValueError("value must be finite and numeric")
    return tuple(row[field] for field in IDENTITY)


def day(row, field):
    value = row[field]
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must use YYYY-MM-DD")
    return parsed


def compare(data):
    outcomes, forecasts = {}, defaultdict(dict)
    for row in data["outcomes"]:
        key = identity(row)
        day(row, "publishedAt")
        if key in outcomes:
            raise ValueError("Duplicate outcome; select one explicit outcome vintage")
        outcomes[key] = row
    for row in data["forecasts"]:
        key = identity(row)
        model = row["model"]
        if model not in MODELS + OPTIONAL_MODELS:
            raise ValueError(f"Unknown model {model}")
        origin, cutoff = day(row, "forecastDate"), day(row, "informationCutoff")
        if day(row, "inputsLatestRelease") > cutoff or cutoff > origin:
            raise ValueError("Input release or information cutoff is later than allowed")
        if row["targetYear"] < origin.year:
            raise ValueError("Historical target: this scorer covers current/future-year forecasts")
        if not isinstance(row.get("modelVersion"), str) or not row["modelVersion"].strip():
            raise ValueError("modelVersion is required")
        if type(row.get("usesBenchmarkOutputs")) is not bool:
            raise ValueError("Explicit usesBenchmarkOutputs declaration is required")
        if model != "skr" and row["usesBenchmarkOutputs"]:
            raise ValueError("Candidate and simple baselines must not use benchmark outputs")
        matched_key = (*key, row["forecastDate"], row["informationCutoff"])
        if model in forecasts[matched_key]:
            raise ValueError("Duplicate forecast; select one version before evaluation")
        forecasts[matched_key][model] = row

    cases, skipped, grouped = [], [], defaultdict(list)
    pair_cases = defaultdict(list)
    for key, models in sorted(forecasts.items()):
        descriptor = dict(zip((*IDENTITY, "forecastDate", "informationCutoff"), key))
        actual = outcomes.get(key[:len(IDENTITY)])
        missing = [model for model in MODELS if model not in models]
        if actual is not None and "candidate" in models:
            if day(actual, "publishedAt") <= date.fromisoformat(descriptor["forecastDate"]):
                raise ValueError("Outcome was already published at the forecast origin")
            for comparator in (*MODELS[1:], *OPTIONAL_MODELS):
                if comparator not in models:
                    continue
                origin_date = date.fromisoformat(descriptor["forecastDate"])
                pair_cases[comparator].append({**descriptor,
                    "horizonYears": descriptor["targetYear"] - origin_date.year,
                    "forecastMonth": origin_date.month, "actual": actual["value"],
                    "candidateError": models["candidate"]["value"] - actual["value"],
                    "comparatorError": models[comparator]["value"] - actual["value"]})
        if actual is None or missing:
            skipped.append({**descriptor, "missingModels": missing, "missingOutcome": actual is None})
            continue
        if day(actual, "publishedAt") <= date.fromisoformat(descriptor["forecastDate"]):
            raise ValueError("Outcome was already published at the forecast origin")
        errors = {model: models[model]["value"] - actual["value"] for model in MODELS}
        horizon = descriptor["targetYear"] - date.fromisoformat(descriptor["forecastDate"]).year
        month = date.fromisoformat(descriptor["forecastDate"]).month
        case = {**descriptor, "horizonYears": horizon, "forecastMonth": month,
                "actual": actual["value"], "errors": errors,
                "candidateMinusSkrAbsoluteError": abs(errors["candidate"]) - abs(errors["skr"])}
        cases.append(case)
        grouped[(*key[:5], horizon, month)].append(case)

    scores = []
    for key, rows in sorted(grouped.items()):
        metrics = {}
        for model in MODELS:
            errors = [r["errors"][model] for r in rows]
            metrics[model] = {"mae": mean(abs(e) for e in errors), "bias": mean(errors),
                              "rmse": math.sqrt(mean(e*e for e in errors))}
        scores.append({
            **dict(zip((*IDENTITY[:5], "horizonYears", "forecastMonth"), key)),
            "n": len(rows), "distinctTargetYears": len({r["targetYear"] for r in rows}),
            "models": metrics,
            "meanPairedAbsoluteErrorDifference": mean(r["candidateMinusSkrAbsoluteError"] for r in rows),
            "candidateLowerMAEInThisSample": all(metrics["candidate"]["mae"] < metrics[m]["mae"]
                                                   for m in MODELS[1:]),
        })
    used = {tuple(c[field] for field in IDENTITY) for c in cases}
    comparisons = {}
    for comparator in (*MODELS[1:], *OPTIONAL_MODELS):
        pairs = pair_cases[comparator]
        strata = defaultdict(list)
        for row in pairs:
            strata[tuple(row[k] for k in (*IDENTITY[:5], "horizonYears", "forecastMonth"))].append(row)
        pair_scores = []
        for key, rows in sorted(strata.items()):
            c = [r["candidateError"] for r in rows]
            b = [r["comparatorError"] for r in rows]
            stats = lambda es: {"mae": mean(abs(e) for e in es), "bias": mean(es),
                                "rmse": math.sqrt(mean(e*e for e in es))}
            pair_scores.append({**dict(zip((*IDENTITY[:5], "horizonYears", "forecastMonth"), key)),
                "n": len(rows), "distinctTargetYears": len({r["targetYear"] for r in rows}),
                "candidate": stats(c), "comparator": stats(b),
                "meanPairedAbsoluteErrorDifference": mean(abs(x)-abs(y) for x,y in zip(c,b))})
        comparisons[comparator] = {"status": "scored" if pairs else "insufficient_matched_data",
                                   "matchedCases": len(pairs), "scores": pair_scores, "cases": pairs}
    return {"status": "scored" if cases else ("partially_scored" if any(pair_cases.values()) else "insufficient_matched_data"),
            "comparisons": comparisons,
            "matchedCases": len(cases), "skippedCases": skipped,
            "unusedOutcomes": len(set(outcomes) - used), "scores": scores, "cases": cases,
            "forecastSuperiorityProven": False,
            "interpretation": "Descriptive paired errors only. Metadata checks do not establish genuine historical availability or independent held-out model selection."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = compare(json.loads(args.data.read_text()))
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"Invalid benchmark data: {exc}")
    text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
