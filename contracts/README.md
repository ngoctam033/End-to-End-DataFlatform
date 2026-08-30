# Canonical data contracts

This directory contains the executable contracts for records entering the
Canonical Silver layer. Version `1.0.0` uses JSON Schema Draft 2020-12 written
as YAML.

## Layout

- `schemas/common.yaml`: shared metadata-envelope definitions.
- `schemas/{entity}.yaml`: envelope plus the canonical payload for one entity.
- `mappings/source_mapping_matrix.yaml`: tested source-to-canonical mapping metadata.
- `tests/fixtures/contracts/valid_records.yaml`: representative valid records.
- `tests/fixtures/contracts/multi_source_records.yaml`: canonical records mapped from every source profile.

The six supported entities are `order`, `order_line`, `inventory`, `shipment`,
`return`, and `payment`. A contract validates a canonical record after source
mapping; it does not validate the immutable Bronze source payload.

## Python validator

`DataContractValidator` loads and caches the YAML schemas, constructs the
metadata envelope, validates it, and returns a routing-friendly result:

```python
from contracts import DataContractValidator

validator = DataContractValidator()
result = validator.validate_payload(
    "order",
    mapped_order_payload,
    business_key="ORD-POSTGRES_ERP-SO-1001",
    source_key="SO-1001",
    source_system="postgres_erp",
    event_time="2026-08-28T01:30:00Z",
)

if result.is_valid:
    write_silver(result.record)
else:
    write_dlq(result.as_dict())
```

Valid results have `processing_status=VALID` and `destination=silver`.
Invalid results preserve the submitted payload, use
`processing_status=QUARANTINED`, route to `quarantine`, and include structured
JSON Schema errors. The validator performs structural contract validation;
source mapping and cross-record business rules remain separate stages.

## Validate locally

From the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest -v tests.test_contract_schemas
python -m unittest -v tests.test_source_mapping_matrix
python -m unittest -v tests.test_contract_validator
pytest -q tests/test_contracts.py
```

The tests load every YAML document, verify it against the Draft 2020-12
meta-schema, resolve references to `common.yaml`, accept the valid fixtures,
and reject representative missing-field, wrong-type, and invalid-enum cases.

## Evolution rules

Contract versions follow the policy in
`docs/data_contracts/02_schema_evolution_policy.md`. Update `$id`, `version`,
and the envelope `schema_version` together when publishing a new version.
Cross-record business rules (for example payment versus invoice outstanding,
or return quantity versus sold quantity) belong to BL-030 rather than these
structural contracts.
