"""Omnichannel D2C FMCG sample scenarios."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from datetime import timedelta
from decimal import Decimal

from data_source.mock_data_factory.interfaces import TransactionScenarioProvider
from data_source.mock_data_factory.models import (
    BusinessScenarioSet,
    OrderLineScenario,
    PaymentScenario,
    SalesOrderScenario,
)


def shift_scenario_set(scenario_set: BusinessScenarioSet, days: int) -> BusinessScenarioSet:
    """Shift transaction dates while keeping master-data business codes stable."""
    delta = timedelta(days=days)
    shifted_orders = []

    for order in scenario_set.sales_orders:
        shifted_payments = tuple(
            replace(payment, payment_date=payment.payment_date + delta)
            for payment in order.payments
        )
        shifted_returns = tuple(
            replace(return_item, return_date=return_item.return_date + delta)
            for return_item in order.returns
        )
        shifted_orders.append(
            replace(
                order,
                order_date=order.order_date + delta,
                fulfillment_date=order.fulfillment_date + delta
                if order.fulfillment_date is not None
                else None,
                invoice_date=order.invoice_date + delta
                if order.invoice_date is not None
                else None,
                payments=shifted_payments,
                returns=shifted_returns,
            )
        )

    return replace(scenario_set, sales_orders=tuple(shifted_orders))


class OmnichannelFmcgScenarioProvider(TransactionScenarioProvider):
    """Produces repeatable omnichannel transaction batches."""

    def __init__(self, days_per_batch: int = 1) -> None:
        if days_per_batch < 0:
            raise ValueError("days_per_batch must be zero or positive")

        self._base_scenario_set = build_scenario_set()
        self._days_per_batch = days_per_batch
        self._batch_index = 0

    def next_batch(self) -> BusinessScenarioSet:
        scenario_set = shift_scenario_set(
            self._base_scenario_set,
            days=self._batch_index * self._days_per_batch,
        )
        self._batch_index += 1
        return scenario_set


def build_scenario_set() -> BusinessScenarioSet:
    return BusinessScenarioSet(
        name="omnichannel_d2c_fmcg",
        sales_orders=(
            SalesOrderScenario(
                name="vip_customer_website_order_partial_payment",
                customer_code="CUS-00001",
                channel_code="WEB",
                branch_code="HN",
                order_date=date(2026, 8, 1),
                lines=(
                    OrderLineScenario(
                        sku="TEA-LEM-330",
                        warehouse_code="WH-HN",
                        quantity=Decimal("12"),
                        promotion_code="WEB-TEA-AUG10",
                    ),
                    OrderLineScenario(
                        sku="BIS-OAT-120",
                        warehouse_code="WH-HN",
                        quantity=Decimal("5"),
                    ),
                ),
                fulfillment_date=date(2026, 8, 2),
                carrier_code="GHTK-EXP",
                invoice_date=date(2026, 8, 2),
                due_days=15,
                payments=(
                    PaymentScenario(
                        amount=Decimal("100000"),
                        method="e_wallet",
                        payment_date=date(2026, 8, 3),
                    ),
                ),
            ),
            SalesOrderScenario(
                name="b2b_bulk_order_partial_payment",
                customer_code="CUS-00003",
                channel_code="B2B",
                branch_code="HCM",
                order_date=date(2026, 8, 2),
                lines=(
                    OrderLineScenario(
                        sku="TEA-PEA-330",
                        warehouse_code="WH-HCM",
                        quantity=Decimal("50"),
                        unit_price=Decimal("10000"),
                        promotion_code="B2B-BULK-AUG5",
                    ),
                    OrderLineScenario(
                        sku="JUI-ORA-500",
                        warehouse_code="WH-HCM",
                        quantity=Decimal("20"),
                        unit_price=Decimal("20000"),
                        discount_amount=Decimal("20000"),
                    ),
                ),
                fulfillment_date=date(2026, 8, 4),
                carrier_code="INTERNAL-B2B",
                invoice_date=date(2026, 8, 4),
                due_days=30,
                payments=(
                    PaymentScenario(
                        amount=Decimal("300000"),
                        method="bank_transfer",
                        payment_date=date(2026, 8, 5),
                    ),
                ),
            ),
        ),
    )
