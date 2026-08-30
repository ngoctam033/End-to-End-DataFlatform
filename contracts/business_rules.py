"""Versioned business-rule validation for canonical source records."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from .validator import DataContractValidator


DEFAULT_RULE_CATALOG = Path(__file__).resolve().parent / "rules" / "business_rules.yaml"


class BusinessRuleConfigurationError(RuntimeError):
    """Raised when the versioned rule catalog is invalid."""


@dataclass(frozen=True)
class BusinessValidationError:
    code: str
    message: str
    path: str
    disposition: str
    source_system: str
    source_record_key: str
    validation_time: str
    rule_version: str


@dataclass(frozen=True)
class BusinessValidationResult:
    entity: str
    status: str
    destination: str
    validation_id: str
    validation_time: str
    rule_version: str
    record: dict[str, Any]
    errors: tuple[BusinessValidationError, ...]

    @property
    def is_accepted(self) -> bool:
        return self.status == "ACCEPTED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "status": self.status,
            "destination": self.destination,
            "validation_id": self.validation_id,
            "validation_time": self.validation_time,
            "rule_version": self.rule_version,
            "record": copy.deepcopy(self.record),
            "errors": [asdict(error) for error in self.errors],
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_string(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("validation clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _date(value: str) -> date:
    return date.fromisoformat(value)


class SourceBusinessRuleValidator:
    """Apply structural validation followed by deterministic business rules."""

    ORDER_TRANSITIONS = {
        "DRAFT": {"DRAFT", "CONFIRMED", "CANCELLED"},
        "CONFIRMED": {"CONFIRMED", "FULFILLED", "INVOICED", "CANCELLED"},
        "FULFILLED": {"FULFILLED", "INVOICED"},
        "INVOICED": {"INVOICED", "PAID"},
        "PAID": {"PAID"},
        "CANCELLED": {"CANCELLED"},
    }
    SHIPMENT_TRANSITIONS = {
        "PLANNED": {"PLANNED", "IN_TRANSIT", "CANCELLED"},
        "IN_TRANSIT": {"IN_TRANSIT", "DELIVERED", "FAILED", "RETURNED"},
        "FAILED": {"FAILED", "IN_TRANSIT", "RETURNED"},
        "DELIVERED": {"DELIVERED", "RETURNED"},
        "RETURNED": {"RETURNED"},
        "CANCELLED": {"CANCELLED"},
    }
    PAYMENT_TRANSITIONS = {
        "PENDING": {"PENDING", "AUTHORIZED", "PAID", "FAILED", "CANCELLED"},
        "AUTHORIZED": {"AUTHORIZED", "PAID", "FAILED", "CANCELLED"},
        "PAID": {"PAID", "REVERSED", "REFUNDED"},
        "FAILED": {"FAILED", "PENDING"},
        "REVERSED": {"REVERSED"},
        "REFUNDED": {"REFUNDED"},
        "CANCELLED": {"CANCELLED"},
    }

    def __init__(
        self,
        contract_validator: DataContractValidator | None = None,
        rule_catalog: str | Path = DEFAULT_RULE_CATALOG,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.contract_validator = contract_validator or DataContractValidator()
        self._clock = clock
        self.catalog = self._load_catalog(Path(rule_catalog))
        self.rule_version = self.catalog["version"]

    def validate(
        self,
        entity: str,
        record: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> BusinessValidationResult:
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        checked_at = _utc_string(self._clock())
        structural = self.contract_validator.validate_record(entity, record)
        candidate = structural.record
        validation_id = self._validation_id(entity, candidate)
        if not structural.is_valid:
            errors = tuple(
                BusinessValidationError(
                    code=error.code,
                    message=error.message,
                    path=error.path,
                    disposition="quarantined",
                    source_system=str(candidate.get("source_system", "")),
                    source_record_key=str(candidate.get("source_key", "")),
                    validation_time=checked_at,
                    rule_version=self.rule_version,
                )
                for error in structural.errors
            )
            return self._result(entity, "QUARANTINED", validation_id, checked_at, candidate, errors)

        failures: list[tuple[str, str, str]] = []
        payload = candidate["payload"]
        ctx = dict(context or {})
        self._check_business_key(entity, candidate, ctx, failures)
        checker = getattr(self, f"_check_{entity}")
        checker(payload, ctx, failures)
        errors = tuple(self._error(code, message, path, candidate, checked_at) for code, message, path in failures)
        dispositions = {error.disposition for error in errors}
        status = "REJECTED" if "rejected" in dispositions else "QUARANTINED" if errors else "ACCEPTED"
        candidate["processing_status"] = "VALID" if status == "ACCEPTED" else "QUARANTINED"
        return self._result(entity, status, validation_id, checked_at, candidate, errors)

    def _check_business_key(self, entity, record, context, failures):
        source = record["source_system"].upper()
        p = record["payload"]
        if entity == "order_line":
            components = [p["order_key"], record["source_key"]]
        elif entity == "inventory":
            components = [p["warehouse_code"], p["sku"]]
        elif entity == "shipment":
            components = [p["tracking_number"]]
        elif entity == "payment":
            components = [p["transaction_reference"]]
        else:
            components = [record["source_key"]]
        prefixes = {"order":"ORD", "order_line":"ORDL", "inventory":"INV", "shipment":"SHP", "return":"RET", "payment":"PAY"}
        expected = "-".join([prefixes[entity], source, *map(str, components)])
        if record["business_key"] != expected:
            failures.append(("COMMON_BUSINESS_KEY_MISMATCH", f"Expected business_key {expected!r}", "/business_key"))

    def _check_order(self, p, c, f):
        if _decimal(p["net_amount"]) != _decimal(p["gross_amount"]) - _decimal(p["discount_amount"]):
            f.append(("ORDER_AMOUNT_MISMATCH", "net_amount must equal gross_amount minus discount_amount", "/payload/net_amount"))
        self._transition("order", p["order_status"], c, self.ORDER_TRANSITIONS, "ORDER_INVALID_STATUS_TRANSITION", f)

    def _check_order_line(self, p, c, f):
        gross = _decimal(p["ordered_qty"]) * _decimal(p["unit_price_amount"])
        if _decimal(p["gross_amount"]) != gross or _decimal(p["net_amount"]) != gross - _decimal(p["discount_amount"]):
            f.append(("ORDER_LINE_AMOUNT_MISMATCH", "Line amounts do not reconcile with quantity, unit price and discount", "/payload/net_amount"))
        self._relationship(p["order_key"], c.get("known_order_keys"), "order", f)

    def _check_inventory(self, p, c, f):
        if _decimal(p["reserved_qty"]) > _decimal(p["on_hand_qty"]) or _decimal(p["available_qty"]) != _decimal(p["on_hand_qty"]) - _decimal(p["reserved_qty"]):
            f.append(("INVENTORY_BALANCE_MISMATCH", "Inventory balance quantities do not reconcile", "/payload/available_qty"))
        if p.get("manufacturing_date") and p.get("expiration_date") and _date(p["expiration_date"]) <= _date(p["manufacturing_date"]):
            f.append(("INVENTORY_LOT_DATE_INVALID", "expiration_date must be later than manufacturing_date", "/payload/expiration_date"))
        for index, move in enumerate(c.get("stock_moves", [])):
            qty, cost, value = _decimal(move["quantity"]), _decimal(move["unit_cost"]), _decimal(move["move_value"])
            positive = {"purchase_receipt", "return_receipt"}
            negative = {"sale_delivery"}
            invalid_sign = move["move_type"] in positive and qty <= 0 or move["move_type"] in negative and qty >= 0
            if invalid_sign or value != qty * cost:
                f.append(("INVENTORY_MOVE_INVALID", f"Invalid stock movement at index {index}", f"/context/stock_moves/{index}"))

    def _check_shipment(self, p, c, f):
        self._relationship(p["order_key"], c.get("known_order_keys"), "order", f)
        if "order_date" not in c:
            f.append(("CONTEXT_RELATIONSHIP_MISSING", "order_date context is required", "/context/order_date"))
        self._transition("shipment", p["shipment_status"], c, self.SHIPMENT_TRANSITIONS, "SHIPMENT_INVALID_STATUS_TRANSITION", f)
        dates = [p["planned_ship_date"], p["planned_delivery_date"]]
        invalid = _date(dates[1]) < _date(dates[0])
        if c.get("order_date") and _date(p["planned_ship_date"]) < _date(c["order_date"]): invalid = True
        if p.get("actual_ship_date") and _date(p["actual_ship_date"]) < _date(p["planned_ship_date"]): invalid = True
        if p.get("actual_delivery_date") and _date(p["actual_delivery_date"]) < _date(p["actual_ship_date"] or p["planned_ship_date"]): invalid = True
        if invalid: f.append(("SHIPMENT_TIMELINE_INVALID", "Shipment dates are not chronologically valid", "/payload/planned_ship_date"))
        maximum_days = c.get("sla_max_days")
        planned_days = (_date(p["planned_delivery_date"]) - _date(p["planned_ship_date"])).days
        if maximum_days is not None and planned_days > int(maximum_days):
            f.append(("SHIPMENT_SLA_POLICY_INVALID", "Planned delivery window exceeds configured SLA", "/payload/planned_delivery_date"))
        for index, attempt in enumerate(c.get("delivery_attempts", [])):
            status = attempt.get("attempt_status")
            attempt_invalid = _date(attempt["attempt_date"]) < _date(p["planned_ship_date"])
            attempt_invalid = attempt_invalid or status not in {"DELIVERED", "FAILED", "RESCHEDULED", "RETURNED"}
            attempt_invalid = attempt_invalid or (status in {"FAILED", "RETURNED"} and not attempt.get("failure_reason"))
            if attempt_invalid:
                f.append(("SHIPMENT_DELIVERY_ATTEMPT_INVALID", f"Invalid delivery attempt at index {index}", f"/context/delivery_attempts/{index}"))

    def _check_payment(self, p, c, f):
        invoice = c.get("invoice")
        if not invoice:
            f.append(("CONTEXT_RELATIONSHIP_MISSING", "Invoice context is required", "/context/invoice")); return
        invoice_fields = {"invoice_key", "order_key", "customer_key", "gross_amount", "discount_amount", "tax_amount", "net_amount", "amount_paid", "invoice_date"}
        missing = sorted(invoice_fields - set(invoice))
        if missing:
            f.append(("CONTEXT_RELATIONSHIP_MISSING", f"Invoice context is missing: {', '.join(missing)}", "/context/invoice")); return
        expected_invoice_net = _decimal(invoice["gross_amount"]) - _decimal(invoice["discount_amount"]) + _decimal(invoice["tax_amount"])
        if _decimal(invoice["net_amount"]) != expected_invoice_net:
            f.append(("INVOICE_AMOUNT_MISMATCH", "Invoice amounts do not reconcile", "/context/invoice/net_amount"))
        for field in ("invoice_key", "customer_key", "order_key"):
            if p.get(field) and invoice.get(field) and p[field] != invoice[field]:
                f.append(("PAYMENT_RELATIONSHIP_MISMATCH", f"{field} does not match invoice context", f"/payload/{field}"))
        outstanding = _decimal(invoice["net_amount"]) - _decimal(invoice.get("amount_paid", 0))
        if _decimal(p["paid_amount"]) > outstanding:
            f.append(("PAYMENT_EXCEEDS_OUTSTANDING", "paid_amount exceeds invoice outstanding amount", "/payload/paid_amount"))
        if _date(p["payment_date"]) < _date(invoice["invoice_date"]):
            f.append(("PAYMENT_TIMELINE_INVALID", "payment_date cannot precede invoice_date", "/payload/payment_date"))
        self._transition("payment", p["payment_status"], c, self.PAYMENT_TRANSITIONS, "PAYMENT_INVALID_STATUS_TRANSITION", f)

    def _check_return(self, p, c, f):
        line = c.get("order_line")
        if not line:
            f.append(("CONTEXT_RELATIONSHIP_MISSING", "Order-line context is required", "/context/order_line")); return
        line_fields = {"sold_qty", "net_amount", "order_date", "order_status"}
        missing = sorted(line_fields - set(line))
        if missing:
            f.append(("CONTEXT_RELATIONSHIP_MISSING", f"Order-line context is missing: {', '.join(missing)}", "/context/order_line")); return
        sold, previous, returned = _decimal(line["sold_qty"]), _decimal(line.get("previous_returned_qty", 0)), _decimal(p["returned_qty"])
        if returned > sold - previous:
            f.append(("RETURN_QUANTITY_EXCEEDED", "returned_qty exceeds remaining sold quantity", "/payload/returned_qty"))
        maximum_refund = _decimal(line["net_amount"]) / sold * returned
        if _decimal(p["refund_amount"]) > maximum_refund:
            f.append(("RETURN_REFUND_EXCEEDED", "refund_amount exceeds proportional line net amount", "/payload/refund_amount"))
        if _date(p["return_date"]) < _date(line["order_date"]):
            f.append(("RETURN_TIMELINE_INVALID", "return_date cannot precede order_date", "/payload/return_date"))
        if line["order_status"] not in {"FULFILLED", "INVOICED", "PAID"}:
            f.append(("RETURN_ORDER_STATUS_INVALID", "Order status does not allow returns", "/context/order_line/order_status"))

    def _transition(self, entity, current, context, transitions, code, failures):
        previous = context.get("previous_status")
        if previous is not None and current not in transitions.get(previous, set()):
            status_field = {"order": "order_status", "shipment": "shipment_status", "payment": "payment_status"}[entity]
            failures.append((code, f"Invalid {entity} transition {previous} -> {current}", f"/payload/{status_field}"))

    def _relationship(self, key, known, relation, failures):
        if known is None:
            failures.append(("CONTEXT_RELATIONSHIP_MISSING", f"known_{relation}_keys context is required", f"/context/known_{relation}_keys"))
        elif key not in known:
            failures.append(("CONTEXT_RELATIONSHIP_MISSING", f"Related {relation} {key!r} was not found", f"/payload/{relation}_key"))

    def _error(self, code, message, path, record, checked_at):
        rule = self.catalog["rules"][code]
        return BusinessValidationError(code, message, path, rule["disposition"], record["source_system"], record["source_key"], checked_at, self.rule_version)

    def _result(self, entity, status, validation_id, checked_at, record, errors):
        return BusinessValidationResult(entity, status, "accepted" if status == "ACCEPTED" else "quarantine", validation_id, checked_at, self.rule_version, record, errors)

    def _validation_id(self, entity, record):
        identity = {"entity":entity, "source_system":record.get("source_system"), "source_key":record.get("source_key"), "event_time":record.get("event_time"), "rule_version":self.rule_version}
        return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _load_catalog(path):
        try: catalog = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error: raise BusinessRuleConfigurationError(f"Cannot load business-rule catalog {path}: {error}") from error
        if not isinstance(catalog, dict) or not isinstance(catalog.get("version"), str) or not isinstance(catalog.get("rules"), dict):
            raise BusinessRuleConfigurationError("Business-rule catalog must define version and rules")
        return catalog
