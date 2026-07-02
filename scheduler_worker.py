import argparse
import signal

from app import crear_app
from app.servicios.servicio_logging_worker import configurar_logging_worker
from app.servicios.servicio_scheduler_worker import ejecutar_worker_continuo, ejecutar_worker_una_vez


def _registrar_senales_detencion():
    def _manejar_detencion(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _manejar_detencion)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _manejar_detencion)


def main():
    parser = argparse.ArgumentParser(description="Worker automatico separado de APP Scheduler.")
    parser.add_argument("--once", action="store_true", help="Ejecuta un solo ciclo y termina.")
    argumentos = parser.parse_args()

    configurar_logging_worker()
    _registrar_senales_detencion()
    app = crear_app()
    try:
        with app.app_context():
            if argumentos.once:
                ejecutar_worker_una_vez()
            else:
                ejecutar_worker_continuo()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
