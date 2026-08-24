from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import CLAVE_IDENTIDAD, TIPO_BASE_DATOS, IdentidadSesion
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos
from app_scheduler.modulos.auditoria.casos_uso import ServicioConsultaAuditoria
from app_scheduler.modulos.papelera.casos_uso import ServicioPapelera
from app_scheduler.persistencia.modelos import (
    ElementoPapelera,
    Pagina,
    Paginacion,
    RegistroAuditoria,
)
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_papelera import RepositorioPapelera
from tests.reconstruccion.fakes_sql import ConexionProgramada, ResultadoSQL


AHORA = datetime(2026, 8, 24, 12, 0, 0)


def identidad(permisos=frozenset(), identificador=7):
    return IdentidadSesion(identificador, "operador", "Operador TI", TIPO_BASE_DATOS,
                           frozenset({"TI"}), frozenset(permisos))


def iniciar_sesion(cliente, actor):
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {"tipo": actor.tipo_identidad,
                                  "id_usuario": actor.id_usuario,
                                  "usuario": actor.usuario}


def csrf(cliente):
    cliente.get("/")
    with cliente.session_transaction() as sesion:
        return sesion["_csrf"]["token"]


def evento_auditoria(descripcion="Evento seguro"):
    return RegistroAuditoria(1, AHORA, "operador", 7, "EDITADO", "tareas", "3",
                             "Proceso", descripcion, '{"antes": 1}', '{"despues": 2}',
                             "127.0.0.1", "pytest", "OK", "TAREAS", "/tareas/3", "POST")


def test_repositorio_auditoria_pagina_parametrizada_y_orden_fijo():
    fila = tuple(getattr(evento_auditoria(), campo) for campo in RegistroAuditoria.__dataclass_fields__)
    conexion = ConexionProgramada(
        ResultadoSQL(fila=(0,)), ResultadoSQL(fila=(1,)), ResultadoSQL(filas=[fila])
    )
    resultado = RepositorioAuditoria(conexion).listar(
        Paginacion(2, 25),
        usuario="%' OR 1=1 --", entidad="tareas",
    )
    assert resultado.total == 1 and resultado.elementos[0].entidad == "tareas"
    sql = conexion.ejecuciones[2][0]
    assert "ORDER BY fecha_evento DESC, id_auditoria DESC" in sql
    assert "OR 1=1" not in sql
    assert any("OR 1=1" in str(valor) for valor in conexion.ejecuciones[2][1])


def test_repositorio_auditoria_legacy_usa_semantica_canonica():
    conexion = ConexionProgramada(ResultadoSQL(fila=(1,)), ResultadoSQL(fila=None))
    assert RepositorioAuditoria(conexion).obtener(99) is None
    sql = conexion.ejecuciones[1][0]
    assert "COALESCE(fecha_evento, fecha_hora)" in sql
    assert "COALESCE(NULLIF(entidad, ''), tabla_afectada)" in sql


class ProveedorLectura:
    def __init__(self, estado): self.estado = estado
    @contextmanager
    def conexion_lectura(self): yield self.estado


class RepoAuditoriaFake:
    def __init__(self, estado): self.estado = estado
    def listar(self, paginacion, **_): return Pagina(tuple(self.estado), len(self.estado), paginacion.pagina, paginacion.por_pagina)
    def opciones_filtros(self): return ("EDITADO",), ("tareas",)
    def obtener(self, identificador): return next((x for x in self.estado if x.id_auditoria == identificador), None)


def test_servicio_auditoria_valida_fechas_y_formatea_json():
    servicio = ServicioConsultaAuditoria(ProveedorLectura([evento_auditoria()]), repositorio=RepoAuditoriaFake)
    with pytest.raises(ErrorValidacion, match="posterior"):
        servicio.listar({"fecha_desde": "2026-08-25", "fecha_hasta": "2026-08-24"})
    detalle = servicio.obtener(1)
    assert '"antes": 1' in detalle["valores_antes"]


def elemento(entidad="tareas", retirado=True):
    return ElementoPapelera(entidad, 3, "Proceso <script>", "Descripcion", "Cliente / Categoria",
                            False, AHORA if retirado else None, "operador", "Depuracion")


def test_repositorio_papelera_filtra_en_sql_sin_cargar_todo():
    item = elemento()
    fila = (item.entidad, item.id_registro, item.nombre, item.descripcion, item.contexto,
            item.activo_anterior, item.fecha_retiro, item.usuario_retiro, item.motivo_retiro)
    conexion = ConexionProgramada(ResultadoSQL(fila=(1,)), ResultadoSQL(filas=[fila]))
    resultado = RepositorioPapelera(conexion).listar(
        Paginacion(1, 25),
        entidad="tareas", busqueda="%' OR 1=1 --",
    )
    assert resultado.total == 1
    sql, parametros = conexion.ejecuciones[1]
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert "OR 1=1" not in sql
    assert any("OR 1=1" in str(valor) for valor in parametros)


