INSERT INTO erp_core.companies (
    company_id,
    company_code,
    company_name,
    country,
    currency
)
VALUES
    (1, 'GSFMCG', 'GreenStyle FMCG Vietnam', 'Vietnam', 'VND');

INSERT INTO erp_core.branches (
    branch_id,
    company_id,
    branch_code,
    branch_name,
    city,
    region
)
VALUES
    (1, 1, 'HN', 'Ha Noi Flagship Store', 'Ha Noi', 'North'),
    (2, 1, 'HCM', 'Ho Chi Minh City Store', 'Ho Chi Minh City', 'South'),
    (3, 1, 'DN', 'Da Nang Store', 'Da Nang', 'Central');

INSERT INTO erp_core.warehouses (
    warehouse_id,
    company_id,
    branch_id,
    warehouse_code,
    warehouse_name,
    city
)
VALUES
    (1, 1, 1, 'WH-HN', 'Ha Noi Warehouse', 'Ha Noi'),
    (2, 1, 2, 'WH-HCM', 'Ho Chi Minh City Warehouse', 'Ho Chi Minh City'),
    (3, 1, 3, 'WH-DN', 'Da Nang Warehouse', 'Da Nang');

INSERT INTO erp_core.sales_channels (
    channel_id,
    channel_code,
    channel_name,
    channel_type
)
VALUES
    (1, 'STORE', 'Retail Store', 'offline'),
    (2, 'WEB', 'Website', 'online'),
    (3, 'MKT', 'Marketplace', 'online'),
    (4, 'B2B', 'B2B Sales', 'direct_sales'),
    (5, 'SOCIAL', 'Social Commerce', 'online');

INSERT INTO erp_core.carriers (
    carrier_id,
    carrier_code,
    carrier_name,
    service_level
)
VALUES
    (1, 'GHN-STD', 'Giao Hang Nhanh Standard', 'standard'),
    (2, 'GHTK-EXP', 'Giao Hang Tiet Kiem Express', 'express'),
    (3, 'VTP-STD', 'Viettel Post Standard', 'standard'),
    (4, 'JNT-SD', 'J&T Same Day', 'same_day'),
    (5, 'INTERNAL-B2B', 'Internal B2B Fleet', 'b2b_freight');

INSERT INTO erp_core.customer_segments (
    segment_id,
    segment_code,
    segment_name,
    description
)
VALUES
    (1, 'NEW', 'New Customer', 'First-time or recently acquired customers.'),
    (2, 'RETURNING', 'Returning Customer', 'Customers with repeat purchases.'),
    (3, 'VIP', 'VIP', 'High-value retail customers.'),
    (4, 'B2B', 'B2B', 'Business buyers and corporate customers.'),
    (5, 'WHOLESALE', 'Wholesale', 'Bulk buyers and distributors.');

INSERT INTO erp_core.customers (
    customer_id,
    segment_id,
    customer_code,
    customer_name,
    customer_type,
    city,
    region
)
VALUES
    (1, 3, 'CUS-00001', 'Nguyen Minh Anh', 'individual', 'Ha Noi', 'North'),
    (2, 2, 'CUS-00002', 'Tran Gia Bao', 'individual', 'Ho Chi Minh City', 'South'),
    (3, 4, 'CUS-00003', 'An Phat Retail Co.', 'business', 'Da Nang', 'Central'),
    (4, 5, 'CUS-00004', 'Mekong Wholesale Ltd.', 'business', 'Can Tho', 'South');

INSERT INTO erp_core.product_categories (
    category_id,
    parent_category_id,
    category_code,
    category_name,
    level
)
VALUES
    (1, NULL, 'BEVERAGE', 'Beverages', 1),
    (2, 1, 'TEA', 'Ready-to-drink Tea', 2),
    (3, 1, 'JUICE', 'Fruit Juice', 2),
    (4, NULL, 'SNACK', 'Snacks', 1),
    (5, 4, 'BISCUIT', 'Biscuits', 2);

