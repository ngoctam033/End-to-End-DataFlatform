---
id: BL-011
status: backlog
priority: P1
priority_rank: 30
category: platform
owner: unassigned
created_at: 2026-08-13
updated_at: 2026-08-13
progress: 0
effort: L
value: high
dependencies: [BL-016]
tags: [minio, raw, staging, parquet, replay]
target_release: null
---

# Backlog 11: Raw/Staging Layer on MinIO

Ngay ghi nhan: 13/08/2026
Trang thai: backlog, chua trien khai

## Muc tieu

Bo sung data lake raw/staging de luu snapshot du lieu truoc khi transformation.

## Pham vi du kien

- Ghi raw data tu source vao MinIO theo partition ngay va source system.
- Thiet ke format Parquet va metadata ingestion.
- Tach cac tang raw/bronze, staging/silver va curated/gold.
- Ho tro replay pipeline tu raw data.

## Ket qua mong muon

Du lieu nguon duoc luu lai co lich su, co the truy vet va tai xu ly khi transformation thay doi.
