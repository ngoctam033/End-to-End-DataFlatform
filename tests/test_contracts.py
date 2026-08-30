"""BL-020.5 end-to-end contract verification across source profiles."""

from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from contracts import DataContractValidator


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILE = ROOT / "tests" / "fixtures" / "contracts" / "multi_source_records.yaml"
MAPPING_FILE = ROOT / "contracts" / "mappings" / "source_mapping_matrix.yaml"
SCHEMA_DIR = ROOT / "contracts" / "schemas"
EXPECTED_ENTITIES = {"order", "order_line", "inventory", "shipment", "return", "payment"}
EXPECTED_PROFILES = {
    "mock_erp_pg",
    "odoo",
    "oms",
    "wms",
    "ops",
    "mongodb_catalog",
    "external_api",
}
FIXED_INGESTION_TIME = datetime(2026, 8, 28, 8, 0, tzinfo=timezone.utc)


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict):
        raise TypeError(f"Expected a YAML object in {path}")
    return document


class MultiSourceContractVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture_document = load_yaml(FIXTURE_FILE)
        cls.cases = fixture_document["cases"]
        cls.mapping = load_yaml(MAPPING_FILE)
        cls.validator = DataContractValidator(clock=lambda: FIXED_INGESTION_TIME)

    @staticmethod
    def validate_case(case: dict):
        return MultiSourceContractVerificationTests.validator.validate_payload(
            case["entity"],
            case["payload"],
            business_key=case["business_key"],
            source_key=case["source_key"],
            source_system=case["source_system"],
            event_time=case["event_time"],
        )

    def test_fixtures_cover_every_declared_source_and_canonical_entity(self) -> None:
        self.assertEqual(EXPECTED_PROFILES, {case["source_profile"] for case in self.cases})
        self.assertEqual(EXPECTED_ENTITIES, {case["entity"] for case in self.cases})
        self.assertEqual(len(self.cases), len({case["case_id"] for case in self.cases}))

    def test_fixture_sources_match_profiles_and_entity_routing(self) -> None:
        profiles = self.mapping["source_profiles"]
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                profile = case["source_profile"]
                self.assertEqual(profiles[profile]["source_system"], case["source_system"])
                entity_config = self.mapping["entities"][case["entity"]]
                routed = set(entity_config["owner_sources"]) | set(
                    entity_config["prospective_sources"]
                )
                self.assertIn(profile, routed)

    def test_all_multi_source_payloads_pass_and_receive_complete_envelopes(self) -> None:
        required_envelope = {
            "business_key",
            "source_key",
            "source_system",
            "event_time",
            "ingestion_time",
            "schema_version",
            "processing_status",
            "payload",
        }
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                result = self.validate_case(case)
                self.assertTrue(result.is_valid, result.errors)
                self.assertEqual("silver", result.destination)
                self.assertEqual(required_envelope, set(result.record))
                self.assertEqual("VALID", result.record["processing_status"])
                self.assertEqual("1.0.0", result.record["schema_version"])
                self.assertEqual("2026-08-28T08:00:00.000000Z", result.record["ingestion_time"])

    def test_missing_business_key_and_event_time_are_caught_exactly(self) -> None:
        valid_record = self.validate_case(self.cases[0]).record
        for field in ("business_key", "event_time"):
            with self.subTest(field=field):
                invalid_record = copy.deepcopy(valid_record)
                del invalid_record[field]
                result = self.validator.validate_record("order", invalid_record)
                self.assertFalse(result.is_valid)
                self.assertEqual("quarantine", result.destination)
                self.assertEqual("QUARANTINED", result.record["processing_status"])
                matching = [
                    error
                    for error in result.errors
                    if error.code == "SCHEMA_REQUIRED" and field in error.message
                ]
                self.assertEqual(1, len(matching), result.errors)

    def test_string_quantity_is_rejected_at_the_expected_path(self) -> None:
        case = next(case for case in self.cases if case["entity"] == "order_line")
        invalid_case = copy.deepcopy(case)
        invalid_case["payload"]["ordered_qty"] = "5"
        result = self.validate_case(invalid_case)
        self.assertFalse(result.is_valid)
        self.assertEqual("quarantine", result.destination)
        matching = [
            error
            for error in result.errors
            if error.code == "SCHEMA_TYPE" and error.path == "/payload/ordered_qty"
        ]
        self.assertEqual(1, len(matching), result.errors)

    def test_all_six_yaml_schemas_load_as_draft_2020_12(self) -> None:
        schema_paths = sorted(
            path for path in SCHEMA_DIR.glob("*.yaml") if path.stem != "common"
        )
        self.assertEqual(EXPECTED_ENTITIES, {path.stem for path in schema_paths})
        self.assertEqual(EXPECTED_ENTITIES, set(self.validator.supported_entities))
        for path in schema_paths:
            with self.subTest(schema=path.stem):
                schema = load_yaml(path)
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema", schema["$schema"]
                )
                self.assertEqual("1.0.0", schema["version"])
                Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
