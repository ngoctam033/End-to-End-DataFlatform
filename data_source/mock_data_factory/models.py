"""Business scenario models used by mock-data adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class OrderLineScenario:
    product_id: int
    warehouse_id: int
    quantity: Decimal
    unit_price: Decimal | None = None
    discount_amount: Decimal = Decimal("0")
    promotion_id: int | None = None


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
    customer_id: int
    channel_id: int
    branch_id: int
    order_date: date
    lines: tuple[OrderLineScenario, ...]
    fulfillment_date: date | None = None
    carrier_id: int = 1
    invoice_date: date | None = None
    due_days: int = 15
    payments: tuple[PaymentScenario, ...] = ()
    returns: tuple[ReturnScenario, ...] = ()


@dataclass(frozen=True)
class BusinessScenarioSet:
    name: str
    sales_orders: tuple[SalesOrderScenario, ...]
