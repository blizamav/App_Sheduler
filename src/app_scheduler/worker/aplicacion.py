"""Bootstrap no funcional del worker reconstruido."""

from __future__ import annotations

import argparse

from app_scheduler.compartido.logging import configurar_logging
from app_scheduler.configuracion import ConfiguracionAplicacion


def preparar_worker(
    configuracion: ConfiguracionAplicacion | None = None,
):
    configuracion = configuracion or ConfiguracionAplicacion.desde_entorno()
    configuracion.validar("worker")
    return configurar_logging(
        "app_scheduler.worker",
        configuracion.log_level,
        configuracion.secretos_conocidos(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Base tecnica del worker reconstruido.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida configuracion e inicializacion sin iniciar scheduler ni ejecuciones.",
    )
    argumentos = parser.parse_args()
    logger = preparar_worker()
    if argumentos.check:
        logger.info("Worker base validado", extra={"evento": "WORKER_BASE_OK"})
        return 0
    logger.warning(
        "El worker funcional aun no esta habilitado en el runtime reconstruido.",
        extra={"evento": "WORKER_NO_IMPLEMENTADO"},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
