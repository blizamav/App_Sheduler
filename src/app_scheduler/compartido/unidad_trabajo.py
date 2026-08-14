"""Unidad de trabajo explicita para operaciones SQL multi-repositorio."""

from __future__ import annotations

from app_scheduler.compartido.base_datos import ConexionDBAPI, ProveedorConexionesSQLServer
from app_scheduler.compartido.errores import ErrorPersistencia


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
        conexion = self.obtener_conexion()
        try:
            conexion.commit()
        except Exception as error:
            raise ErrorPersistencia(
                detalle_tecnico=f"Fallo al confirmar transaccion: {error.__class__.__name__}."
            ) from error
        self._finalizada = True

    def revertir(self) -> None:
        if self.conexion is not None and not self._finalizada:
            try:
                self.conexion.rollback()
            except Exception as error:
                raise ErrorPersistencia(
                    detalle_tecnico=f"Fallo al revertir transaccion: {error.__class__.__name__}."
                ) from error
            self._finalizada = True

    def obtener_conexion(self) -> ConexionDBAPI:
        if self.conexion is None:
            raise RuntimeError("La unidad de trabajo no esta abierta.")
        return self.conexion

    def __exit__(self, tipo_error, _error, _traceback) -> bool:
        try:
            if self.conexion is not None and not self._finalizada:
                try:
                    self.conexion.rollback()
                except Exception as error:
                    raise ErrorPersistencia(
                        detalle_tecnico=(
                            "Fallo al revertir transaccion durante el cierre: "
                            f"{error.__class__.__name__}."
                        )
                    ) from error
        finally:
            if self.conexion is not None:
                self.conexion.close()
            self.conexion = None
            self._finalizada = True
        return False
