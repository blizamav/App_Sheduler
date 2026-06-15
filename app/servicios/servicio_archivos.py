import hashlib
import os
import re
import unicodedata
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from app.config import BASE_DIR


CARACTERES_SEGUROS = re.compile(r"[^A-Za-z0-9_]+")


def normalizar_segmento(valor, mayusculas=True):
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode("ascii")
    texto = CARACTERES_SEGUROS.sub("_", texto.strip())
    texto = re.sub(r"_+", "_", texto).strip("_")
    texto = texto or "SIN_NOMBRE"
    return texto.upper() if mayusculas else texto.lower()


def nombre_archivo_seguro(nombre_archivo, extension):
    nombre = secure_filename(nombre_archivo or "")
    if not nombre:
        raise ValueError("Nombre de archivo no valido.")
    if extension == ".env" and nombre.lower() == "env":
        return ".env"
    if extension == ".env" and nombre.lower().endswith(".env"):
        return ".env"
    if Path(nombre).suffix.lower() != extension:
        raise ValueError(f"El archivo debe tener extension {extension}.")
    base = normalizar_segmento(Path(nombre).stem, mayusculas=False)
    return f"{base}{extension}"


def validar_tamano(archivo, max_bytes):
    posicion = archivo.stream.tell()
    archivo.stream.seek(0, os.SEEK_END)
    tamano = archivo.stream.tell()
    archivo.stream.seek(posicion)
    if tamano <= 0:
        raise ValueError("El archivo esta vacio.")
    if tamano > max_bytes:
        raise ValueError("El archivo supera el tamano maximo permitido.")


def construir_ruta_relativa(base, tarea, numero_version, nombre_archivo):
    partes = [
        base,
        normalizar_segmento(tarea.get("nombre_categoria")),
        normalizar_segmento(tarea.get("nombre_tipo")),
        normalizar_segmento(tarea.get("nombre_cliente")),
        normalizar_segmento(tarea.get("nombre_tarea")),
        f"v{numero_version}",
        nombre_archivo,
    ]
    return Path(*partes)


def resolver_ruta_segura(ruta_relativa):
    destino = (BASE_DIR / ruta_relativa).resolve()
    base = BASE_DIR.resolve()
    if base not in destino.parents and destino != base:
        raise ValueError("Ruta de destino no permitida.")
    return destino


def guardar_archivo(archivo, ruta_relativa):
    ruta_fisica = resolver_ruta_segura(ruta_relativa)
    ruta_fisica.parent.mkdir(parents=True, exist_ok=True)
    archivo.stream.seek(0)
    archivo.save(ruta_fisica)
    return str(ruta_fisica), ruta_relativa.as_posix()


def calcular_hash_archivo(ruta_fisica):
    digest = hashlib.sha256()
    with open(ruta_fisica, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def eliminar_archivo_seguro(ruta_relativa):
    if not ruta_relativa:
        return
    ruta_fisica = resolver_ruta_segura(Path(ruta_relativa))
    if ruta_fisica.exists() and ruta_fisica.is_file():
        ruta_fisica.unlink()


def max_script_bytes():
    return int(current_app.config.get("MAX_SCRIPT_SIZE_MB", 5)) * 1024 * 1024


def max_env_bytes():
    return int(current_app.config.get("MAX_ENV_SIZE_KB", 100)) * 1024
