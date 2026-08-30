# Multi-Source Mapping Matrix

## 1. Mục tiêu và phạm vi

Tài liệu này định nghĩa cách chuyển dữ liệu từ các nguồn nghiệp vụ về sáu
contract Canonical Silver phiên bản `1.0.0`: `order`, `order_line`,
`inventory`, `shipment`, `return` và `payment`.

Nguồn máy đọc của ma trận nằm tại
`contracts/mappings/source_mapping_matrix.yaml`. File đó là nguồn kiểm thử độ
phủ field và enum; tài liệu này giải thích cách developer áp dụng mapping.

### 1.1 Mức độ cam kết

| Nguồn | `source_system` | Trạng thái | Ý nghĩa |
|---|---|---|---|
| Mock ERP PostgreSQL | `postgres_erp` | `implemented` | Table và column đã tồn tại trong repository; mapping có thể triển khai ngay. |
| Odoo | `odoo` | `contract_only` | Tên model chuẩn được đề xuất; phải xác minh field/module trên instance Odoo trước khi code adapter. |
| Mock OMS | `oms` | `contract_only` | Logical JSON paths dành cho BL-021; chưa có API thực tế. |
| Mock WMS | `wms` | `contract_only` | Logical JSON paths dành cho BL-022; chưa có API thực tế. |
| Mock OPS | `ops` | `contract_only` | Logical JSON paths dành cho BL-023; chưa có API thực tế. |
| MongoDB Catalog | `mongodb_catalog` | `contract_only` | Logical document paths dành cho BL-024; chủ yếu bổ sung product/lot metadata. |
| External API | `external_api` | `contract_only` | Logical JSON paths dành cho BL-025; adapter cụ thể phải khai báo provider. |

`contract_only` không được hiểu là connector đã hoạt động. Khi source thật được
tạo, adapter phải cập nhật ma trận với schema/version thực tế và contract test.

## 2. Quy tắc chung

### 2.1 Metadata envelope

| Canonical field | Quy tắc |
|---|---|
| `business_key` | Tạo sau khi chuẩn hóa source key, theo bảng ở mục 3. Không lấy trực tiếp một key không được kiểm soát từ source. |
| `source_key` | Ép khóa ổn định của source thành string; không dùng row number hoặc ingestion offset. |
| `source_system` | Dùng đúng giá trị trong bảng mức độ cam kết. |
| `event_time` | Thời điểm record thay đổi tại source; chuyển sang UTC ISO-8601 có hậu tố `Z`. Không có timestamp thì quarantine, không thay bằng thời gian hiện tại. |
| `ingestion_time` | UTC timestamp do ingestion ghi khi nhận record. |
| `schema_version` | `1.0.0`. |
| `processing_status` | `VALID`, `WARNING` hoặc `QUARANTINED` từ validation engine. |
| `payload` | Object sau mapping, chỉ chứa field được canonical schema cho phép. |

### 2.2 Chuyển đổi kiểu và null

- Timestamp: parse timezone của source, chuyển UTC và serialize
  `YYYY-MM-DDTHH:mm:ssZ`. Timestamp không có timezone phải dùng timezone được
  cấu hình cho source; không tự đoán.
- Date: serialize `YYYY-MM-DD` và không dịch ngày theo timezone sau khi đã xác
  định business date.
- Amount: parse bằng decimal, scale tối đa 4 chữ số; không qua binary float.
- Quantity: parse decimal, scale tối đa 3 chữ số.
- Currency và enum: trim rồi uppercase trước khi map.
- Optional field không có dữ liệu ghi `null`; không dùng chuỗi rỗng,
  `"N/A"` hoặc `"null"`.
- Required field thiếu, parse thất bại hoặc enum không được biết phải đi
  quarantine cùng source key và mã lỗi. Không âm thầm gán default.
- Field ngoài contract được giữ ở Bronze nhưng không đi vào payload Silver.

### 2.3 Grain và deduplication

| Entity | Grain canonical | Deduplication key |
|---|---|---|
| Order | Một order header | `business_key` + newest `event_time` |
| Order line | Một line trong order | `business_key` + newest `event_time` |
| Inventory | Một warehouse + SKU; lot chỉ enrichment trong v1 | `business_key` + newest `event_time` |
| Shipment | Một tracking number | `business_key` + newest `event_time` |
| Return | Một return request/record | `business_key` + newest `event_time` |
| Payment | Một transaction reference | `business_key` + newest `event_time` |

