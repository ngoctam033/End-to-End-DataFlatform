# End-to-End Data Engineering Platform 🚀

Dự án này là một hệ thống Data Engineering hoàn chỉnh (End-to-End), được thiết kế theo tư tưởng **Microservices** và **Technology-Agnostic** (Chia theo các Logical Nodes độc lập, dễ dàng thay thế công nghệ). 

Toàn bộ các dịch vụ trong hệ thống được đóng gói bằng Docker và kết nối với nhau thông qua một mạng lưới chung.

## 🎯 Business Domain (Lĩnh Vực Bài Toán)

Dự án này được thiết kế để giải quyết bài toán dữ liệu cho mô hình **Omnichannel D2C FMCG** - một trong những mô hình phức tạp và thực tế nhất hiện nay. Đây là sự kết hợp của 3 lĩnh vực lớn:

1. **FMCG (Hàng tiêu dùng nhanh):** Quản lý vòng đời sản phẩm, ngày sản xuất, hạn sử dụng (Expiration dates/Lots) để tránh rủi ro tồn kho cận date.
2. **E-commerce & Bán lẻ đa kênh (Omnichannel Retail):** Dữ liệu phân mảnh từ bán hàng online (D2C Website) đến offline (Cửa hàng vật lý - POS) và bán buôn (Wholesale). Mục tiêu là hợp nhất dữ liệu để phân tích Customer 360 và hiệu suất doanh thu theo từng kênh.
3. **Logistics & Supply Chain:** Theo dõi luồng dịch chuyển của hàng hóa từ kho trung tâm đến các điểm bán và người dùng cuối. Đo lường thời gian xử lý đơn hàng (Fulfillment Lead time) và cảnh báo đứt gãy tồn kho (Out-of-stock).

**Kịch bản dữ liệu (Data Scenario):** Hệ thống sử dụng **Odoo ERP** làm trái tim vận hành (Master Data & Transactional Data). Toàn bộ dữ liệu Bán hàng, Kho bãi, và Khách hàng từ Odoo sẽ được hệ thống Data Pipeline này tự động thu thập, làm sạch, và biến đổi thành các Data Models chuẩn mực (Star-schema) để phục vụ cho các Báo cáo chiến lược (BI Dashboards).

## 🏗 Kiến Trúc Hệ Thống (Architecture)

Dữ liệu đi qua hệ thống theo đường ống (pipeline) dưới đây:

```mermaid
flowchart LR
    %% Main data path: left to right
    subgraph SOURCES["① Sources — Operational systems"]
        ODOO["🛒 Odoo ERP\nSales · CRM · Inventory · Logistics"]
        MOCK["🧪 Mock ERP PostgreSQL\nTest transactions"]
    end

    subgraph INGEST["② Ingestion — Collect & land"]
        PY["🐍 Custom Python\nExtract / API / batch"]
        KAFKA["🔴 Apache Kafka\nEvent streaming / CDC"]
        RAW[("🪣 MinIO\nRaw Data Lake")]
    end

    subgraph MODEL["③ Processing & Transform"]
        SPARK["✨ Apache Spark\nBatch / streaming processing"]
        DBT["⚙️ dbt\nSQL models · tests"]
        MART[("🗄️ PostgreSQL\nData Warehouse / marts")]
    end

    subgraph SERVE["④ Serve — Consume insights"]
        BI["📊 Metabase\nBI dashboards"]
        POWERBI["📈 Power BI\nSelf-service analytics"]
        USERS["👥 Business users\nExecutive · Supply Chain · Sales"]
    end

    ODOO --> PY
    MOCK --> PY
    PY -->|raw / immutable| RAW
    RAW --> DBT
    DBT -->|clean · conform · aggregate| MART
    MART --> BI
    MART --> POWERBI
    BI --> USERS
    POWERBI --> USERS

    ODOO -. learning branch .-> KAFKA
    MOCK -. learning branch .-> KAFKA
    KAFKA -. events / CDC .-> SPARK
    RAW -. parquet / objects .-> SPARK
    SPARK -. curated data .-> RAW
    SPARK -. analytical tables .-> MART

    AIRFLOW{{"🎛️ Apache Airflow\nOrchestrate · schedule · monitor"}}
    AIRFLOW -. trigger .-> PY
    AIRFLOW -. trigger .-> SPARK
    AIRFLOW -. trigger .-> DBT
    AIRFLOW -. refresh / monitor .-> BI
    AIRFLOW -. refresh / monitor .-> POWERBI

    classDef source fill:#fff1e8,stroke:#e76f51,stroke-width:2px,color:#1f2937;
    classDef ingest fill:#fff8d8,stroke:#e9c46a,stroke-width:2px,color:#1f2937;
    classDef transform fill:#f0e9ff,stroke:#8064a2,stroke-width:2px,color:#1f2937;
    classDef serve fill:#e5f6f2,stroke:#2a9d8f,stroke-width:2px,color:#1f2937;
    classDef control fill:#eef2f7,stroke:#64748b,stroke-width:2px,stroke-dasharray:5 5,color:#1f2937;
    classDef future fill:#ffffff,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:4 4,color:#1f2937;

    class ODOO,MOCK source;
    class PY,RAW ingest;
    class KAFKA future;
    class DBT,MART transform;
    class SPARK future;
    class BI,USERS serve;
    class POWERBI future;
    class AIRFLOW control;
```

