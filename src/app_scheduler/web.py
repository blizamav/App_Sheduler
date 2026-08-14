"""Entrada independiente para validar el runtime web reconstruido."""

from __future__ import annotations

import argparse

from app_scheduler import crear_aplicacion


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime web reconstruido APP Scheduler.")
    parser.add_argument("--check", action="store_true", help="Valida el arranque sin abrir puerto.")
    argumentos = parser.parse_args()
    app = crear_aplicacion()
    if argumentos.check:
        return 0
    app.run(
        host=app.config["APP_HOST"],
        port=app.config["APP_PORT"],
        debug=app.config["APP_DEBUG"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
