# Data Contract & Canonical Model Specification

## 1. Tổng quan và phạm vi kiến trúc

Tài liệu này quy định cấu trúc tiêu chuẩn của **Canonical Data Model** và **Metadata Envelope** cho toàn bộ Data Platform. Canonical model là hợp đồng logic giữa các hệ thống nguồn và các tầng dữ liệu downstream; nó không phụ thuộc vào một database duy nhất.

Để tránh nhầm lẫn giữa mô hình dữ liệu và công nghệ triển khai, kiến trúc được mô tả theo hai góc nhìn:

1. **Kiến trúc logic**: Source, Bronze, Silver và Gold.
2. **Kiến trúc vật lý**: các công nghệ cụ thể dùng để ingest, lưu trữ, xử lý, điều phối và phục vụ dữ liệu.

### 1.1 Kiến trúc logic ELT/Medallion

```text
┌──────────────────────────────┐
│ Source Systems               │
│ OMS · WMS · OPS · PostgreSQL │
│ MongoDB · API · File Sources │
└──────────────┬───────────────┘
               │ Extract & Load
               ▼
┌──────────────────────────────┐
│ Bronze / Raw                 │
│ Dữ liệu nguyên bản, bất biến │
│ Có metadata ingestion        │
└──────────────┬───────────────┘
               │ Map · Normalize · Validate
               ▼
┌──────────────────────────────┐
│ Silver / Canonical           │
│ Order · Line · Inventory     │
│ Shipment · Return · Payment  │
└──────────────┬───────────────┘
               │ Conform · Aggregate · Model
               ▼
┌──────────────────────────────┐
│ Gold / Data Products         │
│ Dimension · Fact · Data Mart │
│ KPI · Dashboard Dataset      │
└──────────────────────────────┘
```

- **Source Systems**: các hệ thống nghiệp vụ sở hữu dữ liệu gốc. Mỗi source có schema, khóa và nhịp cập nhật riêng.
- **Bronze / Raw**: lưu dữ liệu nguyên bản theo nguồn và thời điểm ingestion. Không loại bỏ record chỉ vì chưa đạt canonical contract; record lỗi vẫn phải được lưu để truy vết và tái xử lý.
- **Silver / Canonical**: ánh xạ dữ liệu nguồn về canonical model, chuẩn hóa kiểu dữ liệu, bổ sung envelope metadata và kiểm tra data contract. Record không hợp lệ được chuyển sang khu vực quarantine cùng thông tin lỗi.
- **Gold / Data Products**: mô hình dimension, fact, data mart và KPI phục vụ API, dashboard, đối soát và báo cáo nghiệp vụ.

### 1.2 Kiến trúc vật lý hiện tại

Pipeline đang hoạt động trong repository hiện tại là:

```text
Mock ERP PostgreSQL
        │
        ▼
Custom Python full-refresh pipeline
        │
        ▼
PostgreSQL Data Warehouse
        │
        ▼
SQL dimensions · facts · marts
        │
        ▼
FastAPI Dashboard API · Web Dashboard
```

Ở trạng thái hiện tại:

- PostgreSQL đóng cả vai trò source giả lập và analytical warehouse.
- Transformation được thực hiện bằng SQL trong PostgreSQL.
- Pipeline vẫn là full refresh và chưa áp dụng canonical contract tự động.
- MinIO, Airflow, dbt, Kafka và Spark mới ở mức cấu hình, backlog hoặc nhánh mở rộng; chưa phải toàn bộ luồng production đang chạy.

### 1.3 Kiến trúc vật lý mục tiêu

```text
OMS · WMS · OPS · PostgreSQL · MongoDB · API · File Sources
                              │
                     Python Connectors
                    Airflow Orchestration
                              │
                              ▼
                  MinIO Bronze / Raw Zone
               JSON · CSV · Parquet as-is
                              │
                  PySpark Mapping/Validation
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
       MinIO Silver / Canonical     MinIO Quarantine
          Parquet / Iceberg          Invalid records
                 │
          PySpark curated loading
                 │
                 ▼
       PostgreSQL staging/warehouse
                 │
            dbt SQL models
                 │
                 ▼
       PostgreSQL Gold Data Marts
       Dimensions · Facts · Marts
                 │
                 ▼
       FastAPI · Metabase · Reports
```

Vai trò của từng công nghệ:

