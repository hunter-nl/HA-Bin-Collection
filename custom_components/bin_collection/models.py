"""Normalized data used by all Bin Collection providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Collection:
    """One scheduled collection."""

    date: date
    waste_type: str
    source_type: str


@dataclass(frozen=True, slots=True)
class Notice:
    """A message published by a collector."""

    id: str
    title: str
    body: str
    published: date | None = None


@dataclass(frozen=True, slots=True)
class BinCollectionData:
    """The normalized result returned by a provider."""

    collections: tuple[Collection, ...]
    notices: tuple[Notice, ...]
