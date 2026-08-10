"""Business scenario models used by mock-data adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class OrderLineScenario:
    sku: str
    warehouse_code: str
    quantity: Decimal
    unit_price: Decimal | None = None
    discount_amount: Decimal = Decimal("0")
    promotion_code: str | None = None


@dataclass(frozen=True)
class PaymentScenario:
    amount: Decimal
    method: str
    payment_date: date


@dataclass(frozen=True)
class ReturnScenario:
    line_index: int
    quantity: Decimal
    reason: str
    return_date: date


@dataclass(frozen=True)
class SalesOrderScenario:
    name: str
    customer_code: str
    channel_code: str
    branch_code: str
    order_date: date
    lines: tuple[OrderLineScenario, ...]
    fulfillment_date: date | None = None
    carrier_code: str = "GHN-STD"
    invoice_date: date | None = None
    due_days: int = 15
    payments: tuple[PaymentScenario, ...] = ()
    returns: tuple[ReturnScenario, ...] = ()


@dataclass(frozen=True)
class BusinessScenarioSet:
    name: str
    sales_orders: tuple[SalesOrderScenario, ...]
