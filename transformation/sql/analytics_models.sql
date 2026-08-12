CREATE SCHEMA IF NOT EXISTS analytics;

DROP TABLE IF EXISTS analytics.mart_logistics_performance;
DROP TABLE IF EXISTS analytics.mart_inventory_alerts;
DROP TABLE IF EXISTS analytics.mart_top_products;
DROP TABLE IF EXISTS analytics.mart_sales_by_channel;
DROP TABLE IF EXISTS analytics.mart_daily_sales;
DROP TABLE IF EXISTS analytics.mart_customer_rfm;
DROP TABLE IF EXISTS analytics.mart_dashboard_kpis;
DROP TABLE IF EXISTS analytics.fact_payments;
DROP TABLE IF EXISTS analytics.fact_logistics_shipments;
DROP TABLE IF EXISTS analytics.fact_inventory_balance;
DROP TABLE IF EXISTS analytics.fact_sales_order_lines;
DROP TABLE IF EXISTS analytics.dim_carrier;
DROP TABLE IF EXISTS analytics.dim_warehouse;
DROP TABLE IF EXISTS analytics.dim_channel;
DROP TABLE IF EXISTS analytics.dim_product;
DROP TABLE IF EXISTS analytics.dim_customer;
DROP TABLE IF EXISTS analytics.dim_date;

CREATE TABLE analytics.dim_date AS
WITH date_range AS (
    SELECT generate_series(
        (SELECT MIN(order_date) FROM erp_sales.sales_orders),
        GREATEST(
            (SELECT MAX(order_date) FROM erp_sales.sales_orders),
            CURRENT_DATE
        ),
        INTERVAL '1 day'
    )::DATE AS date_key
)
SELECT
    date_key,
    EXTRACT(YEAR FROM date_key)::INTEGER AS year,
    EXTRACT(QUARTER FROM date_key)::INTEGER AS quarter,
    EXTRACT(MONTH FROM date_key)::INTEGER AS month,
    TO_CHAR(date_key, 'Mon') AS month_name,
    EXTRACT(DAY FROM date_key)::INTEGER AS day_of_month,
    EXTRACT(ISODOW FROM date_key)::INTEGER AS iso_day_of_week,
    TO_CHAR(date_key, 'Dy') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM date_key) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_range;

CREATE TABLE analytics.dim_customer AS
SELECT
    c.customer_id AS customer_key,
    c.customer_code,
    c.customer_name,
    c.customer_type,
    c.city,
    c.region,
    cs.segment_code,
    cs.segment_name,
    c.is_active
FROM erp_core.customers c
LEFT JOIN erp_core.customer_segments cs ON cs.segment_id = c.segment_id;

CREATE TABLE analytics.dim_product AS
SELECT
    p.product_id AS product_key,
    p.sku,
    p.product_name,
    p.brand,
    p.unit_of_measure,
    p.standard_cost,
    p.list_price,
    p.shelf_life_days,
    c.category_code,
    c.category_name,
    pc.category_code AS parent_category_code,
    pc.category_name AS parent_category_name,
    p.is_active
FROM erp_core.products p
LEFT JOIN erp_core.product_categories c ON c.category_id = p.category_id
LEFT JOIN erp_core.product_categories pc ON pc.category_id = c.parent_category_id;

CREATE TABLE analytics.dim_channel AS
SELECT
    channel_id AS channel_key,
    channel_code,
    channel_name,
    channel_type,
    is_active
FROM erp_core.sales_channels;

CREATE TABLE analytics.dim_warehouse AS
SELECT
    w.warehouse_id AS warehouse_key,
    w.warehouse_code,
    w.warehouse_name,
    w.city,
    b.branch_code,
    b.branch_name,
    b.region
FROM erp_core.warehouses w
LEFT JOIN erp_core.branches b ON b.branch_id = w.branch_id;

CREATE TABLE analytics.dim_carrier AS
SELECT
    carrier_id AS carrier_key,
    carrier_code,
    carrier_name,
    service_level,
    is_active
FROM erp_core.carriers;

