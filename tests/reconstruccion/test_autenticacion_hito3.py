from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import (
    CLAVE_IDENTIDAD,
    IdentidadSesion,
    TIPO_BASE_DATOS,
    TIPO_SUPER_ADMIN_ENV,
)
from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.modulos.autenticacion.casos_uso import (
    MENSAJE_CREDENCIALES_INVALIDAS,
    ResultadoAutenticacion,
    ServicioAutenticacion,
)
from app_scheduler.modulos.usuarios.casos_uso import PaginaUsuarios, ResumenSeguridad, UsuarioConRoles
from app_scheduler.persistencia.modelos import CredencialUsuario, Permiso, Rol, Usuario


def _usuario(*, activo=True, bloqueado=False):
    return Usuario(
        id_usuario=7,
        usuario="operador",
        nombre_completo="Operador QA",
        email="operador@example.test",
        debe_cambiar_password=False,
        ultimo_login=None,
        intentos_fallidos=0,
        bloqueado=bloqueado,
        eliminado_operativo=False,
        fecha_eliminado_operativo=None,
        fecha_creacion=datetime(2026, 1, 1),
        fecha_actualizacion=None,
        activo=activo,
    )


ROL_ADMIN = Rol(2, "ADMIN", "Administrador", None, True, True)
ROL_SUPER_ADMIN = Rol(1, "SUPER_ADMIN", "Super Admin", None, True, True)
PERMISO_PANEL = Permiso(1, "PANEL_VER", "PANEL", "VER", None, True)


class EstadoAuth:
    def __init__(self, credencial=None):
        self.credencial = credencial
        self.eventos = []
        self.intentos = 0
        self.ultimo_login = None
        self.confirmaciones = 0

    @contextmanager
    def conexion_lectura(self):
        yield self


class UowAuth:
    def __init__(self, estado):
        self.estado = estado

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def obtener_conexion(self):
        return self.estado

    def confirmar(self):
        self.estado.confirmaciones += 1


class UsuariosAuth:
    def __init__(self, estado):
        self.estado = estado

    def obtener_credencial_por_identificador(self, _usuario):
        return self.estado.credencial

    def incrementar_intentos_fallidos(self, _id):
        self.estado.intentos += 1

    def actualizar_ultimo_login(self, _id, fecha, _actor):
        self.estado.ultimo_login = fecha

    def obtener_por_id(self, _id):
        return self.estado.credencial.usuario if self.estado.credencial else None


class SeguridadAuth:
    def __init__(self, _estado):
        pass

    def obtener_roles_usuario(self, _id):
        return (ROL_ADMIN,)

    def obtener_permisos_efectivos(self, _id):
        return (PERMISO_PANEL,)


class AuditoriaAuth:
    def __init__(self, estado):
        self.estado = estado

    def registrar(self, evento):
        self.estado.eventos.append(evento)


def _servicio(configuracion, estado):
    return ServicioAutenticacion(
        configuracion,
        estado,
        fabrica_uow=UowAuth,
        repositorio_usuarios=UsuariosAuth,
        repositorio_seguridad=SeguridadAuth,
        repositorio_auditoria=AuditoriaAuth,
        reloj=lambda: datetime(2026, 8, 14, 12, 0),
    )


def test_login_super_admin_env_tiene_prioridad_y_no_guarda_secretos(configuracion):
    estado = EstadoAuth()
    resultado = _servicio(configuracion, estado).autenticar(
        configuracion.usuario_admin_defecto,
        configuracion.password_admin_defecto,
        ContextoAuditoria(ruta="/login", metodo_http="POST"),
    )

    assert resultado.exito is True
    assert resultado.identidad.es_super_admin_env is True
    assert resultado.identidad.tiene_permiso("CUALQUIER_PERMISO") is True
    assert len(estado.eventos) == 1
    assert configuracion.password_admin_defecto not in repr(estado.eventos)


def test_login_bd_valido_carga_roles_permisos_y_audita(configuracion):
    estado = EstadoAuth(CredencialUsuario(_usuario(), generate_password_hash("clave-segura")))

    resultado = _servicio(configuracion, estado).autenticar(
        "operador", "clave-segura", ContextoAuditoria(ip_origen="127.0.0.1")
    )

    assert resultado.exito is True
    assert resultado.identidad.roles == frozenset({"ADMIN"})
    assert resultado.identidad.permisos == frozenset({"PANEL_VER"})
    assert estado.ultimo_login == datetime(2026, 8, 14, 12, 0)
    assert estado.eventos[0].accion == "LOGIN_OK"
    assert estado.confirmaciones == 1


