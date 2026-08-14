from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import (
    CLAVE_IDENTIDAD,
    IdentidadSesion,
    TIPO_BASE_DATOS,
    TIPO_SUPER_ADMIN_ENV,
)
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.modulos.catalogos.casos_uso import (
    CATALOGOS,
    ServicioCatalogos,
    normalizar_nombre,
)
from app_scheduler.persistencia.modelos import Categoria, Cliente, Pagina, Tipo


FECHA = datetime(2026, 8, 14, 12, 0)
MODELOS = {
    "clientes": lambda **cambios: Cliente(
        7, "Cliente Base", "CLIENTE BASE", "Descripcion", False,
        FECHA, None, True, **cambios
    ),
    "categorias": lambda **cambios: Categoria(
        7, "Categoria Base", "CATEGORIA BASE", "Descripcion", False,
        FECHA, None, True, **cambios
    ),
    "tipos": lambda **cambios: Tipo(
        7, "Tipo Base", "TIPO BASE", "Descripcion", False,
        FECHA, None, True, **cambios
    ),
}


class EstadoCatalogos:
    def __init__(self, clave="clientes"):
        self.actual = MODELOS[clave]()
        self.duplicado = None
        self.creados = []
        self.actualizados = []
        self.estados = []
        self.eventos = []
        self.confirmaciones = 0
        self.reversiones = 0
        self.fallar_auditoria = False
        self.fallar_duplicado_sql = False

    @contextmanager
    def conexion_lectura(self):
        yield self


class UowCatalogos:
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


class RepoCatalogo:
    def __init__(self, estado):
        self.e = estado

    def listar_paginado(self, paginacion, **_filtros):
        return Pagina((self.e.actual,), 1, paginacion.pagina, paginacion.por_pagina)

    def obtener_por_id(self, identificador):
        return self.e.actual if identificador == 7 else None

    def buscar_por_clave(self, _nombre):
        return self.e.duplicado

    def crear(self, *datos):
        if self.e.fallar_duplicado_sql:
            raise ErrorPersistencia(detalle_tecnico="crear_clientes SQLSTATE=23000.")
        self.e.creados.append(datos)
        return 8

    def actualizar(self, *datos):
        self.e.actualizados.append(datos)
        return True

    def cambiar_estado(self, *datos):
        self.e.estados.append(datos)
        return True


class RepoAuditoria:
    def __init__(self, estado):
        self.e = estado

    def registrar(self, evento):
        if self.e.fallar_auditoria:
            raise RuntimeError("fallo auditoria controlado")
        self.e.eventos.append(evento)


def _actor(permisos=frozenset({"CLIENTES_VER"})):
    return IdentidadSesion(
        1, "actor", "Actor", TIPO_BASE_DATOS, frozenset({"ADMIN"}), permisos
    )


def _servicio(estado, clave):
    definicion = replace(CATALOGOS[clave], repositorio=RepoCatalogo)
    return ServicioCatalogos(
        estado,
        fabrica_uow=UowCatalogos,
        repositorio_auditoria=RepoAuditoria,
        catalogos={clave: definicion},
    )


@pytest.mark.parametrize("clave", ("clientes", "categorias", "tipos"))
def test_crear_catalogo_normaliza_audita_y_confirma(clave):
    estado = EstadoCatalogos(clave)

    identificador = _servicio(estado, clave).crear(
        clave,
        {"nombre": "  Gestion Ágil  ", "descripcion": "  Base operativa  "},
        _actor(),
        ContextoAuditoria(ruta=f"/{clave}/nuevo", metodo_http="POST"),
    )

    assert identificador == 8
    assert estado.creados == [("Gestion Ágil", "GESTION AGIL", "Base operativa", "actor")]
    assert estado.eventos[0].accion.endswith("_CREADO")
    assert estado.eventos[0].entidad == clave
    assert estado.confirmaciones == 1


def test_validacion_longitud_y_duplicado_incluye_papelera():
    estado = EstadoCatalogos()
    servicio = _servicio(estado, "clientes")

    with pytest.raises(ErrorValidacion, match="obligatorio"):
        servicio.crear("clientes", {"nombre": ""}, _actor(), ContextoAuditoria())
    with pytest.raises(ErrorValidacion, match="normalizado"):
        servicio.crear(
            "clientes", {"nombre": "ß" * 100}, _actor(), ContextoAuditoria()
        )
    estado.duplicado = MODELOS["clientes"]()
    with pytest.raises(ErrorValidacion, match="retirado"):
        servicio.crear(
            "clientes", {"nombre": "Cliente Base"}, _actor(), ContextoAuditoria()
        )

    assert estado.creados == [] and estado.confirmaciones == 0


