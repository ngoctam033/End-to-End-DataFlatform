"""Unit tests for the BL-020.4 contract validation engine."""

from __future__ import annotations

import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from contracts import ContractConfigurationError, DataContractValidator
from contracts.validator import clear_schema_cache, schema_cache_info


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILE = ROOT / "tests" / "fixtures" / "contracts" / "valid_records.yaml"
FIXED_TIME = datetime(2026, 8, 28, 8, 15, 30, 123456, tzinfo=timezone.utc)


def load_fixtures() -> dict:
    with FIXTURE_FILE.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class DataContractValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_fixtures()

    def setUp(self) -> None:
        self.validator = DataContractValidator(clock=lambda: FIXED_TIME)

    def validate_fixture_payload(self, entity: str):
        fixture = self.fixtures[entity]
        return self.validator.validate_payload(
            entity,
            fixture["payload"],
            business_key=fixture["business_key"],
            source_key=fixture["source_key"],
            source_system=fixture["source_system"],
            event_time=fixture["event_time"],
        )

    def test_supported_entities_match_the_six_published_contracts(self) -> None:
        self.assertEqual(
            ("inventory", "order", "order_line", "payment", "return", "shipment"),
            self.validator.supported_entities,
        )

    def test_valid_payloads_receive_complete_valid_envelopes(self) -> None:
        for entity, fixture in self.fixtures.items():
            with self.subTest(entity=entity):
                result = self.validate_fixture_payload(entity)
                self.assertTrue(result.is_valid)
                self.assertEqual("silver", result.destination)
                self.assertEqual((), result.errors)
                self.assertEqual("VALID", result.record["processing_status"])
                self.assertEqual("1.0.0", result.record["schema_version"])
                self.assertEqual(
                    "2026-08-28T08:15:30.123456Z",
                    result.record["ingestion_time"],
                )
                self.assertEqual(fixture["payload"], result.record["payload"])

    def test_invalid_payload_is_preserved_and_routed_to_quarantine(self) -> None:
        fixture = self.fixtures["order"]
        payload = copy.deepcopy(fixture["payload"])
        payload["order_status"] = "NOT_A_STATUS"
        original = copy.deepcopy(payload)

        result = self.validator.validate_payload(
            "order",
            payload,
            business_key=fixture["business_key"],
            source_key=fixture["source_key"],
            source_system=fixture["source_system"],
            event_time=fixture["event_time"],
        )

        self.assertFalse(result.is_valid)
        self.assertEqual("quarantine", result.destination)
        self.assertEqual("QUARANTINED", result.record["processing_status"])
        self.assertEqual(original, result.record["payload"])
        self.assertEqual(original, payload)
        self.assertTrue(any(error.path == "/payload/order_status" for error in result.errors))
        self.assertTrue(any(error.code == "SCHEMA_ENUM" for error in result.errors))

    def test_multiple_schema_errors_are_detailed_and_deterministic(self) -> None:
        fixture = self.fixtures["payment"]
        payload = copy.deepcopy(fixture["payload"])
        del payload["customer_key"]
        payload["paid_amount"] = "one hundred"
        result = self.validator.validate_payload(
            "payment",
            payload,
            business_key="wrong-prefix",
            source_key=fixture["source_key"],
            source_system=fixture["source_system"],
            event_time="not-a-timestamp",
        )

        self.assertGreaterEqual(len(result.errors), 4)
        serialized = result.as_dict()
        self.assertFalse(serialized["is_valid"])
        self.assertEqual("quarantine", serialized["destination"])
        for error in serialized["errors"]:
            self.assertEqual(
                {"code", "path", "message", "validator", "schema_path"},
                set(error),
            )

    def test_explicit_timezone_aware_ingestion_time_is_converted_to_utc(self) -> None:
        fixture = self.fixtures["inventory"]
        local_time = datetime(
            2026, 8, 28, 15, 15, tzinfo=timezone(timedelta(hours=7))
        )
        result = self.validator.validate_payload(
            "inventory",
            fixture["payload"],
            business_key=fixture["business_key"],
            source_key=fixture["source_key"],
            source_system=fixture["source_system"],
            event_time=fixture["event_time"],
            ingestion_time=local_time,
        )
        self.assertTrue(result.is_valid)
        self.assertEqual("2026-08-28T08:15:00.000000Z", result.record["ingestion_time"])

    def test_naive_ingestion_datetime_is_rejected(self) -> None:
        fixture = self.fixtures["return"]
        with self.assertRaisesRegex(ValueError, "timezone"):
            self.validator.validate_payload(
                "return",
                fixture["payload"],
                business_key=fixture["business_key"],
                source_key=fixture["source_key"],
                source_system=fixture["source_system"],
                event_time=fixture["event_time"],
                ingestion_time=datetime(2026, 8, 28, 8, 15),
            )

    def test_unknown_entity_and_non_mapping_payload_fail_fast(self) -> None:
        with self.assertRaisesRegex(ContractConfigurationError, "Unknown contract entity"):
            self.validator.validate_payload(
                "invoice",
                {},
                business_key="INV-X-1",
                source_key="1",
                source_system="x",
                event_time="2026-08-28T00:00:00Z",
            )
        with self.assertRaisesRegex(TypeError, "payload must be a mapping"):
            self.validator.validate_payload(
                "order",
                [],
                business_key="ORD-X-1",
                source_key="1",
                source_system="xx",
                event_time="2026-08-28T00:00:00Z",
            )

    def test_validate_record_does_not_mutate_existing_envelope(self) -> None:
        fixture = copy.deepcopy(self.fixtures["shipment"])
        fixture["processing_status"] = "WARNING"
        original = copy.deepcopy(fixture)
        result = self.validator.validate_record("shipment", fixture)
        self.assertTrue(result.is_valid)
        self.assertEqual("VALID", result.record["processing_status"])
        self.assertEqual(original, fixture)

    def test_schema_files_are_cached_across_validator_instances(self) -> None:
        clear_schema_cache()
        DataContractValidator()
        after_first = schema_cache_info()
        DataContractValidator()
        after_second = schema_cache_info()
        self.assertEqual(7, after_first.misses)
        self.assertGreaterEqual(after_second.hits - after_first.hits, 7)

    def test_missing_schema_directory_fails_with_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaisesRegex(ContractConfigurationError, "does not exist"):
                DataContractValidator(missing)


if __name__ == "__main__":
    unittest.main()