def test_login_invalido_no_enumera_estado_e_incrementa_intento(configuracion):
    estado = EstadoAuth(CredencialUsuario(_usuario(), generate_password_hash("correcta")))

    resultado = _servicio(configuracion, estado).autenticar(
        "operador", "incorrecta", ContextoAuditoria()
    )

    assert resultado.exito is False
    assert resultado.mensaje == MENSAJE_CREDENCIALES_INVALIDAS
    assert estado.intentos == 1
    assert estado.eventos[0].accion == "LOGIN_FALLIDO"
    assert "incorrecta" not in repr(estado.eventos)


def test_login_rechaza_entrada_sobredimensionada_sin_consultar_usuario(configuracion):
    estado = EstadoAuth()

    resultado = _servicio(configuracion, estado).autenticar(
        "u" * 101, "clave-segura", ContextoAuditoria()
    )

    assert resultado.exito is False
    assert resultado.mensaje == MENSAJE_CREDENCIALES_INVALIDAS
    assert estado.eventos[0].usuario == "u" * 100
    assert estado.eventos[0].descripcion == "Entrada de autenticacion no valida."


def test_usuario_inactivo_no_inicia_sesion_y_recibe_mensaje_generico(configuracion):
    estado = EstadoAuth(
        CredencialUsuario(_usuario(activo=False), generate_password_hash("clave-segura"))
    )

    resultado = _servicio(configuracion, estado).autenticar(
        "operador", "clave-segura", ContextoAuditoria()
    )

    assert resultado.exito is False
    assert resultado.mensaje == MENSAJE_CREDENCIALES_INVALIDAS
    assert estado.intentos == 0
    assert estado.eventos[0].descripcion == "Credenciales o estado no validos."


def test_identidad_bd_inactiva_invalida_sesion(configuracion):
    estado = EstadoAuth(CredencialUsuario(_usuario(activo=False), "hash-no-expuesto"))
    identidad = _servicio(configuracion, estado).cargar_identidad(
        {"tipo": TIPO_BASE_DATOS, "id_usuario": 7, "usuario": "operador"}
    )

    assert identidad is None


class ServicioWebFalso:
    def __init__(self, identidad):
        self.identidad = identidad
        self.logout = 0

    def autenticar(self, usuario, password, _contexto):
        if usuario == "operador" and password == "clave-segura":
            return ResultadoAutenticacion(True, "Sesion iniciada.", self.identidad)
        return ResultadoAutenticacion(False, MENSAJE_CREDENCIALES_INVALIDAS)

    def cargar_identidad(self, datos):
        if self.identidad is None:
            return None
        return self.identidad if datos.get("id_usuario") == self.identidad.id_usuario else None

    def registrar_logout(self, _identidad, _contexto):
        self.logout += 1


def _app_web(configuracion, identidad):
    app = crear_aplicacion(
        configuracion,
        ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )
    servicio = ServicioWebFalso(identidad)
    app.extensions["servicio_autenticacion"] = servicio
    app.extensions["cargador_identidad"] = servicio.cargar_identidad
    return app, servicio


def _csrf(cliente):
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        return sesion["_csrf"]["token"]


