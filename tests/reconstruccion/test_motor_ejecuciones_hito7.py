from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from threading import Lock, Thread
from types import SimpleNamespace

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import CLAVE_IDENTIDAD, IdentidadSesion, TIPO_BASE_DATOS
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.persistencia.modelos import ContextoEjecucion, DetalleEjecucion, Pagina
from app_scheduler.persistencia.repositorio_ejecuciones import RepositorioEjecuciones
from app_scheduler.modulos.ejecuciones.casos_uso import ServicioEjecuciones
from app_scheduler.worker.evidencias import CapturadorEvidencia
from app_scheduler.worker.motor import MotorEjecucionSubprocess
from app_scheduler.worker.cola import ProcesadorColaEjecuciones
from app_scheduler.worker.procesos import construir_entorno_base
from tests.reconstruccion.fakes_sql import ConexionProgramada, ResultadoSQL


AHORA = datetime(2026, 8, 19, 12, 0)


class EstadoMotor:
    def __init__(self, contexto):
        self.contexto = contexto
        self.logs = []
        self.pid = None
        self.final = None
        self.evidencia = None
        self.cancelar = False
        self.commits = 0


class RepoMotorFake:
    def __init__(self, estado): self.estado = estado
    def obtener_contexto(self, _id): return self.estado.contexto
    def crear_log(self, contexto, **datos): self.estado.logs.append((contexto, datos))
    def registrar_pid(self, _id, pid): self.estado.pid = pid; return True
    def cancelacion_solicitada(self, _id): return self.estado.cancelar
    def registrar_evidencia(self, _id, datos): self.estado.evidencia = datos
    def finalizar(self, _id, estado, codigo, mensaje, **datos):
        self.estado.final = (estado, codigo, mensaje, datos); return True


class UowFake:
    def __init__(self, proveedor): self.estado = proveedor.estado
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1


class ProveedorFake:
    def __init__(self, estado): self.estado = estado
    @contextmanager
    def conexion_lectura(self): yield self.estado


def crear_contexto(script: Path, env: Path | None = None, evidencia=False):
    return ContextoEjecucion(
        9, 1, 2, 3, "MANUAL", "EN_EJECUCION", "operador", "worker-test",
        "Proceso", "Script", script.name, 1, str(script), "scripts/x/v1/test.py",
        env is not None, str(env) if env else None, "env_scripts/x/v1/.env" if env else None,
        evidencia,
    )


def motor(tmp_path, configuracion, script_texto, *, env_texto=None, evidencia=False,
          timeout=None, estado=None, notificador=None):
    scripts = tmp_path / "scripts"; envs = tmp_path / "env_scripts"; logs = tmp_path / "logs_tareas"
    script = scripts / "x" / "v1" / "test.py"; script.parent.mkdir(parents=True)
    script.write_text(script_texto, encoding="utf-8")
    ruta_env = None
    if env_texto is not None:
        ruta_env = envs / "x" / "v1" / ".env"; ruta_env.parent.mkdir(parents=True)
        ruta_env.write_text(env_texto, encoding="utf-8")
    config = replace(configuracion, ruta_base_scripts=scripts, ruta_base_env_scripts=envs,
                     ruta_base_logs_tareas=logs)
    estado = estado or EstadoMotor(crear_contexto(script, ruta_env, evidencia))
    logger = SimpleNamespace(exception=lambda *_a, **_k: None)
    instancia = MotorEjecucionSubprocess(
        ProveedorFake(estado), config, logger, repositorio=RepoMotorFake,
        fabrica_uow=UowFake, timeout_segundos=timeout,
        espera_terminacion_segundos=0.2, intervalo_control_segundos=0.05,
        notificador=notificador,
    )
    return instancia, estado, logs


def contenido_log(logs):
    archivos = list(logs.rglob("*.log")); assert len(archivos) == 1
    return archivos[0].read_text(encoding="utf-8")


def test_motor_exito_streams_separados_y_codigo_salida(tmp_path, configuracion):
    instancia, estado, logs = motor(
        tmp_path, configuracion,
        "import sys\nprint('hola UTF-8 á')\nprint('advertencia', file=sys.stderr)\n",
    )
    assert instancia.ejecutar(9) == "EXITOSA"
    texto = contenido_log(logs)
    assert "STDOUT | hola UTF-8" in texto and "STDERR | advertencia" in texto
    assert estado.final[:2] == ("EXITOSA", 0) and estado.pid


