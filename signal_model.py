#signal_model.py
from __future__ import annotations

"""signal_model.py – Modelo de señal mínimo pero completo para Anima REX.

Campos obligatorios (los únicos que realmente usa el flujo actual):
    pair        → par/activo (ej. "EURUSD")
    direction   → "CALL" o "PUT" (se normaliza a mayúsculas)
    strategy    → nombre de la estrategia
    timestamp   → fecha‑hora UTC auto‑generada

Incluye:
    • Validación de dirección.
    • Serialización a/desde dict con timestamp ISO‑8601.
    • __repr__ legible y __hash__ para sets/dicts.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Literal
import logging

logger = logging.getLogger(__name__)

VALID_DIRECTIONS: tuple[str, ...] = ("CALL", "PUT")


@dataclass(slots=True)
class Signal:
    pair: str
    direction: Literal["CALL", "PUT"]
    strategy: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def __post_init__(self):
        dir_up = self.direction.upper()
        if dir_up not in VALID_DIRECTIONS:
            raise ValueError(f"direction debe ser CALL o PUT, no '{self.direction}'")
        object.__setattr__(self, "direction", dir_up)

    # ------------------------------------------------------------------
    # Serialización
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signal":
        data = dict(data)
        ts = data.get("timestamp")
        if isinstance(ts, str):
            data["timestamp"] = datetime.fromisoformat(ts)
        return cls(**data)

    # ------------------------------------------------------------------
    # Representación y hashing
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return (f"<Signal {self.timestamp:%Y-%m-%d %H:%M:%S%z} | "
                f"{self.pair} | {self.direction} | {self.strategy}>")

    def __hash__(self) -> int:  # usable en sets/dicts
        return hash((self.timestamp, self.pair, self.strategy, self.direction))
