from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import (
    CLAVE_IDENTIDAD,
    TIPO_BASE_DATOS,
    IdentidadSesion,
)
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.modulos.configuracion_operativa.casos_uso import ServicioConfiguracionOperativa
from app_scheduler.modulos.evidencias.casos_uso import validar_soporte_estatico
from app_scheduler.modulos.evidencias.casos_uso import ServicioEvidencias
from app_scheduler.modulos.operacion.casos_uso import ServicioLogsSistema, ServicioObservabilidad
from app_scheduler.persistencia.modelos import (
    ConfiguracionSchedulerOperativa,
    ConfiguracionEvidenciaTarea,
    HeartbeatWorker,
    LogSistema,
    Pagina,
    Paginacion,
    Tarea,
)
from app_scheduler.persistencia.repositorio_operacion import RepositorioLogsSistema
from tests.reconstruccion.fakes_sql import ConexionProgramada, ProveedorProgramado, ResultadoSQL


AHORA = datetime(2026, 8, 24, 10, 0, 0)


def identidad(permisos):
    return IdentidadSesion(7, "operador", "Operador TI", TIPO_BASE_DATOS,
                           frozenset({"OPERADOR"}), frozenset(permisos))


def iniciar_sesion(cliente, actor):
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {
            "tipo": actor.tipo_identidad,
            "id_usuario": actor.id_usuario,
            "usuario": actor.usuario,
        }


def token_csrf(cliente):
    cliente.get("/")
    with cliente.session_transaction() as sesion:
        return sesion["_csrf"]["token"]


def test_repositorio_logs_parametriza_filtros_y_pagina():
    fila = (1, "actor", "EVENTO", "MODULO", "mensaje", None, None, None,
            None, AHORA, "INFO")
    conexion = ConexionProgramada(ResultadoSQL(fila=(1,)), ResultadoSQL(filas=[fila]))
    pagina = RepositorioLogsSistema(conexion).listar(
        Paginacion(2, 25), nivel="INFO", modulo="MODULO",
        busqueda="%' OR 1=1 --",
    )
    assert pagina.total == 1 and pagina.elementos[0].accion == "EVENTO"
    sql_lista, parametros = conexion.ejecuciones[1]
    assert "ORDER BY fecha_hora DESC, id DESC" in sql_lista
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql_lista
    assert "OR 1=1" not in sql_lista
    assert parametros[-2:] == (25, 25)
    assert any("OR 1=1" in str(valor) for valor in parametros)


class ProveedorLectura:
    def __init__(self, estado): self.estado = estado
    @contextmanager
    def conexion_lectura(self): yield self.estado


class RepoLogsFake:
    def __init__(self, estado): self.estado = estado
    def listar(self, paginacion, **_):
        return Pagina(tuple(self.estado), len(self.estado), paginacion.pagina, paginacion.por_pagina)
    def opciones(self): return ("SEGURIDAD",), ("LOGIN",)
    def obtener(self, identificador):
        return next((item for item in self.estado if item.id == identificador), None)


def test_servicio_logs_protege_secretos_sin_destruir_contexto():
    log = LogSistema(1, "actor", "LOGIN", "SEGURIDAD",
        "Fallo controlado password=secreto token:abc123", None,
        '{"client_secret":"valor"}', None, None, AHORA, "ERROR")
    servicio = ServicioLogsSistema(ProveedorLectura([log]), repositorio=RepoLogsFake)
    seguro = servicio.listar(pagina=1)["pagina"].elementos[0]
    assert "secreto" not in seguro.descripcion and "abc123" not in seguro.descripcion
    assert "valor" not in seguro.valor_nuevo
    assert seguro.accion == "LOGIN" and "[PROTEGIDO]" in seguro.descripcion


def test_filtros_logs_rechazan_nivel_y_rango_invalidos():
    servicio = ServicioLogsSistema(ProveedorLectura([]), repositorio=RepoLogsFake)
    with pytest.raises(ErrorValidacion, match="nivel"):
        servicio.listar(nivel="DEBUG")
    with pytest.raises(ErrorValidacion, match="posterior"):
        servicio.listar(desde="2026-08-25", hasta="2026-08-24")


class RepoOperacionFake:
    def __init__(self, estado): self.estado = estado
    def obtener_configuracion_scheduler(self): return self.estado["config"]
    def obtener_heartbeat(self, _nombre=None): return self.estado.get("heartbeat")
    def metricas(self): return self.estado["metricas"]


def configuracion_scheduler(**cambios):
    base = dict(id_configuracion=1, scheduler_activo=True,
        intervalo_revision_segundos=60, max_ejecuciones_concurrentes=3,
        permitir_ejecucion_automatica=True, modo_mantenimiento=False,
        nombre_worker_principal=None, descripcion=None,
        fecha_actualizacion=None, usuario_actualizacion=None)
    base.update(cambios)
    return ConfiguracionSchedulerOperativa(**base)


def heartbeat(fecha, estado="ESPERANDO"):
    return HeartbeatWorker(1, "worker", estado, AHORA - timedelta(hours=1), fecha,
        fecha, "OK", None, 10, 2, 1, 1, 321, "host", "hito8")


