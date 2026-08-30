# Data Contract Schema Evolution Policy

## 1. Mục tiêu & Nguyên tắc

Trong hệ thống dữ liệu doanh nghiệp đa nguồn (Omnichannel FMCG), các hệ thống nguồn (OMS, WMS, ERP, API...) liên tục được cập nhật và thay đổi cấu trúc. **Schema Evolution Policy (Chính sách Quản lý Thay đổi Cấu trúc)** quy định nguyên tắc và quy trình xử lý để đảm bảo:

1. **Không gián đoạn Pipeline (Zero Downtime)**: Các thay đổi từ hệ thống nguồn không làm sập các pipeline xử lý dbt/Spark hay báo cáo BI Metabase downstream.
2. **Minh bạch & Quản lý phiên bản**: Mọi thay đổi về Data Contract đều được đánh phiên bản (Semantic Versioning) và lưu trữ lịch sử rõ ràng.
3. **Phân định trách nhiệm**: Phân định rõ ràng trách nhiệm giữa đội ngũ phát triển Nguồn (Data Producers) và đội ngũ Phân tích dữ liệu (Data Consumers).

---

## 2. Quy tắc Đánh Phiên Bản (Semantic Versioning Rules)

Data Contracts áp dụng chuẩn **Semantic Versioning (SemVer 2.0.0)** với cú pháp `MAJOR.MINOR.PATCH`:

```
v MAJOR . MINOR . PATCH
  │       │       └─ Sửa lỗi nhỏ / Thêm mô tả tài liệu (Patch)
  │       └───────── Thêm trường optional mới / Nới lỏng constraint (Non-breaking Minor)
  └───────────────── Xóa trường / Thay đổi kiểu dữ liệu / Đổi tên trường (Breaking Major)
```

### 2.1 Major Version Upgrade (Thay đổi gây vỡ hệ thống - Breaking Changes)
- **Định nghĩa**: Những thay đổi khiến các pipeline hoặc dashboard cũ không thể đọc hoặc xử lý dữ liệu mới một cách chính xác.
- **Các trường hợp được coi là Major Change**:
  - Xóa một trường đang tồn tại trong Contract.
  - Thêm một trường mới nhưng đánh dấu là **Bắt buộc (Required)**.
  - Thay đổi kiểu dữ liệu của một trường không thể ép kiểu tự động (ví dụ: đổi `String` thành `Array` hoặc `Integer` thành `Timestamp`).
  - Thay đổi quy tắc tạo `business_key`.
  - Thay đổi ý nghĩa nghiệp vụ (Semantic meaning) của một trường.
- **Quy trình xử lý**:
  - Yêu cầu tạo một Schema Version mới (ví dụ từ `v1.2.0` nâng lên `v2.0.0`).
  - Áp dụng **Thời gian Chuyển tiếp (Grace Period)** tối thiểu 30 ngày. Hệ thống duy trì song song 2 phiên bản contract (Dual-version transformation) cho đến khi toàn bộ Data Consumers chuyển đổi đổi sang version `v2`.

### 2.2 Minor Version Upgrade (Thay đổi tương thích - Non-breaking Changes)
- **Định nghĩa**: Những thay đổi mở rộng tính năng nhưng vẫn tương thích ngược (Backward Compatible) với các hệ thống downstream.
- **Các trường hợp được coi là Minor Change**:
  - Thêm một trường mới và đánh dấu là **Tùy chọn (Optional / Nullable)**.
  - Nới lỏng ràng buộc (ví dụ: thay đổi độ dài chuỗi tối đa từ `String(50)` thành `String(255)`).
  - Thêm một enum value mới vào danh sách tùy chọn (ví dụ: thêm kênh bán mới `TIKTOK_SHOP` vào enum `sales_channel`).
- **Quy trình xử lý**:
  - Nâng phiên bản `MINOR` (ví dụ từ `v1.0.0` lên `v1.1.0`).
  - Tự động áp dụng cho pipeline mà không cần dừng hay thay đổi code downstream.

### 2.3 Patch Version Upgrade (Sửa đổi tài liệu / Mô tả)
- **Định nghĩa**: Thay đổi mô tả trường, tài liệu ghi chú hoặc sửa lỗi chính tả mà không ảnh hưởng tới cấu trúc hay kiểu dữ liệu.
- **Quy trình xử lý**: Nâng phiên bản `PATCH` (ví dụ từ `v1.0.0` lên `v1.0.1`).

---

## 3. Fallback & Default Value Rules

Khi dữ liệu từ hệ thống nguồn thiếu các trường optional được bổ sung trong các phiên bản Contract mới, Silver Transformation Layer sẽ áp dụng quy tắc gán giá trị mặc định (Fallback Rules) như sau:

| Kiểu dữ liệu | Giá trị mặc định (Default Fallback) |
| :--- | :--- |
| `String` | `null` hoặc `"UNKNOWN"` (tùy theo cấu hình trường) |
| `Numeric / Decimal` | `0.00` |
| `Boolean` | `false` |
| `Array / List` | `[]` (Mảng rỗng) |
| `Object / Map` | `{}` (Đối tượng rỗng) |
| `Timestamp` | `null` |

---

## 4. Deprecation & Sunset Protocol

Khi một trường hoặc một phiên bản Contract không còn được sử dụng (Deprecated):

1. **Bước 1 (Deprecation Warning)**: Đánh dấu nhãn `deprecated: true` trong file YAML schema và gửi cảnh báo tới Data Consumers. Đặt mốc thời gian Ngừng hỗ trợ (Sunset Date).
2. **Bước 2 (Migration Phase)**: Đội ngũ Data Engineering hỗ trợ nâng cấp các dbt models và Metabase dashboards sang trường mới hoặc phiên bản contract mới.
3. **Bước 3 (Sunset Execution)**: Đúng mốc Sunset Date, phiên bản Contract cũ chính thức bị loại bỏ.