def test_motor_error_conserva_exit_code(tmp_path, configuracion):
    instancia, estado, _ = motor(tmp_path, configuracion, "raise SystemExit(7)\n")
    assert instancia.ejecutar(9) == "ERROR"
    assert estado.final[0] == "ERROR" and estado.final[1] == 7


def test_fallo_notificacion_no_cambia_estado_ejecucion(tmp_path, configuracion):
    class NotificadorFallido:
        def procesar(self, *_): raise RuntimeError("graph simulado")
    instancia, estado, _ = motor(
        tmp_path, configuracion, "print('ok')\n", notificador=NotificadorFallido(),
    )
    assert instancia.ejecutar(9) == "EXITOSA"
    assert estado.final[:2] == ("EXITOSA", 0)


def test_motor_salida_grande_se_escribe_incremental(tmp_path, configuracion):
    instancia, estado, logs = motor(
        tmp_path, configuracion, "for i in range(3000): print(f'linea-{i}')\n",
    )
    assert instancia.ejecutar(9) == "EXITOSA"
    texto = contenido_log(logs)
    assert "linea-0" in texto and "linea-2999" in texto
    assert estado.final[:2] == ("EXITOSA", 0)


def test_motor_env_aislado_y_no_contamina_worker(tmp_path, configuracion, monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "secreto-interno-no-heredable")
    instancia, estado, logs = motor(
        tmp_path, configuracion,
        "import os\nprint(os.getenv('AMBIENTE'))\nprint(os.getenv('APP_SECRET_KEY', 'NO_HEREDADO'))\n",
        env_texto="AMBIENTE=QA_FICTICIO\n",
    )
    assert instancia.ejecutar(9) == "EXITOSA"
    texto = contenido_log(logs)
    assert "QA_FICTICIO" in texto and "NO_HEREDADO" in texto
    assert "secreto-interno-no-heredable" not in texto
    assert "AMBIENTE" not in __import__("os").environ


def test_motor_timeout_termina_y_cierra_error(tmp_path, configuracion):
    instancia, estado, _ = motor(
        tmp_path, configuracion, "import time\ntime.sleep(10)\n", timeout=0.2,
    )
    assert instancia.ejecutar(9) == "ERROR"
    assert estado.final[0] == "ERROR" and "timeout" in estado.final[2]


def test_motor_detencion_solicitada_no_usa_pid_de_request(tmp_path, configuracion):
    instancia, estado, _ = motor(tmp_path, configuracion, "import time\ntime.sleep(10)\n")
    estado.cancelar = True
    assert instancia.ejecutar(9) == "DETENIDA_MANUALMENTE"
    assert estado.final[0] == "DETENIDA_MANUALMENTE"


def test_motor_archivo_desaparecido_cierra_error_sin_subprocess(tmp_path, configuracion):
    instancia, estado, _ = motor(tmp_path, configuracion, "print('no se ejecuta')\n")
    Path(estado.contexto.ruta_script_fisica).unlink()
    assert instancia.ejecutar(9) == "ERROR"
    assert estado.pid is None and estado.final[0] == "ERROR"


def test_motor_evidencia_stdout_guarda_solo_metadata(tmp_path, configuracion):
    evidencia = '{"version_contrato":"1.0","estado":"EXITOSO","tipo_evidencia":"QA","titulo":"OK","resumen":[],"problemas":[],"adjuntos":[]}'
    codigo = f"print('###APP_SCHEDULER_EVIDENCIA_INICIO###')\nprint({evidencia!r})\nprint('###APP_SCHEDULER_EVIDENCIA_FIN###')\n"
    instancia, estado, logs = motor(tmp_path, configuracion, codigo, evidencia=True)
    assert instancia.ejecutar(9) == "EXITOSA"
    assert estado.evidencia["estado_evidencia"] == "VALIDADA"
    assert "hash_evidencia" in estado.evidencia and "evidencia_parseada" not in estado.evidencia
    assert evidencia in contenido_log(logs)


def test_capturador_rechaza_bloque_ausente_e_invalido():
    assert CapturadorEvidencia().procesar(0)["estado_evidencia"] == "NO_EMITIDA"
    capturador = CapturadorEvidencia(); capturador.recibir("###APP_SCHEDULER_EVIDENCIA_INICIO###")
    capturador.recibir("no-json"); capturador.recibir("###APP_SCHEDULER_EVIDENCIA_FIN###")
    assert capturador.procesar(0)["estado_evidencia"] == "INVALIDA"