CREATE TABLE analytics.fact_sales_order_lines AS
SELECT
    sol.order_line_id AS sales_order_line_key,
    so.order_id AS sales_order_key,
    so.order_number,
    so.order_date AS date_key,
    so.order_status,
    so.customer_id AS customer_key,
    so.channel_id AS channel_key,
    so.branch_id,
    sol.product_id AS product_key,
    sol.warehouse_id AS warehouse_key,
    sol.promotion_id,
    promo.promotion_code,
    sol.quantity,
    sol.unit_price,
    sol.gross_amount,
    sol.discount_amount,
    sol.net_amount,
    sol.estimated_cost,
    sol.net_amount - sol.estimated_cost AS gross_margin_amount,
    CASE
        WHEN sol.net_amount = 0 THEN 0
        ELSE ROUND((sol.net_amount - sol.estimated_cost) / sol.net_amount, 4)
    END AS gross_margin_rate
FROM erp_sales.sales_order_lines sol
JOIN erp_sales.sales_orders so ON so.order_id = sol.order_id
LEFT JOIN erp_sales.promotions promo ON promo.promotion_id = sol.promotion_id;

CREATE TABLE analytics.fact_inventory_balance AS
SELECT
    sb.warehouse_id AS warehouse_key,
    sb.product_id AS product_key,
    CURRENT_DATE AS snapshot_date,
    sb.on_hand_qty,
    sb.reserved_qty,
    sb.on_hand_qty - sb.reserved_qty AS available_qty,
    sb.reorder_point,
    CASE
        WHEN sb.on_hand_qty - sb.reserved_qty <= 0 THEN 'OUT_OF_STOCK'
        WHEN sb.on_hand_qty - sb.reserved_qty <= sb.reorder_point THEN 'REORDER'
        ELSE 'HEALTHY'
    END AS stock_status,
    COALESCE(sales_14d.quantity_sold_14d, 0) AS quantity_sold_14d,
    ROUND(COALESCE(sales_14d.quantity_sold_14d, 0) / 14.0, 3) AS avg_daily_sales_14d,
    CASE
        WHEN COALESCE(sales_14d.quantity_sold_14d, 0) = 0 THEN NULL
        ELSE ROUND((sb.on_hand_qty - sb.reserved_qty) / (sales_14d.quantity_sold_14d / 14.0), 2)
    END AS days_of_inventory
FROM erp_inventory.stock_balances sb
LEFT JOIN (
    SELECT
        product_key,
        warehouse_key,
        SUM(quantity) AS quantity_sold_14d
    FROM analytics.fact_sales_order_lines
    WHERE date_key >= (SELECT MAX(date_key) - 13 FROM analytics.fact_sales_order_lines)
    GROUP BY product_key, warehouse_key
) sales_14d
    ON sales_14d.product_key = sb.product_id
   AND sales_14d.warehouse_key = sb.warehouse_id;

CREATE TABLE analytics.fact_logistics_shipments AS
SELECT
    s.shipment_id AS shipment_key,
    s.order_id AS sales_order_key,
    so.order_number,
    so.order_date,
    s.warehouse_id AS warehouse_key,
    s.carrier_id AS carrier_key,
    s.planned_ship_date,
    s.actual_ship_date,
    s.planned_delivery_date,
    s.actual_delivery_date,
    s.shipment_status,
    s.shipping_fee,
    s.actual_ship_date - so.order_date AS fulfillment_lead_days,
    s.actual_delivery_date - so.order_date AS delivery_lead_days,
    CASE
        WHEN s.actual_delivery_date IS NULL THEN FALSE
        WHEN s.actual_delivery_date <= s.planned_delivery_date THEN TRUE
        ELSE FALSE
    END AS is_on_time_delivery
FROM erp_logistics.shipments s
JOIN erp_sales.sales_orders so ON so.order_id = s.order_id;

CREATE TABLE analytics.fact_payments AS
SELECT
    p.payment_id AS payment_key,
    p.invoice_id AS invoice_key,
    i.order_id AS sales_order_key,
    p.customer_id AS customer_key,
    p.payment_date AS date_key,
    p.payment_method,
    p.payment_status,
    p.amount_paid
FROM erp_finance.payments p
JOIN erp_finance.invoices i ON i.invoice_id = p.invoice_id;

CREATE TABLE analytics.mart_dashboard_kpis AS
SELECT
    COUNT(DISTINCT sales_order_key) AS total_orders,
    COALESCE(SUM(net_amount), 0) AS net_revenue,
    COALESCE(SUM(gross_margin_amount), 0) AS gross_margin,
    CASE
        WHEN COALESCE(SUM(net_amount), 0) = 0 THEN 0
        ELSE ROUND(SUM(gross_margin_amount) / SUM(net_amount), 4)
    END AS gross_margin_rate,
    COALESCE(AVG(net_amount), 0) AS avg_order_line_value,
    COALESCE(SUM(quantity), 0) AS units_sold
