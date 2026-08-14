from __future__ import annotations

from datetime import datetime

import pytest

from app_scheduler.compartido.auditoria import ContextoAuditoria, crear_evento_auditoria
from app_scheduler.compartido.autorizacion import (
    IdentidadSesion,
    TIPO_BASE_DATOS,
    TIPO_SUPER_ADMIN_ENV,
)
from app_scheduler.compartido.errores import ErrorAutorizacion, ErrorValidacion
from app_scheduler.modulos.usuarios.casos_uso import ServicioUsuarios
from app_scheduler.persistencia.modelos import Rol, Usuario


ROL_SUPER = Rol(1, "SUPER_ADMIN", "Super Admin", None, True, True)
ROL_ADMIN = Rol(2, "ADMIN", "Administrador", None, True, True)
ROL_TI = Rol(3, "TI", "TI", None, True, True)


def _usuario(id_usuario=10, usuario="destino", activo=True):
    return Usuario(
        id_usuario=id_usuario,
        usuario=usuario,
        nombre_completo="Usuario Destino",
        email="destino@example.test",
        debe_cambiar_password=False,
        ultimo_login=None,
        intentos_fallidos=0,
        bloqueado=False,
        eliminado_operativo=False,
        fecha_eliminado_operativo=None,
        fecha_creacion=datetime(2026, 1, 1),
        fecha_actualizacion=None,
        activo=activo,
    )


class EstadoUsuarios:
    def __init__(self):
        self.usuarios = {10: _usuario()}
        self.rol_actual = ROL_ADMIN
        self.roles = {1: ROL_SUPER, 2: ROL_ADMIN, 3: ROL_TI}
        self.eventos = []
        self.creados = []
        self.actualizados = []
        self.estados = []
        self.asignaciones = []
        self.confirmaciones = 0
        self.super_admin_restantes = 1
        self.fallar_asignacion = False
        self.reversiones = 0


class UowUsuarios:
    def __init__(self, estado):
        self.estado = estado

    def __enter__(self):
        return self

    def __exit__(self, tipo_error, *_args):
        if tipo_error is not None:
            self.estado.reversiones += 1
        return False

    def obtener_conexion(self):
        return self.estado

    def confirmar(self):
        self.estado.confirmaciones += 1


class RepoUsuarios:
    def __init__(self, estado):
        self.e = estado

    def existe_usuario(self, usuario):
        return any(u.usuario == usuario for u in self.e.usuarios.values())

    def existe_email(self, email, excluir_id=None):
        return any(u.email == email and i != excluir_id for i, u in self.e.usuarios.items())

    def crear(self, usuario, nombre, email, password_hash, activo, actor):
        self.e.creados.append((usuario, nombre, email, password_hash, activo, actor))
        return 11

    def obtener_por_id(self, id_usuario):
        return self.e.usuarios.get(id_usuario)

    def actualizar(self, *args):
        self.e.actualizados.append(args)

    def cambiar_estado(self, *args):
        self.e.estados.append(args)


class RepoSeguridad:
    def __init__(self, estado):
        self.e = estado

    def obtener_rol_por_id(self, id_rol):
        return self.e.roles.get(id_rol)

    def asignar_rol_usuario(self, *args):
        if self.e.fallar_asignacion:
            raise RuntimeError("fallo controlado de prueba")
        self.e.asignaciones.append(args)

    def obtener_roles_usuario(self, _id_usuario):
        return (self.e.rol_actual,)

    def contar_super_admin_activos(self, excluir_id=None):
        return self.e.super_admin_restantes


class RepoAuditoria:
    def __init__(self, estado):
        self.e = estado

    def registrar(self, evento):
        self.e.eventos.append(evento)


def _actor(*, super_admin=False, id_usuario=1):
    return IdentidadSesion(
        id_usuario,
        "actor",
        "Actor",
        TIPO_BASE_DATOS,
        frozenset({"SUPER_ADMIN" if super_admin else "ADMIN"}),
        frozenset({"USUARIOS_ADMIN"}),
    )


def _actor_env():
    return IdentidadSesion(
        None,
        "admin-env",
        "admin-env",
        TIPO_SUPER_ADMIN_ENV,
        frozenset({TIPO_SUPER_ADMIN_ENV}),
        frozenset({"*"}),
    )


def _servicio(estado):
    return ServicioUsuarios(
        estado,
        fabrica_uow=UowUsuarios,
        repositorio_usuarios=RepoUsuarios,
        repositorio_seguridad=RepoSeguridad,
        repositorio_auditoria=RepoAuditoria,
        generar_hash=lambda valor: f"hash:{len(valor)}",
    )


