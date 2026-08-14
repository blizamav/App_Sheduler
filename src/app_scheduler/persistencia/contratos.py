"""Contratos que consumiran los casos de uso de hitos posteriores."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, TypeVar

from app_scheduler.persistencia.modelos import (
    CredencialUsuario,
    Pagina,
    Paginacion,
    Permiso,
    Rol,
    Usuario,
)


T = TypeVar("T", covariant=True)


class RepositorioUsuariosContrato(Protocol):
    def obtener_por_id(self, id_usuario: int) -> Usuario | None: ...

    def obtener_credencial_por_identificador(
        self, identificador: str
    ) -> CredencialUsuario | None: ...

    def listar(
        self,
        paginacion: Paginacion,
        *,
        activo: bool | None = None,
        busqueda: str | None = None,
    ) -> Pagina[Usuario]: ...

    def actualizar_ultimo_login(
        self, id_usuario: int, fecha: datetime, actor: str
    ) -> bool: ...


class RepositorioSeguridadContrato(Protocol):
    def listar_roles(self, *, solo_activos: bool = True) -> tuple[Rol, ...]: ...

    def listar_permisos(self, *, solo_activos: bool = True) -> tuple[Permiso, ...]: ...

    def obtener_roles_usuario(self, id_usuario: int) -> tuple[Rol, ...]: ...

    def obtener_permisos_efectivos(self, id_usuario: int) -> tuple[Permiso, ...]: ...


class RepositorioCatalogoContrato(Protocol[T]):
    def obtener_por_id(self, identificador: int) -> T | None: ...

    def buscar_por_clave(self, nombre_normalizado: str) -> T | None: ...

    def listar(
        self, *, solo_activos: bool = False, incluir_eliminados: bool = False
    ) -> tuple[T, ...]: ...