def test_capturador_rechaza_multiples_bloques():
    capturador = CapturadorEvidencia()
    for _ in range(2):
        capturador.recibir("###APP_SCHEDULER_EVIDENCIA_INICIO###")
        capturador.recibir('{"version_contrato":"1.0"}')
        capturador.recibir("###APP_SCHEDULER_EVIDENCIA_FIN###")
    resultado = capturador.procesar(0)
    assert resultado["estado_evidencia"] == "INVALIDA"
    assert "unico bloque" in resultado["error_validacion"]


def test_capturador_valida_adjuntos_dentro_de_la_version(tmp_path):
    capturador = CapturadorEvidencia()
    datos = {
        "version_contrato": "1.0", "estado": "EXITOSO", "tipo_evidencia": "QA",
        "titulo": "OK", "resumen": [], "problemas": [],
        "adjuntos": [{"ruta": "salida/reporte.csv", "obligatorio": True}],
    }
    capturador.recibir("###APP_SCHEDULER_EVIDENCIA_INICIO###")
    capturador.recibir(json.dumps(datos))
    capturador.recibir("###APP_SCHEDULER_EVIDENCIA_FIN###")
    assert capturador.procesar(0, tmp_path)["estado_evidencia"] == "ADJUNTO_FALTANTE"

    archivo = tmp_path / "salida" / "reporte.csv"
    archivo.parent.mkdir()
    archivo.write_text("ok", encoding="utf-8")
    assert capturador.procesar(0, tmp_path)["estado_evidencia"] == "VALIDADA"


def test_capturador_no_exige_adjunto_opcional(tmp_path):
    capturador = CapturadorEvidencia()
    datos = {
        "version_contrato": "1.0", "estado": "EXITOSO", "tipo_evidencia": "QA",
        "titulo": "OK", "resumen": [], "problemas": [],
        "adjuntos": [{"ruta": "salida/opcional.csv", "obligatorio": False}],
    }
    capturador.recibir("###APP_SCHEDULER_EVIDENCIA_INICIO###")
    capturador.recibir(json.dumps(datos))
    capturador.recibir("###APP_SCHEDULER_EVIDENCIA_FIN###")
    assert capturador.procesar(0, tmp_path)["estado_evidencia"] == "VALIDADA"


def test_entorno_base_no_hereda_secretos(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "secreto")
    monkeypatch.setenv("FACTORY_RESET_DB_PASSWORD", "secreto2")
    entorno = construir_entorno_base()
    assert "DB_PASSWORD" not in entorno and "FACTORY_RESET_DB_PASSWORD" not in entorno
    assert entorno["PYTHONUNBUFFERED"] == "1"


def test_claim_atomico_usa_lock_readpast_y_limite():
    conexion = ConexionProgramada(ResultadoSQL(fila=(44,)))
    assert RepositorioEjecuciones(conexion).reclamar_siguiente("worker-a", 3) == 44
    sql, parametros = conexion.ejecuciones[0]
    assert "sp_getapplock" in sql and "UPDLOCK, READPAST, ROWLOCK" in sql
    assert "WHERE estado_ejecucion = 'PENDIENTE'" in sql
    assert parametros == (3, "worker-a")


def test_claim_sin_capacidad_retorna_none_sin_error_driver():
    conexion = ConexionProgramada(ResultadoSQL(fila=None))
    assert RepositorioEjecuciones(conexion).reclamar_siguiente("worker-b", 1) is None


def test_contrato_sql_real_no_inventa_timeout_ni_id_programacion():
    raiz = Path(__file__).resolve().parents[2]
    ddl = (raiz / "database/release/002_schema_final.sql").read_text(encoding="utf-8-sig")
    bloque = ddl.split("CREATE TABLE dbo.ejecuciones (", 1)[1].split("\n    );", 1)[0]
    for campo in ("id_tarea", "id_script", "id_version", "usuario_ejecucion",
                  "nombre_worker", "pid_proceso", "codigo_salida", "clave_programacion"):
        assert campo in bloque
    assert "timeout" not in bloque.lower() and "id_programacion" not in bloque
    for estado in ("PENDIENTE", "EN_EJECUCION", "EXITOSA", "ERROR",
                   "CANCELADA", "DETENIDA_MANUALMENTE"):
        assert estado in (raiz / "database/release/004_seed_catalogos_base.sql").read_text(encoding="utf-8-sig")


