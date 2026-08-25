"""Motor unico compartido por ejecuciones manuales y automaticas."""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_ejecuciones import RepositorioEjecuciones
from app_scheduler.worker.evidencias import CapturadorEvidencia
from app_scheduler.worker.procesos import construir_entorno_base, iniciar_python, terminar_arbol


CLAVE_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EscritorLogEjecucion:
    def __init__(self, ruta: Path):
        self.ruta = ruta
        self._lock = threading.Lock()

    def escribir(self, mensaje: str, nivel: str = "INFO", canal: str = "MOTOR") -> None:
        texto = str(mensaje).rstrip("\r\n")
        linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {nivel:<5} | {canal:<6} | {texto}\n"
        with self._lock, self.ruta.open("a", encoding="utf-8", errors="replace") as archivo:
            archivo.write(linea)
            archivo.flush()


class MotorEjecucionSubprocess:
    def __init__(self, proveedor, configuracion, logger, *,
                 fabrica_uow=UnidadTrabajoSQL, repositorio=RepositorioEjecuciones,
                 timeout_segundos: float | None = None,
                 espera_terminacion_segundos: float = 5.0,
                 evento_detencion=None, reloj=time.monotonic,
                 intervalo_control_segundos: float = 0.5,
                 notificador=None):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.logger = logger
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.timeout_segundos = timeout_segundos
        self.espera_terminacion_segundos = espera_terminacion_segundos
        self.evento_detencion = evento_detencion or threading.Event()
        self.reloj = reloj
        self.intervalo_control_segundos = max(0.05, intervalo_control_segundos)
        self.notificador = notificador
        self.almacen = AlmacenArchivosProcesos(
            Path(configuracion.ruta_base_scripts), Path(configuracion.ruta_base_env_scripts),
        )

    def ejecutar(self, id_ejecucion: int) -> str:
        contexto = self._contexto(id_ejecucion)
        if contexto is None:
            self._cerrar_sin_proceso(id_ejecucion, "No existe contexto ejecutable para la version congelada.")
            return "ERROR"
        ruta_script = None
        escritor = None
        proceso = None
        capturador = CapturadorEvidencia()
        resultado_evidencia = None
        forzada = False
        motivo_control = None
        inicio = self.reloj()
        try:
            ruta_script = self.almacen.validar_ruta_persistida(Path(contexto.ruta_script_fisica))
            if ruta_script.suffix.lower() != ".py" or not ruta_script.is_file():
                raise ValueError("El archivo Python congelado no esta disponible.")
            entorno = self._entorno(contexto)
            ruta_log, relativa = self._crear_log(contexto.id_ejecucion)
            escritor = EscritorLogEjecucion(ruta_log)
            escritor.escribir(f"Inicio de ejecucion {contexto.origen_ejecucion}")
            escritor.escribir(f"Tarea: {contexto.nombre_tarea}")
            escritor.escribir(f"Script: {contexto.nombre_archivo} v{contexto.numero_version}")
            escritor.escribir("Contenido .env: no mostrado por seguridad.")
            with self.fabrica_uow(self.proveedor) as uow:
                self.tipo_repositorio(uow.obtener_conexion()).crear_log(
                    contexto, ruta_fisica=str(ruta_log), ruta_relativa=relativa,
                    nombre_archivo=ruta_log.name,
                )
                uow.confirmar()
            proceso = iniciar_python(ruta_script, entorno, ruta_script.parent)
            self._registrar_pid(id_ejecucion, proceso.pid)
            escritor.escribir(f"PID proceso: {proceso.pid}")
            hilos = [
                threading.Thread(target=self._leer_pipe,
                    args=(proceso.stdout, escritor, "STDOUT", "INFO", capturador), daemon=True),
                threading.Thread(target=self._leer_pipe,
                    args=(proceso.stderr, escritor, "STDERR", "ERROR", None), daemon=True),
            ]
            for hilo in hilos: hilo.start()
            while proceso.poll() is None:
                if self._cancelacion_solicitada(id_ejecucion):
                    motivo_control = "DETENIDA_MANUALMENTE"
                    forzada = terminar_arbol(
                        proceso, espera_segundos=self.espera_terminacion_segundos,
                    )
                    break
                if self.evento_detencion.is_set():
                    motivo_control = "WORKER_DETENIDO"
                    forzada = terminar_arbol(
                        proceso, espera_segundos=self.espera_terminacion_segundos,
                    )
                    break
                if self.timeout_segundos is not None and self.reloj() - inicio >= self.timeout_segundos:
                    motivo_control = "TIMEOUT"
                    forzada = terminar_arbol(
                        proceso, espera_segundos=self.espera_terminacion_segundos,
                    )
                    break
                time.sleep(self.intervalo_control_segundos)
            codigo = proceso.wait()
            for hilo in hilos: hilo.join(timeout=5)
            if contexto.enviar_evidencia:
                resultado_evidencia = capturador.procesar(codigo, ruta_script.parent)
                self._registrar_evidencia(
                    id_ejecucion,
                    resultado_evidencia,
                )
            if motivo_control == "DETENIDA_MANUALMENTE":
                estado, mensaje = "DETENIDA_MANUALMENTE", "Ejecucion detenida por solicitud autorizada."
            elif motivo_control == "TIMEOUT":
                estado, mensaje = "ERROR", "La ejecucion excedio el timeout tecnico configurado."
            elif motivo_control == "WORKER_DETENIDO":
                estado, mensaje = "ERROR", "La ejecucion fue interrumpida por detencion del worker."
            else:
                estado = "EXITOSA" if codigo == 0 else "ERROR"
                mensaje = None if codigo == 0 else f"Proceso finalizo con codigo {codigo}."
            escritor.escribir(f"Codigo salida proceso: {codigo}", "INFO" if codigo == 0 else "ERROR")
            escritor.escribir(f"Estado final: {estado}", "INFO" if estado == "EXITOSA" else "ERROR")
            estado_final = self._finalizar(
                id_ejecucion, estado, codigo, mensaje, forzada=forzada,
            )
            self._notificar(id_ejecucion, resultado_evidencia)
            return estado_final
        except Exception as error:
            mensaje = f"Fallo controlado del motor: {error.__class__.__name__}."
            if escritor:
                escritor.escribir(mensaje, "ERROR")
            if proceso is not None and proceso.poll() is None:
                terminar_arbol(proceso, espera_segundos=self.espera_terminacion_segundos)
            self._finalizar(id_ejecucion, "ERROR", None, mensaje)
            self._notificar(id_ejecucion, resultado_evidencia)
            self.logger.exception(
                "Motor de ejecucion finalizo con error controlado",
                extra={"evento": "EJECUCION_ERROR", "id_ejecucion": id_ejecucion},
            )
            return "ERROR"
        finally:
            for pipe in ((proceso.stdout, proceso.stderr) if proceso is not None else ()):
                if pipe is not None and not pipe.closed:
                    pipe.close()

    def _contexto(self, id_ejecucion):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).obtener_contexto(id_ejecucion)

    def _entorno(self, contexto):
        entorno = construir_entorno_base()
        if not contexto.requiere_env:
            return entorno
        if not contexto.ruta_env_fisica:
            raise ValueError("La version requiere .env y no tiene ruta persistida.")
        ruta = self.almacen.validar_ruta_persistida(Path(contexto.ruta_env_fisica))
        if not ruta.is_file():
            raise ValueError("El archivo .env requerido no esta disponible.")
        if ruta.stat().st_size > int(self.configuracion.max_env_size_kb) * 1024:
            raise ValueError("El archivo .env supera el tamano permitido.")
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8-sig").splitlines(), 1):
            limpia = linea.strip()
            if limpia and not limpia.startswith("#"):
                clave = limpia.split("=", 1)[0].strip() if "=" in limpia else ""
                if not CLAVE_ENV.fullmatch(clave):
                    raise ValueError(f"Formato .env invalido en linea {numero}.")
        valores = dotenv_values(ruta, interpolate=False)
        entorno.update({str(k): str(v) for k, v in valores.items() if k and v is not None})
        return entorno

    def _crear_log(self, id_ejecucion: int):
        ahora = datetime.now()
        raiz = Path(self.configuracion.ruta_base_logs_tareas).expanduser().resolve()
        carpeta = raiz / f"{ahora:%Y}" / f"{ahora:%m}" / f"{ahora:%d}"
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = (carpeta / f"ejecucion_{id_ejecucion}.log").resolve()
        ruta.relative_to(raiz)
        return ruta, (Path(raiz.name) / ruta.relative_to(raiz)).as_posix()

    @staticmethod
    def _leer_pipe(pipe, escritor, canal, nivel, capturador):
        if pipe is None: return
        for linea in iter(pipe.readline, ""):
            escritor.escribir(linea, nivel, canal)
            if capturador is not None: capturador.recibir(linea)

    def _registrar_pid(self, id_ejecucion, pid):
        with self.fabrica_uow(self.proveedor) as uow:
            if not self.tipo_repositorio(uow.obtener_conexion()).registrar_pid(id_ejecucion, pid):
                raise RuntimeError("La ejecucion perdio ownership antes de registrar PID.")
            uow.confirmar()

    def _cancelacion_solicitada(self, id_ejecucion):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).cancelacion_solicitada(id_ejecucion)

    def _registrar_evidencia(self, id_ejecucion, datos):
        with self.fabrica_uow(self.proveedor) as uow:
            self.tipo_repositorio(uow.obtener_conexion()).registrar_evidencia(id_ejecucion, datos)
            uow.confirmar()

    def _finalizar(self, id_ejecucion, estado, codigo, mensaje, *, forzada=False):
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            if estado != "DETENIDA_MANUALMENTE" and repo.cancelacion_solicitada(id_ejecucion):
                estado, mensaje = "DETENIDA_MANUALMENTE", "Ejecucion detenida por solicitud autorizada."
            repo.finalizar(id_ejecucion, estado, codigo, mensaje, forzada=forzada)
            uow.confirmar()
        return estado

    def _cerrar_sin_proceso(self, id_ejecucion, mensaje):
        self._finalizar(id_ejecucion, "ERROR", None, mensaje)
        self._notificar(id_ejecucion, None)

    def _notificar(self, id_ejecucion, resultado_evidencia):
        if self.notificador is None:
            return
        try:
            evidencia = resultado_evidencia.get("evidencia") if resultado_evidencia else None
            self.notificador.procesar(id_ejecucion, evidencia)
        except Exception:
            self.logger.exception(
                "Fallo controlado al procesar notificacion post-ejecucion",
                extra={"evento": "GRAPH_ENVIO_ERROR", "id_ejecucion": id_ejecucion},
            )
