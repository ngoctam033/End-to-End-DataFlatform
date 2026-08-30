---
id: BL-048
status: backlog
priority: P2
priority_rank: 480
category: analytics
owner: unassigned
created_at: 2026-08-30
updated_at: 2026-08-30
progress: 0
effort: XL
value: high
dependencies: [BL-033, BL-046, BL-047]
tags: [crm, customer-360, identity-resolution, golden-record, pii]
target_release: null
---

# Backlog 48: Customer 360 and Identity Resolution

## Muc tieu

Xay dung customer 360 va golden customer record tu CRM, OMS, POS va cac giao dich lien quan.

## Pham vi

- Chuan hoa customer identity va contact attributes.
- Mapping nhieu source key ve `customer_master_key`.
- Phat hien va xu ly duplicate customer.
- Xac dinh survivorship rule va match confidence.
- Ket hop profile, segment, order, payment, return va interaction.
- Xem xet masking va phan quyen PII.

## Ket qua mong muon

Moi customer co mot ho so thong nhat, truy vet duoc nguon va khong bi double-count trong analytics.
