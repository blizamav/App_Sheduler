"""Casos de uso de login, identidad vigente y logout."""

from __future__ import annotations

import hmac
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from werkzeug.security import check_password_hash

from app_scheduler.compartido.auditoria import ContextoAuditoria, crear_evento_auditoria
from app_scheduler.compartido.autorizacion import (
    IdentidadSesion,
    TIPO_BASE_DATOS,
    TIPO_SUPER_ADMIN_ENV,
)
from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_seguridad import RepositorioSeguridad
from app_scheduler.persistencia.repositorio_usuarios import RepositorioUsuarios


MENSAJE_CREDENCIALES_INVALIDAS = "Usuario o contrasena incorrectos."


@dataclass(frozen=True, slots=True)
class ResultadoAutenticacion:
    exito: bool
    mensaje: str
    identidad: IdentidadSesion | None = None


class ServicioAutenticacion:
    def __init__(
        self,
        configuracion: ConfiguracionAplicacion,
        proveedor,
        *,
        fabrica_uow: Callable = UnidadTrabajoSQL,
        repositorio_usuarios=RepositorioUsuarios,
        repositorio_seguridad=RepositorioSeguridad,
        repositorio_auditoria=RepositorioAuditoria,
        reloj: Callable[[], datetime] = datetime.now,
        logger: logging.Logger | None = None,
    ):
        self.configuracion = configuracion
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio_usuarios = repositorio_usuarios
        self.tipo_repositorio_seguridad = repositorio_seguridad
        self.tipo_repositorio_auditoria = repositorio_auditoria
        self.reloj = reloj
        self.logger = logger or logging.getLogger("app_scheduler.autenticacion")

    def autenticar(
        self,
        usuario: str,
        password: str,
        contexto: ContextoAuditoria,
    ) -> ResultadoAutenticacion:
        usuario = str(usuario or "").strip()
        password = str(password or "")
        if not usuario or not password or len(usuario) > 100 or len(password) > 4096:
            self._auditar_tolerante(
                crear_evento_auditoria(
                    usuario=usuario[:100] or "anonimo",
                    accion="LOGIN_FALLIDO",
                    entidad="autenticacion",
                    descripcion="Entrada de autenticacion no valida.",
                    resultado="ERROR",
                    contexto=contexto,
                )
            )
            return ResultadoAutenticacion(False, MENSAJE_CREDENCIALES_INVALIDAS)

        if self._coincide_super_admin_env(usuario, password):
            identidad = self._identidad_super_admin_env()
            self._auditar_tolerante(
                crear_evento_auditoria(
                    usuario=identidad.usuario,
                    accion="LOGIN_OK",
                    entidad="autenticacion",
                    nombre_entidad="SUPER_ADMIN_ENV",
                    descripcion="Login de recuperacion desde configuracion segura.",
                    contexto=contexto,
                )
            )
            return ResultadoAutenticacion(True, "Sesion iniciada correctamente.", identidad)

        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            auditoria = self.tipo_repositorio_auditoria(conexion)
            credencial = usuarios.obtener_credencial_por_identificador(usuario)

            if credencial is None:
                auditoria.registrar(
                    crear_evento_auditoria(
                        usuario=usuario,
                        accion="LOGIN_FALLIDO",
                        entidad="autenticacion",
                        descripcion="Credenciales no validas.",
                        resultado="ERROR",
                        contexto=contexto,
                    )
                )
                uow.confirmar()
                return ResultadoAutenticacion(False, MENSAJE_CREDENCIALES_INVALIDAS)

            usuario_bd = credencial.usuario
            habilitado = (
                usuario_bd.activo
                and not usuario_bd.bloqueado
                and not usuario_bd.eliminado_operativo
            )
            password_valido = False
            if habilitado:
                try:
                    password_valido = check_password_hash(credencial.password_hash, password)
                except (TypeError, ValueError):
                    password_valido = False

            if not habilitado or not password_valido:
                if habilitado:
                    usuarios.incrementar_intentos_fallidos(usuario_bd.id_usuario)
                auditoria.registrar(
                    crear_evento_auditoria(
                        usuario=usuario,
                        id_usuario=usuario_bd.id_usuario,
                        accion="LOGIN_FALLIDO",
                        entidad="autenticacion",
                        descripcion="Credenciales o estado no validos.",
                        resultado="ERROR",
                        contexto=contexto,
                    )
                )
                uow.confirmar()
                return ResultadoAutenticacion(False, MENSAJE_CREDENCIALES_INVALIDAS)

            roles = seguridad.obtener_roles_usuario(usuario_bd.id_usuario)
            permisos = seguridad.obtener_permisos_efectivos(usuario_bd.id_usuario)
            usuarios.actualizar_ultimo_login(
                usuario_bd.id_usuario,
                self.reloj(),
                usuario_bd.usuario,
            )
            auditoria.registrar(
                crear_evento_auditoria(
                    usuario=usuario_bd.usuario,
                    id_usuario=usuario_bd.id_usuario,
                    accion="LOGIN_OK",
                    entidad="autenticacion",
                    id_entidad=usuario_bd.id_usuario,
                    nombre_entidad=usuario_bd.usuario,
                    descripcion="Login correcto con usuario de APP Scheduler.",
                    contexto=contexto,
                )
            )
            uow.confirmar()
            identidad = self._crear_identidad_db(usuario_bd, roles, permisos)
            return ResultadoAutenticacion(True, "Sesion iniciada correctamente.", identidad)

    def cargar_identidad(self, datos_sesion: dict[str, object]) -> IdentidadSesion | None:
        tipo = str(datos_sesion.get("tipo") or "")
        if tipo == TIPO_SUPER_ADMIN_ENV:
            usuario = str(datos_sesion.get("usuario") or "")
            if hmac.compare_digest(usuario, self.configuracion.usuario_admin_defecto):
                return self._identidad_super_admin_env()
            return None
        if tipo != TIPO_BASE_DATOS:
            return None
        try:
            id_usuario = int(datos_sesion.get("id_usuario"))
        except (TypeError, ValueError):
            return None
        with self.proveedor.conexion_lectura() as conexion:
            usuarios = self.tipo_repositorio_usuarios(conexion)
            seguridad = self.tipo_repositorio_seguridad(conexion)
            usuario = usuarios.obtener_por_id(id_usuario)
            if (
                usuario is None
                or not usuario.activo
                or usuario.bloqueado
                or usuario.eliminado_operativo
            ):
                return None
            return self._crear_identidad_db(
                usuario,
                seguridad.obtener_roles_usuario(id_usuario),
                seguridad.obtener_permisos_efectivos(id_usuario),
            )

    def registrar_logout(
        self,
        identidad: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> None:
        self._auditar_tolerante(
            crear_evento_auditoria(
                usuario=identidad.usuario,
                id_usuario=identidad.id_usuario,
                accion="LOGOUT",
                entidad="autenticacion",
                id_entidad=identidad.id_usuario,
                nombre_entidad=identidad.usuario,
                descripcion="Sesion cerrada por el usuario.",
                contexto=contexto,
            )
        )

    def _coincide_super_admin_env(self, usuario: str, password: str) -> bool:
        usuario_ok = hmac.compare_digest(usuario, self.configuracion.usuario_admin_defecto)
        password_ok = hmac.compare_digest(password, self.configuracion.password_admin_defecto)
        return usuario_ok and password_ok

    def _identidad_super_admin_env(self) -> IdentidadSesion:
        usuario = self.configuracion.usuario_admin_defecto
        return IdentidadSesion(
            id_usuario=None,
            usuario=usuario,
            nombre=usuario,
            tipo_identidad=TIPO_SUPER_ADMIN_ENV,
            roles=frozenset({TIPO_SUPER_ADMIN_ENV}),
            permisos=frozenset({"*"}),
        )

    @staticmethod
    def _crear_identidad_db(usuario, roles, permisos) -> IdentidadSesion:
        return IdentidadSesion(
            id_usuario=usuario.id_usuario,
            usuario=usuario.usuario,
            nombre=usuario.nombre_completo,
            tipo_identidad=TIPO_BASE_DATOS,
            roles=frozenset(rol.codigo_rol for rol in roles),
            permisos=frozenset(permiso.codigo_permiso for permiso in permisos),
        )

    def _auditar_tolerante(self, evento) -> None:
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                self.tipo_repositorio_auditoria(uow.obtener_conexion()).registrar(evento)
                uow.confirmar()
        except ErrorPersistencia:
            self.logger.warning(
                "Auditoria de autenticacion no disponible.",
                extra={"evento": "AUDITORIA_AUTH_NO_DISPONIBLE"},
            )