def test_finalizacion_no_sobrescribe_detencion():
    conexion = ConexionProgramada(ResultadoSQL(rowcount=0))
    assert not RepositorioEjecuciones(conexion).finalizar(1, "EXITOSA", 0, None)
    assert "fecha_hora_detencion IS NULL" in conexion.ejecuciones[0][0]


class EstadoCola:
    def __init__(self):
        self.config = (3, 0); self.en_ejecucion = 0; self.pendientes = [51]
        self.claims = []; self.ejecutadas = []; self.commits = 0; self.lock = Lock()


class RepoColaFake:
    def __init__(self, estado): self.estado = estado
    def obtener_configuracion(self): return self.estado.config
    def contar_en_ejecucion(self): return self.estado.en_ejecucion
    def reclamar_siguiente(self, worker, limite):
        with self.estado.lock:
            if self.estado.en_ejecucion >= limite or not self.estado.pendientes: return None
            item = self.estado.pendientes.pop(0); self.estado.en_ejecucion += 1
            self.estado.claims.append((item, worker)); return item


class MotorColaFake:
    def __init__(self, estado): self.estado = estado
    def ejecutar(self, identificador): self.estado.ejecutadas.append(identificador); return "EXITOSA"


def test_dos_workers_solo_reclaman_una_vez_la_misma_pendiente(configuracion):
    estado = EstadoCola(); proveedor = ProveedorFake(estado)
    procesadores = [ProcesadorColaEjecuciones(
        proveedor, configuracion, MotorColaFake(estado), nombre,
        fabrica_uow=UowFake, repositorio=RepoColaFake,
        control_runtime=lambda _ruta: (False, "NORMAL"),
    ) for nombre in ("worker-a", "worker-b")]
    hilos = [Thread(target=p.procesar_disponibles) for p in procesadores]
    for hilo in hilos: hilo.start()
    for hilo in hilos: hilo.join()
    for procesador in procesadores: procesador.cerrar(esperar=True)
    assert len(estado.claims) == 1 and estado.ejecutadas == [51]


def test_cola_no_reclama_en_mantenimiento_o_factory_reset(configuracion):
    for mantenimiento, bloqueado in ((1, False), (0, True)):
        estado = EstadoCola(); estado.config = (3, mantenimiento)
        procesador = ProcesadorColaEjecuciones(
            ProveedorFake(estado), configuracion, MotorColaFake(estado), "worker",
            fabrica_uow=UowFake, repositorio=RepoColaFake,
            control_runtime=lambda _ruta, valor=bloqueado: (valor, "TEST"),
        )
        assert procesador.procesar_disponibles() == 0
        procesador.cerrar(esperar=True)
        assert not estado.claims


def identidad(permisos):
    return IdentidadSesion(1, "operador", "Operador", TIPO_BASE_DATOS,
                           frozenset({"OPERADOR"}), frozenset(permisos))


class ServicioWebFake:
    def __init__(self): self.solicitudes = []; self.detenciones = []
    def solicitar_manual(self, id_tarea, actor, _contexto): self.solicitudes.append((id_tarea, actor.usuario)); return 77
    def solicitar_detencion(self, id_ejecucion, actor, _contexto, motivo): self.detenciones.append((id_ejecucion, actor.usuario, motivo))
    def obtener(self, _id): return None
    def listar(self, **_): return Pagina((), 0, 1, 25)


def app_web(configuracion, usuario):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    app.extensions["cargador_identidad"] = lambda _datos: usuario
    servicio = ServicioWebFake(); app.extensions["servicio_ejecuciones"] = servicio
    return app, servicio


def sesion_y_token(cliente, usuario):
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {"tipo": usuario.tipo_identidad, "id_usuario": 1, "usuario": usuario.usuario}
        return sesion["_csrf"]["token"]


def test_manual_http_reserva_sin_ejecutar_y_exige_csrf(configuracion):
    usuario = identidad({"EJECUCIONES_EJECUTAR"}); app, servicio = app_web(configuracion, usuario)
    cliente = app.test_client(); token = sesion_y_token(cliente, usuario)
    assert cliente.post("/tareas/1/ejecutar").status_code == 403
    respuesta = cliente.post("/tareas/1/ejecutar", data={"csrf_token": token})
    assert respuesta.status_code == 302 and respuesta.headers["Location"].endswith("/ejecuciones/77")
    assert servicio.solicitudes == [(1, "operador")]


