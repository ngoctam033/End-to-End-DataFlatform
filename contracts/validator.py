"""Validate mapped payloads against versioned canonical data contracts.

The validator operates at the Bronze-to-Silver boundary. It never mutates the
caller's payload and never discards an invalid record: callers receive a
QUARANTINED envelope plus structured errors suitable for a DLQ.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


DEFAULT_SCHEMA_DIRECTORY = Path(__file__).resolve().parent / "schemas"
RESERVED_SCHEMA_NAMES = frozenset({"common"})


class ContractConfigurationError(RuntimeError):
    """Raised when schemas are missing, malformed, or internally inconsistent."""


@dataclass(frozen=True)
class ContractValidationError:
    """Serializable detail for one JSON Schema validation failure."""

    code: str
    path: str
    message: str
    validator: str
    schema_path: str


@dataclass(frozen=True)
class ContractValidationResult:
    """A canonical record and the errors that determine its routing."""

    entity: str
    record: dict[str, Any]
    errors: tuple[ContractValidationError, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def destination(self) -> str:
        return "silver" if self.is_valid else "quarantine"

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "is_valid": self.is_valid,
            "destination": self.destination,
            "record": copy.deepcopy(self.record),
            "errors": [asdict(error) for error in self.errors],
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("ingestion_time datetime must include timezone information")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


@lru_cache(maxsize=128)
def _load_yaml_schema(path_string: str) -> dict[str, Any]:
    """Load a schema once per resolved path and return its parsed document."""

    path = Path(path_string)
    try:
        with path.open(encoding="utf-8") as stream:
            schema = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as error:
        raise ContractConfigurationError(f"Cannot load contract schema {path}: {error}") from error
    if not isinstance(schema, dict):
        raise ContractConfigurationError(f"Contract schema {path} must be a YAML object")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise ContractConfigurationError(f"Invalid JSON Schema in {path}: {error}") from error
    if not isinstance(schema.get("$id"), str):
        raise ContractConfigurationError(f"Contract schema {path} must define a string $id")
    return schema


def clear_schema_cache() -> None:
    """Clear the process schema cache, primarily for tests and controlled reloads."""

    _load_yaml_schema.cache_clear()


def schema_cache_info():
    """Expose cache statistics without exposing the cached mutable documents."""

    return _load_yaml_schema.cache_info()


class DataContractValidator:
    """Load canonical schemas and validate mapped entity payloads."""

    def __init__(
        self,
        schema_directory: str | Path = DEFAULT_SCHEMA_DIRECTORY,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.schema_directory = Path(schema_directory).resolve()
        self._clock = clock
        self._schemas = self._load_schema_set()
        resources = [
            (schema["$id"], Resource.from_contents(schema))
            for schema in self._schemas.values()
        ]
        self._registry = Registry().with_resources(resources)
        self._validators = {
            entity: Draft202012Validator(
                schema,
                registry=self._registry,
                format_checker=FormatChecker(),
            )
            for entity, schema in self._schemas.items()
            if entity not in RESERVED_SCHEMA_NAMES
        }
        if not self._validators:
            raise ContractConfigurationError(
                f"No entity schemas found in {self.schema_directory}"
            )

    @property
    def supported_entities(self) -> tuple[str, ...]:
        return tuple(sorted(self._validators))

    def schema_version(self, entity: str) -> str:
        self._require_entity(entity)
        version = self._schemas[entity].get("version")
        if not isinstance(version, str) or not version:
            raise ContractConfigurationError(
                f"Entity schema {entity!r} must define a non-empty version"
            )
        return version

    def validate_payload(
        self,
        entity: str,
        payload: Mapping[str, Any],
        *,
        business_key: str,
        source_key: str,
        source_system: str,
        event_time: str,
        ingestion_time: str | datetime | None = None,
    ) -> ContractValidationResult:
        """Build an envelope, validate it, and assign VALID or QUARANTINED."""

        self._require_entity(entity)
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        received_at = self._resolve_ingestion_time(ingestion_time)
        record: dict[str, Any] = {
            "business_key": business_key,
            "source_key": source_key,
            "source_system": source_system,
            "event_time": event_time,
            "ingestion_time": received_at,
            "schema_version": self.schema_version(entity),
            "processing_status": "VALID",
            "payload": copy.deepcopy(dict(payload)),
        }
        errors = self._validation_errors(entity, record)
        if errors:
            record["processing_status"] = "QUARANTINED"
        return ContractValidationResult(entity=entity, record=record, errors=errors)

    def validate_record(
        self, entity: str, record: Mapping[str, Any]
    ) -> ContractValidationResult:
        """Validate an existing envelope and normalize its routing status."""

        self._require_entity(entity)
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        candidate = copy.deepcopy(dict(record))
        candidate["processing_status"] = "VALID"
        errors = self._validation_errors(entity, candidate)
        if errors:
            candidate["processing_status"] = "QUARANTINED"
        return ContractValidationResult(entity=entity, record=candidate, errors=errors)

    def _load_schema_set(self) -> dict[str, dict[str, Any]]:
        if not self.schema_directory.is_dir():
            raise ContractConfigurationError(
                f"Schema directory does not exist: {self.schema_directory}"
            )
        paths = sorted(self.schema_directory.glob("*.yaml"))
        if not paths:
            raise ContractConfigurationError(
                f"No YAML schemas found in {self.schema_directory}"
            )
        schemas: dict[str, dict[str, Any]] = {}
        ids: set[str] = set()
        for path in paths:
            schema = _load_yaml_schema(str(path.resolve()))
            schema_id = schema["$id"]
            if schema_id in ids:
                raise ContractConfigurationError(f"Duplicate schema $id: {schema_id}")
            ids.add(schema_id)
            schemas[path.stem] = schema
        if "common" not in schemas:
            raise ContractConfigurationError("Required common.yaml schema is missing")
        return schemas

    def _require_entity(self, entity: str) -> None:
        if entity not in self._validators:
            supported = ", ".join(self.supported_entities)
            raise ContractConfigurationError(
                f"Unknown contract entity {entity!r}; supported entities: {supported}"
            )

    def _resolve_ingestion_time(self, value: str | datetime | None) -> str:
        if value is None:
            value = self._clock()
        if isinstance(value, datetime):
            return _format_utc(value)
        if isinstance(value, str):
            return value
        raise TypeError("ingestion_time must be a string, timezone-aware datetime, or None")

    def _validation_errors(
        self, entity: str, record: Mapping[str, Any]
    ) -> tuple[ContractValidationError, ...]:
        raw_errors = sorted(
            self._validators[entity].iter_errors(record),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                tuple(str(part) for part in error.absolute_schema_path),
                error.message,
            ),
        )
        return tuple(self._convert_error(error) for error in raw_errors)

    @staticmethod
    def _convert_error(error) -> ContractValidationError:
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        schema_path = "/" + "/".join(
            str(part) for part in error.absolute_schema_path
        )
        validator_name = str(error.validator or "unknown")
        return ContractValidationError(
            code=f"SCHEMA_{validator_name.upper()}",
            path=path,
            message=error.message,
            validator=validator_name,
            schema_path=schema_path,
        )
