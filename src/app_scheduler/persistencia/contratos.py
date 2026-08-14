"""Contratos que consumiran los casos de uso de hitos posteriores."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence, TypeVar

from app_scheduler.persistencia.modelos import (
    CredencialUsuario,
    Pagina,
    Paginacion,
    Permiso,
    Rol,
    Usuario,
    EventoAuditoria,
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
        id_rol: int | None = None,
    ) -> Pagina[Usuario]: ...

    def actualizar_ultimo_login(
        self, id_usuario: int, fecha: datetime, actor: str
    ) -> bool: ...

    def crear(
        self,
        usuario: str,
        nombre_completo: str,
        email: str | None,
        password_hash: str,
        activo: bool,
        actor: str,
    ) -> int: ...

    def actualizar(
        self,
        id_usuario: int,
        nombre_completo: str,
        email: str | None,
        actor: str,
        password_hash: str | None = None,
    ) -> bool: ...

    def cambiar_estado(self, id_usuario: int, activo: bool, actor: str) -> bool: ...


class RepositorioSeguridadContrato(Protocol):
    def listar_roles(self, *, solo_activos: bool = True) -> tuple[Rol, ...]: ...

    def listar_permisos(self, *, solo_activos: bool = True) -> tuple[Permiso, ...]: ...

    def obtener_roles_usuario(self, id_usuario: int) -> tuple[Rol, ...]: ...

    def obtener_permisos_efectivos(self, id_usuario: int) -> tuple[Permiso, ...]: ...

    def asignar_rol_usuario(self, id_usuario: int, id_rol: int, actor: str) -> None: ...

    def obtener_roles_por_usuarios(
        self, ids_usuarios: Sequence[int]
    ) -> dict[int, tuple[Rol, ...]]: ...


class RepositorioAuditoriaContrato(Protocol):
    def registrar(self, evento: EventoAuditoria) -> int: ...


class RepositorioCatalogoContrato(Protocol[T]):
    def obtener_por_id(self, identificador: int) -> T | None: ...

    def buscar_por_clave(self, nombre_normalizado: str) -> T | None: ...

    def listar(
        self, *, solo_activos: bool = False, incluir_eliminados: bool = False
    ) -> tuple[T, ...]: ...

    def listar_paginado(
        self,
        paginacion: Paginacion,
        *,
        activo: bool | None = None,
        busqueda: str | None = None,
    ) -> Pagina[T]: ...

    def crear(
        self,
        nombre: str,
        nombre_normalizado: str,
        descripcion: str | None,
        actor: str,
    ) -> int: ...

    def actualizar(
        self,
        identificador: int,
        nombre: str,
        nombre_normalizado: str,
        descripcion: str | None,
        actor: str,
    ) -> bool: ...

    def cambiar_estado(self, identificador: int, activo: bool, actor: str) -> bool: ...
