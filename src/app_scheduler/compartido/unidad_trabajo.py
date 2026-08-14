"""Unidad de trabajo explicita para operaciones SQL multi-repositorio."""

from __future__ import annotations

from app_scheduler.compartido.base_datos import ConexionDBAPI, ProveedorConexionesSQLServer


class UnidadTrabajoSQL:
    def __init__(self, proveedor: ProveedorConexionesSQLServer):
        self._proveedor = proveedor
        self.conexion: ConexionDBAPI | None = None
        self._finalizada = False

    def __enter__(self) -> "UnidadTrabajoSQL":
        self.conexion = self._proveedor.abrir()
        self._finalizada = False
        return self

    def confirmar(self) -> None:
        if self.conexion is None:
            raise RuntimeError("La unidad de trabajo no esta abierta.")
        self.conexion.commit()
        self._finalizada = True

    def revertir(self) -> None:
        if self.conexion is not None and not self._finalizada:
            self.conexion.rollback()
            self._finalizada = True

    def __exit__(self, tipo_error, _error, _traceback) -> bool:
        try:
            if self.conexion is not None and not self._finalizada:
                self.conexion.rollback()
        finally:
            if self.conexion is not None:
                self.conexion.close()
            self.conexion = None
            self._finalizada = True
        return False