Inventory v1 có key `warehouse + SKU`, vì vậy nhiều lot không được phát thành
nhiều record có cùng key. Adapter phải tổng hợp balance và chỉ gắn lot khi có
một lot xác định; phân tích inventory theo lot sẽ cần contract version mới.

## 3. Business key theo entity và nguồn

`SOURCE` là `source_system.upper()`, giữ underscore. Các thành phần phải trim,
không rỗng và giữ nguyên chữ/số/dấu phân cách nghiệp vụ của source.

| Entity | Template | Ví dụ |
|---|---|---|
| Order | `ORD-{SOURCE}-{source_key}` | `ORD-POSTGRES_ERP-SO-1001` |
| Order line | `ORDL-{SOURCE}-{source_order_key}-{source_line_key}` | `ORDL-OMS-10045-1` |
| Inventory | `INV-{SOURCE}-{warehouse_code}-{sku}` | `INV-WMS-WH01-SKU8839` |
| Shipment | `SHP-{SOURCE}-{tracking_number}` | `SHP-OPS-GHN99281` |
| Return | `RET-{SOURCE}-{source_key}` | `RET-OMS-RET0012` |
| Payment | `PAY-{SOURCE}-{transaction_reference}` | `PAY-EXTERNAL_API-PAYPAL9981` |

Nếu source không có tracking number hoặc transaction reference ổn định thì
record bị quarantine; không dùng timestamp ngẫu nhiên để tạo key.

## 4. Source ownership và routing

| Entity | Nguồn sở hữu/được phép phát | Nguồn enrichment hoặc prospective | Nguồn không áp dụng |
|---|---|---|---|
| Order | PostgreSQL, Odoo, OMS | External API/marketplace | WMS, OPS, MongoDB Catalog |
| Order line | PostgreSQL, Odoo, OMS | External API/marketplace | WMS, OPS, MongoDB Catalog |
| Inventory | PostgreSQL, Odoo, WMS | MongoDB Catalog enrichment | OMS, OPS, External payment API |
| Shipment | PostgreSQL, Odoo, OPS | Carrier External API | OMS, WMS, MongoDB Catalog |
| Return | PostgreSQL, Odoo, OMS | OPS và External API enrichment | WMS, MongoDB Catalog |
| Payment | PostgreSQL, Odoo, OMS | Payment External API | WMS, OPS, MongoDB Catalog |

Một source “không áp dụng” không cần tạo record rỗng cho entity đó.

## 5. Mapping triển khai: Mock ERP PostgreSQL

Các bảng được join bằng foreign-key logical trong
`data_source/mock_erp_pg/init/02_tables.sql`. Dù constraint hiện bị tắt, adapter
phải xử lý thiếu lookup như lỗi referential integrity.

### 5.1 Order

Base table: `erp_sales.sales_orders`.

| Canonical payload | Source/expression | Null |
|---|---|---|
| `order_key` | `sales_orders.order_number` | Không |
| `customer_key` | `customers.customer_code` | Không |
| `company_code` | `companies.company_code` | Optional |
| `branch_code` | `branches.branch_code` | Optional |
| `channel_code` | `sales_channels.channel_code` | Không |
| `order_date` | `sales_orders.order_date` | Không |
| `order_status` | enum map mục 6 | Không |
| `currency` | `upper(sales_orders.currency)` | Không |
| `gross_amount` | `sales_orders.gross_amount` | Không |
| `discount_amount` | `sales_orders.discount_amount` | Không |
| `tax_amount` | `0` vì source order chưa có tax | Optional |
| `shipping_amount` | tổng `shipments.shipping_fee`, mặc định `0` | Optional |
| `net_amount` | `sales_orders.net_amount` | Không |
| `created_at` | `utc(sales_orders.created_at)` | Không |
| `updated_at` | `utc(sales_orders.updated_at)` | Không |

Envelope dùng `source_key = order_number`, `event_time = updated_at`.

### 5.2 Order line

Base table: `erp_sales.sales_order_lines`; join order, product, warehouse,
promotion và lot (nếu đã có allocation xác định).

