from __future__ import annotations

import csv
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.collector import (
    SECClient,
    SECRequestError,
    collect_records,
    collect_to_csv,
    load_seed_ciks,
)
from backend.metrics import calculate_metrics
from backend.parser import parse_latest_13f
from backend.validator import ValidationError, normalize_cik, validate_investor


def submissions_payload(cik: str = "0001067983") -> dict:
    return {
        "cik": int(cik),
        "name": "Example Investment Adviser",
        "filings": {
            "recent": {
                "form": ["13F-HR/A", "10-K", "13F-HR"],
                "filingDate": ["2025-02-14", "2025-02-10", "2024-11-14"],
                "accessionNumber": [
                    "0001067983-25-000001",
                    "0001067983-25-000002",
                    "0001067983-24-000003",
                ],
                "primaryDocument": ["primary.htm", "annual.htm", "older.htm"],
            }
        },
    }


class BackendTests(unittest.TestCase):
    def test_cik_normalization_and_validation(self):
        self.assertEqual(normalize_cik("123"), "0000000123")
        with self.assertRaises(ValidationError):
            normalize_cik("12x")

    def test_parser_chooses_latest_13f_amendment_and_builds_source_urls(self):
        record = parse_latest_13f(submissions_payload(), "1067983")
        self.assertEqual(record["latest_filing_date"], "2025-02-14")
        self.assertEqual(record["latest_form"], "13F-HR/A")
        self.assertIn("/Archives/edgar/data/1067983/000106798325000001/primary.htm", record["filing_url"])
        self.assertEqual(
            record["source_url"],
            "https://data.sec.gov/submissions/CIK0001067983.json",
        )

    def test_parser_rejects_shape_or_cik_mismatch(self):
        with self.assertRaises(ValidationError):
            parse_latest_13f({"filings": {}}, "1067983")
        with self.assertRaises(ValidationError):
            parse_latest_13f(submissions_payload("0000320193"), "1067983")

    def test_parser_does_not_accept_malformed_filing_identifiers(self):
        payload = submissions_payload()
        payload["filings"]["recent"]["accessionNumber"][0] = "../invalid"
        record = parse_latest_13f(payload, "1067983")
        self.assertEqual(record["latest_filing_date"], "2024-11-14")
        self.assertFalse(record["_history_complete"])

    def test_investor_sources_must_be_canonical_sec_urls(self):
        with self.assertRaises(ValidationError):
            validate_investor({
                "cik": "0000000123",
                "name": "Example",
                "source_url": "https://example.com/submissions/CIK0000000123.json",
            })

    def test_collection_marks_activity_at_configured_threshold_and_nulls_unknown_profile(self):
        class Client:
            def get_json(self, _url):
                return submissions_payload()

        record = collect_records(
            ["1067983"], Client(), active_months=24, as_of=date(2025, 2, 14)
        )[0]
        self.assertTrue(record["is_active"])
        self.assertIsNone(record["aum_usd"])
        self.assertIsNone(record["check_size_min_usd"])
        self.assertIsNone(record["target_sectors"])
        inactive = collect_records(
            ["1067983"], Client(), active_months=12, as_of=date(2026, 2, 15)
        )
        self.assertEqual(inactive, [])

    def test_collection_searches_submission_history_when_recent_window_has_no_13f(self):
        current = submissions_payload()
        recent = current["filings"]["recent"]
        recent.update(
            {
                "form": ["10-K"],
                "filingDate": ["2025-02-10"],
                "accessionNumber": ["0001067983-25-000002"],
                "primaryDocument": ["annual.htm"],
            }
        )
        current["filings"]["files"] = [
            {"name": "CIK0001067983-submissions-001.json", "filingTo": "2024-12-31"}
        ]

        class Client:
            def get_json(self, url):
                if url.endswith("CIK0001067983.json"):
                    return current
                return {
                    "form": ["13F-HR"],
                    "filingDate": ["2024-11-14"],
                    "accessionNumber": ["0001067983-24-000003"],
                    "primaryDocument": ["older.htm"],
                }

        record = collect_records(["1067983"], Client(), as_of=date(2025, 1, 1))[0]
        self.assertEqual(record["latest_filing_date"], "2024-11-14")
        self.assertEqual(record["latest_filing_form"], "13F-HR")

    def test_failed_history_request_leaves_activity_unknown(self):
        current = submissions_payload()
        current["filings"]["recent"].update(
            {
                "form": [],
                "filingDate": [],
                "accessionNumber": [],
                "primaryDocument": [],
            }
        )
        current["filings"]["files"] = [
            {"name": "CIK0001067983-submissions-001.json", "filingTo": "2024-12-31"}
        ]

        class Client:
            def get_json(self, url):
                if url.endswith("CIK0001067983.json"):
                    return current
                raise SECRequestError("synthetic history outage")

        records = collect_records(["1067983"], Client())
        self.assertEqual(records, [])

    def test_invalid_active_window_rejected(self):
        with self.assertRaises(ValueError):
            collect_records([], object(), active_months=11)

    def test_metrics_are_null_without_a_verification_sample(self):
        metrics = calculate_metrics(
            [
                {
                    "cik": "0000000123",
                    "name": "Institution",
                    "latest_filing_date": "2025-01-01",
                    "latest_filing_form": "13F-HR",
                    "source_url": "https://data.sec.gov/example",
                    "is_active": True,
                }
            ],
            as_of=date(2025, 2, 1),
        )
        self.assertEqual(metrics["accuracy_sample_size"], 0)
        self.assertIsNone(metrics["accuracy_percent"])
        self.assertEqual(metrics["verified_records"], 0)
        self.assertEqual(metrics["completeness_percent"], 60)
        self.assertEqual(metrics["as_of"], "2025-02-01")

    def test_metrics_calculate_accuracy_from_independent_field_checks(self):
        records = [{
            "cik": "0000000123",
            "name": "Example Capital",
            "latest_filing_date": "2025-01-01",
            "latest_filing_form": "13F-HR",
            "is_active": True,
            "source_url": "https://data.sec.gov/submissions/CIK0000000123.json",
            "aum_usd": 1250000,
            "check_size_min_usd": None,
            "check_size_max_usd": None,
            "target_sectors": ["Software", "Energy"],
        }]
        checks = [
            {"cik": "0000000123", "field": "name", "verified_value": " example capital "},
            {"cik": "0000000123", "field": "aum_usd", "verified_value": "1250000.00"},
            {"cik": "0000000123", "field": "target_sectors", "verified_value": "Energy|Software"},
            {"cik": "0000000123", "field": "latest_filing_form", "verified_value": "10-K"},
        ]

        metrics = calculate_metrics(records, checks, as_of=date(2025, 2, 1))

        self.assertEqual(metrics["verified_records"], 1)
        self.assertEqual(metrics["accuracy_sample_size"], 1)
        self.assertEqual(metrics["accuracy_percent"], 75)

    def test_seed_csv_deduplicates_and_skips_invalid_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "seeds.csv"
            path.write_text("cik,name\n123,One\n123,Duplicate\nbad,Invalid\n", encoding="utf-8")
            self.assertEqual(load_seed_ciks(path), ["0000000123"])

    def test_no_seeds_exports_header_only_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            seed_path = Path(temp) / "missing.csv"
            output_path = Path(temp) / "out.csv"
            records = collect_to_csv(seed_path, output_path)
            self.assertEqual(records, [])
            with output_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 1)
            self.assertIn("cik", rows[0])
            self.assertIn("filing_url", rows[0])

    def test_sec_client_requires_real_user_agent_and_wraps_bad_json(self):
        with patch.dict(os.environ, {"SEC_USER_AGENT": ""}):
            with self.assertRaises(ValueError):
                SECClient()
        with self.assertRaisesRegex(ValueError, "application name and contact"):
            SECClient("Not a contact-only user agent")

        class BadResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"not json"

        received = {}

        def opener(request, **_kwargs):
            received.update(request.header_items())
            return BadResponse()

        client = SECClient(
            "Example Research App contact@example.org",
            retries=0,
            opener=opener,
        )
        with self.assertRaises(SECRequestError):
            client.get_json("https://data.sec.gov/example")
        self.assertEqual(
            received["User-agent"],
            "Example Research App contact@example.org",
        )

    def test_api_endpoint_contracts(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "investors.csv"
            verification_path = Path(temp) / "verification.csv"
            csv_path.write_text(
                "cik,name,latest_filing_date,latest_filing_form,is_active,source_url,"
                "aum_usd,check_size_min_usd,check_size_max_usd,target_sectors\n"
                "0001067983,Example,2025-02-14,13F-HR,true,"
                "https://data.sec.gov/submissions/CIK0001067983.json,,,,\n",
                encoding="utf-8",
            )
            verification_path.write_text(
                "cik,field,verified_value,source_url,verified_at\n"
                "0001067983,name,Example,https://research.example.org,2025-02-14\n"
                "0001067983,aum_usd,1000000,https://research.example.org,2025-02-14\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "INVESTORS_CSV": str(csv_path),
                    "SCALING_TARGET_RECORDS": "500",
                    "COST_PER_RECORD_USD": "1.25",
                    "VERIFICATION_SAMPLE_CSV": str(verification_path),
                },
            ):
                client = TestClient(app)
                investors_response = client.get("/api/investors")
                self.assertEqual(investors_response.status_code, 200)
                investors = investors_response.json()["investors"]
                self.assertEqual(len(investors), 1)
                self.assertEqual(
                    set(investors[0]),
                    {
                        "cik", "name", "latest_filing_date", "latest_filing_form",
                        "is_active", "source_url", "aum_usd",
                        "check_size_min_usd", "check_size_max_usd", "target_sectors",
                    },
                )
                self.assertEqual(investors[0]["target_sectors"], [])

                metrics_response = client.get("/api/metrics")
                metrics = metrics_response.json()
                self.assertEqual(metrics_response.status_code, 200)
                self.assertEqual(
                    set(metrics),
                    {
                        "total_records", "active_records", "verified_records",
                        "accuracy_percent", "accuracy_sample_size",
                        "completeness_percent", "as_of",
                    },
                )
                self.assertEqual(metrics["total_records"], 1)
                self.assertEqual(metrics["active_records"], 1)
                self.assertEqual(metrics["verified_records"], 1)
                self.assertEqual(metrics["accuracy_sample_size"], 1)
                self.assertEqual(metrics["accuracy_percent"], 50)
                self.assertEqual(metrics["completeness_percent"], 60)

                scaling_response = client.get("/api/scaling")
                scaling = scaling_response.json()
                self.assertEqual(scaling_response.status_code, 200)
                self.assertEqual(
                    set(scaling),
                    {
                        "current_records", "target_records", "cost_per_record_usd",
                        "estimated_total_cost_usd", "assumptions",
                    },
                )
                self.assertEqual(scaling["target_records"], 500)
                self.assertEqual(scaling["estimated_total_cost_usd"], 625)

    def test_scaling_cost_remains_unset_without_a_cost_assumption(self):
        with patch.dict(
            os.environ,
            {"INVESTORS_CSV": "/nonexistent/investors.csv"},
            clear=True,
        ):
            response = TestClient(app).get("/api/scaling")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["cost_per_record_usd"])
        self.assertIsNone(response.json()["estimated_total_cost_usd"])

    def test_missing_dataset_returns_empty_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"INVESTORS_CSV": str(Path(temp) / "absent.csv")}):
                response = TestClient(app).get("/api/investors")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"investors": []})


if __name__ == "__main__":
    unittest.main()