| Thành phần | Vai trò |
| :--- | :--- |
| PostgreSQL source | Giả lập hoặc kết nối dữ liệu giao dịch từ ERP/OMS/WMS/OPS |
| Python connectors | Extract batch/incremental từ database, API và file source |
| Airflow | Điều phối dependency, schedule, retry và backfill |
| MinIO | Object storage cho Bronze, Silver, quarantine và dữ liệu có thể replay |
| Parquet | Định dạng file columnar cho dữ liệu lakehouse |
| Apache Iceberg | Table format mục tiêu cho schema evolution, ACID và time travel trên MinIO |
| PySpark | Xử lý dữ liệu lớn, mapping source-to-canonical, deduplication và validation |
| dbt | Quản lý transformation SQL, test, documentation và lineage ở warehouse/SQL engine |
| PostgreSQL warehouse | Phục vụ Gold dimensions, facts, marts và truy vấn BI |
| FastAPI/Metabase | Cung cấp dữ liệu cho dashboard và người dùng nghiệp vụ |

MinIO chỉ cung cấp **storage**, không phải database engine hoặc compute engine. Dữ liệu trên MinIO phải được xử lý hoặc truy vấn thông qua Spark, Trino, Flink, DuckDB hoặc một engine tương thích khác. Trong phạm vi hiện tại, Spark là processing engine mục tiêu và PostgreSQL là serving warehouse cho Gold layer.

### 1.4 Điểm áp dụng Data Contract

Data contract được áp dụng khi chuyển dữ liệu từ Bronze sang Silver:

1. Source payload được lưu nguyên bản vào Bronze cùng ingestion metadata.
2. Mapping rule chuyển source fields về canonical fields.
3. Pipeline tạo `business_key`, chuẩn hóa timestamp và enum.
4. Metadata envelope được bổ sung.
5. Canonical payload được validate theo schema version tương ứng.
6. Record hợp lệ được ghi vào Silver; record không hợp lệ được ghi vào quarantine.

Không áp dụng schema rejection trước khi dữ liệu gốc được lưu vào Bronze. Nguyên tắc này bảo đảm auditability, traceability và khả năng replay khi mapping hoặc contract thay đổi.

---

## 2. Đặc tả Metadata Envelope chuẩn

Mọi bản ghi dữ liệu tại lớp Canonical Silver Layer đều phải được đóng gói trong một **Metadata Envelope tiêu chuẩn** bao gồm các trường sau:

| Trường (Field) | Kiểu Dữ liệu | Bắt buộc | Mô tả | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `business_key` | `String` | **Có** | Mã định danh nghiệp vụ duy nhất toàn hệ thống (Cross-system key). | `ORD-OMS-10045` |
| `source_key` | `String` | **Có** | Khóa chính nguyên bản tại hệ thống nguồn. | `10045` hoặc `65a12f89...` |
| `source_system` | `String` | **Có** | Mã nhận diện hệ thống nguồn gửi dữ liệu. | `oms`, `wms`, `ops`, `postgres_erp`, `mongodb_catalog`, `external_api` |
| `event_time` | `String (ISO-8601)` | **Có** | Thời điểm sự kiện phát sinh tại hệ thống nguồn (UTC). | `2026-08-16T08:30:00Z` |
| `ingestion_time` | `String (ISO-8601)` | **Có** | Thời điểm dữ liệu được nạp vào Data Lake Bronze layer (UTC). | `2026-08-16T08:31:05Z` |
| `schema_version` | `String` | **Có** | Phiên bản Data Contract áp dụng cho bản ghi này (SemVer). | `1.0.0` |
| `processing_status` | `String` | **Có** | Trạng thái kiểm duyệt dữ liệu (`VALID`, `QUARANTINED`, `WARNING`). | `VALID` |
| `payload` | `Object / Record` | **Có** | Cấu trúc dữ liệu chi tiết của thực thể nghiệp vụ sau khi đã chuẩn hóa. | `{ "order_id": "ORD-OMS-10045", ... }` |

---

## 3. Quy ước đặt tên và tiêu chuẩn kiểu dữ liệu

