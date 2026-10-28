"""Source-reference metadata; intentionally contains no data values or joined KPIs."""

from __future__ import annotations

from dataclasses import dataclass
import re

_SHA256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Identify one reviewed publisher observation without asserting comparability."""

    source_id: str
    region_id: str
    reference_period: str
    statistical_population: str
    unit: str
    source_sha256: str

    def __post_init__(self) -> None:
        for name in ("source_id", "region_id", "reference_period", "statistical_population", "unit"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        if not isinstance(self.source_sha256, str) or not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("source_sha256 must be a lowercase 64-character SHA-256 digest")
