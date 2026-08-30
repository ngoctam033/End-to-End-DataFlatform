---
id: BL-020
status: done
priority: P1
priority_rank: 20
category: platform
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-28
progress: 100
effort: M
value: high
dependencies: [BL-016]
tags: [data-contract, canonical-model, schema, source-system]
target_release: null
---

# Backlog 20: Source Contracts and Canonical Data Model

## Muc tieu

Thiet lap hop dong du lieu va mo hinh canonical chung truoc khi ket noi nhieu he thong nguon.

## Pham vi

- Xac dinh schema cho order, order line, inventory, shipment, return va payment.
- Quy dinh business key, source key, event time, ingestion time va source system.
- Dinh nghia versioning va quy tac schema evolution.
- Xac dinh mapping tu OMS/WMS/OPS/PostgreSQL/MongoDB/API ve canonical model.

## Ket qua mong muon

Moi source moi co the thay doi doc lap ma khong lam sai lech mo hinh analytics chung.

## Kết quả triển khai

- Hoàn thành đặc tả metadata envelope và schema evolution (`BL-020.1`).
- Hoàn thành 6 canonical JSON Schemas (`BL-020.2`).
- Hoàn thành multi-source mapping matrix (`BL-020.3`).
- Hoàn thành Python validation engine và routing Silver/quarantine (`BL-020.4`).
- Hoàn thành automated multi-source contract verification (`BL-020.5`).
