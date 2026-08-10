\echo 'Running mock ERP business-rule tests...'

BEGIN;

DO $$
DECLARE
    v_order_id INTEGER;
    v_order_line_id INTEGER;
    v_invoice_id INTEGER;
    v_before_available NUMERIC;
    v_after_available NUMERIC;
    v_order_status TEXT;
    v_invoice_amount NUMERIC;
BEGIN
    v_before_available := erp_inventory.available_qty(1, 1);

    v_order_id := erp_sales.create_sales_order(1, 2, 1, DATE '2026-08-10');
    v_order_line_id := erp_sales.add_sales_order_line(v_order_id, 1, 1, 3, NULL, 0);

    PERFORM erp_sales.confirm_order(v_order_id);

    SELECT order_status
    INTO STRICT v_order_status
    FROM erp_sales.sales_orders
    WHERE order_id = v_order_id;

    IF v_order_status <> 'confirmed' THEN
        RAISE EXCEPTION 'Expected order to be confirmed';
    END IF;

    SELECT erp_inventory.available_qty(1, 1)
    INTO v_after_available;

    IF v_after_available <> v_before_available - 3 THEN
        RAISE EXCEPTION 'Stock reservation did not reduce available quantity correctly. before=%, after=%',
            v_before_available, v_after_available;
    END IF;

    PERFORM erp_sales.fulfill_order(v_order_id, DATE '2026-08-11', 2);

    IF NOT EXISTS (
        SELECT 1
        FROM erp_logistics.shipments s
        JOIN erp_logistics.delivery_attempts da ON da.shipment_id = s.shipment_id
        WHERE s.order_id = v_order_id
          AND s.carrier_id = 2
          AND s.shipment_status = 'delivered'
          AND da.attempt_status = 'delivered'
    ) THEN
        RAISE EXCEPTION 'Expected fulfillment to create a delivered shipment and delivery attempt';
    END IF;

    v_invoice_id := erp_finance.create_invoice_from_order(v_order_id, DATE '2026-08-11', 15);

    SELECT net_amount
    INTO v_invoice_amount
    FROM erp_finance.invoices
    WHERE invoice_id = v_invoice_id;

    PERFORM erp_finance.record_payment(v_invoice_id, v_invoice_amount, 'card', DATE '2026-08-12');

    IF (
        SELECT invoice_status
        FROM erp_finance.invoices
        WHERE invoice_id = v_invoice_id
    ) <> 'paid' THEN
        RAISE EXCEPTION 'Invoice should be paid after full payment';
    END IF;

    PERFORM erp_sales.create_return(v_order_line_id, 1, 'damaged_package', DATE '2026-08-13');

    IF (
        SELECT COALESCE(SUM(quantity), 0)
        FROM erp_sales.returns
        WHERE order_line_id = v_order_line_id
    ) <> 1 THEN
        RAISE EXCEPTION 'Expected one returned unit for order line %', v_order_line_id;
    END IF;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
    v_order_line_id INTEGER;
    v_expected_price NUMERIC;
    v_actual_price NUMERIC;
    v_discount_amount NUMERIC;
BEGIN
    v_order_id := erp_sales.create_sales_order(1, 2, 1, DATE '2026-08-10');
    v_order_line_id := erp_sales.add_sales_order_line(v_order_id, 1, 1, 2, NULL, 0, 1);

    SELECT unit_price
    INTO v_expected_price
    FROM erp_sales.price_lists
    WHERE product_id = 1
      AND channel_id = 2
      AND DATE '2026-08-10' BETWEEN valid_from AND valid_to
    ORDER BY valid_from DESC, price_list_id DESC
    LIMIT 1;

    SELECT unit_price, discount_amount
    INTO v_actual_price, v_discount_amount
    FROM erp_sales.sales_order_lines
    WHERE order_line_id = v_order_line_id;

    IF v_actual_price <> v_expected_price THEN
        RAISE EXCEPTION 'Expected website price list to be applied. expected=%, actual=%',
            v_expected_price, v_actual_price;
    END IF;

    IF v_discount_amount <> ROUND(v_expected_price * 2 * 0.10, 2) THEN
        RAISE EXCEPTION 'Expected website tea promotion discount to be calculated';
    END IF;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
