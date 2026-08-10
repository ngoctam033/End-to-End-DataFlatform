"""Stable IDs used by mock scenarios.

These IDs must match `data_source/mock_erp_pg/init/04_seed_master_data.sql`.
Keeping them in one Python module makes scenario generation easier to read and
keeps adapters independent from handwritten SQL seed details.
"""

from __future__ import annotations


CUSTOMERS = {
    "vip_hanoi": 1,
    "returning_hcm": 2,
    "b2b_danang": 3,
    "wholesale_mekong": 4,
}

CHANNELS = {
    "store": 1,
    "website": 2,
    "marketplace": 3,
    "b2b": 4,
    "social": 5,
}

BRANCHES = {
    "hanoi": 1,
    "hcm": 2,
    "danang": 3,
}

WAREHOUSES = {
    "hanoi": 1,
    "hcm": 2,
    "danang": 3,
}

PRODUCTS = {
    "lemon_tea_330ml": 1,
    "peach_tea_330ml": 2,
    "orange_juice_500ml": 3,
    "oat_biscuit_120g": 4,
    "chocolate_biscuit_120g": 5,
}

CARRIERS = {
    "ghn_standard": 1,
    "ghtk_express": 2,
    "viettel_post_standard": 3,
    "jnt_same_day": 4,
    "internal_b2b_fleet": 5,
}

PROMOTIONS = {
    "website_tea_aug10": 1,
    "marketplace_snack_fixed_5k": 2,
    "b2b_bulk_aug5": 3,
}
