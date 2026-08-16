---
id: BL-004
status: backlog
priority: P2
priority_rank: 200
category: architecture
owner: unassigned
created_at: 2026-08-11
updated_at: 2026-08-13
progress: 0
effort: L
value: medium
dependencies: [BL-012, BL-013]
tags: [kafka, spark, learning, branch]
target_release: null
---

# Backlog 4: Kafka/Spark Learning Branch

Ngay ghi nhan: 11/08/2026
Trang thai: backlog, chua trien khai

## Muc tieu

Thu nghiem luong streaming va xu ly phan tan ma khong anh huong pipeline hien tai.

## Kafka

- Phat su kien order, payment, shipment hoac inventory movement.
- Chuan hoa event envelope gom `event_id`, `event_type`, `event_time`, `source_system` va ingestion metadata.
- Kiem thu partition, consumer group, retry va idempotency.

## Spark

- Doc du lieu batch tu raw layer.
- Doc event tu Kafka cho nhanh streaming.
- Xu ly va ghi ket qua ve cac bang curated/mart phu hop.

## Cach to chuc

Trien khai tren mot branch rieng, them node xu ly moi trong architecture, khong thay the hoac sua luong hien tai.

## Ket qua mong muon

Co the so sanh batch processing voi streaming processing tren cung mot loai nghiep vu.
