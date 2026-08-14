"""Casos de uso transaccionales de usuarios y asociaciones de rol."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Mapping

from werkzeug.security import generate_password_hash

from app_scheduler.compartido.auditoria import ContextoAuditoria, crear_evento_auditoria
from app_scheduler.compartido.autorizacion import IdentidadSesion
from app_scheduler.compartido.errores import ErrorAutorizacion, ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Pagina, Paginacion, Permiso, Rol, Usuario
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_seguridad import RepositorioSeguridad
from app_scheduler.persistencia.repositorio_usuarios import RepositorioUsuarios


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USUARIO_RE = re.compile(r"^[A-Za-z0-9._@-]{3,100}$")
ROL_SUPER_ADMIN = "SUPER_ADMIN"


@dataclass(frozen=True, slots=True)
class UsuarioConRoles:
    usuario: Usuario
    roles: tuple[Rol, ...]

    @property
    def rol_principal(self) -> Rol | None:
        return self.roles[0] if self.roles else None


@dataclass(frozen=True, slots=True)
class PaginaUsuarios:
    elementos: tuple[UsuarioConRoles, ...]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


@dataclass(frozen=True, slots=True)
class ResumenSeguridad:
    roles: tuple[Rol, ...]
    permisos: tuple[Permiso, ...]
    matriz: dict[str, frozenset[str]]


class ServicioUsuarios:
    def __init__(
        self,
        proveedor,
        *,
        fabrica_uow: Callable = UnidadTrabajoSQL,
        repositorio_usuarios=RepositorioUsuarios,
        repositorio_seguridad=RepositorioSeguridad,
        repositorio_auditoria=RepositorioAuditoria,
        generar_hash: Callable[[str], str] = generate_password_hash,
    ):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio_usuarios = repositorio_usuarios
        self.tipo_repositorio_seguridad = repositorio_seguridad
        self.tipo_repositorio_auditoria = repositorio_auditoria
        self.generar_hash = generar_hash

    def listar(
        self,
        *,
        pagina: int = 1,
        por_pagina: int = 25,
        activo: bool | None = None,
        busqueda: str | None = None,
        id_rol: int | None = None,
    ) -> PaginaUsuarios:
        with self.proveedor.conexion_lectura() as conexion:
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            resultado: Pagina[Usuario] = usuarios.listar(
                Paginacion(pagina, por_pagina),
                activo=activo,
                busqueda=busqueda,
                id_rol=id_rol,
            )
            roles = seguridad.obtener_roles_por_usuarios(
                [usuario.id_usuario for usuario in resultado.elementos]
            )
        return PaginaUsuarios(
            elementos=tuple(
                UsuarioConRoles(usuario, roles.get(usuario.id_usuario, ()))
                for usuario in resultado.elementos
            ),
            total=resultado.total,
            pagina=resultado.pagina,
            por_pagina=resultado.por_pagina,
            total_paginas=resultado.total_paginas,
        )

    def obtener(self, id_usuario: int) -> UsuarioConRoles | None:
        with self.proveedor.conexion_lectura() as conexion:
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            usuario = usuarios.obtener_por_id(id_usuario)
            if usuario is None:
                return None
            return UsuarioConRoles(usuario, seguridad.obtener_roles_usuario(id_usuario))

    def roles_disponibles(self, actor: IdentidadSesion) -> tuple[Rol, ...]:
        with self.proveedor.conexion_lectura() as conexion:
            roles = self.tipo_repositorio_seguridad(conexion).listar_roles()
        if self._actor_super_admin(actor):
            return roles
        return tuple(rol for rol in roles if rol.codigo_rol != ROL_SUPER_ADMIN)

    def crear(
        self,
        datos: Mapping[str, object],
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> int:
        normalizados = self._validar_datos(datos, modo="crear")
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            auditoria = self.tipo_repositorio_auditoria(conexion)
            rol = self._rol_valido(seguridad, normalizados["id_rol"])
            self._validar_asignacion_super_admin(actor, rol)
            if usuarios.existe_usuario(normalizados["usuario"]):
                raise ErrorValidacion("El identificador de usuario ya existe.")
            if normalizados["email"] and usuarios.existe_email(normalizados["email"]):
                raise ErrorValidacion("El correo ya esta asociado a otro usuario.")
            id_usuario = usuarios.crear(
                normalizados["usuario"],
                normalizados["nombre_completo"],
                normalizados["email"],
                self.generar_hash(normalizados["password"]),
                normalizados["activo"],
                actor.usuario,
            )
            seguridad.asignar_rol_usuario(id_usuario, rol.id_rol, actor.usuario)
            auditoria.registrar(
                crear_evento_auditoria(
                    usuario=actor.usuario,
                    id_usuario=actor.id_usuario,
                    accion="USUARIO_CREADO",
                    entidad="usuarios",
                    id_entidad=id_usuario,
                    nombre_entidad=normalizados["usuario"],
                    descripcion="Usuario creado en APP Scheduler.",
                    valores_despues={
                        "usuario": normalizados["usuario"],
                        "nombre_completo": normalizados["nombre_completo"],
                        "email": normalizados["email"],
                        "activo": normalizados["activo"],
                        "codigo_rol": rol.codigo_rol,
                    },
                    contexto=contexto,
                    modulo="USUARIOS",
                )
            )
            uow.confirmar()
            return id_usuario

    def actualizar(
        self,
        id_usuario: int,
        datos: Mapping[str, object],
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> None:
        normalizados = self._validar_datos(datos, modo="editar")
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            auditoria = self.tipo_repositorio_auditoria(conexion)
            actual = usuarios.obtener_por_id(id_usuario)
            if actual is None:
                raise ErrorValidacion("Usuario no encontrado.")
            roles_actuales = seguridad.obtener_roles_usuario(id_usuario)
            rol_anterior = roles_actuales[0] if roles_actuales else None
            rol_nuevo = self._rol_valido(seguridad, normalizados["id_rol"])
            self._validar_objetivo_super_admin(actor, actual, rol_anterior)
            self._validar_asignacion_super_admin(actor, rol_nuevo)
            if (
                rol_anterior
                and rol_anterior.codigo_rol == ROL_SUPER_ADMIN
                and rol_nuevo.codigo_rol != ROL_SUPER_ADMIN
                and seguridad.contar_super_admin_activos(excluir_id=id_usuario) == 0
            ):
                raise ErrorValidacion("No puedes quitar el ultimo SUPER_ADMIN activo.")
            if normalizados["email"] and usuarios.existe_email(
                normalizados["email"], excluir_id=id_usuario
            ):
                raise ErrorValidacion("El correo ya esta asociado a otro usuario.")
            password_hash = (
                self.generar_hash(normalizados["password"])
                if normalizados["password"]
                else None
            )
            usuarios.actualizar(
                id_usuario,
                normalizados["nombre_completo"],
                normalizados["email"],
                actor.usuario,
                password_hash,
            )
            seguridad.asignar_rol_usuario(id_usuario, rol_nuevo.id_rol, actor.usuario)
            auditoria.registrar(
                crear_evento_auditoria(
                    usuario=actor.usuario,
                    id_usuario=actor.id_usuario,
                    accion="USUARIO_EDITADO",
                    entidad="usuarios",
                    id_entidad=id_usuario,
                    nombre_entidad=actual.usuario,
                    descripcion="Datos de usuario actualizados.",
                    valores_antes={
                        "nombre_completo": actual.nombre_completo,
                        "email": actual.email,
                        "codigo_rol": rol_anterior.codigo_rol if rol_anterior else None,
                    },
                    valores_despues={
                        "nombre_completo": normalizados["nombre_completo"],
                        "email": normalizados["email"],
                        "codigo_rol": rol_nuevo.codigo_rol,
                        "credencial_actualizada": bool(password_hash),
                    },
                    contexto=contexto,
                    modulo="USUARIOS",
                )
            )
            if rol_anterior is None or rol_anterior.id_rol != rol_nuevo.id_rol:
                auditoria.registrar(
                    crear_evento_auditoria(
                        usuario=actor.usuario,
                        id_usuario=actor.id_usuario,
                        accion="ROLES_USUARIO_MODIFICADOS",
                        entidad="usuarios",
                        id_entidad=id_usuario,
                        nombre_entidad=actual.usuario,
                        valores_antes={
                            "codigo_rol": rol_anterior.codigo_rol if rol_anterior else None
                        },
                        valores_despues={"codigo_rol": rol_nuevo.codigo_rol},
                        contexto=contexto,
                        modulo="USUARIOS",
                    )
                )
            uow.confirmar()

    def cambiar_estado(
        self,
        id_usuario: int,
        activo: bool,
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            auditoria = self.tipo_repositorio_auditoria(conexion)
            actual = usuarios.obtener_por_id(id_usuario)
            if actual is None:
                raise ErrorValidacion("Usuario no encontrado.")
            roles = seguridad.obtener_roles_usuario(id_usuario)
            rol = roles[0] if roles else None
            self._validar_objetivo_super_admin(actor, actual, rol)
            if not activo and actor.id_usuario == id_usuario:
                raise ErrorValidacion("No puedes desactivar el usuario de tu sesion actual.")
            if (
                not activo
                and rol
                and rol.codigo_rol == ROL_SUPER_ADMIN
                and seguridad.contar_super_admin_activos(excluir_id=id_usuario) == 0
            ):
                raise ErrorValidacion("No puedes desactivar el ultimo SUPER_ADMIN activo.")
            usuarios.cambiar_estado(id_usuario, activo, actor.usuario)
            auditoria.registrar(
                crear_evento_auditoria(
                    usuario=actor.usuario,
                    id_usuario=actor.id_usuario,
                    accion="USUARIO_ACTIVADO" if activo else "USUARIO_DESACTIVADO",
                    entidad="usuarios",
                    id_entidad=id_usuario,
                    nombre_entidad=actual.usuario,
                    descripcion="Estado de usuario actualizado.",
                    valores_antes={"activo": actual.activo},
                    valores_despues={"activo": activo},
                    contexto=contexto,
                    modulo="USUARIOS",
                )
            )
            uow.confirmar()

    def resumen_seguridad(self) -> ResumenSeguridad:
        with self.proveedor.conexion_lectura() as conexion:
            seguridad = self.tipo_repositorio_seguridad(conexion)
            return ResumenSeguridad(
                roles=seguridad.listar_roles(),
                permisos=seguridad.listar_permisos(),
                matriz=seguridad.obtener_matriz_roles_permisos(),
            )

    @staticmethod
    def _validar_datos(datos: Mapping[str, object], *, modo: str) -> dict[str, object]:
        usuario = str(datos.get("usuario") or "").strip()
        nombre = str(datos.get("nombre_completo") or "").strip()
        email = str(datos.get("email") or "").strip() or None
        password = str(datos.get("password") or "")
        confirmacion = str(datos.get("confirmacion_password") or "")
        try:
            id_rol = int(datos.get("id_rol"))
        except (TypeError, ValueError):
            id_rol = 0
        errores = []
        if modo == "crear" and not USUARIO_RE.fullmatch(usuario):
            errores.append("El usuario debe tener entre 3 y 100 caracteres validos.")
        if not nombre or len(nombre) > 200:
            errores.append("El nombre completo es obligatorio y admite hasta 200 caracteres.")
        if email and (len(email) > 200 or not EMAIL_RE.fullmatch(email)):
            errores.append("El correo informado no tiene un formato valido.")
        if id_rol <= 0:
            errores.append("Debes seleccionar un rol valido.")
        if modo == "crear" and not password:
            errores.append("La contrasena es obligatoria.")
        if password or confirmacion:
            if password != confirmacion:
                errores.append("La confirmacion de contrasena no coincide.")
            elif len(password) < 8:
                errores.append("La contrasena debe tener al menos 8 caracteres.")
        if errores:
            raise ErrorValidacion(" ".join(errores))
        return {
            "usuario": usuario,
            "nombre_completo": nombre,
            "email": email,
            "password": password,
            "id_rol": id_rol,
            "activo": str(datos.get("activo") or "") in {"1", "true", "on", "True"},
        }

    @staticmethod
    def _rol_valido(seguridad, id_rol: int) -> Rol:
        rol = seguridad.obtener_rol_por_id(id_rol)
        if rol is None:
            raise ErrorValidacion("El rol seleccionado no es valido.")
        return rol

    @staticmethod
    def _actor_super_admin(actor: IdentidadSesion) -> bool:
        return actor.es_super_admin_env or ROL_SUPER_ADMIN in actor.roles

    def _validar_asignacion_super_admin(self, actor: IdentidadSesion, rol: Rol) -> None:
        if rol.codigo_rol == ROL_SUPER_ADMIN and not self._actor_super_admin(actor):
            raise ErrorAutorizacion("Solo un SUPER_ADMIN puede asignar ese rol.")

    def _validar_objetivo_super_admin(
        self,
        actor: IdentidadSesion,
        usuario: Usuario,
        rol: Rol | None,
    ) -> None:
        if rol and rol.codigo_rol == ROL_SUPER_ADMIN and not self._actor_super_admin(actor):
            raise ErrorAutorizacion("Solo un SUPER_ADMIN puede modificar ese usuario.")
