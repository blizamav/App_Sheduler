import logging
import sys
from collections import deque
from pathlib import Path
from threading import Lock


NOMBRE_LOGGER_WORKER = "app_scheduler.worker"
MAX_LINEAS_BUFFER_WORKER = 300
NOMBRE_ARCHIVO_BUFFER_WORKER = "worker_console.log"


class _FiltroOrigenWorker(logging.Filter):
    def filter(self, registro):
        if not hasattr(registro, "origen"):
            registro.origen = "WORKER"
        return True


class BufferVisualWorkerHandler(logging.Handler):
    def __init__(self, ruta_archivo, max_lineas=MAX_LINEAS_BUFFER_WORKER, encoding="utf-8"):
        super().__init__(level=logging.INFO)
        self.ruta_archivo = Path(ruta_archivo)
        self.max_lineas = max_lineas
        self.encoding = encoding
        self._lock = Lock()
        self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        self._cabecera_sesion = None

    def emit(self, record):
        try:
            linea = self.format(record)
            self._agregar_linea(linea)
        except Exception:
            self.handleError(record)

    def _reiniciar_buffer(self):
        if self._cabecera_sesion is None:
            self._cabecera_sesion = self._crear_cabecera_sesion()
        with self._lock:
            self.ruta_archivo.write_text(self._cabecera_sesion + "\n", encoding=self.encoding)

    def reiniciar_sesion(self):
        self._cabecera_sesion = self._crear_cabecera_sesion()
        self._reiniciar_buffer()

    def _agregar_linea(self, linea):
        with self._lock:
            lineas_actuales = []
            if self.ruta_archivo.exists():
                lineas_actuales = self.ruta_archivo.read_text(encoding=self.encoding).splitlines()
            if not lineas_actuales or lineas_actuales[0] != self._cabecera_sesion:
                lineas_actuales = [self._cabecera_sesion]
            buffer = deque(lineas_actuales[1:], maxlen=max(0, self.max_lineas - 1))
            buffer.append(linea)
            contenido = "\n".join([self._cabecera_sesion, *buffer])
            if contenido:
                contenido += "\n"
            self.ruta_archivo.write_text(contenido, encoding=self.encoding)

    def _crear_cabecera_sesion(self):
        registro = logging.LogRecord(
            name=NOMBRE_LOGGER_WORKER,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="Nueva sesion worker iniciada.",
            args=(),
            exc_info=None,
        )
        registro.origen = "WORKER"
        if self.formatter:
            return self.formatter.format(registro)
        return "Nueva sesion worker iniciada."


def configurar_logging_worker():
    logger = logging.getLogger(NOMBRE_LOGGER_WORKER)
    if getattr(logger, "_app_scheduler_configurado", False):
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formateador = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(origen)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    filtro_origen = _FiltroOrigenWorker()

    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(logging.INFO)
    handler_consola.setFormatter(formateador)
    handler_consola.addFilter(filtro_origen)

    handler_buffer = BufferVisualWorkerHandler(obtener_ruta_buffer_worker())
    handler_buffer.setFormatter(formateador)
    handler_buffer.addFilter(filtro_origen)
    handler_buffer.reiniciar_sesion()

    logger.addHandler(handler_consola)
    logger.addHandler(handler_buffer)
    logger._app_scheduler_configurado = True
    return logger


def obtener_logger_worker():
    return configurar_logging_worker()


def obtener_ruta_buffer_worker():
    return Path(__file__).resolve().parents[2] / "logs" / NOMBRE_ARCHIVO_BUFFER_WORKER


def leer_buffer_worker(limite_lineas=100):
    limite = _limite_respuesta_seguro(limite_lineas)
    ruta = obtener_ruta_buffer_worker()
    if not ruta.exists():
        return {
            "archivo_disponible": False,
            "lineas": [],
            "total_lineas_disponibles": 0,
            "limite_archivo": MAX_LINEAS_BUFFER_WORKER,
            "limite_respuesta": limite,
            "mensaje": "Consola del worker no disponible. El worker aun no ha iniciado o el buffer fue limpiado.",
        }

    lineas = ruta.read_text(encoding="utf-8").splitlines()
    lineas_visibles = lineas[1:] if lineas and "Nueva sesion worker iniciada." in lineas[0] else lineas
    return {
        "archivo_disponible": True,
        "lineas": lineas_visibles[-limite:],
        "total_lineas_disponibles": len(lineas_visibles),
        "limite_archivo": MAX_LINEAS_BUFFER_WORKER,
        "limite_respuesta": limite,
        "mensaje": "Consola del worker disponible.",
    }


def registrar_log_worker(mensaje, origen="WORKER", nivel="INFO"):
    logger = obtener_logger_worker()
    nivel_log = getattr(logging, str(nivel).upper(), logging.INFO)
    logger.log(nivel_log, mensaje, extra={"origen": origen})


def _limite_respuesta_seguro(valor):
    try:
        limite = int(valor or 100)
    except (TypeError, ValueError):
        return 100
    return max(10, min(200, limite))
