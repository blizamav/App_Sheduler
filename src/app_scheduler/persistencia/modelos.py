"""DTO inmutables de persistencia para los modulos fundacionales."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

from app_scheduler.compartido.errores import ErrorValidacion


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Paginacion:
    pagina: int = 1
    por_pagina: int = 50

    def __post_init__(self) -> None:
        if self.pagina < 1:
            raise ErrorValidacion("La pagina debe ser mayor o igual a 1.")
        if not 1 <= self.por_pagina <= 200:
            raise ErrorValidacion("El tamano de pagina debe estar entre 1 y 200.")

    @property
    def desplazamiento(self) -> int:
        return (self.pagina - 1) * self.por_pagina


@dataclass(frozen=True, slots=True)
class Pagina(Generic[T]):
    elementos: tuple[T, ...]
    total: int
    pagina: int
    por_pagina: int

    @property
    def total_paginas(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.por_pagina - 1) // self.por_pagina


@dataclass(frozen=True, slots=True)
class Usuario:
    id_usuario: int
    usuario: str
    nombre_completo: str
    email: str | None
    debe_cambiar_password: bool
    ultimo_login: datetime | None
    intentos_fallidos: int
    bloqueado: bool
    eliminado_operativo: bool
    fecha_eliminado_operativo: datetime | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class CredencialUsuario:
    usuario: Usuario
    password_hash: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class Rol:
    id_rol: int
    codigo_rol: str
    nombre_rol: str
    descripcion: str | None
    es_sistema: bool
    activo: bool


@dataclass(frozen=True, slots=True)
class Permiso:
    id_permiso: int
    codigo_permiso: str
    modulo: str
    accion: str
    descripcion: str | None
    activo: bool


@dataclass(frozen=True, slots=True)
class EventoAuditoria:
    usuario: str
    accion: str
    entidad: str
    id_usuario: int | None = None
    id_entidad: str | None = None
    nombre_entidad: str | None = None
    descripcion: str | None = None
    valores_antes: str | None = None
    valores_despues: str | None = None
    ip_origen: str | None = None
    user_agent: str | None = None
    resultado: str = "OK"
    modulo: str = "SEGURIDAD"
    ruta: str | None = None
    metodo_http: str | None = None


@dataclass(frozen=True, slots=True)
class Cliente:
    id_cliente: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Categoria:
    id_categoria: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Tipo:
    id_tipo: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Tarea:
    id_tarea: int
    nombre_tarea: str
    descripcion: str | None
    observacion_tecnica: str | None
    id_cliente: int
    cliente: str
    id_categoria: int
    categoria: str
    id_tipo: int
    tipo: str
    tipo_tarea: str
    estado_tarea: str
    permite_ejecucion_manual: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Script:
    id_script: int
    id_tarea: int
    nombre_script: str
    descripcion: str | None
    id_version_activa: int | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class VersionScript:
    id_version: int
    id_script: int
    numero_version: int
    nombre_archivo: str
    ruta_fisica: str
    ruta_relativa: str
    hash_archivo: str
    estado_version: str
    es_activa: bool
    requiere_env: bool
    ruta_env_fisica: str | None
    ruta_env_relativa: str | None
    usuario_carga: str
    fecha_carga: datetime
    observacion: str | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
