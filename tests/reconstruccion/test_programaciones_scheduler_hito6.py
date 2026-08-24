from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from pathlib import Path
import re
from threading import Event
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import CLAVE_IDENTIDAD, IdentidadSesion, TIPO_BASE_DATOS
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.modulos.programaciones.calculo import (
    calcular_ocurrencia_vencida,
    calcular_proxima_ejecucion,
)
from app_scheduler.modulos.programaciones.casos_uso import ServicioProgramaciones
from app_scheduler.persistencia.modelos import (
    CandidatoProgramacion,
    ConfiguracionScheduler,
    Pagina,
    Programacion,
    Tarea,
)
from app_scheduler.persistencia.repositorio_scheduler import RepositorioScheduler
from app_scheduler.persistencia.repositorio_programaciones import RepositorioProgramaciones
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.worker.contratos import OrigenEjecucion
from app_scheduler.worker.scheduler import ResultadoCiclo, ResultadoDespacho, ServicioScheduler
from app_scheduler.worker.scheduler import DespachadorPersistente
from app_scheduler.worker.servicio import ServicioWorker
from tests.reconstruccion.fakes_sql import ConexionProgramada, ProveedorProgramado, ResultadoSQL


AHORA = datetime(2026, 8, 19, 12, 0)
RAIZ = Path(__file__).resolve().parents[2]


def test_contrato_sql_programaciones_idempotencia_y_permisos_reales():
    ddl = (RAIZ / "database/release/002_schema_final.sql").read_text(encoding="utf-8-sig")
    bloque = re.search(
        r"CREATE TABLE dbo\.programaciones \((.*?)\n\s*\);", ddl, re.DOTALL,
    )
    assert bloque is not None
    cuerpo = bloque.group(1)
    for columna in (
        "tipo_programacion", "modo_ejecucion_dia", "hora_inicio", "hora_termino",
        "hora_ejecucion", "intervalo_minutos", "dias_semana", "dia_mes",
        "fecha_especifica", "fechas_especificas", "ejecutar_en_feriados",
        "zona_horaria", "fecha_inicio_vigencia", "fecha_fin_vigencia", "activo",
    ):
        assert re.search(rf"\b{columna}\b", cuerpo)
    assert "usuario_ejecucion" not in cuerpo and "id_version" not in cuerpo
    assert (
        "CREATE UNIQUE INDEX UX_ejecuciones_clave_programacion_automatica "
        "ON dbo.ejecuciones(clave_programacion) WHERE origen_ejecucion = "
        "'AUTOMATICA' AND clave_programacion IS NOT NULL;"
    ) in ddl
    permisos = (RAIZ / "database/release/003_seed_roles_permisos.sql").read_text(
        encoding="utf-8-sig",
    )
    for permiso in ("TAREAS_VER", "TAREAS_EDITAR", "TAREAS_ESTADO"):
        assert f"N'{permiso}'" in permisos


def programacion(**cambios):
    valores = dict(
        id_programacion=7, id_tarea=1, nombre_tarea="Proceso", estado_tarea="ACTIVA",
        tipo_programacion="DIARIA", modo_ejecucion_dia="UNA_VEZ",
        hora_inicio=None, hora_termino=None, hora_ejecucion=time(12, 0),
        intervalo_minutos=None, dias_semana=None, dia_mes=None,
        fecha_especifica=None, fechas_especificas=None, ejecutar_en_feriados=False,
        zona_horaria="America/Santiago", fecha_inicio_vigencia=None,
        fecha_fin_vigencia=None, fecha_creacion=AHORA, fecha_actualizacion=None,
        activo=True,
    )
    valores.update(cambios)
    return Programacion(**valores)


def candidato(**cambios):
    valores = dict(
        programacion=programacion(), id_script=11, id_version=22,
        estado_version="ACTIVA", script_activo=True, version_activa=True,
        proxima_ejecucion=AHORA,
    )
    valores.update(cambios)
    return CandidatoProgramacion(**valores)


