"""Synthetic fixtures only; these tests provide no forecast accuracy evidence."""

import copy
import io
import unittest
import zipfile

from compare import compare
from fetch import validate_workbook


def fixture():
    common = {"municipality": "0583", "scope": "kommunen", "metric": "tax",
              "unit": "mnkr", "definition": "synthetic-tax-including-settlements-v1",
              "targetYear": 2024, "source": "synthetic test fixture"}
    forecasts = [{**common, "model": model, "value": value,
                  "forecastDate": "2023-10-01", "informationCutoff": "2023-09-30",
                  "inputsLatestRelease": "2023-09-01", "modelVersion": "test-v1",
                  "usesBenchmarkOutputs": False}
                 for model, value in (("candidate", 102), ("skr", 110),
                                      ("persistence", 90), ("trend", 104))]
    return {"forecasts": forecasts,
            "outcomes": [{**common, "value": 100, "publishedAt": "2025-04-01"}]}


class BenchmarkTests(unittest.TestCase):
    def test_paired_errors_and_no_superiority_claim(self):
        result = compare(fixture())
        self.assertEqual(result["matchedCases"], 1)
        score = result["scores"][0]
        self.assertEqual(score["models"]["candidate"], {"mae": 2, "bias": 2, "rmse": 2})
        self.assertEqual(score["models"]["persistence"]["bias"], -10)
        self.assertEqual(score["meanPairedAbsoluteErrorDifference"], -8)
        self.assertTrue(score["candidateLowerMAEInThisSample"])
        self.assertFalse(result["forecastSuperiorityProven"])

    def test_mismatched_dates_definitions_and_units_are_not_paired(self):
        for field, value in (("forecastDate", "2023-10-02"),
                             ("informationCutoff", "2023-09-29"),
                             ("definition", "different-accounting-basis"),
                             ("unit", "SEK"), ("municipality", "0180")):
            with self.subTest(field=field):
                data = fixture()
                data["forecasts"][1][field] = value
                result = compare(data)
                self.assertEqual(result["matchedCases"], 0)
                self.assertEqual(result["comparisons"]["skr"]["matchedCases"], 0)
                self.assertEqual(result["comparisons"]["trend"]["matchedCases"], 1)
                self.assertTrue(result["skippedCases"])

    def test_rejects_future_information_and_benchmark_feedthrough(self):
        for field, value in (("inputsLatestRelease", "2024-01-01"),
                             ("informationCutoff", "2023-10-02"),
                             ("usesBenchmarkOutputs", True), ("value", float("nan"))):
            with self.subTest(field=field):
                data = fixture()
                data["forecasts"][0][field] = value
                with self.assertRaises(ValueError):
                    compare(data)

    def test_known_outcomes_are_not_forecasts(self):
        data = fixture()
        data["outcomes"][0]["publishedAt"] = "2023-09-01"
        with self.assertRaises(ValueError):
            compare(data)

    def test_missing_outcome_or_baseline_does_not_get_zero_error(self):
        for array in ("outcomes", "forecasts"):
            data = fixture()
            data[array].pop()
            result = compare(data)
            self.assertEqual(result["scores"], [])
            self.assertEqual(result["matchedCases"], 0)

    def test_duplicate_versions_are_rejected(self):
        for array in ("outcomes", "forecasts"):
            data = fixture()
            data[array].append(copy.deepcopy(data[array][0]))
            with self.assertRaises(ValueError):
                compare(data)

    def test_empty_data_does_not_claim_success(self):
        result = compare({"forecasts": [], "outcomes": []})
        self.assertEqual(result["status"], "insufficient_matched_data")
        self.assertFalse(result["forecastSuperiorityProven"])

    def test_horizons_and_origin_seasons_stay_separate(self):
        data = fixture()
        extra = copy.deepcopy(data["forecasts"])
        for row in extra:
            row.update(forecastDate="2022-04-01", informationCutoff="2022-03-31",
                       inputsLatestRelease="2022-03-01")
        data["forecasts"].extend(extra)
        result = compare(data)
        self.assertEqual(result["matchedCases"], 2)
        self.assertEqual({(r["horizonYears"], r["forecastMonth"]) for r in result["scores"]},
                         {(1, 10), (2, 4)})

    def test_missing_skr_does_not_block_baselines(self):
        data = fixture()
        data["forecasts"] = [r for r in data["forecasts"] if r["model"] != "skr"]
        result = compare(data)
        self.assertEqual(result["status"], "partially_scored")
        self.assertEqual(result["matchedCases"], 0)
        self.assertEqual(result["comparisons"]["skr"]["matchedCases"], 0)
        self.assertEqual(result["comparisons"]["persistence"]["matchedCases"], 1)
        self.assertEqual(result["comparisons"]["trend"]["matchedCases"], 1)

    def test_download_rejects_html_and_non_excel_archives(self):
        with self.assertRaises(zipfile.BadZipFile):
            validate_workbook(b"<html>Download failed</html>")
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("unrelated.txt", "not a workbook")
        with self.assertRaises(ValueError):
            validate_workbook(stream.getvalue())


if __name__ == "__main__":
    unittest.main()