### 3.1 Quy tắc đặt tên (Naming Conventions)
- **Cú pháp**: Tất cả các tên trường (field names) phải sử dụng cú pháp `snake_case`.
- **Thực thể**: Đặt tên danh từ số ít (ví dụ: `order`, `inventory`, `shipment`).
- **Hậu tố bắt buộc**:
  - Thời gian / Timestamp: kết thúc bằng `_at` (ví dụ: `created_at`, `shipped_at`, `updated_at`).
  - Ngày / Date: kết thúc bằng `_date` (ví dụ: `order_date`, `expiry_date`).
  - Giá trị tiền tệ: kết thúc bằng `_amount` (ví dụ: `total_amount`, `discount_amount`, `tax_amount`).
  - Số lượng: kết thúc bằng `_qty` hoặc `_quantity` (ví dụ: `ordered_qty`, `shipped_qty`).
  - Mã định danh / Foreign keys: kết thúc bằng `_id` hoặc `_key` (ví dụ: `customer_id`, `product_id`, `business_key`).

### 3.2 Quy chuẩn Kiểu dữ liệu (Datatype Standards)
- **Thời gian (Timestamps)**: Định dạng chuỗi ISO-8601 chuẩn UTC (`YYYY-MM-DDTHH:mm:ssZ`).
- **Tiền tệ (Currency)**: Định dạng Decimal/Numeric với độ chính xác `Decimal(18, 4)` để tránh lỗi làm tròn số thực. Chuẩn tiền tệ mặc định là `VND` (hoặc `USD` theo cấu hình).
- **Mã địa lý (Geography & Country)**: Sử dụng chuẩn mã quốc gia ISO-3166-1 alpha-2 (ví dụ: `VN`, `US`).
- **Số điện thoại**: Định dạng chuẩn quốc tế E.164 (ví dụ: `+84901234567`).

---

## 4. Quy tắc tạo Business Key

`business_key` giúp định danh duy nhất một đối tượng nghiệp vụ trên toàn bộ data platform ngay cả khi tích hợp dữ liệu từ nhiều hệ thống nguồn độc lập.

| Thực thể (Entity) | Cấu trúc Business Key | Ví dụ |
| :--- | :--- | :--- |
| **Order** | `ORD-{SOURCE_SYSTEM_UPPER}-{SOURCE_KEY}` | `ORD-OMS-10045`, `ORD-ERP-SO992` |
| **Order Line** | `ORDL-{SOURCE_SYSTEM_UPPER}-{SOURCE_ORDER_ID}-{LINE_ID}` | `ORDL-OMS-10045-1` |
| **Inventory** | `INV-{SOURCE_SYSTEM_UPPER}-{WAREHOUSE_CODE}-{SKU}` | `INV-WMS-WH01-SKU8839` |
| **Shipment** | `SHP-{SOURCE_SYSTEM_UPPER}-{TRACKING_NUMBER}` | `SHP-OPS-GHN99281` |
| **Return** | `RET-{SOURCE_SYSTEM_UPPER}-{RETURN_ID}` | `RET-OMS-RET0012` |
| **Payment** | `PAY-{SOURCE_SYSTEM_UPPER}-{TRANSACTION_REF}` | `PAY-API-PAYPAL9981` |

---

## 5. Quy trình bổ sung Metadata

Khi pipeline chuyển đổi dữ liệu từ Bronze sang Silver:
1. Đọc bản ghi thô từ Bronze (`raw_payload`, `received_at`, `source_name`).
2. Trích xuất hoặc tạo `business_key` theo quy tắc section 4.
3. Chuyển đổi timestamp nguồn về chuẩn UTC ISO-8601 cho `event_time`.
4. Gán `ingestion_time` từ thuộc tính của file Bronze.
5. Gán `schema_version` tương ứng với file contract đang thực thi (`1.0.0`).
6. Kiểm tra các ràng buộc schema bắt buộc. Nếu hợp lệ -> gán `processing_status = "VALID"`. Nếu vi phạm trường bắt buộc -> gán `processing_status = "QUARANTINED"`.

---

## 6. Tài liệu tham khảo (References)

- **Backlog tổng**: [BL-020: Source Contracts and Canonical Data Model](../../backlog/13_08_2026/backlog_20_source_contracts_canonical_model.md)
- **Sub-task triển khai**: [BL-020.1: Specification & Schema Evolution Policy](../../backlog/13_08_2026/backlog_20_1_specification_evolution_policy.md)
- **Chính sách liên quan**: [02_schema_evolution_policy.md](./02_schema_evolution_policy.md)