def estado_operacion(heartbeat_actual):
    return {"config": configuracion_scheduler(), "heartbeat": heartbeat_actual,
            "metricas": {"ejecuciones_en_curso": 1, "errores_24h": 0,
                         "ultima_ejecucion_automatica": AHORA,
                         "tareas_candidatas": 2}}


def test_observabilidad_clasifica_worker_activo_stale_e_inexistente():
    activo = ServicioObservabilidad(
        ProveedorLectura(estado_operacion(heartbeat(AHORA - timedelta(seconds=30)))),
        repositorio=RepoOperacionFake, reloj=lambda: AHORA,
    ).obtener_estado()
    assert activo["estado_worker"]["codigo"] == "ACTIVO"
    stale = ServicioObservabilidad(
        ProveedorLectura(estado_operacion(heartbeat(AHORA - timedelta(minutes=6)))),
        repositorio=RepoOperacionFake, reloj=lambda: AHORA,
    ).obtener_estado()
    assert stale["estado_worker"]["codigo"] == "STALE"
    vacio = ServicioObservabilidad(
        ProveedorLectura(estado_operacion(None)), repositorio=RepoOperacionFake,
        reloj=lambda: AHORA,
    ).obtener_estado()
    assert vacio["estado_worker"]["codigo"] == "NO_REGISTRADO"


def test_configuracion_scheduler_aplica_allowlist_audita_y_confirma():
    fila_config = (1, 1, 60, 3, 1, 0, "worker", "desc", None, None)
    conexion = ConexionProgramada(
        ResultadoSQL(fila=fila_config), ResultadoSQL(rowcount=1),
        ResultadoSQL(fila=(0,)), ResultadoSQL(fila=(99,)),
    )
    servicio = ServicioConfiguracionOperativa(ProveedorProgramado(conexion))
    servicio.guardar_scheduler({
        "scheduler_activo": "1", "intervalo_revision_segundos": "120",
        "max_ejecuciones_concurrentes": "4", "permitir_ejecucion_automatica": "1",
        "modo_mantenimiento": "0", "DB_PASSWORD": "no-debe-usarse",
    }, identidad({"CONFIGURACION_ADMIN"}), ContextoAuditoria(ruta="/configuracion/scheduler"))
    assert conexion.commits == 1 and conexion.rollbacks == 0
    sql_update, parametros = conexion.ejecuciones[1]
    assert "DB_PASSWORD" not in sql_update
    assert "no-debe-usarse" not in parametros
    assert parametros[:5] == (1, 120, 4, 1, 0)
    assert "INSERT INTO dbo.auditoria_cambios" in conexion.ejecuciones[3][0]


def test_configuracion_scheduler_valida_rangos_y_revierte_error_sql():
    servicio = ServicioConfiguracionOperativa(ProveedorProgramado(ConexionProgramada()))
    with pytest.raises(ErrorValidacion, match="intervalo"):
        servicio.guardar_scheduler({"intervalo_revision_segundos": "2",
            "max_ejecuciones_concurrentes": "3"}, identidad(set()), ContextoAuditoria())
    fila_config = (1, 1, 60, 3, 1, 0, None, None, None, None)
    conexion = ConexionProgramada(ResultadoSQL(fila=fila_config),
                                  ResultadoSQL(error=Exception("HY000", "fallo")))
    with pytest.raises(ErrorPersistencia):
        ServicioConfiguracionOperativa(ProveedorProgramado(conexion)).guardar_scheduler({
            "scheduler_activo": "0", "intervalo_revision_segundos": "60",
            "max_ejecuciones_concurrentes": "3",
            "permitir_ejecucion_automatica": "1", "modo_mantenimiento": "0",
        }, identidad(set()), ContextoAuditoria())
    assert conexion.commits == 0 and conexion.rollbacks == 1


def test_validacion_estatica_evidencia_ignora_comentarios_y_no_ejecuta():
    solo_comentarios = """APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = '1.0'
# ###APP_SCHEDULER_EVIDENCIA_INICIO###
# ###APP_SCHEDULER_EVIDENCIA_FIN###
raise RuntimeError('no debe ejecutarse')
"""
    assert validar_soporte_estatico(solo_comentarios)["compatible"] is False
    valido = """APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = '1.0'
INICIO = '###APP_SCHEDULER_EVIDENCIA_INICIO###'
FIN = '###APP_SCHEDULER_EVIDENCIA_FIN###'
raise RuntimeError('analisis estatico, no ejecucion')
"""
    assert validar_soporte_estatico(valido)["compatible"] is True


class EstadoEvidencia:
    def __init__(self, ruta):
        self.ruta = ruta
        self.config = ConfiguracionEvidenciaTarea(None, 1, False, "STDOUT_V1", True, False)
        self.eventos = []
        self.commits = 0


class UowEvidencia:
    def __init__(self, estado): self.estado = estado
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1


class RepoEvidenciaFake:
    def __init__(self, estado): self.estado = estado
    def obtener_configuracion(self, _): return self.estado.config
    def obtener_script_activo(self, _): return (str(self.estado.ruta), self.estado.ruta.name)
    def guardar(self, config): self.estado.config = config