@pytest.mark.parametrize(
    ("programa", "referencia", "esperada"),
    (
        (programacion(hora_ejecucion=time(8)), datetime(2026, 8, 19, 9), datetime(2026, 8, 20, 8)),
        (programacion(tipo_programacion="SEMANAL", dias_semana="VIERNES", hora_ejecucion=time(9)), datetime(2026, 8, 19, 10), datetime(2026, 8, 21, 9)),
        (programacion(tipo_programacion="MENSUAL", dia_mes=31, hora_ejecucion=time(9)), datetime(2027, 2, 1, 0), datetime(2027, 3, 31, 9)),
        (programacion(tipo_programacion="FECHA_ESPECIFICA", fecha_especifica=date(2026, 12, 31), hora_ejecucion=time(23)), datetime(2026, 12, 30, 0), datetime(2026, 12, 31, 23)),
        (programacion(tipo_programacion="FECHAS_ESPECIFICAS", fechas_especificas='["2026-08-20","2027-01-02"]', hora_ejecucion=time(7)), datetime(2026, 8, 20, 8), datetime(2027, 1, 2, 7)),
    ),
)
def test_calculo_proxima_ejecucion_en_bordes(programa, referencia, esperada):
    assert calcular_proxima_ejecucion(programa, referencia) == esperada


def test_calculo_intervalo_y_ventana_de_polling():
    programa = programacion(
        modo_ejecucion_dia="INTERVALO", hora_ejecucion=None,
        hora_inicio=time(8), hora_termino=time(9), intervalo_minutos=20,
    )
    assert calcular_proxima_ejecucion(programa, datetime(2026, 8, 19, 8, 20)) == datetime(2026, 8, 19, 8, 40)
    assert calcular_ocurrencia_vencida(programa, datetime(2026, 8, 19, 8, 40, 30), 60) == datetime(2026, 8, 19, 8, 40)


def test_calculo_respeta_vigencia_fecha_pasada_y_timezone_aware():
    programa = programacion(
        tipo_programacion="FECHA_ESPECIFICA", fecha_especifica=date(2026, 1, 1),
        fecha_fin_vigencia=date(2026, 1, 1),
    )
    assert calcular_proxima_ejecucion(programa, AHORA.replace(tzinfo=timezone.utc)) is None


def test_dst_omite_hora_inexistente_y_recalcula_sin_deriva():
    programa = programacion(
        zona_horaria="America/New_York", hora_ejecucion=time(2, 30),
    )
    referencia = datetime(2026, 3, 7, 3, tzinfo=ZoneInfo("America/New_York"))
    assert calcular_proxima_ejecucion(programa, referencia) == datetime(2026, 3, 9, 2, 30)


def test_dst_hora_ambigua_se_reserva_solo_en_primer_fold():
    programa = programacion(
        zona_horaria="America/New_York", hora_ejecucion=time(1, 30),
    )
    zona = ZoneInfo("America/New_York")
    antes = datetime(2026, 11, 1, 0, 30, tzinfo=zona)
    despues_primer_fold = datetime(2026, 11, 1, 1, 45, tzinfo=zona, fold=0)
    assert calcular_proxima_ejecucion(programa, antes) == datetime(2026, 11, 1, 1, 30)
    assert calcular_proxima_ejecucion(programa, despues_primer_fold) == datetime(2026, 11, 2, 1, 30)


class EstadoScheduler:
    def __init__(self, candidatos=()):
        self.configuracion = ConfiguracionScheduler(True, 60, 3, True, False, "worker")
        self.candidatos = tuple(candidatos)
        self.en_curso = 0
        self.feriado = False

    @contextmanager
    def conexion_lectura(self):
        yield self


class RepoSchedulerFake:
    def __init__(self, estado): self.estado = estado
    def obtener_configuracion(self): return self.estado.configuracion
    def contar_ejecuciones_en_curso(self): return self.estado.en_curso
    def listar_candidatos(self, _ahora): return self.estado.candidatos
    def es_feriado(self, _fecha): return self.estado.feriado