FROM analytics.fact_sales_order_lines;

CREATE TABLE analytics.mart_daily_sales AS
SELECT
    date_key,
    COUNT(DISTINCT sales_order_key) AS orders,
    SUM(net_amount) AS net_revenue,
    SUM(quantity) AS units_sold,
    SUM(gross_margin_amount) AS gross_margin
FROM analytics.fact_sales_order_lines
GROUP BY date_key
ORDER BY date_key;

CREATE TABLE analytics.mart_sales_by_channel AS
SELECT
    ch.channel_code,
    ch.channel_name,
    ch.channel_type,
    COUNT(DISTINCT f.sales_order_key) AS orders,
    SUM(f.net_amount) AS net_revenue,
    SUM(f.quantity) AS units_sold,
    SUM(f.gross_margin_amount) AS gross_margin
FROM analytics.fact_sales_order_lines f
JOIN analytics.dim_channel ch ON ch.channel_key = f.channel_key
GROUP BY ch.channel_code, ch.channel_name, ch.channel_type
ORDER BY net_revenue DESC;

CREATE TABLE analytics.mart_top_products AS
SELECT
    p.sku,
    p.product_name,
    p.category_name,
    SUM(f.quantity) AS units_sold,
    SUM(f.net_amount) AS net_revenue,
    SUM(f.gross_margin_amount) AS gross_margin
FROM analytics.fact_sales_order_lines f
JOIN analytics.dim_product p ON p.product_key = f.product_key
GROUP BY p.sku, p.product_name, p.category_name
ORDER BY net_revenue DESC;

CREATE TABLE analytics.mart_inventory_alerts AS
SELECT
    w.warehouse_code,
    w.warehouse_name,
    p.sku,
    p.product_name,
    f.available_qty,
    f.reorder_point,
    f.avg_daily_sales_14d,
    f.days_of_inventory,
    f.stock_status,
    CASE
        WHEN p.shelf_life_days <= 180 THEN 'SHORT_SHELF_LIFE'
        ELSE 'NORMAL'
    END AS shelf_life_status
FROM analytics.fact_inventory_balance f
JOIN analytics.dim_warehouse w ON w.warehouse_key = f.warehouse_key
JOIN analytics.dim_product p ON p.product_key = f.product_key
ORDER BY
    CASE f.stock_status
        WHEN 'OUT_OF_STOCK' THEN 1
        WHEN 'REORDER' THEN 2
        ELSE 3
    END,
    f.available_qty ASC;

CREATE TABLE analytics.mart_logistics_performance AS
SELECT
    c.carrier_code,
    c.carrier_name,
    c.service_level,
    COUNT(*) AS shipments,
    ROUND(AVG(fulfillment_lead_days), 2) AS avg_fulfillment_lead_days,
    ROUND(AVG(delivery_lead_days), 2) AS avg_delivery_lead_days,
    ROUND(AVG(CASE WHEN is_on_time_delivery THEN 1 ELSE 0 END), 4) AS on_time_delivery_rate,
    SUM(shipping_fee) AS shipping_fee
FROM analytics.fact_logistics_shipments f
JOIN analytics.dim_carrier c ON c.carrier_key = f.carrier_key
GROUP BY c.carrier_code, c.carrier_name, c.service_level
ORDER BY shipments DESC;

CREATE TABLE analytics.mart_customer_rfm AS
SELECT
    c.customer_code,
    c.customer_name,
    c.segment_name,
    MAX(f.date_key) AS last_order_date,
    CURRENT_DATE - MAX(f.date_key) AS recency_days,
    COUNT(DISTINCT f.sales_order_key) AS frequency_orders,
    SUM(f.net_amount) AS monetary_value,
    CASE
        WHEN CURRENT_DATE - MAX(f.date_key) > 45 THEN 'AT_RISK'
        WHEN COUNT(DISTINCT f.sales_order_key) >= 5 THEN 'LOYAL'
        ELSE 'ACTIVE'
    END AS customer_status
FROM analytics.fact_sales_order_lines f
JOIN analytics.dim_customer c ON c.customer_key = f.customer_key
GROUP BY c.customer_code, c.customer_name, c.segment_name
ORDER BY monetary_value DESC;
