---
id: BL-025
status: backlog
priority: P2
priority_rank: 170
category: platform
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-15
progress: 0
effort: M
value: medium
dependencies: [BL-020]
tags: [mock, api, rest, pagination, rate-limit]
target_release: null
---

# Backlog 25: Mock External API Source

## Muc tieu

Tao REST API gia lap de kiem thu ingestion tu he thong ben ngoai.

## Pham vi

- Endpoint co pagination, filter va cursor.
- Authentication token va rate limit.
- Response versioning va schema evolution.
- Loi tam thoi, timeout, duplicate response va late response.
- Extractor co retry, checkpoint va idempotent load.

## Ket qua mong muon

Pipeline co the xu ly cac han che pho bien cua external API trong moi truong test.