class DispatcherFake:
    def __init__(self, estado="DESPACHADA"):
        self.estado = estado; self.solicitudes = []; self.omisiones = []
    def despachar(self, candidato_actual, solicitud, **_opciones):
        self.solicitudes.append((candidato_actual, solicitud))
        return ResultadoDespacho(self.estado, 31 if self.estado == "DESPACHADA" else None)
    def omitir(self, candidato_actual, **datos): self.omisiones.append((candidato_actual, datos))


def servicio_scheduler(estado, dispatcher=None, bloqueado=False):
    configuracion = SimpleNamespace(ruta_control_runtime="runtime_control")
    return ServicioScheduler(
        estado, configuracion, despachador=dispatcher or DispatcherFake(),
        repositorio=RepoSchedulerFake,
        control_runtime=lambda _ruta: (bloqueado, "TEST"),
    )


def test_scheduler_congela_version_y_no_inventa_usuario_ejecutor():
    estado = EstadoScheduler((candidato(),)); dispatcher = DispatcherFake()
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker-qa")
    solicitud = dispatcher.solicitudes[0][1]
    assert resultado.despachadas == 1
    assert solicitud.id_script == 11 and solicitud.id_version == 22
    assert solicitud.origen is OrigenEjecucion.AUTOMATICA
    assert solicitud.usuario_ejecucion is None and solicitud.actor == "worker-qa"
    assert solicitud.clave_programacion == "PROGRAMACION_7_20260819T120000"


def test_solicitud_reservada_conserva_version_aunque_luego_cambie_la_activa():
    estado = EstadoScheduler((candidato(id_version=21),)); dispatcher = DispatcherFake()
    servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker-qa")
    solicitud_reservada = dispatcher.solicitudes[0][1]
    estado.candidatos = (candidato(id_version=22),)
    assert solicitud_reservada.id_version == 21
    assert estado.candidatos[0].id_version == 22


def test_scheduler_poll_duplicado_no_duplica_solicitud_logica():
    estado = EstadoScheduler((candidato(),)); dispatcher = DispatcherFake("DUPLICADA")
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker")
    assert resultado.despachadas == 0 and resultado.duplicadas == 1


def test_scheduler_sin_vencimientos_no_despacha():
    estado = EstadoScheduler(); dispatcher = DispatcherFake()
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker")
    assert resultado.evaluadas == 0 and not dispatcher.solicitudes


@pytest.mark.parametrize(
    ("configuracion", "esperado"),
    (
        (ConfiguracionScheduler(False, 60, 3, True, False, None), "SCHEDULER_INACTIVO"),
        (ConfiguracionScheduler(True, 60, 3, False, False, None), "AUTOMATICAS_DESHABILITADAS"),
        (ConfiguracionScheduler(True, 60, 3, True, True, None), "MANTENIMIENTO"),
    ),
)
def test_scheduler_respeta_interruptores_operativos(configuracion, esperado):
    estado = EstadoScheduler((candidato(),)); estado.configuracion = configuracion
    assert servicio_scheduler(estado).ejecutar_ciclo(AHORA, "worker").resultado == esperado


def test_scheduler_factory_reset_y_limite_bloquean_despacho():
    estado = EstadoScheduler((candidato(),))
    assert servicio_scheduler(estado, bloqueado=True).ejecutar_ciclo(AHORA, "worker").resultado == "BLOQUEADO_FACTORY_RESET"
    estado.en_curso = 3
    assert servicio_scheduler(estado).ejecutar_ciclo(AHORA, "worker").resultado == "LIMITE_CONCURRENCIA"


def test_scheduler_omite_version_invalida_y_avanza():
    estado = EstadoScheduler((candidato(id_version=None, version_activa=False),)); dispatcher = DispatcherFake()
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker")
    assert resultado.omitidas == 1 and not dispatcher.solicitudes
    assert dispatcher.omisiones[0][1]["motivo"] == "SCRIPT_SIN_VERSION_ACTIVA"


