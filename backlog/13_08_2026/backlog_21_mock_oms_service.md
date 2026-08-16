---
id: BL-021
status: backlog
priority: P2
priority_rank: 120
category: business
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-15
progress: 0
effort: M
value: high
dependencies: [BL-020]
tags: [mock, oms, orders, api]
target_release: null
---

# Backlog 21: Mock OMS Service

## Muc tieu

Tao service gia lap Order Management System de phat sinh va cung cap vong doi don hang.

## Pham vi

- API tao, cap nhat, huy va truy van order/order line.
- Trang thai don hang va lich su thay doi.
- Customer, channel, payment summary va fulfillment request.
- API pagination, filter, retry va idempotency key.
- Phat event order created/updated/cancelled.

## Ket qua mong muon

Pipeline co the ingest OMS nhu mot he thong doc lap thay vi doc truc tiep mock ERP PostgreSQL.
