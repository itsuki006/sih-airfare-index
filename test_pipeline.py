"""
test_pipeline.py

Automated tests for the APIx prototype (explicitly required by the
problem statement: "The solution must include documentation, automated
testing...").

Uses only Python's built-in `unittest` -- no extra packages to install,
so this runs anywhere Python 3 does.

Run with: python3 test_pipeline.py -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import mock_data_generator
import data_cleaning
import index_calculator


class PipelineTestCase(unittest.TestCase):
    """Base class that builds one shared raw+clean dataset for all tests."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.raw_path = str(Path(cls.tmpdir) / "raw_test.csv")
        cls.clean_path = str(Path(cls.tmpdir) / "clean_test.csv")
        mock_data_generator.generate_dataset(num_days=10, out_path=cls.raw_path)
        data_cleaning.run(raw_path=cls.raw_path, out_path=cls.clean_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)


class TestMockDataGenerator(PipelineTestCase):

    def test_produces_expected_columns(self):
        df = pd.read_csv(self.raw_path)
        expected = {
            "scrape_date", "origin", "destination", "carrier",
            "advance_window_days", "base_fare", "taxes", "total_fare", "status",
        }
        self.assertTrue(expected.issubset(set(df.columns)))

    def test_produces_all_configured_routes(self):
        df = pd.read_csv(self.raw_path)
        route_pairs = set(zip(df["origin"], df["destination"]))
        expected_pairs = {(r["origin"], r["destination"]) for r in mock_data_generator.ROUTES}
        self.assertEqual(route_pairs, expected_pairs)

    def test_includes_sold_out_and_ok_statuses(self):
        df = pd.read_csv(self.raw_path)
        statuses = set(df["status"].unique())
        self.assertIn("OK", statuses)
        self.assertIn("SOLD_OUT", statuses)  # confirms messiness simulation works


class TestDataCleaning(PipelineTestCase):

    def test_removes_sold_out_rows(self):
        df = pd.read_csv(self.clean_path)
        self.assertTrue((df["status"] == "OK").all())

    def test_no_missing_fares_remain(self):
        df = pd.read_csv(self.clean_path)
        self.assertEqual(df["base_fare"].isna().sum(), 0)
        self.assertEqual(df["total_fare"].isna().sum(), 0)

    def test_total_equals_base_plus_taxes(self):
        df = pd.read_csv(self.clean_path)
        recomputed = (df["base_fare"] + df["taxes"]).round(2)
        self.assertTrue((recomputed == df["total_fare"].round(2)).all())

    def test_no_duplicates_remain(self):
        df = pd.read_csv(self.clean_path)
        self.assertEqual(df.duplicated().sum(), 0)

    def test_cleaning_reduces_row_count(self):
        raw_count = len(pd.read_csv(self.raw_path))
        clean_count = len(pd.read_csv(self.clean_path))
        self.assertLess(clean_count, raw_count)  # sold-outs alone guarantee this
        self.assertGreater(clean_count, 0)


class TestIndexCalculator(PipelineTestCase):

    def setUp(self):
        df = index_calculator.load_clean(self.clean_path)
        self.daily_index, self.route_daily = index_calculator.compute_index(df)

    def test_base_period_is_approximately_100(self):
        base_period_end = self.daily_index["scrape_date"].min() + pd.Timedelta(
            days=index_calculator.BASE_PERIOD_DAYS - 1
        )
        base_rows = self.daily_index[self.daily_index["scrape_date"] <= base_period_end]
        self.assertLess(abs(base_rows["APIx"].mean() - 100), 15)

    def test_one_row_per_day(self):
        df = index_calculator.load_clean(self.clean_path)
        n_days = df["scrape_date"].nunique()
        self.assertEqual(len(self.daily_index), n_days)

    def test_index_values_are_positive(self):
        self.assertTrue((self.daily_index["APIx"] > 0).all())

    def test_route_weights_sum_to_one(self):
        total_weight = sum(index_calculator.ROUTE_WEIGHTS.values())
        self.assertLess(abs(total_weight - 1.0), 0.001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