def test_scheduler_usa_feriado_local_sin_internet():
    estado = EstadoScheduler((candidato(),)); estado.feriado = True; dispatcher = DispatcherFake()
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker")
    assert resultado.omitidas == 1
    assert dispatcher.omisiones[0][1]["motivo"] == "FERIADO"


def test_scheduler_salta_atraso_fuera_de_ventana():
    estado = EstadoScheduler((candidato(proxima_ejecucion=AHORA.replace(hour=10)),)); dispatcher = DispatcherFake()
    resultado = servicio_scheduler(estado, dispatcher).ejecutar_ciclo(AHORA, "worker")
    assert resultado.omitidas == 1
    assert dispatcher.omisiones[0][1]["motivo"] == "FUERA_DE_VENTANA"


def test_scheduler_propaga_fallo_del_dispatcher_al_worker():
    estado = EstadoScheduler((candidato(),))
    class Dispatcher:
        def despachar(self, *_args, **_kwargs): raise RuntimeError("persistencia no disponible")
    with pytest.raises(RuntimeError, match="persistencia"):
        servicio_scheduler(estado, Dispatcher()).ejecutar_ciclo(AHORA, "worker")


def test_repositorio_reserva_pendiente_parametrizada_sin_commit():
    solicitud = SimpleNamespace(
        id_tarea=1, id_script=2, id_version=3, fecha_programada=AHORA,
        clave_programacion="clave", nombre_worker="worker",
    )
    conexion = ConexionProgramada(ResultadoSQL(fila=(99,)))
    assert RepositorioScheduler(conexion).reservar(solicitud) == 99
    sql, parametros = conexion.ejecuciones[0]
    assert "'PENDIENTE'" in sql and "usuario_ejecucion" in sql
    assert parametros == (AHORA, "clave", "worker", 2, 3, 1)
    assert "nombre_tarea_snapshot" in sql and "v.id_version = ?" in sql
    assert conexion.commits == 0


def test_repositorio_programaciones_mapea_proximo_disparo_sin_commit():
    fila = (7, 1, "Proceso", "ACTIVA", "DIARIA", "UNA_VEZ", None, None,
        time(12), None, None, None, None, None, 0, "America/Santiago",
        None, None, AHORA, None, 1, datetime(2026, 8, 20, 12))
    conexion = ConexionProgramada(ResultadoSQL(fila=(1,)), ResultadoSQL(filas=[fila]))
    pagina = RepositorioProgramaciones(conexion).listar_paginado(Paginacion(1, 25), id_tarea=1)
    assert pagina.elementos[0].proxima_ejecucion == datetime(2026, 8, 20, 12)
    assert conexion.ejecuciones[0][1] == (1,)
    assert conexion.commits == 0


def test_despachador_confirma_reserva_y_avance_en_una_transaccion():
    conexion = ConexionProgramada(
        ResultadoSQL(fila=(91,)), ResultadoSQL(rowcount=1), ResultadoSQL(rowcount=1),
    )
    dispatcher = DespachadorPersistente(ProveedorProgramado(conexion))
    solicitud = SimpleNamespace(
        id_tarea=1, id_script=11, id_version=22, fecha_programada=AHORA,
        clave_programacion="clave", nombre_worker="worker",
        proxima_ejecucion=datetime(2026, 8, 20, 12),
    )
    resultado = dispatcher.despachar(candidato(), solicitud)
    assert resultado == ResultadoDespacho("DESPACHADA", 91)
    assert conexion.commits == 1 and conexion.rollbacks == 0
    assert len(conexion.ejecuciones) == 3