@pytest.mark.parametrize("clave", ("clientes", "categorias", "tipos"))
def test_editar_catalogo_excluye_identidad_actual_y_audita(clave):
    estado = EstadoCatalogos(clave)
    estado.duplicado = estado.actual

    _servicio(estado, clave).actualizar(
        clave,
        7,
        {"nombre": "Nombre Actualizado", "descripcion": "Nueva"},
        _actor(),
        ContextoAuditoria(),
    )

    assert estado.actualizados[0][0] == 7
    assert estado.actualizados[0][1:4] == ("Nombre Actualizado", "NOMBRE ACTUALIZADO", "Nueva")
    assert estado.eventos[0].accion.endswith("_EDITADO")
    assert estado.confirmaciones == 1


def test_editar_inexistente_y_sin_cambios_son_errores_funcionales():
    estado = EstadoCatalogos()
    servicio = _servicio(estado, "clientes")

    with pytest.raises(ErrorValidacion, match="no encontrado"):
        servicio.actualizar(
            "clientes", 99, {"nombre": "Otro"}, _actor(), ContextoAuditoria()
        )
    with pytest.raises(ErrorValidacion, match="No hay cambios"):
        servicio.actualizar(
            "clientes",
            7,
            {"nombre": "Cliente Base", "descripcion": "Descripcion"},
            _actor(),
            ContextoAuditoria(),
        )

    assert estado.confirmaciones == 0


@pytest.mark.parametrize("clave", ("clientes", "categorias", "tipos"))
def test_cambiar_estado_audita_y_confirma(clave):
    estado = EstadoCatalogos(clave)

    _servicio(estado, clave).cambiar_estado(
        clave, 7, False, _actor(), ContextoAuditoria()
    )

    assert estado.estados == [(7, False, "actor")]
    assert estado.eventos[0].accion.endswith("_DESACTIVADO")
    assert estado.confirmaciones == 1


def test_fallo_auditoria_revierte_operacion_completa():
    estado = EstadoCatalogos()
    estado.fallar_auditoria = True

    with pytest.raises(RuntimeError, match="fallo auditoria"):
        _servicio(estado, "clientes").crear(
            "clientes", {"nombre": "Nuevo"}, _actor(), ContextoAuditoria()
        )

    assert estado.creados
    assert estado.confirmaciones == 0
    assert estado.reversiones == 1


def test_conflicto_unicidad_sql_se_traduce_sin_detalle_driver():
    estado = EstadoCatalogos()
    estado.fallar_duplicado_sql = True

    with pytest.raises(ErrorValidacion, match="Ya existe") as capturado:
        _servicio(estado, "clientes").crear(
            "clientes", {"nombre": "Nuevo"}, _actor(), ContextoAuditoria()
        )

    assert "SQLSTATE" not in capturado.value.mensaje
    assert estado.confirmaciones == 0
    assert estado.reversiones == 1


def test_normalizacion_historica_controla_acentos_espacios_y_mayusculas():
    assert normalizar_nombre("  Gestión   ágil ") == "GESTION AGIL"
    assert normalizar_nombre("ÁREA TI") == "AREA TI"
    assert normalizar_nombre("Area TI") == "AREA TI"
    assert normalizar_nombre("  área   ti  ") == "AREA TI"


class ServicioAuthFalso:
    def __init__(self, identidad):
        self.identidad = identidad

    def cargar_identidad(self, _datos):
        return self.identidad


class ServicioCatalogosWebFalso:
    def __init__(self):
        self.cambios = []
        self.creaciones = []
        self.actualizaciones = []

    def listar(self, clave, **_filtros):
        return Pagina((MODELOS[clave](),), 1, 1, 25)

    def obtener(self, clave, _identificador):
        return MODELOS[clave]()

    def cambiar_estado(self, clave, identificador, activo, actor, _contexto):
        self.cambios.append((clave, identificador, activo, actor.usuario))

    def crear(self, clave, datos, actor, _contexto):
        self.creaciones.append((clave, datos, actor.usuario))
        return 8

    def actualizar(self, clave, identificador, datos, actor, _contexto):
        self.actualizaciones.append((clave, identificador, datos, actor.usuario))