| Canonical payload | Source/expression | Null |
|---|---|---|
| `order_line_key` | `string(order_line_id)` | Không |
| `order_key` | `sales_orders.order_number` | Không |
| `product_key` | `string(product_id)` | Không |
| `sku` | `products.sku` | Không |
| `warehouse_code` | `warehouses.warehouse_code` | Không |
| `promotion_code` | `promotions.promotion_code` | Có |
| `lot_number` | allocated `stock_lots.lot_number` | Có |
| `expiration_date` | allocated `stock_lots.expiration_date` | Có |
| `ordered_qty` | `quantity` | Không |
| `unit_price_amount` | `unit_price` | Không |
| `discount_amount` | `discount_amount` | Không |
| `gross_amount` | `gross_amount` | Không |
| `net_amount` | `net_amount` | Không |
| `estimated_cost_amount` | `estimated_cost` | Optional |
| `currency` | order `currency` | Không |

Envelope dùng `source_key = order_line_id`, `event_time = order.updated_at`.
Không gắn lot bằng cách chọn tùy ý khi có nhiều lot phù hợp.

### 5.3 Inventory

Base table: `erp_inventory.stock_balances`; join warehouse, product và lot.

| Canonical payload | Source/expression | Null |
|---|---|---|
| `inventory_key` | `warehouse_code || ':' || sku` | Không |
| `warehouse_code` | `warehouses.warehouse_code` | Không |
| `location_code` | `null`; source chưa có location | Có |
| `product_key` | `string(product_id)` | Không |
| `sku` | `products.sku` | Không |
| `lot_number` | lot duy nhất/xác định, nếu có | Có |
| `manufacturing_date` | lot tương ứng | Có |
| `expiration_date` | lot tương ứng | Có |
| `on_hand_qty` | `stock_balances.on_hand_qty` | Không |
| `reserved_qty` | `stock_balances.reserved_qty` | Không |
| `available_qty` | `on_hand_qty - reserved_qty` | Không |
| `reorder_point_qty` | `stock_balances.reorder_point` | Optional |
| `updated_at` | `utc(stock_balances.updated_at)` | Không |

Envelope `source_key` giống `inventory_key`; `event_time = updated_at`.

### 5.4 Shipment

Base table: `erp_logistics.shipments`; join order, warehouse và carrier.

| Canonical payload | Source/expression |
|---|---|
| `shipment_key`, `tracking_number` | `shipments.shipment_number` |
| `order_key` | `sales_orders.order_number` |
| `warehouse_code` | `warehouses.warehouse_code` |
| `carrier_code` | `carriers.carrier_code` |
| planned/actual dates | các column cùng tên trong `shipments` |
| `shipment_status` | enum map mục 6 |
| `shipping_amount` | `shipments.shipping_fee` |
| `currency` | order `currency` |
| `created_at`, `updated_at` | timestamp tương ứng, đổi UTC |

Envelope dùng `source_key = shipment_number`, `event_time = updated_at`.

### 5.5 Return

Base table: `erp_sales.returns`; join order, order line, customer và product.

| Canonical payload | Source/expression |
|---|---|
| `return_key` | `string(return_id)` |
| `order_key` | `sales_orders.order_number` |
| `order_line_key` | `string(returns.order_line_id)` |
| `customer_key` | `customers.customer_code` |
| `product_key` | `string(returns.product_id)` |
| `sku` | `products.sku` |
| `return_date`, `return_reason` | column cùng tên |
| `returned_qty` | `returns.quantity` |
| `refund_amount` | `returns.refund_amount` |
| `currency` | order `currency` |
| `return_status` | enum map mục 6 |
| `created_at` | đổi UTC |

Envelope dùng `source_key = return_id`, `event_time = created_at`.

### 5.6 Payment

Base table: `erp_finance.payments`; join invoice, order và customer.

| Canonical payload | Source/expression |
|---|---|
| `payment_key`, `transaction_reference` | `payments.transaction_reference` |
| `invoice_key` | `invoices.invoice_number` |
| `order_key` | `sales_orders.order_number` |
| `customer_key` | `customers.customer_code` |
| `payment_date` | `payments.payment_date` |
| `payment_method`, `payment_status` | enum map mục 6 |
| `paid_amount` | `payments.amount_paid` |
| `currency` | order `currency` |
| `created_at` | đổi UTC |

Envelope dùng `source_key = transaction_reference`, `event_time = created_at`.

## 6. Enum mapping triển khai

