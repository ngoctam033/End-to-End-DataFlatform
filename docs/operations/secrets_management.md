# Secrets Management

Tài liệu này mô tả cách quản lý credential và cấu hình nhạy cảm cho môi trường local/Docker Compose của End-to-End Data Platform.

## Phạm vi

Các service được bao phủ:

- Mock ERP PostgreSQL và mock data producer.
- Analytics warehouse PostgreSQL.
- MinIO object storage.
- Apache Airflow và Airflow metadata database.
- Odoo và Odoo PostgreSQL.
- Python ingestion pipeline.
- Dashboard API.

Giải pháp hiện tại sử dụng `.env` local. Môi trường production cần chuyển secret sang Docker Secrets, Kubernetes Secrets hoặc một secret manager chuyên dụng.

## Nguyên tắc

- Không ghi password, token, API key hoặc encryption key trực tiếp trong source code, Docker Compose hay tài liệu.
- Không commit `.env`.
- Chỉ commit `.env.example` với placeholder.
- Secret bắt buộc phải fail-fast khi thiếu; không dùng credential mặc định.
- Mỗi service sử dụng nhóm biến riêng để giảm nhầm lẫn và hỗ trợ rotation độc lập.
- Không ghi connection URL chứa credential vào log.

## Khởi tạo môi trường local

Thực hiện từ thư mục gốc repository:

```bash
cp .env.example .env
```

Thay toàn bộ giá trị `change-me` trong `.env` bằng giá trị local đủ mạnh.

Tạo Airflow Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Gán kết quả vào:

```env
AIRFLOW_FERNET_KEY=<generated-fernet-key>
```

Không gửi nội dung `.env` qua chat, issue, pull request hoặc log CI.

## Danh mục biến môi trường

| Nhóm | Biến | Bắt buộc | Mục đích |
|---|---|---:|---|
| Mock ERP | `MOCK_ERP_POSTGRES_USER` | Có | PostgreSQL user |
| Mock ERP | `MOCK_ERP_POSTGRES_PASSWORD` | Có | PostgreSQL password |
| Mock ERP | `MOCK_ERP_POSTGRES_DB` | Có | Database name |
| Mock ERP | `MOCK_ERP_PG_EXTERNAL_PORT` | Không | Cổng local |
| Warehouse | `WAREHOUSE_POSTGRES_USER` | Có | Warehouse user |
| Warehouse | `WAREHOUSE_POSTGRES_PASSWORD` | Có | Warehouse password |
| Warehouse | `WAREHOUSE_POSTGRES_DB` | Có | Warehouse database |
| Warehouse | `DATA_WAREHOUSE_PG_EXTERNAL_PORT` | Không | Cổng local |
| MinIO | `MINIO_ROOT_USER` | Có | MinIO root user |
| MinIO | `MINIO_ROOT_PASSWORD` | Có | MinIO root password |
| MinIO | `MINIO_API_EXTERNAL_PORT` | Không | API port |
| MinIO | `MINIO_CONSOLE_EXTERNAL_PORT` | Không | Console port |
| Airflow | `AIRFLOW_DB_USER` | Có | Metadata database user |
| Airflow | `AIRFLOW_DB_PASSWORD` | Có | Metadata database password |
| Airflow | `AIRFLOW_DB_NAME` | Không | Metadata database name |
| Airflow | `AIRFLOW_FERNET_KEY` | Có | Mã hóa Airflow connections/variables |
| Airflow | `_AIRFLOW_WWW_USER_USERNAME` | Không | Local admin username |
| Airflow | `_AIRFLOW_WWW_USER_PASSWORD` | Có | Local admin password |
| Odoo | `ODOO_DB_USER` | Có | Odoo database user |
| Odoo | `ODOO_DB_PASSWORD` | Có | Odoo database password |
| Odoo | `ODOO_DB_NAME` | Không | Odoo database name |

