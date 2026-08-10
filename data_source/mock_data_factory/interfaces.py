"""Abstract contracts for mock transaction generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from data_source.mock_data_factory.models import BusinessScenarioSet


class TransactionScenarioProvider(ABC):
    """Produces batches of business transaction scenarios."""

    @abstractmethod
    def next_batch(self) -> BusinessScenarioSet:
        """Return the next transaction scenario batch."""


class TransactionWriter(ABC):
    """Writes transaction scenarios to a concrete source system."""

    @abstractmethod
    def write(self, scenario_set: BusinessScenarioSet) -> None:
        """Persist a scenario batch through the target source interface."""