def test_crear_usuario_asigna_rol_y_audita_sin_password():
    estado = EstadoUsuarios()
    id_usuario = _servicio(estado).crear(
        {
            "usuario": "nuevo.usuario",
            "nombre_completo": "Nuevo Usuario",
            "email": "nuevo@example.test",
            "password": "secreto-largo",
            "confirmacion_password": "secreto-largo",
            "id_rol": "3",
            "activo": "1",
        },
        _actor(),
        ContextoAuditoria(ruta="/usuarios/nuevo", metodo_http="POST"),
    )

    assert id_usuario == 11
    assert estado.creados[0][3] == "hash:13"
    assert estado.asignaciones == [(11, 3, "actor")]
    assert estado.eventos[0].accion == "USUARIO_CREADO"
    assert "secreto-largo" not in repr(estado.eventos)
    assert "password" not in (estado.eventos[0].valores_despues or "")
    assert estado.confirmaciones == 1


def test_admin_no_puede_asignar_super_admin():
    estado = EstadoUsuarios()
    with pytest.raises(ErrorAutorizacion):
        _servicio(estado).crear(
            {
                "usuario": "nuevo.admin",
                "nombre_completo": "Nuevo Admin",
                "email": "admin@example.test",
                "password": "secreto-largo",
                "confirmacion_password": "secreto-largo",
                "id_rol": "1",
                "activo": "1",
            },
            _actor(super_admin=False),
            ContextoAuditoria(),
        )
    assert estado.creados == []
    assert estado.confirmaciones == 0


def test_no_permite_desactivar_sesion_actual():
    estado = EstadoUsuarios()
    estado.usuarios[10] = _usuario(id_usuario=10, usuario="actor")
    with pytest.raises(ErrorValidacion, match="sesion actual"):
        _servicio(estado).cambiar_estado(10, False, _actor(id_usuario=10), ContextoAuditoria())
    assert estado.estados == []


def test_no_permite_desactivar_ultimo_super_admin():
    estado = EstadoUsuarios()
    estado.rol_actual = ROL_SUPER
    estado.super_admin_restantes = 0
    with pytest.raises(ErrorValidacion, match="ultimo SUPER_ADMIN"):
        _servicio(estado).cambiar_estado(
            10, False, _actor(super_admin=True), ContextoAuditoria()
        )
    assert estado.estados == []


def test_super_admin_env_no_cuenta_como_super_admin_interno():
    estado = EstadoUsuarios()
    estado.rol_actual = ROL_SUPER
    estado.super_admin_restantes = 0

    with pytest.raises(ErrorValidacion, match="ultimo SUPER_ADMIN"):
        _servicio(estado).cambiar_estado(10, False, _actor_env(), ContextoAuditoria())

    assert estado.estados == []
    assert estado.confirmaciones == 0


def test_editar_usuario_actualiza_perfil_rol_y_auditoria():
    estado = EstadoUsuarios()
    _servicio(estado).actualizar(
        10,
        {
            "nombre_completo": "Nombre Actualizado",
            "email": "actualizado@example.test",
            "password": "",
            "confirmacion_password": "",
            "id_rol": "3",
        },
        _actor(),
        ContextoAuditoria(),
    )

    assert estado.actualizados == [
        (10, "Nombre Actualizado", "actualizado@example.test", "actor", None)
    ]
    assert estado.asignaciones == [(10, 3, "actor")]
    assert [evento.accion for evento in estado.eventos] == [
        "USUARIO_EDITADO",
        "ROLES_USUARIO_MODIFICADOS",
    ]
    assert estado.confirmaciones == 1


def test_activar_usuario_registra_estado_y_auditoria():
    estado = EstadoUsuarios()
    _servicio(estado).cambiar_estado(10, True, _actor(), ContextoAuditoria())

    assert estado.estados == [(10, True, "actor")]
    assert estado.eventos[0].accion == "USUARIO_ACTIVADO"
    assert estado.confirmaciones == 1


def test_fallo_al_asignar_rol_no_confirma_transaccion():
    estado = EstadoUsuarios()
    estado.fallar_asignacion = True

    with pytest.raises(RuntimeError, match="fallo controlado"):
        _servicio(estado).crear(
            {
                "usuario": "nuevo.usuario",
                "nombre_completo": "Nuevo Usuario",
                "email": "nuevo@example.test",
                "password": "secreto-largo",
                "confirmacion_password": "secreto-largo",
                "id_rol": "3",
                "activo": "1",
            },
            _actor(),
            ContextoAuditoria(),
        )

    assert estado.confirmaciones == 0
    assert estado.reversiones == 1
    assert estado.eventos == []


def test_auditoria_sanitiza_campos_sensibles_recursivos():
    evento = crear_evento_auditoria(
        usuario="actor",
        accion="PRUEBA",
        entidad="usuarios",
        valores_despues={"password": "secreto", "perfil": {"token_api": "otro"}},
    )
    assert "secreto" not in evento.valores_despues
    assert "otro" not in evento.valores_despues
    assert evento.valores_despues.count("[PROTEGIDO]") == 2
