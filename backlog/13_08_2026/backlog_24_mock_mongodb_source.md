---
id: BL-024
status: backlog
priority: P2
priority_rank: 160
category: platform
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-15
progress: 0
effort: M
value: medium
dependencies: [BL-020]
tags: [mock, mongodb, document, source]
target_release: null
---

# Backlog 24: Mock MongoDB Source

## Muc tieu

Bo sung document-oriented source de kiem thu ingestion tu MongoDB.

## Pham vi

- Chay MongoDB bang Docker Compose.
- Tao collection cho operational event, customer activity hoac product metadata.
- Sinh document co nested field va schema drift co kiem soat.
- Xay dung extractor full load va incremental theo `updated_at` hoac change stream.

## Ket qua mong muon

Pipeline co the xu ly source document va chuyen doi ve canonical model.
