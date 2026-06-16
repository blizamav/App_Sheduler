import argparse

from app import crear_app
from app.servicios.servicio_scheduler_worker import ejecutar_ciclo_worker, ejecutar_worker_continuo


def main():
    parser = argparse.ArgumentParser(description="Worker automatico separado de APP Scheduler.")
    parser.add_argument("--once", action="store_true", help="Ejecuta un solo ciclo y termina.")
    argumentos = parser.parse_args()

    app = crear_app()
    with app.app_context():
        if argumentos.once:
            ejecutar_ciclo_worker()
        else:
            ejecutar_worker_continuo()


if __name__ == "__main__":
    main()
