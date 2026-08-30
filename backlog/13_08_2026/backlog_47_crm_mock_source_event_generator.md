---
id: BL-047
status: backlog
priority: P2
priority_rank: 470
category: platform
owner: unassigned
created_at: 2026-08-30
updated_at: 2026-08-30
progress: 0
effort: L
value: high
dependencies: [BL-046]
tags: [crm, mock-source, event-generator, api, testing]
target_release: null
---

# Backlog 47: CRM Mock Source and Event Generator

## Muc tieu

Tao nguon CRM gia lap co du lieu va event tai hien duoc cho ingestion pipeline.

## Pham vi

- Sinh lead, contact, account, opportunity, activity va campaign.
- Sinh event create/update/convert/win/lost/close.
- Tao du lieu happy path, invalid record, duplicate va late-arriving event.
- Ho tro batch API va event stream.
- Healthcheck, seed data va reset data cho test.

## Ket qua mong muon

Pipeline co nguon CRM doc lap de test batch, incremental, CDC va data quality.
