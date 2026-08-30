"""Executable checks for BL-020.2 canonical YAML schemas."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
FIXTURE_FILE = ROOT / "tests" / "fixtures" / "contracts" / "valid_records.yaml"
ENTITIES = ("order", "order_line", "inventory", "shipment", "return", "payment")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict):
        raise TypeError(f"Expected a YAML object in {path}")
    return document


class CanonicalContractSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            path.stem: load_yaml(path) for path in sorted(SCHEMA_DIR.glob("*.yaml"))
        }
        cls.records = load_yaml(FIXTURE_FILE)
        cls.registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema))
            for schema in cls.schemas.values()
        )

    def validator(self, entity: str) -> Draft202012Validator:
        schema = self.schemas[entity]
        return Draft202012Validator(
            schema,
            registry=self.registry,
            format_checker=FormatChecker(),
        )

    def assert_invalid(self, entity: str, record: dict) -> None:
        errors = list(self.validator(entity).iter_errors(record))
        self.assertTrue(errors, f"Expected {entity} record to be invalid")

    def test_exactly_six_entity_schemas_are_published(self) -> None:
        published = set(self.schemas) - {"common"}
        self.assertEqual(set(ENTITIES), published)
        self.assertEqual(set(ENTITIES), set(self.records))

    def test_every_schema_is_valid_draft_2020_12(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema",
                    schema.get("$schema"),
                )
                Draft202012Validator.check_schema(schema)

    def test_all_valid_fixtures_are_accepted(self) -> None:
        for entity in ENTITIES:
            with self.subTest(entity=entity):
                self.validator(entity).validate(self.records[entity])

    def test_missing_required_envelope_field_is_rejected(self) -> None:
        for entity in ENTITIES:
            with self.subTest(entity=entity):
                record = copy.deepcopy(self.records[entity])
                del record["business_key"]
                self.assert_invalid(entity, record)

    def test_wrong_payload_type_is_rejected(self) -> None:
        record = copy.deepcopy(self.records["order_line"])
        record["payload"]["ordered_qty"] = "12"
        self.assert_invalid("order_line", record)

    def test_invalid_business_enum_is_rejected(self) -> None:
        enum_fields = {
            "order": ("order_status", "UNKNOWN"),
            "shipment": ("shipment_status", "UNKNOWN"),
            "return": ("return_status", "UNKNOWN"),
            "payment": ("payment_status", "UNKNOWN"),
        }
        for entity, (field, invalid_value) in enum_fields.items():
            with self.subTest(entity=entity):
                record = copy.deepcopy(self.records[entity])
                record["payload"][field] = invalid_value
                self.assert_invalid(entity, record)

    def test_non_utc_timestamp_and_unknown_fields_are_rejected(self) -> None:
        timestamp_record = copy.deepcopy(self.records["order"])
        timestamp_record["event_time"] = "2026-08-28T08:30:00+07:00"
        self.assert_invalid("order", timestamp_record)

        extra_field_record = copy.deepcopy(self.records["inventory"])
        extra_field_record["payload"]["unexpected_field"] = "schema drift"
        self.assert_invalid("inventory", extra_field_record)

    def test_contract_version_is_enforced(self) -> None:
        record = copy.deepcopy(self.records["payment"])
        record["schema_version"] = "1.1.0"
        self.assert_invalid("payment", record)


if __name__ == "__main__":
    unittest.main()