class EstadoPapelera:
    def __init__(self, item, deps=None, rutas=()):
        self.item = item
        self.retirado = item.fecha_retiro is not None
        self.deps = deps or {}
        self.rutas = tuple(rutas)
        self.eventos = []
        self.commits = 0
        self.rollbacks = 0
        self.eliminado = False
        self.error_eliminar = None


class UowFake:
    def __init__(self, estado): self.estado = estado; self.finalizada = False
    def __enter__(self): return self
    def __exit__(self, tipo, *_):
        if tipo and not self.finalizada: self.estado.rollbacks += 1
        return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1; self.finalizada = True


class RepoPapeleraFake:
    def __init__(self, estado): self.estado = estado
    def obtener(self, entidad, identificador, *, retirado=True, bloquear=False):
        if self.estado.eliminado or entidad != self.estado.item.entidad or identificador != self.estado.item.id_registro:
            return None
        return self.estado.item if self.estado.retirado == retirado else None
    def dependencias(self, *_): return dict(self.estado.deps)
    def retirar(self, *_): self.estado.retirado = True; self.estado.item = replace(self.estado.item, fecha_retiro=AHORA); return True
    def restaurar(self, *_): self.estado.retirado = False; self.estado.item = replace(self.estado.item, fecha_retiro=None); return True
    def rutas_operativas(self, *_): return self.estado.rutas
    def eliminar_permanente(self, *_):
        if self.estado.error_eliminar: raise self.estado.error_eliminar
        self.estado.eliminado = True
        return True


class AuditoriaFake:
    def __init__(self, estado): self.estado = estado
    def registrar(self, evento): self.estado.eventos.append(evento); return len(self.estado.eventos)


def servicio_papelera(estado, tmp_path):
    scripts = tmp_path / "scripts"; env = tmp_path / "env_scripts"
    scripts.mkdir(exist_ok=True); env.mkdir(exist_ok=True)
    config = SimpleNamespace(ruta_base_scripts=scripts, ruta_base_env_scripts=env)
    return ServicioPapelera(estado, config, fabrica_uow=UowFake,
                            repositorio=RepoPapeleraFake,
                            repositorio_auditoria=AuditoriaFake,
                            almacen=AlmacenArchivosProcesos(scripts, env))


def test_enviar_papelera_no_es_desactivar_y_audita(tmp_path):
    estado = EstadoPapelera(elemento(retirado=False), {"ejecuciones_en_curso": 0})
    servicio_papelera(estado, tmp_path).enviar("tareas", 3, "Retiro", identidad(), ContextoAuditoria())
    assert estado.retirado and estado.commits == 1
    assert estado.eventos[0].accion == "ENVIADO_A_PAPELERA"


@pytest.mark.parametrize(
    "entidad",
    ("usuarios", "clientes", "categorias", "tipos", "tareas", "scripts", "scripts_versiones"),
)
def test_todas_las_entidades_contractuales_admiten_retiro_y_restauracion_inactiva(
    entidad, tmp_path
):
    deps = {"administradores_restantes": 1, "padre_operativo": 1,
            "tarea_operativa": 1, "ejecuciones_en_curso": 0}
    estado = EstadoPapelera(elemento(entidad, False), deps)
    servicio = servicio_papelera(estado, tmp_path)
    servicio.enviar(entidad, 3, "Retiro controlado", identidad(identificador=9), ContextoAuditoria())
    if entidad == "scripts_versiones":
        scripts = tmp_path / "scripts" / "v1"
        scripts.mkdir()
        archivo = scripts / "proceso.py"
        archivo.write_text("print('ok')", encoding="utf-8")
        estado.rutas = ((str(archivo), None),)
    servicio.restaurar(entidad, 3, identidad(identificador=9), ContextoAuditoria())
    assert estado.retirado is False
    assert [evento.accion for evento in estado.eventos] == ["ENVIADO_A_PAPELERA", "RESTAURADO"]


def test_retiro_usuario_actual_y_ejecucion_en_curso_se_bloquean(tmp_path):
    usuario = EstadoPapelera(elemento("usuarios", False), {"es_admin": 0, "administradores_restantes": 1})
    with pytest.raises(ErrorValidacion, match="iniciaste sesion"):
        servicio_papelera(usuario, tmp_path).enviar("usuarios", 3, None, identidad(identificador=3), ContextoAuditoria())
    assert usuario.commits == 1 and usuario.eventos[0].resultado == "BLOQUEADO"
    tarea = EstadoPapelera(elemento(retirado=False), {"ejecuciones_en_curso": 1})
    with pytest.raises(ErrorValidacion, match="ejecucion en curso"):
        servicio_papelera(tarea, tmp_path).enviar("tareas", 3, None, identidad(), ContextoAuditoria())