Các biến `PIPELINE_SOURCE_DATABASE_URL`, `PIPELINE_WAREHOUSE_DATABASE_URL`, `MOCK_DATA_PRODUCER_DATABASE_URL` và `DASHBOARD_DATABASE_URL` là override tùy chọn. Nếu sử dụng, phải lưu chúng trong `.env` vì URL có thể chứa credential.

## Khởi động service

Khởi động luồng mặc định từ repository root:

```bash
docker network inspect end2end_data_network >/dev/null 2>&1 || docker network create end2end_data_network
docker compose --env-file .env up -d --build
```

Khởi động một Compose riêng:

```bash
docker compose --env-file .env \
  -f storage/data_warehouse_pg/docker-compose.data_warehouse_pg.yml \
  up -d
```

Khi chạy từ thư mục con, trỏ `--env-file` về `.env` ở repository root, ví dụ:

```bash
cd data_source/mock_erp_pg
docker compose --env-file ../../.env \
  -f docker-compose.mock_erp_pg.yml \
  up -d --build
```

## Chạy Python trực tiếp

Các script Python đọc biến từ process environment và không tự động đọc file `.env`. Export biến trước khi chạy:

```bash
set -a
. ./.env
set +a
python data_source/mock_data_factory/run_mock_data_producer.py
```

## Kiểm tra cấu hình

Kiểm tra Compose mà không khởi động container:

```bash
docker compose --env-file .env config >/dev/null
```

Chạy test cấu hình:

```bash
python -m unittest -v shared.tests.test_settings
```

Quét nhanh credential đã biết trước khi commit:

```bash
rg -n "admin123|postgresql://[^ ]+:[^ ]+@" \
  --glob '!.env' \
  --glob '!**/tests/**'
```

## Fail-fast và xử lý lỗi

Nếu thiếu secret bắt buộc, Docker Compose dừng ở bước interpolation với thông báo tên biến bị thiếu. Python services ném `ConfigurationError` trước khi tạo kết nối.

Các lỗi thường gặp:

- `variable is required`: biến chưa có hoặc đang rỗng trong `.env`.
- `password authentication failed`: credential trong application và database volume không đồng nhất.
- `Fernet key must be 32 url-safe base64-encoded bytes`: Fernet key không hợp lệ.
- Connection URL lỗi khi password chứa ký tự đặc biệt: dùng URL override đã encode hoặc chọn secret URL-safe cho môi trường local.

PostgreSQL chỉ áp dụng `POSTGRES_PASSWORD` khi khởi tạo data volume lần đầu. Nếu đổi credential trong `.env` nhưng giữ volume cũ, cần đổi password trong database hoặc tái tạo volume có chủ đích.

## Rotation

Quy trình xoay vòng credential:

1. Xác định service và các consumer phụ thuộc.
2. Tạo secret mới.
3. Cập nhật credential trong database/object storage trước hoặc theo chiến lược dual credential nếu hệ thống hỗ trợ.
4. Cập nhật `.env` local hoặc secret store của môi trường.
5. Restart các consumer liên quan.
6. Chạy healthcheck và smoke test.
7. Thu hồi secret cũ.
8. Xác nhận log và Git diff không chứa secret.

Không commit thay đổi giá trị secret trong quá trình rotation.

## Hướng nâng cấp production

`.env` chỉ phù hợp với local development. Khi triển khai production:

- Dùng Kubernetes Secrets kết hợp External Secrets Operator, Vault hoặc secret manager của cloud provider.
- Mount secret dưới dạng file khi service hỗ trợ, thay vì truyền toàn bộ qua command line.
- Phân quyền secret theo service account và nguyên tắc least privilege.
- Bật audit log, rotation định kỳ và cảnh báo truy cập bất thường.
- Không đưa secret vào image, ConfigMap, Helm values được commit hoặc output CI.

## Checklist trước khi commit

- `.env` không xuất hiện trong `git status`.
- `.env.example` chỉ chứa placeholder.
- Không còn credential thật trong source, Compose hoặc tài liệu.
- Test `shared.tests.test_settings` thành công.
- Docker Compose render thành công khi dùng `.env` hợp lệ.
- Docker Compose dừng rõ ràng khi thiếu secret bắt buộc.
