# Source Business Rule Validation

## Boundary and routing

Business validation runs after source-to-canonical mapping and structural JSON
Schema validation, before a record is admitted to the accepted Silver dataset.
Bronze remains immutable for audit and replay.

| Status | Meaning | Destination |
|---|---|---|
| `ACCEPTED` | Schema and all applicable business rules pass | accepted Silver |
| `REJECTED` | A deterministic business violation is proven | quarantine/DLQ |
| `QUARANTINED` | Schema is invalid or relationship context is unavailable | quarantine/DLQ |

Every result contains a deterministic `validation_id` derived from entity,
source system, source key, event time and rule version. Replaying the same
record under the same rule version therefore produces the same identifier.
Errors contain code, message, path, disposition, source system, source record
key, validation time and rule version.

## Rule version

The executable catalog is `contracts/rules/business_rules.yaml`. Version
`1.0.0` covers order, order line, inventory, shipment, payment and return.
Changing semantics or state transitions requires a version change; prior
results retain their original `rule_version`.

## Context contract

Cross-record checks require explicit context. Missing context is quarantined
rather than guessed.

| Entity | Context |
|---|---|
| Order | Optional `previous_status` |
| Order line | `known_order_keys` collection |
| Inventory | Optional `stock_moves` list with `move_type`, `quantity`, `unit_cost`, `move_value` |
| Shipment | `known_order_keys`, `order_date`, optional `previous_status`, `sla_max_days`, and `delivery_attempts` |
| Payment | `invoice` with invoice/order/customer keys, gross/discount/tax/net amounts, `amount_paid`, `invoice_date`; optional `previous_status` |
| Return | `order_line` with `sold_qty`, `previous_returned_qty`, `net_amount`, `order_date`, `order_status` |

## Rule groups

- Keys and relationships: verify derived business key and referenced entities.
- State: validate order, shipment and payment transitions.
- Money: reconcile order/order-line totals, invoice outstanding payment and
  proportional refund.
- Inventory: reconcile on-hand/reserved/available, lot dates and stock movement
  sign/value.
- Time: validate order, shipment, delivery, invoice/payment and return order.

SLA lateness by itself is an operational event, not corrupt data; chronological
impossibilities are rejected, while a late-but-valid delivery remains accepted
for downstream SLA analytics.

## Usage and replay

```python
result = business_validator.validate(entity, canonical_record, context=context)
if result.is_accepted:
    write_accepted(result.as_dict())
else:
    upsert_quarantine(result.validation_id, result.as_dict())
```

Quarantine storage should upsert by `validation_id`. After correcting source
data or supplying missing context, replay through contract validation and the
same rule version; accepted output can then proceed downstream.