BEGIN
    v_order_id := erp_sales.create_sales_order(2, 1, 1, DATE '2026-08-10');

    BEGIN
        PERFORM erp_sales.add_sales_order_line(v_order_id, 1, 1, 2, NULL, 0, 1);
        RAISE EXCEPTION 'Expected wrong-channel promotion to be blocked';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE 'Promotion % is not valid for channel %' THEN
                RAISE;
            END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
    v_shipment_id INTEGER;
BEGIN
    v_order_id := erp_sales.create_sales_order(2, 2, 1, DATE '2026-08-10');
    PERFORM erp_sales.add_sales_order_line(v_order_id, 2, 1, 2, NULL, 0);
    PERFORM erp_sales.confirm_order(v_order_id);
    PERFORM erp_sales.fulfill_order(v_order_id, DATE '2026-08-11', 4);

    SELECT shipment_id
    INTO STRICT v_shipment_id
    FROM erp_logistics.shipments
    WHERE order_id = v_order_id;

    BEGIN
        PERFORM erp_logistics.record_delivery_attempt(
            v_shipment_id,
            DATE '2026-08-10',
            'failed',
            'customer_not_available',
            0
        );
        RAISE EXCEPTION 'Expected delivery attempt before planned ship date to be blocked';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE 'Delivery attempt date cannot be before planned ship date%' THEN
                RAISE;
            END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
BEGIN
    v_order_id := erp_sales.create_sales_order(1, 2, 1, DATE '2026-08-10');
    PERFORM erp_sales.add_sales_order_line(v_order_id, 1, 1, 100000, NULL, 0);

    BEGIN
        PERFORM erp_sales.confirm_order(v_order_id);
        RAISE EXCEPTION 'Expected insufficient stock to block order confirmation';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE 'Insufficient stock%' THEN
                RAISE;
            END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
    v_invoice_id INTEGER;
    v_invoice_amount NUMERIC;
BEGIN
    v_order_id := erp_sales.create_sales_order(2, 1, 1, DATE '2026-08-10');
    PERFORM erp_sales.add_sales_order_line(v_order_id, 2, 1, 2, NULL, 0);
    PERFORM erp_sales.confirm_order(v_order_id);
    v_invoice_id := erp_finance.create_invoice_from_order(v_order_id, DATE '2026-08-10', 15);

    SELECT net_amount
    INTO v_invoice_amount
    FROM erp_finance.invoices
    WHERE invoice_id = v_invoice_id;

    BEGIN
        PERFORM erp_finance.record_payment(v_invoice_id, v_invoice_amount + 1, 'cash', DATE '2026-08-11');
        RAISE EXCEPTION 'Expected overpayment to be blocked';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE 'Payment exceeds outstanding amount%' THEN
                RAISE;
            END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_order_id INTEGER;
    v_order_line_id INTEGER;
BEGIN
    v_order_id := erp_sales.create_sales_order(2, 1, 1, DATE '2026-08-10');
    v_order_line_id := erp_sales.add_sales_order_line(v_order_id, 3, 1, 2, NULL, 0);
    PERFORM erp_sales.confirm_order(v_order_id);
    PERFORM erp_sales.fulfill_order(v_order_id, DATE '2026-08-11');

    BEGIN
        PERFORM erp_sales.create_return(v_order_line_id, 3, 'too_many_items', DATE '2026-08-12');
        RAISE EXCEPTION 'Expected excessive return quantity to be blocked';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE 'Return quantity exceeds sold quantity%' THEN
                RAISE;
            END IF;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO erp_inventory.stock_lots (
            product_id,
            warehouse_id,
            lot_number,
            manufacturing_date,
            expiration_date,
            quantity_on_hand
        )
        VALUES (
            1,
            1,
            'BAD-EXPIRATION-LOT',
            DATE '2026-08-10',
            DATE '2026-08-09',
            10
        );

        RAISE EXCEPTION 'Expected invalid FMCG expiration date to be blocked';
    EXCEPTION
        WHEN check_violation THEN
            NULL;
    END;
END;
$$;

ROLLBACK;

\echo 'Mock ERP business-rule tests passed.'