def test_manual_http_rechaza_sin_permiso(configuracion):
    usuario = identidad({"TAREAS_VER"}); app, servicio = app_web(configuracion, usuario)
    cliente = app.test_client(); token = sesion_y_token(cliente, usuario)
    assert cliente.post("/tareas/1/ejecutar", data={"csrf_token": token}).status_code == 403
    assert not servicio.solicitudes


def test_detencion_http_exige_permiso_y_csrf(configuracion):
    usuario = identidad({"EJECUCIONES_DETENER"}); app, servicio = app_web(configuracion, usuario)
    cliente = app.test_client(); token = sesion_y_token(cliente, usuario)
    assert cliente.post("/ejecuciones/5/detener").status_code == 403
    respuesta = cliente.post(
        "/ejecuciones/5/detener", data={"csrf_token": token, "motivo": "Prueba"},
    )
    assert respuesta.status_code == 302
    assert servicio.detenciones == [(5, "operador", "Prueba")]


class EstadoManual:
    def __init__(self, fila):
        self.fila = fila; self.commits = 0; self.auditorias = []; self.reservas = []
        self.config = (3, 0); self.ocupadas = 0


class RepoManualFake:
    def __init__(self, estado): self.estado = estado
    def adquirir_lock_despacho(self): return True
    def obtener_configuracion(self): return self.estado.config
    def contar_ocupadas(self): return self.estado.ocupadas
    def obtener_contexto_manual(self, _id): return self.estado.fila
    def reservar_manual(self, fila, usuario): self.estado.reservas.append((fila[12], usuario)); return 88


class RepoAuditoriaFake:
    def __init__(self, estado): self.estado = estado
    def registrar(self, evento): self.estado.auditorias.append(evento); return 1


def fila_manual(script, env=None):
    return (1, "Proceso", "Cliente", "Categoria", "Tipo", "ACTIVA", 1, 1,
            2, "Script", 1, 3, 3, 1, script.name, str(script),
            "scripts/x/v1/test.py", "ACTIVA", 1, 1 if env else 0,
            str(env) if env else None, "env_scripts/x/v1/.env" if env else None, 0)


def test_servicio_manual_congela_version_activa_y_usuario_app(tmp_path, configuracion):
    scripts = tmp_path / "scripts"; envs = tmp_path / "env_scripts"
    script = scripts / "x" / "v1" / "test.py"; script.parent.mkdir(parents=True)
    script.write_text("print('ok')", encoding="utf-8")
    config = replace(configuracion, ruta_base_scripts=scripts, ruta_base_env_scripts=envs)
    estado = EstadoManual(fila_manual(script))
    servicio = ServicioEjecuciones(
        ProveedorFake(estado), config, fabrica_uow=UowFake,
        repositorio=RepoManualFake, repositorio_auditoria=RepoAuditoriaFake,
        control_runtime=lambda _ruta: (False, "NORMAL"),
    )
    actor = identidad({"EJECUCIONES_EJECUTAR"})
    assert servicio.solicitar_manual(1, actor, ContextoAuditoria()) == 88
    assert estado.reservas == [(3, "operador")]
    assert estado.auditorias[0].accion == "EJECUCION_MANUAL_SOLICITADA"
    assert estado.commits == 1


@pytest.mark.parametrize(
    ("config", "ocupadas", "mensaje"),
    (((3, 1), 0, "mantenimiento"), ((3, 0), 3, "maximo")),
)
def test_servicio_manual_respeta_mantenimiento_y_concurrencia(
    tmp_path, configuracion, config, ocupadas, mensaje,
):
    scripts = tmp_path / "scripts"; envs = tmp_path / "env_scripts"
    script = scripts / "x" / "v1" / "test.py"; script.parent.mkdir(parents=True)
    script.write_text("print('ok')", encoding="utf-8")
    app_config = replace(configuracion, ruta_base_scripts=scripts, ruta_base_env_scripts=envs)
    estado = EstadoManual(fila_manual(script)); estado.config = config; estado.ocupadas = ocupadas
    servicio = ServicioEjecuciones(
        ProveedorFake(estado), app_config, fabrica_uow=UowFake,
        repositorio=RepoManualFake, repositorio_auditoria=RepoAuditoriaFake,
        control_runtime=lambda _ruta: (False, "NORMAL"),
    )
    with pytest.raises(ErrorValidacion, match=mensaje):
        servicio.solicitar_manual(1, identidad({"EJECUCIONES_EJECUTAR"}), ContextoAuditoria())
    assert estado.commits == 0 and not estado.reservas