def test_despachador_trata_constraint_unica_como_idempotencia():
    conexion = ConexionProgramada(
        ResultadoSQL(error=Exception("23000", "2601 clave duplicada")),
        ResultadoSQL(rowcount=1),
    )
    dispatcher = DespachadorPersistente(ProveedorProgramado(conexion))
    solicitud = SimpleNamespace(
        id_tarea=1, id_script=11, id_version=22, fecha_programada=AHORA,
        clave_programacion="clave", nombre_worker="worker",
        proxima_ejecucion=datetime(2026, 8, 20, 12),
    )
    resultado = dispatcher.despachar(candidato(), solicitud)
    assert resultado == ResultadoDespacho("DUPLICADA")
    assert conexion.commits == 1 and len(conexion.ejecuciones) == 2


def test_despachador_serializa_y_revalida_limite_concurrente():
    conexion = ConexionProgramada(ResultadoSQL(fila=(0,)), ResultadoSQL(fila=(3,)))
    dispatcher = DespachadorPersistente(ProveedorProgramado(conexion))
    solicitud = SimpleNamespace(
        id_tarea=1, id_script=11, id_version=22, fecha_programada=AHORA,
        clave_programacion="clave", nombre_worker="worker",
        proxima_ejecucion=datetime(2026, 8, 20, 12),
    )
    resultado = dispatcher.despachar(candidato(), solicitud, limite_concurrencia=3)
    assert resultado == ResultadoDespacho("LIMITE_CONCURRENCIA")
    assert "sp_getapplock" in conexion.ejecuciones[0][0]
    assert all("INSERT INTO dbo.ejecuciones" not in sql for sql, _ in conexion.ejecuciones)
    assert conexion.commits == 1


def test_despachador_rechaza_retorno_negativo_de_applock():
    conexion = ConexionProgramada(ResultadoSQL(fila=(-1,)))
    dispatcher = DespachadorPersistente(ProveedorProgramado(conexion))
    solicitud = SimpleNamespace(
        id_tarea=1, id_script=11, id_version=22, fecha_programada=AHORA,
        clave_programacion="clave", nombre_worker="worker",
        proxima_ejecucion=datetime(2026, 8, 20, 12),
    )
    resultado = dispatcher.despachar(candidato(), solicitud, limite_concurrencia=3)
    assert resultado == ResultadoDespacho("LIMITE_CONCURRENCIA")
    assert len(conexion.ejecuciones) == 1 and conexion.commits == 1


class EstadoHeartbeat:
    def __init__(self): self.eventos = []; self.commits = 0


class UowHeartbeat:
    def __init__(self, estado): self.estado = estado
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1


class RepoHeartbeatFake:
    def __init__(self, estado): self._estado = estado
    def iniciar(self, *datos): self._estado.eventos.append(("iniciar", datos))
    def estado(self, *datos): self._estado.eventos.append(("estado", datos))
    def fin_ciclo(self, *datos): self._estado.eventos.append(("fin", datos))
    def error(self, *datos): self._estado.eventos.append(("error", datos))


class LoggerFake:
    def info(self, *_args, **_kwargs): pass
    def exception(self, *_args, **_kwargs): pass


def test_worker_inicia_cicla_heartbeat_y_detiene_ordenado():
    estado = EstadoHeartbeat(); detener = Event()
    class Scheduler:
        def ejecutar_ciclo(self, *_):
            detener.set(); return ResultadoCiclo("OK", intervalo_segundos=1)
    worker = ServicioWorker(
        estado, Scheduler(), SimpleNamespace(app_version="test"), LoggerFake(),
        detener=detener, fabrica_uow=UowHeartbeat, repositorio=RepoHeartbeatFake,
    )
    worker.ejecutar()
    tipos = [item[0] for item in estado.eventos]
    assert tipos == ["iniciar", "estado", "fin", "estado"]
    assert estado.eventos[1][1][1] == "EN_CICLO"


def test_worker_registra_error_recuperable_sin_caer():
    estado = EstadoHeartbeat()
    class Scheduler:
        def ejecutar_ciclo(self, *_): raise RuntimeError("fallo controlado")
    worker = ServicioWorker(
        estado, Scheduler(), SimpleNamespace(app_version="test"), LoggerFake(),
        fabrica_uow=UowHeartbeat, repositorio=RepoHeartbeatFake,
    )
    assert worker.ejecutar_una_vez() is None
    assert [item[0] for item in estado.eventos] == ["estado", "error"]