| Entity.field | Source value | Canonical value |
|---|---|---|
| order.status | `draft`, `confirmed`, `fulfilled`, `invoiced`, `paid`, `cancelled` | cùng nghĩa, uppercase |
| shipment.status | `planned`, `in_transit`, `delivered`, `failed`, `returned`, `cancelled` | cùng nghĩa, uppercase |
| return.status | `approved`, `refunded`, `rejected` | cùng nghĩa, uppercase |
| payment.method | `bank_transfer`, `cash`, `card`, `e_wallet` | cùng nghĩa, uppercase |
| payment.status | `paid`, `reversed` | cùng nghĩa, uppercase |

Enum mới không được tự động uppercase rồi cho qua. Nó phải được thêm vào mapping
và canonical schema theo Schema Evolution Policy, hoặc record đi quarantine.

## 7. Mapping contract-level cho nguồn tương lai

Các path dưới đây là interface mà backlog source tương ứng phải cung cấp hoặc
adapter phải tạo. Tên thật chỉ được chốt sau khi source được triển khai.

| Entity | OMS JSON | WMS JSON | OPS JSON | Odoo model/field | MongoDB | External API |
|---|---|---|---|---|---|---|
| Order | `order.id`, `customer.id`, `channel.code`, totals, status, timestamps | N/A | N/A | `sale.order` và partner/company/team fields | N/A | `orders[].id` cho marketplace |
| Order line | `order.lines[].id/product/warehouse/price` | N/A | N/A | `sale.order.line` | product document chỉ enrichment | `orders[].lines[]` |
| Inventory | N/A | `balances[].warehouse/sku/lot/quantities/updated_at` | N/A | `stock.quant` + `stock.production.lot` | `products[].lots[]` enrichment | N/A |
| Shipment | N/A | warehouse enrichment | `shipments[].tracking_number/status/SLA` | `stock.picking` + carrier | N/A | carrier tracking response |
| Return | `returns[].id/order/line/reason/quantity/refund` | receipt enrichment | delivery exception enrichment | return picking/credit flow | N/A | marketplace return response |
| Payment | `payments[].transaction_reference/order/status/amount` | N/A | N/A | `account.payment` + `account.move` | N/A | payment provider transaction |

Adapter của từng nguồn phải lập bảng source-field chi tiết tương tự mục 5, khai
báo enum map, fixture và test trước khi đổi profile từ `contract_only` thành
`implemented`.

## 8. Trình tự xử lý adapter

1. Lưu payload nguyên bản và source metadata vào Bronze.
2. Chọn entity và mapping theo `source_system` + source schema version.
3. Join/enrich bằng stable business codes; lookup thất bại thì quarantine.
4. Chuẩn hóa type, timezone, decimal, null và enum.
5. Tạo `source_key`, `business_key`, `event_time` và envelope.
6. Validate bằng canonical schema `1.0.0`.
7. Ghi record hợp lệ vào Silver; ghi record lỗi cùng error code vào quarantine.
8. Deduplicate theo grain ở mục 2.3 và giữ record có `event_time` mới nhất.

## 9. Error code tối thiểu

| Error code | Khi dùng |
|---|---|
| `MAPPING_REQUIRED_FIELD_MISSING` | Source thiếu field cần để tạo required canonical field. |
| `MAPPING_LOOKUP_NOT_FOUND` | Không tìm thấy customer/product/warehouse/order liên quan. |
| `MAPPING_TYPE_CONVERSION_FAILED` | Không parse được date, timestamp, decimal hoặc string key. |
| `MAPPING_ENUM_UNKNOWN` | Source enum chưa có trong mapping. |
| `MAPPING_TIMEZONE_MISSING` | Timestamp local nhưng source chưa cấu hình timezone. |
| `MAPPING_BUSINESS_KEY_INVALID` | Thiếu thành phần hoặc key không khớp pattern canonical. |
| `MAPPING_GRAIN_AMBIGUOUS` | Ví dụ inventory có nhiều lot nhưng contract v1 chỉ có grain warehouse + SKU. |

## 10. Kiểm chứng và thay đổi

Chạy:

```bash
python -m unittest -v tests.test_source_mapping_matrix
```

Test bảo đảm đủ source/entity, mapping PostgreSQL phủ toàn bộ field canonical,
required field có expression, enum output nằm trong schema và source table được
tham chiếu thực sự tồn tại. Khi canonical schema thay đổi, test sẽ buộc ma trận
được cập nhật cùng lúc.

Thay đổi mapping phải tuân theo
`docs/data_contracts/02_schema_evolution_policy.md`. Thay đổi business key là
breaking change và phải tăng major version.