class RepoTareaEvidencia:
    def __init__(self, estado): self.estado = estado
    def obtener_por_id(self, identificador):
        return Tarea(1, "Proceso", None, None, 2, "Cliente", 3, "Categoria", 4,
            "Tipo", "MANUAL", "ACTIVA", True, AHORA, None, True) if identificador == 1 else None


class AuditoriaEvidencia:
    def __init__(self, estado): self.estado = estado
    def registrar(self, evento): self.estado.eventos.append(evento)


class AlmacenEvidencia:
    def validar_ruta_persistida(self, ruta): return ruta


def test_configuracion_evidencia_valida_script_audita_y_confirma(tmp_path, configuracion):
    ruta = tmp_path / "proceso.py"
    ruta.write_text("""APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = '1.0'
INICIO = '###APP_SCHEDULER_EVIDENCIA_INICIO###'
FIN = '###APP_SCHEDULER_EVIDENCIA_FIN###'
""", encoding="utf-8")
    estado = EstadoEvidencia(ruta)
    servicio = ServicioEvidencias(
        estado, configuracion, fabrica_uow=UowEvidencia,
        repositorio=RepoEvidenciaFake, repositorio_tareas=RepoTareaEvidencia,
        repositorio_auditoria=AuditoriaEvidencia, almacen=AlmacenEvidencia(),
    )
    servicio.guardar(1, {"enviar_evidencia": "1",
        "adjuntar_archivos_declarados": "1"}, identidad({"TAREAS_EDITAR"}),
        ContextoAuditoria())
    assert estado.config.enviar_evidencia is True and estado.commits == 1
    assert estado.eventos[0].accion == "CONFIGURACION_EVIDENCIA_EDITADA"


def test_configuracion_evidencia_bloquea_comentarios_sin_commit(tmp_path, configuracion):
    ruta = tmp_path / "proceso.py"
    ruta.write_text("""APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = '1.0'
# ###APP_SCHEDULER_EVIDENCIA_INICIO###
# ###APP_SCHEDULER_EVIDENCIA_FIN###
""", encoding="utf-8")
    estado = EstadoEvidencia(ruta)
    servicio = ServicioEvidencias(
        estado, configuracion, fabrica_uow=UowEvidencia,
        repositorio=RepoEvidenciaFake, repositorio_tareas=RepoTareaEvidencia,
        repositorio_auditoria=AuditoriaEvidencia, almacen=AlmacenEvidencia(),
    )
    with pytest.raises(ErrorValidacion, match="No se puede activar"):
        servicio.guardar(1, {"enviar_evidencia": "1"}, identidad(set()),
                         ContextoAuditoria())
    assert estado.commits == 0 and estado.eventos == []


class LogsWeb:
    def listar(self, **_):
        log = LogSistema(1, None, "EVENTO", "WEB", "<script>alert(1)</script>",
                         None, None, None, None, AHORA, "INFO")
        return {"pagina": Pagina((log,), 1, 1, 25), "modulos": ("WEB",),
                "eventos": ("EVENTO",), "filtros": {"desde": "", "hasta": "",
                "nivel": "", "modulo": "", "evento": "", "buscar": ""},
                "niveles": ("INFO",)}
    def obtener(self, _): return None


def test_rutas_logs_exigen_permiso_y_template_escapa_xss(configuracion):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    actor = identidad({"PANEL_VER"})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_logs_sistema"] = LogsWeb()
    cliente = app.test_client(); iniciar_sesion(cliente, actor)
    assert cliente.get("/logs/").status_code == 403
    actor = identidad({"PANEL_VER", "LOGS_VER"})
    respuesta = cliente.get("/logs/")
    assert respuesta.status_code == 200
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in respuesta.data
    assert b"<script>alert(1)</script>" not in respuesta.data


class ConfigWeb:
    def obtener(self):
        return {"scheduler": configuracion_scheduler(), "configuraciones": ()}
    def guardar_scheduler(self, *_): raise AssertionError("CSRF debe bloquear antes")


def test_ruta_configuracion_post_exige_csrf(configuracion):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    actor = identidad({"PANEL_VER", "SCHEDULER_CONFIG_VER", "SCHEDULER_CONFIG_EDITAR"})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_configuracion_operativa"] = ConfigWeb()
    cliente = app.test_client(); iniciar_sesion(cliente, actor)
    assert cliente.post("/configuracion/scheduler", data={}).status_code == 403


def test_ruta_configuracion_separa_permiso_ver_y_editar(configuracion):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    actor = identidad({"PANEL_VER", "SCHEDULER_CONFIG_VER"})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_configuracion_operativa"] = ConfigWeb()
    cliente = app.test_client(); iniciar_sesion(cliente, actor)
    respuesta = cliente.get("/configuracion/")
    assert respuesta.status_code == 200
    assert b"Vista de solo lectura" in respuesta.data
    assert b"Guardar configuracion" not in respuesta.data
    assert cliente.post(
        "/configuracion/scheduler", data={"csrf_token": token_csrf(cliente)}
    ).status_code == 403
