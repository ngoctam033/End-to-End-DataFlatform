---
id: BL-036
status: backlog
priority: P1
priority_rank: 25
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: XL
value: high
dependencies: [BL-016]
tags: [odoo, order-to-cash, fulfillment, fmcg, initiative]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36: Odoo Sales Order Fulfillment Initiative

## Mục tiêu

Dùng Odoo làm operational source đầu tiên cho lát cắt nghiệp vụ Sales Order Fulfillment, từ master data và đơn hàng đến tồn kho, giao hàng, hóa đơn, thanh toán và hoàn trả.

## Nguyên tắc

- Odoo sở hữu business workflow; data platform không thực thi nghiệp vụ nguồn.
- Canonical contract độc lập với tên model và khóa nội bộ của Odoo.
- Workstream Odoo chạy song song với core platform và data contracts.
- Từng giai đoạn chỉ tích hợp downstream sau khi dependency contract cần thiết đã hoàn thành.

## Các giai đoạn

1. `BL-036.1` — Foundation and Minimal Master Data.
2. `BL-036.2` — Sales Order and Canonical Extraction.
3. `BL-036.3` — Inventory, FMCG Lots and Expiration.
4. `BL-036.4` — Delivery and Fulfillment.
5. `BL-036.5` — Invoice and Payment.
6. `BL-036.6` — Return and Refund.

## Kết quả mong muốn

Có một vertical slice Odoo tái lập được, sinh dữ liệu nghiệp vụ hợp lệ và ánh xạ được sang canonical entities của nền tảng.