def test_restauracion_valida_padre_conflicto_y_archivo(tmp_path):
    script = EstadoPapelera(elemento("scripts"), {"tarea_operativa": 0})
    with pytest.raises(ErrorValidacion, match="tarea propietaria"):
        servicio_papelera(script, tmp_path).restaurar("scripts", 3, identidad(), ContextoAuditoria())
    version = EstadoPapelera(elemento("scripts_versiones"), {"padre_operativo": 1}, rutas=())
    with pytest.raises(ErrorValidacion, match="metadata"):
        servicio_papelera(version, tmp_path).restaurar("scripts_versiones", 3, identidad(), ContextoAuditoria())
    catalogo = EstadoPapelera(elemento("clientes"), {"tareas": 0, "conflicto_clave": 1})
    with pytest.raises(ErrorValidacion, match="misma clave"):
        servicio_papelera(catalogo, tmp_path).restaurar("clientes", 3, identidad(), ContextoAuditoria())


def test_eliminacion_maestro_con_historia_operativa_se_bloquea(tmp_path):
    estado = EstadoPapelera(elemento("clientes"), {"tareas": 14})
    with pytest.raises(ErrorValidacion, match="14 tareas"):
        servicio_papelera(estado, tmp_path).eliminar_permanente("clientes", 3, identidad(), ContextoAuditoria())
    assert not estado.eliminado and estado.eventos[0].resultado == "BLOQUEADO"


@pytest.mark.parametrize("entidad", ("tareas", "scripts", "scripts_versiones"))
def test_eliminacion_recurso_con_ejecucion_historica_se_bloquea(entidad, tmp_path):
    estado = EstadoPapelera(elemento(entidad), {
        "ejecuciones_en_curso": 0,
        "ejecuciones_historicas": 1,
        "tarea_operativa": 0,
        "versiones_operativas": 0,
        "version_activa": 0,
    })
    with pytest.raises(ErrorValidacion, match="ejecuciones historicas"):
        servicio_papelera(estado, tmp_path).eliminar_permanente(
            entidad, 3, identidad(), ContextoAuditoria()
        )
    assert not estado.eliminado and estado.eventos[0].resultado == "BLOQUEADO"


def test_eliminacion_filesystem_compensable_y_auditoria_preservada(tmp_path):
    scripts = tmp_path / "scripts" / "cliente" / "v1"; scripts.mkdir(parents=True)
    archivo = scripts / "proceso.py"; archivo.write_text("print('ok')", encoding="utf-8")
    estado = EstadoPapelera(elemento("scripts_versiones"),
                            {"version_activa": 0, "ejecuciones_en_curso": 0},
                            rutas=((str(archivo), None),))
    servicio_papelera(estado, tmp_path).eliminar_permanente("scripts_versiones", 3, identidad(), ContextoAuditoria())
    assert estado.eliminado and not archivo.exists()
    assert estado.eventos[0].accion == "ELIMINADO_PERMANENTEMENTE"


def test_fallo_sql_revierte_cuarentena_sin_huerfano(tmp_path):
    scripts = tmp_path / "scripts"; scripts.mkdir()
    archivo = scripts / "proceso.py"; archivo.write_text("print('ok')", encoding="utf-8")
    estado = EstadoPapelera(elemento("scripts_versiones"),
                            {"version_activa": 0, "ejecuciones_en_curso": 0},
                            rutas=((str(archivo), None),))
    estado.error_eliminar = ErrorPersistencia()
    with pytest.raises(ErrorPersistencia):
        servicio_papelera(estado, tmp_path).eliminar_permanente("scripts_versiones", 3, identidad(), ContextoAuditoria())
    assert archivo.exists() and not list(scripts.glob("*.bak"))
    assert estado.commits == 0 and estado.rollbacks == 1


def test_operacion_repetida_no_vuelve_a_eliminar(tmp_path):
    estado = EstadoPapelera(elemento("clientes"))
    estado.eliminado = True
    with pytest.raises(ErrorValidacion, match="no se encuentra"):
        servicio_papelera(estado, tmp_path).eliminar_permanente(
            "clientes", 3, identidad(), ContextoAuditoria()
        )
    assert estado.commits == 0