INSERT INTO erp_core.products (
    product_id,
    category_id,
    sku,
    product_name,
    brand,
    unit_of_measure,
    standard_cost,
    list_price,
    shelf_life_days
)
VALUES
    (1, 2, 'TEA-LEM-330', 'Lemon Tea 330ml', 'GreenStyle', 'bottle', 4500, 10000, 365),
    (2, 2, 'TEA-PEA-330', 'Peach Tea 330ml', 'GreenStyle', 'bottle', 4800, 11000, 365),
    (3, 3, 'JUI-ORA-500', 'Orange Juice 500ml', 'GreenStyle', 'bottle', 9000, 21000, 180),
    (4, 5, 'BIS-OAT-120', 'Oat Biscuit 120g', 'GreenStyle', 'pack', 7000, 18000, 270),
    (5, 5, 'BIS-CHO-120', 'Chocolate Biscuit 120g', 'GreenStyle', 'pack', 7600, 19000, 270);

INSERT INTO erp_sales.price_lists (
    product_id,
    channel_id,
    valid_from,
    valid_to,
    unit_price,
    currency
)
SELECT
    p.product_id,
    c.channel_id,
    DATE '2026-01-01',
    DATE '2026-12-31',
    ROUND(
        p.list_price * CASE c.channel_code
            WHEN 'B2B' THEN 0.90
            WHEN 'MKT' THEN 0.97
            WHEN 'WEB' THEN 1.00
            WHEN 'SOCIAL' THEN 0.98
            ELSE 1.02
        END,
        2
    ),
    'VND'
FROM erp_core.products p
CROSS JOIN erp_core.sales_channels c;

INSERT INTO erp_sales.promotions (
    promotion_id,
    promotion_code,
    promotion_name,
    channel_id,
    start_date,
    end_date,
    discount_type,
    discount_value,
    budget_amount
)
VALUES
    (1, 'WEB-TEA-AUG10', 'Website tea launch 10 percent off', 2, DATE '2026-08-01', DATE '2026-08-31', 'percent', 10, 50000000),
    (2, 'MKT-SNACK-FS5K', 'Marketplace snack fixed discount', 3, DATE '2026-08-01', DATE '2026-08-31', 'fixed_amount', 5000, 25000000),
    (3, 'B2B-BULK-AUG5', 'B2B bulk order 5 percent off', 4, DATE '2026-08-01', DATE '2026-08-31', 'percent', 5, 100000000);

INSERT INTO erp_inventory.stock_balances (
    warehouse_id,
    product_id,
    on_hand_qty,
    reserved_qty,
    reorder_point
)
SELECT
    w.warehouse_id,
    p.product_id,
    CASE w.warehouse_id
        WHEN 1 THEN 500
        WHEN 2 THEN 700
        ELSE 300
    END,
    0,
    80
FROM erp_core.warehouses w
CROSS JOIN erp_core.products p;

INSERT INTO erp_inventory.stock_lots (
    product_id,
    warehouse_id,
    lot_number,
    manufacturing_date,
    expiration_date,
    quantity_on_hand
)
SELECT
    p.product_id,
    w.warehouse_id,
    'LOT-' || p.sku || '-' || w.warehouse_code || '-202601',
    DATE '2026-01-01',
    DATE '2026-01-01' + p.shelf_life_days,
    100
FROM erp_core.products p
CROSS JOIN erp_core.warehouses w;

SELECT setval('erp_core.companies_company_id_seq', (SELECT MAX(company_id) FROM erp_core.companies));
SELECT setval('erp_core.branches_branch_id_seq', (SELECT MAX(branch_id) FROM erp_core.branches));
SELECT setval('erp_core.warehouses_warehouse_id_seq', (SELECT MAX(warehouse_id) FROM erp_core.warehouses));
SELECT setval('erp_core.sales_channels_channel_id_seq', (SELECT MAX(channel_id) FROM erp_core.sales_channels));
SELECT setval('erp_core.carriers_carrier_id_seq', (SELECT MAX(carrier_id) FROM erp_core.carriers));
SELECT setval('erp_core.customer_segments_segment_id_seq', (SELECT MAX(segment_id) FROM erp_core.customer_segments));
SELECT setval('erp_core.customers_customer_id_seq', (SELECT MAX(customer_id) FROM erp_core.customers));
SELECT setval('erp_core.product_categories_category_id_seq', (SELECT MAX(category_id) FROM erp_core.product_categories));
SELECT setval('erp_core.products_product_id_seq', (SELECT MAX(product_id) FROM erp_core.products));
SELECT setval('erp_sales.price_lists_price_list_id_seq', (SELECT MAX(price_list_id) FROM erp_sales.price_lists));
SELECT setval('erp_sales.promotions_promotion_id_seq', (SELECT MAX(promotion_id) FROM erp_sales.promotions));