def test_worker_once_ejecuta_un_ciclo_y_deja_heartbeat_detenido():
    estado = EstadoHeartbeat()
    class Scheduler:
        ciclos = 0
        def ejecutar_ciclo(self, *_):
            self.ciclos += 1
            return ResultadoCiclo("OK", intervalo_segundos=3600)
    scheduler = Scheduler()
    worker = ServicioWorker(
        estado, scheduler, SimpleNamespace(app_version="test"), LoggerFake(),
        fabrica_uow=UowHeartbeat, repositorio=RepoHeartbeatFake,
    )
    resultado = worker.ejecutar_solo_un_ciclo()
    assert resultado.resultado == "OK" and scheduler.ciclos == 1
    assert [item[0] for item in estado.eventos] == ["iniciar", "estado", "fin", "estado"]
    assert estado.eventos[-1][1][1] == "DETENIDO"


def test_validacion_programacion_rechaza_combinaciones_y_acepta_lista(configuracion):
    servicio = ServicioProgramaciones(None, configuracion)
    with pytest.raises(ErrorValidacion, match="hora"):
        servicio._validar({"tipo_programacion": "DIARIA", "modo_ejecucion_dia": "UNA_VEZ"})
    datos = servicio._validar({
        "tipo_programacion": "SEMANAL", "modo_ejecucion_dia": "UNA_VEZ",
        "hora_ejecucion": "09:30", "dias_semana": ["VIERNES", "LUNES"],
        "zona_horaria": "America/Santiago", "activo": True,
    })
    assert datos["dias_semana"] == "LUNES,VIERNES"


class EstadoProgramaciones:
    def __init__(self, *, estado_tarea="ACTIVA"):
        self.tarea = Tarea(1, "Proceso", None, None, 2, "Cliente", 3, "Categoria", 4,
            "Tipo", "MANUAL", estado_tarea, True, AHORA, None, True)
        self.programas = []; self.eventos = []; self.resumenes = []; self.commits = 0

    @contextmanager
    def conexion_lectura(self): yield self


class UowProgramaciones:
    def __init__(self, estado): self.estado = estado
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1


class RepoTareasProgramaciones:
    def __init__(self, estado): self.estado = estado
    def obtener_por_id(self, identificador): return self.estado.tarea if identificador == 1 else None


class RepoProgramacionesFake:
    def __init__(self, estado): self.estado = estado
    def bloquear_tarea(self, identificador): return identificador == 1
    def existe_otra_activa(self, _id_tarea, excluir_id=None):
        return any(item.activo and item.id_programacion != excluir_id for item in self.estado.programas)
    def crear(self, id_tarea, datos, _actor):
        nuevo = SimpleNamespace(id_programacion=7, id_tarea=id_tarea,
            nombre_tarea="Proceso", estado_tarea=self.estado.tarea.estado_tarea, **datos)
        self.estado.programas.append(nuevo); return 7
    def obtener(self, identificador):
        return next((item for item in self.estado.programas if item.id_programacion == identificador), None)
    def listar_activas_tarea(self, _): return tuple(item for item in self.estado.programas if item.activo)
    def actualizar(self, identificador, datos, _actor):
        actual = self.obtener(identificador)
        self.estado.programas = [SimpleNamespace(**{
            **vars(item), **(datos if item is actual else {})
        }) for item in self.estado.programas]
        return True
    def cambiar_estado(self, identificador, activo, _actor):
        self.estado.programas = [SimpleNamespace(**{**vars(item), "activo": activo})
            if item.id_programacion == identificador else item for item in self.estado.programas]
        return True
    def actualizar_resumen_tarea(self, id_tarea, programada, proxima, actor):
        self.estado.resumenes.append((id_tarea, programada, proxima, actor))