def test_ruta_login_sesion_minima_destino_local_y_logout(configuracion):
    identidad = IdentidadSesion(
        7,
        "operador",
        "Operador QA",
        TIPO_BASE_DATOS,
        frozenset({"ADMIN"}),
        frozenset({"PANEL_VER"}),
    )
    app, servicio = _app_web(configuracion, identidad)
    cliente = app.test_client()
    token = _csrf(cliente)

    respuesta = cliente.post(
        "/login?next=/",
        data={"csrf_token": token, "usuario": "operador", "password": "clave-segura"},
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")
    with cliente.session_transaction() as sesion:
        assert sesion[CLAVE_IDENTIDAD] == {
            "tipo": TIPO_BASE_DATOS,
            "id_usuario": 7,
            "usuario": "operador",
        }
        assert "permisos" not in sesion[CLAVE_IDENTIDAD]
    assert cliente.get("/").status_code == 200
    with cliente.session_transaction() as sesion:
        token_logout = sesion["_csrf"]["token"]
    assert cliente.post("/logout", data={"csrf_token": token_logout}).status_code == 302
    assert servicio.logout == 1
    with cliente.session_transaction() as sesion:
        assert CLAVE_IDENTIDAD not in sesion


def test_login_invalido_muestra_mensaje_dentro_de_la_pantalla(configuracion):
    app, _ = _app_web(configuracion, None)
    cliente = app.test_client()
    token = _csrf(cliente)

    respuesta = cliente.post(
        "/login",
        data={"csrf_token": token, "usuario": "no-existe", "password": "incorrecta"},
    )

    assert respuesta.status_code == 200
    assert MENSAJE_CREDENCIALES_INVALIDAS.encode() in respuesta.data
    assert b'id="tituloLogin"' in respuesta.data
    assert b'class="login-contenedor"' in respuesta.data


def test_error_publico_no_renderiza_pagina_vacia(configuracion):
    app, _ = _app_web(configuracion, None)
    respuesta = app.test_client().get("/ruta-inexistente")

    assert respuesta.status_code == 404
    assert b"No fue posible completar la solicitud" in respuesta.data
    assert b"La pagina solicitada no existe" in respuesta.data
    assert b"Volver al acceso" in respuesta.data


def test_login_rechaza_open_redirect_y_post_sin_csrf(configuracion):
    identidad = IdentidadSesion(
        7, "operador", "Operador", TIPO_BASE_DATOS, frozenset(), frozenset({"PANEL_VER"})
    )
    app, _ = _app_web(configuracion, identidad)
    cliente = app.test_client()

    assert cliente.post("/login", data={"usuario": "operador"}).status_code == 403
    token = _csrf(cliente)
    respuesta = cliente.post(
        "/login?next=https://sitio.example/phishing",
        data={"csrf_token": token, "usuario": "operador", "password": "clave-segura"},
    )
    assert respuesta.headers["Location"].endswith("/")


def test_sesion_abierta_se_invalida_al_desactivar_usuario(configuracion):
    identidad = IdentidadSesion(
        7,
        "operador",
        "Operador",
        TIPO_BASE_DATOS,
        frozenset({"ADMIN"}),
        frozenset({"PANEL_VER"}),
    )
    app, servicio = _app_web(configuracion, identidad)
    cliente = app.test_client()
    token = _csrf(cliente)
    assert cliente.post(
        "/login",
        data={"csrf_token": token, "usuario": "operador", "password": "clave-segura"},
    ).status_code == 302
    assert cliente.get("/").status_code == 200

    servicio.identidad = None
    respuesta = cliente.get("/")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login?next=/")
    with cliente.session_transaction() as sesion:
        assert CLAVE_IDENTIDAD not in sesion


def test_super_admin_sql_y_super_admin_env_son_identidades_distintas(configuracion):
    estado = EstadoAuth(CredencialUsuario(_usuario(), generate_password_hash("clave-segura")))
    servicio = _servicio(configuracion, estado)
    identidad_env = servicio._identidad_super_admin_env()
    identidad_sql = servicio._crear_identidad_db(
        _usuario(), (ROL_SUPER_ADMIN,), (PERMISO_PANEL,)
    )

    assert identidad_env.tipo_identidad == TIPO_SUPER_ADMIN_ENV
    assert identidad_env.id_usuario is None
    assert identidad_env.roles == frozenset({TIPO_SUPER_ADMIN_ENV})
    assert identidad_sql.tipo_identidad == TIPO_BASE_DATOS
    assert identidad_sql.id_usuario == 7
    assert identidad_sql.roles == frozenset({"SUPER_ADMIN"})
    assert TIPO_SUPER_ADMIN_ENV not in identidad_sql.roles


def test_backend_deniega_usuarios_sin_permiso(configuracion):
    identidad = IdentidadSesion(
        7, "operador", "Operador", TIPO_BASE_DATOS, frozenset({"TI"}), frozenset({"PANEL_VER"})
    )
    app, _ = _app_web(configuracion, identidad)
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {"tipo": TIPO_BASE_DATOS, "id_usuario": 7, "usuario": "operador"}

    respuesta_usuarios = cliente.get("/usuarios/")
    respuesta_roles = cliente.get("/seguridad/roles-permisos")

    assert respuesta_usuarios.status_code == 403
    assert b"No fue posible completar la solicitud" in respuesta_usuarios.data
    assert b"No tienes permiso" in respuesta_usuarios.data
    assert respuesta_roles.status_code == 403
    assert b"No tienes permiso" in respuesta_roles.data


def test_panel_organiza_acciones_sin_texto_concatenado(configuracion):
    identidad = IdentidadSesion(
        7,
        "operador",
        "Operador",
        TIPO_BASE_DATOS,
        frozenset({"ADMIN"}),
        frozenset(
            {
                "PANEL_VER",
                "TAREAS_VER",
                "EJECUCIONES_VER",
                "CLIENTES_VER",
                "CATEGORIAS_VER",
                "TIPOS_VER",
                "USUARIOS_ADMIN",
            }
        ),
    )
    app, _ = _app_web(configuracion, identidad)
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {
            "tipo": TIPO_BASE_DATOS,
            "id_usuario": 7,
            "usuario": "operador",
        }

    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert b"Trabajo diario" in respuesta.data
    assert b"Datos de organizacion" in respuesta.data
    assert b"Acceso y autorizacion" in respuesta.data
    assert b"UoW explicita" not in respuesta.data
    assert b"<span><strong>Administrar usuarios</strong><small>" in respuesta.data

    css = (
        Path(__file__).parents[2]
        / "src/app_scheduler/presentacion/static/css/modulos/base-tecnica.css"
    ).read_text(encoding="utf-8")
    assert ".acciones-principales" in css
    assert ".accion-principal > span" in css


def test_error_persistencia_no_expone_detalle_sql_en_respuesta(configuracion):
    identidad = IdentidadSesion(
        7, "operador", "Operador", TIPO_BASE_DATOS, frozenset(), frozenset({"PANEL_VER"})
    )
    app, servicio = _app_web(configuracion, identidad)

    def fallar(*_args):
        raise ErrorPersistencia(detalle_tecnico="SQLSTATE=08001;PWD=secreto-no-visible")

    servicio.autenticar = fallar
    cliente = app.test_client()
    token = _csrf(cliente)
    respuesta = cliente.post(
        "/login",
        data={"csrf_token": token, "usuario": "operador", "password": "clave-segura"},
    )

    assert respuesta.status_code == 503
    assert b"No fue posible completar la solicitud" in respuesta.data
    assert b"El servicio de datos no esta disponible" in respuesta.data
    assert b"secreto-no-visible" not in respuesta.data
    assert b"SQLSTATE" not in respuesta.data


def test_error_500_muestra_respuesta_segura(configuracion):
    app, _ = _app_web(configuracion, None)

    @app.get("/prueba-error-interno")
    def _error_interno():
        raise RuntimeError("detalle-interno-no-visible")

    respuesta = app.test_client().get("/prueba-error-interno")

    assert respuesta.status_code == 500
    assert b"No fue posible completar la solicitud" in respuesta.data
    assert b"Ocurrio un error interno" in respuesta.data
    assert b"detalle-interno-no-visible" not in respuesta.data


class UsuariosWebFalso:
    def __init__(self):
        self.cambios_estado = []

    def listar(self, **_filtros):
        return PaginaUsuarios(
            (UsuarioConRoles(_usuario(), (ROL_ADMIN,)),), 1, 1, 25, 1
        )

    def roles_disponibles(self, _actor):
        return (ROL_ADMIN,)

    def resumen_seguridad(self):
        return ResumenSeguridad(
            (ROL_ADMIN,),
            (PERMISO_PANEL,),
            {"ADMIN": frozenset({"PANEL_VER"})},
        )

    def cambiar_estado(self, id_usuario, activo, actor, _contexto):
        self.cambios_estado.append((id_usuario, activo, actor.usuario))


def test_usuario_con_permiso_renderiza_modulos_y_csrf_protege_estado(configuracion):
    identidad = IdentidadSesion(
        7,
        "operador",
        "Operador",
        TIPO_BASE_DATOS,
        frozenset({"ADMIN"}),
        frozenset({"PANEL_VER", "USUARIOS_ADMIN"}),
    )
    app, _ = _app_web(configuracion, identidad)
    usuarios = UsuariosWebFalso()
    app.extensions["servicio_usuarios"] = usuarios
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {"tipo": TIPO_BASE_DATOS, "id_usuario": 7, "usuario": "operador"}

    listado = cliente.get("/usuarios/")
    matriz = cliente.get("/seguridad/roles-permisos")

    assert listado.status_code == 200 and b"Operador QA" in listado.data
    assert b"password_hash" not in listado.data
    assert matriz.status_code == 200 and b"PANEL_VER" in matriz.data
    assert cliente.post("/usuarios/7/estado", data={"activo": "0"}).status_code == 403
    cliente.get("/usuarios/")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]
    respuesta = cliente.post(
        "/usuarios/7/estado", data={"csrf_token": token, "activo": "0"}
    )
    assert respuesta.status_code == 302
    assert usuarios.cambios_estado == [(7, False, "operador")]
