"""Omnichannel D2C FMCG sample scenarios."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from data_source.mock_data_factory.catalog import (
    BRANCHES,
    CARRIERS,
    CHANNELS,
    CUSTOMERS,
    PRODUCTS,
    PROMOTIONS,
    WAREHOUSES,
)
from data_source.mock_data_factory.models import (
    BusinessScenarioSet,
    OrderLineScenario,
    PaymentScenario,
    SalesOrderScenario,
)


def build_scenario_set() -> BusinessScenarioSet:
    return BusinessScenarioSet(
        name="omnichannel_d2c_fmcg",
        sales_orders=(
            SalesOrderScenario(
                name="vip_customer_website_order_partial_payment",
                customer_id=CUSTOMERS["vip_hanoi"],
                channel_id=CHANNELS["website"],
                branch_id=BRANCHES["hanoi"],
                order_date=date(2026, 8, 1),
                lines=(
                    OrderLineScenario(
                        product_id=PRODUCTS["lemon_tea_330ml"],
                        warehouse_id=WAREHOUSES["hanoi"],
                        quantity=Decimal("12"),
                        promotion_id=PROMOTIONS["website_tea_aug10"],
                    ),
                    OrderLineScenario(
                        product_id=PRODUCTS["oat_biscuit_120g"],
                        warehouse_id=WAREHOUSES["hanoi"],
                        quantity=Decimal("5"),
                    ),
                ),
                fulfillment_date=date(2026, 8, 2),
                carrier_id=CARRIERS["ghtk_express"],
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
                customer_id=CUSTOMERS["b2b_danang"],
                channel_id=CHANNELS["b2b"],
                branch_id=BRANCHES["hcm"],
                order_date=date(2026, 8, 2),
                lines=(
                    OrderLineScenario(
                        product_id=PRODUCTS["peach_tea_330ml"],
                        warehouse_id=WAREHOUSES["hcm"],
                        quantity=Decimal("50"),
                        unit_price=Decimal("10000"),
                        promotion_id=PROMOTIONS["b2b_bulk_aug5"],
                    ),
                    OrderLineScenario(
                        product_id=PRODUCTS["orange_juice_500ml"],
                        warehouse_id=WAREHOUSES["hcm"],
                        quantity=Decimal("20"),
                        unit_price=Decimal("20000"),
                        discount_amount=Decimal("20000"),
                    ),
                ),
                fulfillment_date=date(2026, 8, 4),
                carrier_id=CARRIERS["internal_b2b_fleet"],
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