class AuditoriaProgramaciones:
    def __init__(self, estado): self.estado = estado
    def registrar(self, evento): self.estado.eventos.append(evento)


def servicio_programaciones(estado, configuracion):
    return ServicioProgramaciones(
        estado, configuracion, fabrica_uow=UowProgramaciones,
        repositorio=RepoProgramacionesFake, repositorio_tareas=RepoTareasProgramaciones,
        repositorio_auditoria=AuditoriaProgramaciones, reloj=lambda: AHORA,
    )


def datos_programacion():
    return {"tipo_programacion": "DIARIA", "modo_ejecucion_dia": "UNA_VEZ",
        "hora_ejecucion": "13:00", "zona_horaria": "America/Santiago",
        "activo": True}


def test_crear_programacion_audita_y_actualiza_resumen(configuracion):
    estado = EstadoProgramaciones(); servicio = servicio_programaciones(estado, configuracion)
    id_programacion = servicio.crear(
        1, datos_programacion(), identidad({"TAREAS_EDITAR"}), ContextoAuditoria(),
    )
    assert id_programacion == 7 and estado.commits == 1
    assert estado.eventos[0].accion == "PROGRAMACION_CREADA"
    assert estado.resumenes[-1][:2] == (1, True)
    assert estado.resumenes[-1][2] == datetime(2026, 8, 19, 13)


def test_programacion_activa_requiere_tarea_activa(configuracion):
    estado = EstadoProgramaciones(estado_tarea="INACTIVA")
    with pytest.raises(ErrorValidacion, match="tarea activa"):
        servicio_programaciones(estado, configuracion).crear(
            1, datos_programacion(), identidad({"TAREAS_EDITAR"}), ContextoAuditoria(),
        )
    assert estado.commits == 0 and not estado.programas


def test_programacion_activa_rechaza_fecha_sin_ocurrencia_futura(configuracion):
    estado = EstadoProgramaciones(); datos = datos_programacion()
    datos.update({"tipo_programacion": "FECHA_ESPECIFICA", "fecha_especifica": "2026-01-01"})
    with pytest.raises(ErrorValidacion, match="ocurrencias futuras"):
        servicio_programaciones(estado, configuracion).crear(
            1, datos, identidad({"TAREAS_EDITAR"}), ContextoAuditoria(),
        )
    assert estado.commits == 0 and not estado.programas


def test_desactivar_programacion_audita_y_deja_tarea_manual(configuracion):
    estado = EstadoProgramaciones()
    estado.programas = [SimpleNamespace(
        id_programacion=7, id_tarea=1, nombre_tarea="Proceso", estado_tarea="ACTIVA",
        tipo_programacion="DIARIA", modo_ejecucion_dia="UNA_VEZ", hora_inicio=None,
        hora_termino=None, hora_ejecucion=time(13), intervalo_minutos=None,
        dias_semana=None, dia_mes=None, fecha_especifica=None, fechas_especificas=None,
        ejecutar_en_feriados=False, zona_horaria="America/Santiago",
        fecha_inicio_vigencia=None, fecha_fin_vigencia=None, activo=True,
    )]
    servicio_programaciones(estado, configuracion).cambiar_estado(
        1, 7, False, identidad({"TAREAS_ESTADO"}), ContextoAuditoria(),
    )
    assert estado.eventos[0].accion == "PROGRAMACION_DESACTIVADA"
    assert estado.resumenes[-1][:3] == (1, False, None)


class TareasWeb:
    def obtener(self, identificador):
        return Tarea(1, "Proceso", None, None, 2, "Cliente", 3, "Categoria", 4,
                     "Tipo", "PROGRAMADA", "ACTIVA", True, AHORA, None, True) if identificador == 1 else None