def _app_web(configuracion, identidad):
    app = crear_aplicacion(
        configuracion,
        ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )
    auth = ServicioAuthFalso(identidad)
    app.extensions["servicio_autenticacion"] = auth
    app.extensions["cargador_identidad"] = auth.cargar_identidad
    catalogos = ServicioCatalogosWebFalso()
    app.extensions["servicio_catalogos"] = catalogos
    return app, catalogos


def _sesion(cliente, identidad):
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {
            "tipo": identidad.tipo_identidad,
            "id_usuario": identidad.id_usuario,
            "usuario": identidad.usuario,
        }


def test_rutas_catalogos_exigen_sesion_y_permiso(configuracion):
    identidad = _actor(frozenset({"PANEL_VER"}))
    app, _ = _app_web(configuracion, identidad)
    cliente = app.test_client()

    assert cliente.get("/clientes/").status_code == 302
    _sesion(cliente, identidad)
    assert cliente.get("/clientes/").status_code == 403


def test_estado_catalogo_exige_csrf_y_permiso_especifico(configuracion):
    identidad = _actor(frozenset({"PANEL_VER", "CLIENTES_VER", "CLIENTES_ESTADO"}))
    app, catalogos = _app_web(configuracion, identidad)
    cliente = app.test_client()
    _sesion(cliente, identidad)

    assert cliente.get("/clientes/").status_code == 200
    assert cliente.post("/clientes/7/estado", data={"activo": "0"}).status_code == 403
    cliente.get("/clientes/")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]
    respuesta = cliente.post(
        "/clientes/7/estado", data={"csrf_token": token, "activo": "0"}
    )

    assert respuesta.status_code == 302
    assert catalogos.cambios == [("clientes", 7, False, "actor")]


def test_token_valido_no_reemplaza_permiso_backend(configuracion):
    identidad = _actor(frozenset({"PANEL_VER", "CLIENTES_VER"}))
    app, catalogos = _app_web(configuracion, identidad)
    cliente = app.test_client()
    _sesion(cliente, identidad)
    cliente.get("/clientes/")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]

    respuesta = cliente.post(
        "/clientes/7/estado", data={"csrf_token": token, "activo": "0"}
    )

    assert respuesta.status_code == 403
    assert catalogos.cambios == []


def test_formulario_mapea_solo_campos_editables(configuracion):
    identidad = _actor(
        frozenset({"PANEL_VER", "CLIENTES_VER", "CLIENTES_CREAR", "CLIENTES_EDITAR"})
    )
    app, catalogos = _app_web(configuracion, identidad)
    cliente = app.test_client()
    _sesion(cliente, identidad)
    cliente.get("/clientes/")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]

    creado = cliente.post(
        "/clientes/nuevo",
        data={
            "csrf_token": token,
            "nombre": "Nuevo",
            "descripcion": "Descripcion",
            "activo": "0",
            "id_cliente": "999",
            "eliminado_operativo": "1",
        },
    )
    editado = cliente.post(
        "/clientes/7/editar",
        data={
            "csrf_token": token,
            "nombre": "Editado",
            "descripcion": "Nueva",
            "usuario_creacion": "suplantado",
        },
    )

    assert creado.status_code == 302 and editado.status_code == 302
    assert catalogos.creaciones[0][1] == {
        "nombre": "Nuevo",
        "descripcion": "Descripcion",
    }
    assert catalogos.actualizaciones[0][2] == {
        "nombre": "Editado",
        "descripcion": "Nueva",
    }


def test_super_admin_env_usa_permisos_efectivos_comunes(configuracion):
    identidad = IdentidadSesion(
        None,
        "admin-env",
        "Admin Entorno",
        TIPO_SUPER_ADMIN_ENV,
        frozenset({TIPO_SUPER_ADMIN_ENV}),
        frozenset({"*"}),
    )
    app, _ = _app_web(configuracion, identidad)
    cliente = app.test_client()
    _sesion(cliente, identidad)

    respuesta = cliente.get("/tipos/")

    assert respuesta.status_code == 200
    assert b"Crear tipo" in respuesta.data
