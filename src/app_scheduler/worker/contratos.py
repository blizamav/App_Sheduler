"""Contrato comun para futuras ejecuciones manuales y automaticas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class OrigenEjecucion(str, Enum):
    MANUAL = "MANUAL"
    AUTOMATICA = "AUTOMATICA"


@dataclass(frozen=True, slots=True)
class SolicitudEjecucion:
    id_tarea: int
    id_script: int
    id_version: int
    origen: OrigenEjecucion
    actor: str
    id_programacion: int | None = None


class MotorEjecucion(Protocol):
    def solicitar(self, solicitud: SolicitudEjecucion) -> int:
        """Persiste una solicitud y retorna su identificador."""
        ...


class MotorNoImplementado:
    """Impide ejecutar procesos antes del Hito 7."""

    def solicitar(self, _solicitud: SolicitudEjecucion) -> int:
        raise NotImplementedError("El motor de ejecucion se implementara en Hito 7.")
