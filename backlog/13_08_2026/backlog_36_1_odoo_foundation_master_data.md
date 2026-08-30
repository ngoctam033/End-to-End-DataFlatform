---
id: BL-036.1
status: backlog
priority: P1
priority_rank: 25.1
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-016]
tags: [odoo, master-data, product, customer, warehouse, fmcg]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.1: Odoo Foundation and Minimal Master Data

## Mục tiêu

Thiết lập Odoo và bộ master data tối thiểu để chạy được luồng Sales Order Fulfillment có dữ liệu tái lập.

## Phạm vi

- Chuẩn hóa cấu hình Docker Compose, healthcheck và secret qua `.env`.
- Kích hoạt các module Contacts, Sales, Inventory và Accounting cần thiết.
- Tạo product category, SKU, UoM, customer, warehouse, stock location và sales channel.
- Tạo bộ dữ liệu demo nhỏ, ổn định và có business code để tham chiếu chéo.
- Bật lot/serial tracking và expiration setting cho sản phẩm FMCG phù hợp.
- Viết smoke test xác nhận Odoo và dữ liệu nền sẵn sàng.

## Kết quả mong muốn

Odoo khởi động lặp lại được và có master data đủ để tạo sales order, nhập tồn đầu kỳ và theo dõi lot.