def test_entidad_manipulada_se_rechaza_antes_de_consultar(tmp_path):
    estado = EstadoPapelera(elemento("clientes"))
    with pytest.raises(ErrorValidacion, match="no soportada"):
        servicio_papelera(estado, tmp_path).eliminar_permanente(
            "auditoria_cambios", 3, identidad(), ContextoAuditoria()
        )
    assert estado.commits == 0 and not estado.eliminado


def test_path_traversal_bloquea_antes_de_delete(tmp_path):
    externo = tmp_path / "externo.py"; externo.write_text("x=1", encoding="utf-8")
    estado = EstadoPapelera(elemento("scripts_versiones"),
                            {"version_activa": 0, "ejecuciones_en_curso": 0},
                            rutas=((str(externo), None),))
    with pytest.raises(ErrorValidacion, match="fuera"):
        servicio_papelera(estado, tmp_path).eliminar_permanente("scripts_versiones", 3, identidad(), ContextoAuditoria())
    assert externo.exists() and not estado.eliminado


class AuditoriaWeb:
    def listar(self, _):
        return {"resultado": Pagina((evento_auditoria("<script>alert(1)</script>"),), 1, 1, 25),
                "filtros": {k: "" for k in ("busqueda", "fecha_desde", "fecha_hasta", "usuario", "accion", "entidad", "id_entidad")},
                "acciones": ("EDITADO",), "entidades": ("tareas",)}
    def obtener(self, _): return {"registro": evento_auditoria(), "valores_antes": "<script>", "valores_despues": "{}"}


class PapeleraWeb:
    def listar(self, *_): return {"resultado": Pagina((), 0, 1, 25),
        "filtros": {k: "" for k in ("busqueda", "entidad", "usuario", "fecha_desde", "fecha_hasta")},
        "entidades": (("tareas", "Tareas"),)}
    def enviar(self, *_): raise AssertionError("CSRF debe bloquear")
    def restaurar(self, *_): raise AssertionError("CSRF debe bloquear")
    def eliminar_permanente(self, *_): raise AssertionError("CSRF debe bloquear")


def test_rutas_separan_permisos_csrf_y_escapan_xss(configuracion):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    actor = identidad({"AUDITORIA_VER", "PAPELERA_VER"})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_consulta_auditoria"] = AuditoriaWeb()
    app.extensions["servicio_papelera"] = PapeleraWeb()
    cliente = app.test_client(); iniciar_sesion(cliente, actor)
    respuesta = cliente.get("/auditoria/")
    assert respuesta.status_code == 200
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in respuesta.data
    assert cliente.get("/auditoria/1").status_code == 403
    assert cliente.get("/papelera/").status_code == 200
    assert cliente.post("/papelera/tareas/3/restaurar").status_code == 403
    assert cliente.post("/papelera/tareas/3/eliminar-permanente").status_code == 403


def test_ruta_retiro_exige_permiso_entidad_y_csrf(configuracion):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    actor = identidad({"PAPELERA_VER"})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_papelera"] = PapeleraWeb()
    cliente = app.test_client(); iniciar_sesion(cliente, actor)
    token = csrf(cliente)
    assert cliente.post("/papelera/tareas/3/retirar", data={"csrf_token": token}).status_code == 403


def test_templates_no_usan_safe_ni_confirm_nativo():
    raiz = Path("src/app_scheduler/presentacion")
    contenido = "\n".join(path.read_text(encoding="utf-8") for path in (
        raiz / "templates/auditoria/listado.html",
        raiz / "templates/auditoria/detalle.html",
        raiz / "templates/papelera/listado.html",
    ))
    assert "|safe" not in contenido
    assert "window.confirm" not in contenido and "onclick=" not in contenido


def test_sql_purga_preserva_historia_e_identificadores_de_ejecucion():
    contenido = Path("src/app_scheduler/persistencia/repositorio_papelera.py").read_text(
        encoding="utf-8"
    )
    for tabla in (
        "dbo.auditoria_cambios",
        "dbo.ejecuciones",
        "dbo.logs_tareas",
        "dbo.logs_sistema",
        "dbo.evidencias_ejecucion",
    ):
        assert f"DELETE FROM {tabla}" not in contenido
    assert "ejecuciones_historicas" in contenido
    for asignacion in ("id_tarea=NULL", "id_script=NULL", "id_version=NULL"):
        assert asignacion not in contenido.replace(" ", "")


def test_scheduler_y_ejecucion_manual_excluyen_tareas_retiradas():
    scheduler = Path("src/app_scheduler/persistencia/repositorio_scheduler.py").read_text(
        encoding="utf-8"
    )
    ejecuciones = Path("src/app_scheduler/persistencia/repositorio_ejecuciones.py").read_text(
        encoding="utf-8"
    )
    assert "t.eliminado_operativo = 0" in scheduler
    assert "t.eliminado_operativo = 0" in ejecuciones
