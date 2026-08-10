CREATE OR REPLACE FUNCTION erp_core.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER set_companies_updated_at
BEFORE UPDATE ON erp_core.companies
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_branches_updated_at
BEFORE UPDATE ON erp_core.branches
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_warehouses_updated_at
BEFORE UPDATE ON erp_core.warehouses
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_customers_updated_at
BEFORE UPDATE ON erp_core.customers
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_products_updated_at
BEFORE UPDATE ON erp_core.products
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_sales_orders_updated_at
BEFORE UPDATE ON erp_sales.sales_orders
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_invoices_updated_at
BEFORE UPDATE ON erp_finance.invoices
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE TRIGGER set_shipments_updated_at
BEFORE UPDATE ON erp_logistics.shipments
FOR EACH ROW EXECUTE FUNCTION erp_core.set_updated_at();

CREATE OR REPLACE FUNCTION erp_inventory.available_qty(
    p_warehouse_id INTEGER,
    p_product_id INTEGER
)
RETURNS NUMERIC
LANGUAGE sql
AS $$
    SELECT on_hand_qty - reserved_qty
    FROM erp_inventory.stock_balances
    WHERE warehouse_id = p_warehouse_id
      AND product_id = p_product_id;
$$;

CREATE OR REPLACE FUNCTION erp_inventory.ensure_stock_balance(
    p_warehouse_id INTEGER,
    p_product_id INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO erp_inventory.stock_balances (
        warehouse_id,
        product_id,
        on_hand_qty,
        reserved_qty,
        reorder_point
    )
    VALUES (p_warehouse_id, p_product_id, 0, 0, 0)
    ON CONFLICT (warehouse_id, product_id) DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION erp_inventory.reserve_stock(
    p_warehouse_id INTEGER,
    p_product_id INTEGER,
    p_quantity NUMERIC,
    p_order_line_id INTEGER,
    p_reference_number TEXT,
    p_move_date DATE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_available_qty NUMERIC;
    v_standard_cost NUMERIC;
BEGIN
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Reservation quantity must be positive';
    END IF;

    SELECT on_hand_qty - reserved_qty
    INTO v_available_qty
    FROM erp_inventory.stock_balances
    WHERE warehouse_id = p_warehouse_id
      AND product_id = p_product_id
    FOR UPDATE;

    IF v_available_qty IS NULL THEN
        RAISE EXCEPTION 'No stock balance for warehouse %, product %', p_warehouse_id, p_product_id;
    END IF;

    IF v_available_qty < p_quantity THEN
        RAISE EXCEPTION 'Insufficient stock for product % in warehouse %. available=%, requested=%',
            p_product_id, p_warehouse_id, v_available_qty, p_quantity;
    END IF;

    UPDATE erp_inventory.stock_balances
    SET
        reserved_qty = reserved_qty + p_quantity,
        updated_at = now()
    WHERE warehouse_id = p_warehouse_id
      AND product_id = p_product_id;

    SELECT standard_cost
    INTO v_standard_cost
    FROM erp_core.products
    WHERE product_id = p_product_id;

    INSERT INTO erp_inventory.stock_moves (
        warehouse_id,
        product_id,
        order_line_id,
        move_type,
        move_date,
        quantity,
        unit_cost,
        move_value,
        reference_number
    )
    VALUES (
        p_warehouse_id,
        p_product_id,
        p_order_line_id,
        'sale_reservation',
        p_move_date,
        -p_quantity,
        v_standard_cost,
        -p_quantity * v_standard_cost,
        p_reference_number
    );
END;
$$;

CREATE OR REPLACE FUNCTION erp_inventory.deliver_reserved_stock(
    p_warehouse_id INTEGER,
    p_product_id INTEGER,
    p_quantity NUMERIC,
    p_order_line_id INTEGER,
    p_reference_number TEXT,
    p_move_date DATE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_standard_cost NUMERIC;
BEGIN
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Delivery quantity must be positive';
    END IF;

    UPDATE erp_inventory.stock_balances
    SET
        on_hand_qty = on_hand_qty - p_quantity,
        reserved_qty = reserved_qty - p_quantity,
        updated_at = now()
    WHERE warehouse_id = p_warehouse_id
      AND product_id = p_product_id
      AND reserved_qty >= p_quantity
      AND on_hand_qty >= p_quantity;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Cannot deliver stock. Reserved/on-hand quantity is not enough for product % in warehouse %',
            p_product_id, p_warehouse_id;
    END IF;

    SELECT standard_cost
    INTO v_standard_cost
    FROM erp_core.products
    WHERE product_id = p_product_id;

    INSERT INTO erp_inventory.stock_moves (
        warehouse_id,
        product_id,
        order_line_id,
        move_type,
        move_date,
        quantity,
        unit_cost,
        move_value,
        reference_number
    )
    VALUES (
        p_warehouse_id,
        p_product_id,
        p_order_line_id,
        'sale_delivery',
        p_move_date,
        -p_quantity,
        v_standard_cost,
        -p_quantity * v_standard_cost,
        p_reference_number
    );
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.recalculate_order_amounts(p_order_id INTEGER)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE erp_sales.sales_orders o
    SET
        gross_amount = totals.gross_amount,
        discount_amount = totals.discount_amount,
        net_amount = totals.net_amount,
        updated_at = now()
    FROM (
        SELECT
            order_id,
            COALESCE(SUM(gross_amount), 0) AS gross_amount,
            COALESCE(SUM(discount_amount), 0) AS discount_amount,
            COALESCE(SUM(net_amount), 0) AS net_amount
        FROM erp_sales.sales_order_lines
        WHERE order_id = p_order_id
        GROUP BY order_id
    ) totals
    WHERE o.order_id = totals.order_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.create_sales_order(
    p_customer_id INTEGER,
    p_channel_id INTEGER,
    p_branch_id INTEGER,
    p_order_date DATE DEFAULT CURRENT_DATE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INTEGER;
    v_company_id INTEGER;
BEGIN
    SELECT company_id
    INTO v_company_id
    FROM erp_core.branches
    WHERE branch_id = p_branch_id
      AND is_active = TRUE;

    IF v_company_id IS NULL THEN
        RAISE EXCEPTION 'Invalid or inactive branch %', p_branch_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM erp_core.customers
        WHERE customer_id = p_customer_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Invalid or inactive customer %', p_customer_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM erp_core.sales_channels
        WHERE channel_id = p_channel_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Invalid or inactive sales channel %', p_channel_id;
    END IF;

    INSERT INTO erp_sales.sales_orders (
        company_id,
        branch_id,
        customer_id,
        channel_id,
        order_number,
        order_date,
        order_status,
        currency
    )
    VALUES (
        v_company_id,
        p_branch_id,
        p_customer_id,
        p_channel_id,
        'SO-' || to_char(now(), 'YYYYMMDDHH24MISSMS') || '-' || nextval('erp_sales.sales_orders_order_id_seq'),
        p_order_date,
        'draft',
        'VND'
    )
    RETURNING order_id INTO v_order_id;

    RETURN v_order_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.add_sales_order_line(
    p_order_id INTEGER,
    p_product_id INTEGER,
    p_warehouse_id INTEGER,
    p_quantity NUMERIC,
    p_unit_price NUMERIC DEFAULT NULL,
    p_discount_amount NUMERIC DEFAULT 0,
    p_promotion_id INTEGER DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_status TEXT;
    v_order_channel_id INTEGER;
    v_order_date DATE;
    v_list_price NUMERIC;
    v_unit_price NUMERIC;
    v_standard_cost NUMERIC;
    v_discount_amount NUMERIC;
    v_gross_amount NUMERIC;
    v_net_amount NUMERIC;
    v_order_line_id INTEGER;
    v_promotion RECORD;
BEGIN
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Order line quantity must be positive';
    END IF;

    SELECT order_status, channel_id, order_date
    INTO v_order_status, v_order_channel_id, v_order_date
    FROM erp_sales.sales_orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_order_status IS NULL THEN
        RAISE EXCEPTION 'Order % does not exist', p_order_id;
    END IF;

    IF v_order_status <> 'draft' THEN
        RAISE EXCEPTION 'Cannot add lines to order % because status is %', p_order_id, v_order_status;
    END IF;

    SELECT p.list_price, p.standard_cost
    INTO v_list_price, v_standard_cost
    FROM erp_core.products p
    WHERE p.product_id = p_product_id
      AND p.is_active = TRUE;

    IF v_list_price IS NULL THEN
        RAISE EXCEPTION 'Invalid or inactive product %', p_product_id;
    END IF;

    IF p_unit_price IS NULL THEN
        SELECT pl.unit_price
        INTO v_unit_price
        FROM erp_sales.price_lists pl
        WHERE pl.product_id = p_product_id
          AND pl.channel_id = v_order_channel_id
          AND pl.is_active = TRUE
          AND v_order_date BETWEEN pl.valid_from AND pl.valid_to
        ORDER BY pl.valid_from DESC, pl.price_list_id DESC
        LIMIT 1;

        v_unit_price := COALESCE(v_unit_price, v_list_price);
    ELSE
        v_unit_price := p_unit_price;
    END IF;

    IF v_unit_price < 0 THEN
        RAISE EXCEPTION 'Unit price cannot be negative';
    END IF;

    v_gross_amount := p_quantity * v_unit_price;
    v_discount_amount := p_discount_amount;

    IF p_promotion_id IS NOT NULL THEN
        SELECT *
        INTO v_promotion
        FROM erp_sales.promotions
        WHERE promotion_id = p_promotion_id
          AND channel_id = v_order_channel_id
          AND is_active = TRUE
          AND v_order_date BETWEEN start_date AND end_date;

        IF v_promotion.promotion_id IS NULL THEN
            RAISE EXCEPTION 'Promotion % is not valid for channel % on %',
                p_promotion_id, v_order_channel_id, v_order_date;
        END IF;

        IF v_discount_amount = 0 THEN
            IF v_promotion.discount_type = 'percent' THEN
                v_discount_amount := ROUND(v_gross_amount * v_promotion.discount_value / 100, 2);
            ELSE
                v_discount_amount := LEAST(v_gross_amount, v_promotion.discount_value);
            END IF;
        END IF;
    END IF;

    IF v_discount_amount < 0 OR v_discount_amount > v_gross_amount THEN
        RAISE EXCEPTION 'Invalid discount %. Gross amount is %', v_discount_amount, v_gross_amount;
    END IF;

    v_net_amount := v_gross_amount - v_discount_amount;

    INSERT INTO erp_sales.sales_order_lines (
        order_id,
        product_id,
        warehouse_id,
        promotion_id,
        quantity,
        unit_price,
        discount_amount,
        gross_amount,
        net_amount,
        estimated_cost
    )
    VALUES (
        p_order_id,
        p_product_id,
        p_warehouse_id,
        p_promotion_id,
        p_quantity,
        v_unit_price,
        v_discount_amount,
        v_gross_amount,
        v_net_amount,
        p_quantity * v_standard_cost
    )
    RETURNING order_line_id INTO v_order_line_id;

    PERFORM erp_sales.recalculate_order_amounts(p_order_id);

    RETURN v_order_line_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.confirm_order(p_order_id INTEGER)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_order erp_sales.sales_orders%ROWTYPE;
    v_line RECORD;
BEGIN
    SELECT *
    INTO v_order
    FROM erp_sales.sales_orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_order.order_id IS NULL THEN
        RAISE EXCEPTION 'Order % does not exist', p_order_id;
    END IF;

    IF v_order.order_status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft orders can be confirmed. Order % is %', p_order_id, v_order.order_status;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM erp_sales.sales_order_lines WHERE order_id = p_order_id) THEN
        RAISE EXCEPTION 'Cannot confirm order % without order lines', p_order_id;
    END IF;

    FOR v_line IN
        SELECT *
        FROM erp_sales.sales_order_lines
        WHERE order_id = p_order_id
        ORDER BY order_line_id
    LOOP
        PERFORM erp_inventory.reserve_stock(
            v_line.warehouse_id,
            v_line.product_id,
            v_line.quantity,
            v_line.order_line_id,
            v_order.order_number,
            v_order.order_date
        );
    END LOOP;

    UPDATE erp_sales.sales_orders
    SET order_status = 'confirmed'
    WHERE order_id = p_order_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.fulfill_order(
    p_order_id INTEGER,
    p_fulfillment_date DATE DEFAULT CURRENT_DATE,
    p_carrier_id INTEGER DEFAULT 1
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_order erp_sales.sales_orders%ROWTYPE;
    v_line RECORD;
    v_carrier_service_level TEXT;
    v_primary_warehouse_id INTEGER;
    v_shipment_id INTEGER;
    v_shipping_fee NUMERIC;
BEGIN
    SELECT *
    INTO v_order
    FROM erp_sales.sales_orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_order.order_status <> 'confirmed' THEN
        RAISE EXCEPTION 'Only confirmed orders can be fulfilled. Order % is %', p_order_id, v_order.order_status;
    END IF;

    SELECT service_level
    INTO v_carrier_service_level
    FROM erp_core.carriers
    WHERE carrier_id = p_carrier_id
      AND is_active = TRUE;

    IF v_carrier_service_level IS NULL THEN
        RAISE EXCEPTION 'Invalid or inactive carrier %', p_carrier_id;
    END IF;

    SELECT MIN(warehouse_id)
    INTO v_primary_warehouse_id
    FROM erp_sales.sales_order_lines
    WHERE order_id = p_order_id;

    v_shipping_fee := CASE v_carrier_service_level
        WHEN 'same_day' THEN 45000
        WHEN 'express' THEN 35000
        WHEN 'b2b_freight' THEN 120000
        ELSE 25000
    END;

    FOR v_line IN
        SELECT *
        FROM erp_sales.sales_order_lines
        WHERE order_id = p_order_id
        ORDER BY order_line_id
    LOOP
        PERFORM erp_inventory.deliver_reserved_stock(
            v_line.warehouse_id,
            v_line.product_id,
            v_line.quantity,
            v_line.order_line_id,
            v_order.order_number,
            p_fulfillment_date
        );
    END LOOP;

    INSERT INTO erp_logistics.shipments (
        order_id,
        warehouse_id,
        carrier_id,
        shipment_number,
        planned_ship_date,
        actual_ship_date,
        planned_delivery_date,
        actual_delivery_date,
        shipment_status,
        shipping_fee
    )
    VALUES (
        p_order_id,
        v_primary_warehouse_id,
        p_carrier_id,
        'SHP-' || to_char(now(), 'YYYYMMDDHH24MISSMS') || '-' || nextval('erp_logistics.shipments_shipment_id_seq'),
        v_order.order_date + 1,
        p_fulfillment_date,
        v_order.order_date + CASE
            WHEN v_carrier_service_level = 'same_day' THEN 1
            WHEN v_carrier_service_level = 'express' THEN 2
            ELSE 3
        END,
        p_fulfillment_date + CASE
            WHEN v_carrier_service_level = 'same_day' THEN 0
            ELSE 1
        END,
        'delivered',
        v_shipping_fee
    )
    RETURNING shipment_id INTO v_shipment_id;

    INSERT INTO erp_logistics.delivery_attempts (
        shipment_id,
        attempt_number,
        attempt_date,
        attempt_status,
        cod_amount
    )
    VALUES (
        v_shipment_id,
        1,
        p_fulfillment_date + CASE
            WHEN v_carrier_service_level = 'same_day' THEN 0
            ELSE 1
        END,
        'delivered',
        0
    );

    UPDATE erp_sales.sales_orders
    SET order_status = 'fulfilled'
    WHERE order_id = p_order_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_logistics.record_delivery_attempt(
    p_shipment_id INTEGER,
    p_attempt_date DATE,
    p_attempt_status TEXT,
    p_failure_reason TEXT DEFAULT NULL,
    p_cod_amount NUMERIC DEFAULT 0
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_shipment erp_logistics.shipments%ROWTYPE;
    v_attempt_number INTEGER;
    v_attempt_id INTEGER;
BEGIN
    SELECT *
    INTO v_shipment
    FROM erp_logistics.shipments
    WHERE shipment_id = p_shipment_id
    FOR UPDATE;

    IF v_shipment.shipment_id IS NULL THEN
        RAISE EXCEPTION 'Shipment % does not exist', p_shipment_id;
    END IF;

    IF p_attempt_date < v_shipment.planned_ship_date THEN
        RAISE EXCEPTION 'Delivery attempt date cannot be before planned ship date';
    END IF;

    IF p_attempt_status NOT IN ('delivered', 'failed', 'rescheduled', 'returned') THEN
        RAISE EXCEPTION 'Invalid delivery attempt status %', p_attempt_status;
    END IF;

    IF p_cod_amount < 0 THEN
        RAISE EXCEPTION 'COD amount cannot be negative';
    END IF;

    SELECT COALESCE(MAX(attempt_number), 0) + 1
    INTO v_attempt_number
    FROM erp_logistics.delivery_attempts
    WHERE shipment_id = p_shipment_id;

    INSERT INTO erp_logistics.delivery_attempts (
        shipment_id,
        attempt_number,
        attempt_date,
        attempt_status,
        failure_reason,
        cod_amount
    )
    VALUES (
        p_shipment_id,
        v_attempt_number,
        p_attempt_date,
        p_attempt_status,
        p_failure_reason,
        p_cod_amount
    )
    RETURNING delivery_attempt_id INTO v_attempt_id;

    UPDATE erp_logistics.shipments
    SET
        shipment_status = CASE
            WHEN p_attempt_status = 'rescheduled' THEN 'in_transit'
            ELSE p_attempt_status
        END,
        actual_delivery_date = CASE
            WHEN p_attempt_status = 'delivered' THEN p_attempt_date
            ELSE actual_delivery_date
        END
    WHERE shipment_id = p_shipment_id;

    RETURN v_attempt_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_finance.create_invoice_from_order(
    p_order_id INTEGER,
    p_invoice_date DATE DEFAULT CURRENT_DATE,
    p_due_days INTEGER DEFAULT 15,
    p_tax_rate NUMERIC DEFAULT 0.08
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_order erp_sales.sales_orders%ROWTYPE;
    v_invoice_id INTEGER;
    v_tax_amount NUMERIC;
    v_line RECORD;
BEGIN
    SELECT *
    INTO v_order
    FROM erp_sales.sales_orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_order.order_status NOT IN ('confirmed', 'fulfilled') THEN
        RAISE EXCEPTION 'Only confirmed or fulfilled orders can be invoiced. Order % is %',
            p_order_id, v_order.order_status;
    END IF;

    IF EXISTS (SELECT 1 FROM erp_finance.invoices WHERE order_id = p_order_id) THEN
        RAISE EXCEPTION 'Order % already has an invoice', p_order_id;
    END IF;

    IF p_invoice_date < v_order.order_date THEN
        RAISE EXCEPTION 'Invoice date cannot be before order date';
    END IF;

    v_tax_amount := ROUND(v_order.net_amount * p_tax_rate, 2);

    INSERT INTO erp_finance.invoices (
        order_id,
        customer_id,
        invoice_number,
        invoice_date,
        due_date,
        invoice_status,
        gross_amount,
        tax_amount,
        discount_amount,
        net_amount
    )
    VALUES (
        p_order_id,
        v_order.customer_id,
        'INV-' || to_char(now(), 'YYYYMMDDHH24MISSMS') || '-' || nextval('erp_finance.invoices_invoice_id_seq'),
        p_invoice_date,
        p_invoice_date + p_due_days,
        'open',
        v_order.gross_amount,
        v_tax_amount,
        v_order.discount_amount,
        v_order.net_amount + v_tax_amount
    )
    RETURNING invoice_id INTO v_invoice_id;

    FOR v_line IN
        SELECT *
        FROM erp_sales.sales_order_lines
        WHERE order_id = p_order_id
        ORDER BY order_line_id
    LOOP
        INSERT INTO erp_finance.invoice_lines (
            invoice_id,
            order_line_id,
            product_id,
            quantity,
            unit_price,
            gross_amount,
            tax_amount,
            net_amount
        )
        VALUES (
            v_invoice_id,
            v_line.order_line_id,
            v_line.product_id,
            v_line.quantity,
            v_line.unit_price,
            v_line.gross_amount,
            ROUND(v_line.net_amount * p_tax_rate, 2),
            v_line.net_amount + ROUND(v_line.net_amount * p_tax_rate, 2)
        );
    END LOOP;

    UPDATE erp_sales.sales_orders
    SET order_status = 'invoiced'
    WHERE order_id = p_order_id;

    RETURN v_invoice_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_finance.record_payment(
    p_invoice_id INTEGER,
    p_amount_paid NUMERIC,
    p_payment_method TEXT,
    p_payment_date DATE DEFAULT CURRENT_DATE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_invoice erp_finance.invoices%ROWTYPE;
    v_payment_id INTEGER;
    v_outstanding_amount NUMERIC;
    v_new_paid_amount NUMERIC;
BEGIN
    IF p_amount_paid <= 0 THEN
        RAISE EXCEPTION 'Payment amount must be positive';
    END IF;

    SELECT *
    INTO v_invoice
    FROM erp_finance.invoices
    WHERE invoice_id = p_invoice_id
    FOR UPDATE;

    IF v_invoice.invoice_id IS NULL THEN
        RAISE EXCEPTION 'Invoice % does not exist', p_invoice_id;
    END IF;

    IF p_payment_date < v_invoice.invoice_date THEN
        RAISE EXCEPTION 'Payment date cannot be before invoice date';
    END IF;

    v_outstanding_amount := v_invoice.net_amount - v_invoice.amount_paid;

    IF p_amount_paid > v_outstanding_amount THEN
        RAISE EXCEPTION 'Payment exceeds outstanding amount. outstanding=%, requested=%',
            v_outstanding_amount, p_amount_paid;
    END IF;

    INSERT INTO erp_finance.payments (
        invoice_id,
        customer_id,
        payment_date,
        payment_method,
        payment_status,
        amount_paid,
        transaction_reference
    )
    VALUES (
        p_invoice_id,
        v_invoice.customer_id,
        p_payment_date,
        p_payment_method,
        'paid',
        p_amount_paid,
        'PAY-' || to_char(now(), 'YYYYMMDDHH24MISSMS') || '-' || nextval('erp_finance.payments_payment_id_seq')
    )
    RETURNING payment_id INTO v_payment_id;

    v_new_paid_amount := v_invoice.amount_paid + p_amount_paid;

    UPDATE erp_finance.invoices
    SET
        amount_paid = v_new_paid_amount,
        invoice_status = CASE
            WHEN v_new_paid_amount = net_amount THEN 'paid'
            WHEN v_new_paid_amount > 0 THEN 'partial'
            ELSE 'open'
        END
    WHERE invoice_id = p_invoice_id;

    UPDATE erp_sales.sales_orders
    SET order_status = 'paid'
    WHERE order_id = v_invoice.order_id
      AND v_new_paid_amount = v_invoice.net_amount;

    RETURN v_payment_id;
END;
$$;

CREATE OR REPLACE FUNCTION erp_sales.create_return(
    p_order_line_id INTEGER,
    p_quantity NUMERIC,
    p_return_reason TEXT,
    p_return_date DATE DEFAULT CURRENT_DATE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_line erp_sales.sales_order_lines%ROWTYPE;
    v_order erp_sales.sales_orders%ROWTYPE;
    v_previous_return_qty NUMERIC;
    v_return_id INTEGER;
    v_unit_refund NUMERIC;
BEGIN
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Return quantity must be positive';
    END IF;

    SELECT *
    INTO v_line
    FROM erp_sales.sales_order_lines
    WHERE order_line_id = p_order_line_id;

    IF v_line.order_line_id IS NULL THEN
        RAISE EXCEPTION 'Order line % does not exist', p_order_line_id;
    END IF;

    SELECT *
    INTO v_order
    FROM erp_sales.sales_orders
    WHERE order_id = v_line.order_id;

    IF v_order.order_status NOT IN ('fulfilled', 'invoiced', 'paid') THEN
        RAISE EXCEPTION 'Returns are only allowed for fulfilled, invoiced, or paid orders. Order % is %',
            v_order.order_id, v_order.order_status;
    END IF;

    IF p_return_date < v_order.order_date THEN
        RAISE EXCEPTION 'Return date cannot be before order date';
    END IF;

    SELECT COALESCE(SUM(quantity), 0)
    INTO v_previous_return_qty
    FROM erp_sales.returns
    WHERE order_line_id = p_order_line_id
      AND return_status IN ('approved', 'refunded');

    IF p_quantity > v_line.quantity - v_previous_return_qty THEN
        RAISE EXCEPTION 'Return quantity exceeds sold quantity. sold=%, already_returned=%, requested=%',
            v_line.quantity, v_previous_return_qty, p_quantity;
    END IF;

    v_unit_refund := v_line.net_amount / v_line.quantity;

    INSERT INTO erp_sales.returns (
        order_id,
        order_line_id,
        customer_id,
        product_id,
        return_date,
        return_reason,
        quantity,
        refund_amount,
        return_status
    )
    VALUES (
        v_order.order_id,
        v_line.order_line_id,
        v_order.customer_id,
        v_line.product_id,
        p_return_date,
        p_return_reason,
        p_quantity,
        ROUND(v_unit_refund * p_quantity, 2),
        'approved'
    )
    RETURNING return_id INTO v_return_id;

    UPDATE erp_inventory.stock_balances
    SET
        on_hand_qty = on_hand_qty + p_quantity,
        updated_at = now()
    WHERE warehouse_id = v_line.warehouse_id
      AND product_id = v_line.product_id;

    INSERT INTO erp_inventory.stock_moves (
        warehouse_id,
        product_id,
        order_line_id,
        move_type,
        move_date,
        quantity,
        unit_cost,
        move_value,
        reference_number
    )
    SELECT
        v_line.warehouse_id,
        v_line.product_id,
        v_line.order_line_id,
        'return_receipt',
        p_return_date,
        p_quantity,
        p.standard_cost,
        p_quantity * p.standard_cost,
        'RET-' || v_return_id
    FROM erp_core.products p
    WHERE p.product_id = v_line.product_id;

    RETURN v_return_id;
END;
$$;