**Cách đọc sơ đồ:** đường liền là luồng dữ liệu hiện tại; đường nét đứt là nhánh mở rộng phục vụ học tập hoặc luồng điều phối. Luồng dashboard hiện tại đọc các mart đã được pipeline tạo trong `storage/data_warehouse_pg`; dashboard không tự chạy transformation SQL. Kafka, Spark và Power BI được đặt như các node tương lai để dễ checkout sang nhánh khác khi muốn thử nghiệm, không làm thay đổi pipeline nền đang có. Các biểu tượng trong node giúp nhận diện nhanh công nghệ, còn tên công nghệ đầy đủ vẫn được giữ lại để sơ đồ không phụ thuộc vào bộ logo bên ngoài.

## 📂 Cấu Trúc Thư Mục (Codebase)

Codebase được thiết kế với chuẩn mực cao: thư mục cấp 1 thể hiện **"bước"** trong quy trình (logical nodes), còn thư mục con thể hiện **"công nghệ"** được áp dụng cho bước đó:

* **`data_sources/`**: Nơi phát sinh dữ liệu (VD: `odoo` - Hệ thống ERP kinh doanh).
* **`ingestion/`**: Khâu thu thập dữ liệu (VD: `custom_python` script để gọi API hoặc kết nối `airbyte`).
* **`storage/`**: Hệ thống lưu trữ, bao gồm `data_lake_minio` (chứa dữ liệu thô - raw data) và `data_warehouse_pg` (chứa dữ liệu đã được làm sạch - structured data).
* **`transformation/`**: Tầng biến đổi dữ liệu (VD: `dbt` để transform, build các data models).
* **`orchestration/`**: Tầng điều phối và quản lý lịch trình chạy pipeline (VD: Apache `airflow`).
* **`serving/`**: Tầng giao tiếp với người dùng cuối, biểu đồ hóa dữ liệu (VD: `metabase`).
* **`shared/`**: Các tài nguyên dùng chung như `notebooks` (khám phá dữ liệu EDA) và dữ liệu tạm `data`.

## 🌐 Mạng Lưới Nội Bộ (Docker Network)

Đặc thù của hệ thống phân tán là các node phải "nhìn thấy" nhau (VD: Airflow phải truy cập được vào Database Odoo). Do đó, toàn bộ các services được cấu hình để chạy chung trên một mạng lưới ngoài có tên là: **`end2end_data_network`**.

Nếu mạng lưới này chưa tồn tại trên máy tính, bạn cần tạo nó trước khi chạy bất kỳ service nào:
```bash
docker network create end2end_data_network
```

*(Quy tắc: Khi viết cấu hình `docker-compose.yml` cho bất kỳ một tool nào mới ở các node khác, luôn ghi đè mạng `default` trỏ về `end2end_data_network`)*.

## 🚀 Hướng Dẫn Sử Dụng (Quickstart)

*(Đang cập nhật - Hiện tại dự án đã hoàn thành cấu hình cho module Orchestration)*

**Khởi động Airflow:**
1. Di chuyển vào thư mục Airflow:
   ```bash
   cd orchestration/airflow
   ```
2. Build và khởi động bằng Docker Compose:
   ```bash
   docker compose -f docker-compose.airflow.yaml up -d --build
   ```
3. Truy cập giao diện Airflow Web UI tại: `http://localhost:8081` 
   *(Tài khoản mặc định: `airflow` / Mật khẩu: `airflow`)*.
