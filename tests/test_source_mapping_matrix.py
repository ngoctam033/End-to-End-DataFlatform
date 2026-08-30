"""Consistency checks for the BL-020.3 multi-source mapping matrix."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MATRIX_FILE = ROOT / "contracts" / "mappings" / "source_mapping_matrix.yaml"
SCHEMA_DIR = ROOT / "contracts" / "schemas"
SOURCE_DDL = ROOT / "data_source" / "mock_erp_pg" / "init" / "02_tables.sql"
DOCUMENTATION = ROOT / "docs" / "data_contracts" / "03_source_mapping_matrix.md"
EXPECTED_ENTITIES = {"order", "order_line", "inventory", "shipment", "return", "payment"}
EXPECTED_SOURCES = {
    "mock_erp_pg",
    "odoo",
    "oms",
    "wms",
    "ops",
    "mongodb_catalog",
    "external_api",
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        result = yaml.safe_load(stream)
    if not isinstance(result, dict):
        raise TypeError(f"Expected mapping object in {path}")
    return result


def payload_definition(schema: dict) -> dict:
    for branch in schema["allOf"]:
        payload = branch.get("properties", {}).get("payload")
        if payload:
            return payload
    raise AssertionError("Schema does not define payload properties")


class SourceMappingMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = load_yaml(MATRIX_FILE)
        cls.schemas = {
            entity: load_yaml(SCHEMA_DIR / f"{entity}.yaml")
            for entity in EXPECTED_ENTITIES
        }
        cls.ddl = SOURCE_DDL.read_text(encoding="utf-8")
        cls.documentation = DOCUMENTATION.read_text(encoding="utf-8")

    def test_matrix_targets_the_published_contract_version(self) -> None:
        self.assertEqual("1.0.0", self.matrix["version"])
        self.assertEqual("1.0.0", self.matrix["canonical_contract_version"])
        for entity, schema in self.schemas.items():
            with self.subTest(entity=entity):
                self.assertEqual("1.0.0", schema["version"])

    def test_all_sources_and_entities_are_declared(self) -> None:
        self.assertEqual(EXPECTED_SOURCES, set(self.matrix["source_profiles"]))
        self.assertEqual(EXPECTED_ENTITIES, set(self.matrix["entities"]))
        self.assertEqual(
            "implemented", self.matrix["source_profiles"]["mock_erp_pg"]["status"]
        )
        for source in EXPECTED_SOURCES - {"mock_erp_pg"}:
            with self.subTest(source=source):
                self.assertEqual(
                    "contract_only", self.matrix["source_profiles"][source]["status"]
                )

    def test_every_source_is_routed_to_at_least_one_entity(self) -> None:
        routed_sources: set[str] = set()
        for entity in self.matrix["entities"].values():
            routed_sources.update(entity["owner_sources"])
            routed_sources.update(entity["prospective_sources"])
        self.assertEqual(EXPECTED_SOURCES, routed_sources)

    def test_postgres_mapping_covers_every_canonical_payload_field(self) -> None:
        for entity, schema in self.schemas.items():
            with self.subTest(entity=entity):
                canonical_fields = set(payload_definition(schema)["properties"])
                mapped_fields = set(self.matrix["entities"][entity]["mappings"])
                self.assertEqual(canonical_fields, mapped_fields)

    def test_required_fields_have_nonempty_mapping_expressions(self) -> None:
        for entity, schema in self.schemas.items():
            payload = payload_definition(schema)
            mappings = self.matrix["entities"][entity]["mappings"]
            for field in payload["required"]:
                with self.subTest(entity=entity, field=field):
                    expression = mappings[field]
                    self.assertIsInstance(expression, (str, int, float))
                    self.assertNotEqual("", str(expression).strip())

    def test_enum_map_outputs_are_allowed_by_canonical_schema(self) -> None:
        for entity, config in self.matrix["entities"].items():
            properties = payload_definition(self.schemas[entity])["properties"]
            for field, value_map in config.get("enum_maps", {}).items():
                with self.subTest(entity=entity, field=field):
                    self.assertIn(field, properties)
                    allowed = set(properties[field]["enum"])
                    self.assertTrue(value_map)
                    self.assertLessEqual(set(value_map.values()), allowed)

    def test_business_key_templates_match_schema_prefixes(self) -> None:
        prefixes = {
            "order": "ORD-",
            "order_line": "ORDL-",
            "inventory": "INV-",
            "shipment": "SHP-",
            "return": "RET-",
            "payment": "PAY-",
        }
        for entity, prefix in prefixes.items():
            with self.subTest(entity=entity):
                template = self.matrix["entities"][entity]["business_key"]
                self.assertTrue(template.startswith(prefix))
                self.assertIn("{SOURCE_SYSTEM_UPPER}", template)

    def test_referenced_postgres_base_tables_exist_in_source_ddl(self) -> None:
        for entity, config in self.matrix["entities"].items():
            references = " ".join(
                [config["source_key"], config["event_time"], *config["joins"]]
            )
            tables = set(re.findall(r"erp_[a-z_]+\.[a-z_]+", references))
            self.assertTrue(tables, entity)
            for table in tables:
                with self.subTest(entity=entity, table=table):
                    self.assertIn(f"CREATE TABLE {table}", self.ddl)

    def test_documentation_covers_rules_sources_and_entities(self) -> None:
        required_sections = (
            "Metadata envelope",
            "Chuyển đổi kiểu và null",
            "Business key theo entity và nguồn",
            "Source ownership và routing",
            "Mapping triển khai: Mock ERP PostgreSQL",
            "Mapping contract-level cho nguồn tương lai",
            "Error code tối thiểu",
        )
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.documentation)
        for source in EXPECTED_SOURCES:
            display_token = self.matrix["source_profiles"][source]["source_system"]
            with self.subTest(source=source):
                self.assertIn(display_token, self.documentation)
        for entity in EXPECTED_ENTITIES:
            with self.subTest(entity=entity):
                self.assertRegex(self.documentation.lower(), rf"\b{re.escape(entity)}\b")


if __name__ == "__main__":
    unittest.main()
