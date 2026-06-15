import os
from pathlib import Path

from dotenv import dotenv_values

from app.config import BASE_DIR


def cargar_env_version(ruta_env_relativa):
    ruta = (BASE_DIR / Path(ruta_env_relativa)).resolve()
    if BASE_DIR.resolve() not in ruta.parents:
        raise ValueError("Ruta .env no permitida.")
    if not ruta.exists() or not ruta.is_file():
        raise ValueError("Esta version requiere un archivo .env, pero no tiene uno asociado o no existe fisicamente.")

    valores = dotenv_values(ruta)
    entorno = os.environ.copy()
    for clave, valor in valores.items():
        if clave and valor is not None:
            entorno[str(clave)] = str(valor)
    return entorno
