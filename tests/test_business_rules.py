"""BL-030 source business-rule validation tests."""

from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

from contracts import DataContractValidator, SourceBusinessRuleValidator


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILE = ROOT / "tests" / "fixtures" / "contracts" / "multi_source_records.yaml"
CATALOG_FILE = ROOT / "contracts" / "rules" / "business_rules.yaml"
FIXED_TIME = datetime(2026, 8, 30, 2, 0, tzinfo=timezone.utc)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class SourceBusinessRuleValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cases = load_yaml(FIXTURE_FILE)["cases"]
        cls.cases = {case["entity"]: case for case in cases}
        cls.contract_validator = DataContractValidator(clock=lambda: FIXED_TIME)
        cls.validator = SourceBusinessRuleValidator(
            cls.contract_validator, clock=lambda: FIXED_TIME
        )

    def record(self, entity: str) -> dict:
        case = self.cases[entity]
        result = self.contract_validator.validate_payload(
            entity,
            case["payload"],
            business_key=case["business_key"],
            source_key=case["source_key"],
            source_system=case["source_system"],
            event_time=case["event_time"],
        )
        self.assertTrue(result.is_valid, result.errors)
        return result.record

    @staticmethod
    def contexts() -> dict:
        return {
            "order": {"previous_status": "DRAFT"},
            "order_line": {"known_order_keys": ["SO2002"]},
            "inventory": {
                "stock_moves": [
                    {
                        "move_type": "purchase_receipt",
                        "quantity": 10,
                        "unit_cost": 5000,
                        "move_value": 50000,
                    }
                ]
            },
            "shipment": {
                "known_order_keys": ["ORD10045"],
                "order_date": "2026-08-27",
                "previous_status": "PLANNED",
                "sla_max_days": 3,
                "delivery_attempts": [
                    {"attempt_date": "2026-08-29", "attempt_status": "RESCHEDULED"}
                ],
            },
            "payment": {
                "previous_status": "PENDING",
                "invoice": {
                    "invoice_key": "INV-1001",
                    "order_key": "ORD10045",
                    "customer_key": "CUS009",
                    "net_amount": 150000,
                    "gross_amount": 140000,
                    "discount_amount": 0,
                    "tax_amount": 10000,
                    "amount_paid": 0,
                    "invoice_date": "2026-08-27",
                },
            },
            "return": {
                "order_line": {
                    "sold_qty": 2,
                    "previous_returned_qty": 0,
                    "net_amount": 20000,
                    "order_date": "2026-08-27",
                    "order_status": "PAID",
                }
            },
        }

    def test_valid_record_for_every_entity_is_accepted(self) -> None:
        for entity, context in self.contexts().items():
            with self.subTest(entity=entity):
                result = self.validator.validate(entity, self.record(entity), context=context)
                self.assertTrue(result.is_accepted, result.errors)
                self.assertEqual("ACCEPTED", result.status)
                self.assertEqual("accepted", result.destination)
                self.assertEqual("1.0.0", result.rule_version)
                self.assertEqual("VALID", result.record["processing_status"])

    def test_schema_error_is_quarantined_with_trace_fields(self) -> None:
        record = self.record("order")
        record["payload"]["net_amount"] = "invalid"
        result = self.validator.validate("order", record)
        self.assertEqual("QUARANTINED", result.status)
        self.assertEqual("quarantine", result.destination)
        error = result.errors[0]
        self.assertEqual("postgres_erp", error.source_system)
        self.assertEqual("SO-1001", error.source_record_key)
        self.assertEqual("1.0.0", error.rule_version)
        self.assertEqual("2026-08-30T02:00:00.000000Z", error.validation_time)

    def test_order_amount_and_state_transition_violations_are_rejected(self) -> None:
        record = self.record("order")
        record["payload"]["net_amount"] = 100000
        result = self.validator.validate(
            "order", record, context={"previous_status": "PAID"}
        )
        self.assertEqual("REJECTED", result.status)
        self.assertEqual(
            {"ORDER_AMOUNT_MISMATCH", "ORDER_INVALID_STATUS_TRANSITION"},
            {error.code for error in result.errors},
        )

    def test_order_line_relationship_context_missing_is_quarantined(self) -> None:
        result = self.validator.validate("order_line", self.record("order_line"))
        self.assertEqual("QUARANTINED", result.status)
        self.assertEqual({"CONTEXT_RELATIONSHIP_MISSING"}, {e.code for e in result.errors})

    def test_incomplete_payment_context_is_quarantined_instead_of_crashing(self) -> None:
        result = self.validator.validate(
            "payment", self.record("payment"), context={"invoice": {"invoice_key": "INV-1001"}}
        )
        self.assertEqual("QUARANTINED", result.status)
        self.assertEqual({"CONTEXT_RELATIONSHIP_MISSING"}, {e.code for e in result.errors})

    def test_inventory_balance_lot_and_move_violations_are_rejected(self) -> None:
        record = self.record("inventory")
        record["payload"].update(
            {"on_hand_qty": 20, "reserved_qty": 15, "available_qty": 10,
             "manufacturing_date": "2026-08-01", "expiration_date": "2026-07-31"}
        )
        context = {"stock_moves": [{"move_type":"sale_delivery", "quantity":5, "unit_cost":2, "move_value":11}]}
        result = self.validator.validate("inventory", record, context=context)
        self.assertEqual("REJECTED", result.status)
        self.assertEqual(
            {"INVENTORY_BALANCE_MISMATCH", "INVENTORY_LOT_DATE_INVALID", "INVENTORY_MOVE_INVALID"},
            {error.code for error in result.errors},
        )

    def test_shipment_invalid_transition_and_timeline_are_rejected(self) -> None:
        record = self.record("shipment")
        record["payload"]["planned_ship_date"] = "2026-08-26"
        result = self.validator.validate(
            "shipment", record,
            context={"known_order_keys":["ORD10045"], "order_date":"2026-08-27",
                "previous_status":"DELIVERED", "sla_max_days":0,
                "delivery_attempts":[{"attempt_date":"2026-08-25", "attempt_status":"FAILED", "failure_reason":None}]},
        )
        self.assertEqual("REJECTED", result.status)
        self.assertEqual(
            {"SHIPMENT_INVALID_STATUS_TRANSITION", "SHIPMENT_TIMELINE_INVALID",
             "SHIPMENT_SLA_POLICY_INVALID", "SHIPMENT_DELIVERY_ATTEMPT_INVALID"},
            {error.code for error in result.errors},
        )

    def test_payment_overpayment_timeline_relationship_and_state_are_rejected(self) -> None:
        record = self.record("payment")
        context = {"previous_status":"CANCELLED", "invoice": {
            "invoice_key":"OTHER", "order_key":"OTHER", "customer_key":"OTHER",
            "gross_amount":100000, "discount_amount":10000, "tax_amount":5000,
            "net_amount":100000, "amount_paid":50000, "invoice_date":"2026-08-29"}}
        result = self.validator.validate("payment", record, context=context)
        self.assertEqual("REJECTED", result.status)
        self.assertEqual(
            {"PAYMENT_RELATIONSHIP_MISMATCH", "PAYMENT_EXCEEDS_OUTSTANDING",
             "PAYMENT_TIMELINE_INVALID", "PAYMENT_INVALID_STATUS_TRANSITION",
             "INVOICE_AMOUNT_MISMATCH"},
            {error.code for error in result.errors},
        )

    def test_return_quantity_refund_timeline_and_status_are_rejected(self) -> None:
        record = self.record("return")
        context = {"order_line": {"sold_qty":1, "previous_returned_qty":1,
            "net_amount":5000, "order_date":"2026-08-29", "order_status":"CONFIRMED"}}
        result = self.validator.validate("return", record, context=context)
        self.assertEqual("REJECTED", result.status)
        self.assertEqual(
            {"RETURN_QUANTITY_EXCEEDED", "RETURN_REFUND_EXCEEDED", "RETURN_TIMELINE_INVALID", "RETURN_ORDER_STATUS_INVALID"},
            {error.code for error in result.errors},
        )

    def test_business_key_mismatch_is_rejected(self) -> None:
        record = self.record("shipment")
        record["business_key"] = "SHP-OPS-WRONG"
        result = self.validator.validate("shipment", record, context=self.contexts()["shipment"])
        self.assertEqual("REJECTED", result.status)
        self.assertIn("COMMON_BUSINESS_KEY_MISMATCH", {e.code for e in result.errors})

    def test_replay_is_idempotent_and_does_not_mutate_input(self) -> None:
        record = self.record("payment")
        original = copy.deepcopy(record)
        first = self.validator.validate("payment", record, context=self.contexts()["payment"])
        second = self.validator.validate("payment", record, context=self.contexts()["payment"])
        self.assertEqual(first.validation_id, second.validation_id)
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(original, record)

    def test_catalog_contains_every_emitted_business_error_code(self) -> None:
        catalog = load_yaml(CATALOG_FILE)
        self.assertEqual("1.0.0", catalog["version"])
        emitted = {
            "COMMON_BUSINESS_KEY_MISMATCH", "CONTEXT_RELATIONSHIP_MISSING",
            "ORDER_AMOUNT_MISMATCH", "ORDER_INVALID_STATUS_TRANSITION",
            "ORDER_LINE_AMOUNT_MISMATCH", "INVENTORY_BALANCE_MISMATCH",
            "INVENTORY_LOT_DATE_INVALID", "INVENTORY_MOVE_INVALID",
            "SHIPMENT_INVALID_STATUS_TRANSITION", "SHIPMENT_TIMELINE_INVALID",
            "SHIPMENT_DELIVERY_ATTEMPT_INVALID", "SHIPMENT_SLA_POLICY_INVALID",
            "PAYMENT_INVALID_STATUS_TRANSITION", "PAYMENT_EXCEEDS_OUTSTANDING",
            "PAYMENT_TIMELINE_INVALID", "PAYMENT_RELATIONSHIP_MISMATCH",
            "INVOICE_AMOUNT_MISMATCH",
            "RETURN_QUANTITY_EXCEEDED", "RETURN_REFUND_EXCEEDED",
            "RETURN_TIMELINE_INVALID", "RETURN_ORDER_STATUS_INVALID",
        }
        self.assertEqual(emitted, set(catalog["rules"]))


if __name__ == "__main__":
    unittest.main()