class ProgramacionesWeb:
    def __init__(self): self.creaciones = []
    def listar(self, **_): return Pagina((), 0, 1, 25)
    def obtener(self, identificador):
        return programacion(
            id_programacion=identificador, tipo_programacion="FECHAS_ESPECIFICAS",
            fechas_especificas='["2026-08-20","2026-08-21"]',
        ) if identificador == 7 else None
    def crear(self, id_tarea, datos, actor, _contexto):
        self.creaciones.append((id_tarea, datos, actor.usuario)); return 7


def identidad(permisos):
    return IdentidadSesion(1, "actor", "Actor", TIPO_BASE_DATOS, frozenset({"ADMIN"}), frozenset(permisos))


def iniciar_sesion(cliente, usuario):
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {
            "tipo": usuario.tipo_identidad, "id_usuario": usuario.id_usuario,
            "usuario": usuario.usuario,
        }


def token_csrf(cliente):
    cliente.get("/")
    with cliente.session_transaction() as sesion: return sesion["_csrf"]["token"]


def app_programaciones(configuracion, usuario):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    app.extensions["cargador_identidad"] = lambda _identidad: usuario
    servicio = ProgramacionesWeb()
    app.extensions["servicio_tareas"] = TareasWeb()
    app.extensions["servicio_programaciones"] = servicio
    return app, servicio


def test_rutas_programaciones_exigen_permiso_y_csrf(configuracion):
    usuario = identidad({"PANEL_VER"}); app, _ = app_programaciones(configuracion, usuario)
    cliente = app.test_client(); iniciar_sesion(cliente, usuario)
    assert cliente.get("/tareas/1/programaciones/").status_code == 403
    token = token_csrf(cliente)
    assert cliente.post(
        "/tareas/1/programaciones/nueva", data={"csrf_token": token},
    ).status_code == 403
    usuario = identidad({"PANEL_VER", "TAREAS_VER", "TAREAS_EDITAR"}); app, _ = app_programaciones(configuracion, usuario)
    cliente = app.test_client(); iniciar_sesion(cliente, usuario)
    assert cliente.get("/tareas/1/programaciones/").status_code == 200
    assert cliente.get("/tareas/1/programaciones/nueva").status_code == 200
    assert cliente.post("/tareas/1/programaciones/nueva", data={}).status_code == 403


def test_formulario_programacion_aplica_allowlist(configuracion):
    usuario = identidad({"PANEL_VER", "TAREAS_VER", "TAREAS_EDITAR"})
    app, servicio = app_programaciones(configuracion, usuario)
    cliente = app.test_client(); iniciar_sesion(cliente, usuario); token = token_csrf(cliente)
    respuesta = cliente.post("/tareas/1/programaciones/nueva", data={
        "csrf_token": token, "tipo_programacion": "DIARIA",
        "modo_ejecucion_dia": "UNA_VEZ", "hora_ejecucion": "12:00",
        "zona_horaria": "America/Santiago", "activo": "1",
        "id_tarea": "999", "usuario_ejecucion": "inyectado",
    })
    assert respuesta.status_code == 302
    _, datos, _ = servicio.creaciones[0]
    assert "id_tarea" not in datos and "usuario_ejecucion" not in datos
    assert set(datos) == {
        "tipo_programacion", "modo_ejecucion_dia", "hora_inicio", "hora_termino",
        "hora_ejecucion", "intervalo_minutos", "dias_semana", "dia_mes",
        "fecha_especifica", "fechas_especificas", "ejecutar_en_feriados",
        "zona_horaria", "fecha_inicio_vigencia", "fecha_fin_vigencia", "activo",
    }


def test_edicion_presenta_fechas_sin_formato_json(configuracion):
    usuario = identidad({"PANEL_VER", "TAREAS_VER", "TAREAS_EDITAR"})
    app, _ = app_programaciones(configuracion, usuario)
    cliente = app.test_client(); iniciar_sesion(cliente, usuario)
    respuesta = cliente.get("/tareas/1/programaciones/7/editar")
    assert respuesta.status_code == 200
    assert b"2026-08-20, 2026-08-21" in respuesta.data
    assert b'[&quot;2026-08-20&quot;' not in respuesta.data
