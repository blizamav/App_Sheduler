"""Filesystem confinado y compensable para scripts y entornos de procesos."""

from __future__ import annotations

import ast
import hashlib
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path

from app_scheduler.compartido.errores import ErrorValidacion


_SEGMENTO_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


def segmento_seguro(valor: str) -> str:
    limpio = _SEGMENTO_SEGURO.sub("_", valor.strip()).strip("._")
    if not limpio or limpio in {".", ".."}:
        raise ErrorValidacion("No fue posible construir una ruta segura.")
    return limpio[:120]


def validar_script(nombre: str, contenido: bytes, max_bytes: int) -> None:
    if Path(nombre).name != nombre or not nombre.lower().endswith(".py"):
        raise ErrorValidacion("El archivo debe ser un .py sin componentes de ruta.")
    if not contenido:
        raise ErrorValidacion("El archivo Python esta vacio.")
    if len(contenido) > max_bytes:
        raise ErrorValidacion("El archivo Python supera el tamano permitido.")
    try:
        fuente = contenido.decode("utf-8-sig")
        ast.parse(fuente, filename=nombre)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ErrorValidacion("El archivo Python no tiene sintaxis UTF-8 valida.") from error


def validar_env(contenido: bytes, max_bytes: int) -> None:
    if not contenido:
        raise ErrorValidacion("La configuracion .env esta vacia.")
    if len(contenido) > max_bytes:
        raise ErrorValidacion("La configuracion .env supera el tamano permitido.")
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ErrorValidacion("La configuracion .env debe usar UTF-8.") from error
    for numero, linea in enumerate(texto.splitlines(), 1):
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        if "=" not in limpia or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", limpia.split("=", 1)[0].strip()):
            raise ErrorValidacion(f"La linea {numero} de la configuracion .env no es KEY=VALUE valida.")


@dataclass(slots=True)
class CambioArchivo:
    destino: Path
    temporal: Path
    respaldo: Path | None = None
    aplicado: bool = False
    permitir_reemplazo: bool = False

    def aplicar(self) -> None:
        self.destino.parent.mkdir(parents=True, exist_ok=True)
        if self.destino.exists() and not self.permitir_reemplazo:
            raise ErrorValidacion("Ya existe un archivo en el destino controlado.")
        if self.destino.exists():
            self.respaldo = self.destino.with_name(f".{self.destino.name}.{secrets.token_hex(8)}.bak")
            os.replace(self.destino, self.respaldo)
        os.replace(self.temporal, self.destino)
        self.aplicado = True

    def confirmar(self) -> None:
        if self.respaldo and self.respaldo.exists():
            self.respaldo.unlink()

    def revertir(self) -> None:
        if self.aplicado and self.destino.exists():
            self.destino.unlink()
        if self.respaldo and self.respaldo.exists():
            os.replace(self.respaldo, self.destino)
        if self.temporal.exists():
            self.temporal.unlink()


@dataclass(slots=True)
class RetiroArchivo:
    origen: Path
    respaldo: Path | None = None

    def aplicar(self) -> None:
        if not self.origen.exists():
            return
        self.respaldo = self.origen.with_name(f".{self.origen.name}.{secrets.token_hex(8)}.bak")
        os.replace(self.origen, self.respaldo)

    def confirmar(self) -> None:
        if self.respaldo and self.respaldo.exists():
            self.respaldo.unlink()

    def revertir(self) -> None:
        if self.respaldo and self.respaldo.exists():
            os.replace(self.respaldo, self.origen)


class AlmacenArchivosProcesos:
    def __init__(self, raiz_scripts: Path, raiz_env: Path):
        self.raiz_scripts = raiz_scripts.resolve()
        self.raiz_env = raiz_env.resolve()

    def ruta_script(self, segmentos: tuple[str, ...], version: int, nombre: str) -> Path:
        if version not in {1, 2, 3}:
            raise ErrorValidacion("El slot de version debe estar entre 1 y 3.")
        return self._resolver(self.raiz_scripts, *(segmento_seguro(s) for s in segmentos), f"v{version}", segmento_seguro(nombre))

    def ruta_env(self, segmentos: tuple[str, ...], version: int) -> Path:
        if version not in {1, 2, 3}:
            raise ErrorValidacion("El slot de version debe estar entre 1 y 3.")
        return self._resolver(self.raiz_env, *(segmento_seguro(s) for s in segmentos), f"v{version}", ".env")

    def preparar(self, destino: Path, contenido: bytes, *, permitir_reemplazo: bool = False) -> CambioArchivo:
        destino = self._validar_destino(destino)
        if destino.exists() and not permitir_reemplazo:
            raise ErrorValidacion("Ya existe un archivo en el destino controlado.")
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_name(f".{destino.name}.{secrets.token_hex(8)}.tmp")
        with temporal.open("xb") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        return CambioArchivo(destino, temporal, permitir_reemplazo=permitir_reemplazo)

    def preparar_retiro(self, origen: Path) -> RetiroArchivo:
        origen = self._validar_destino(origen)
        if origen.exists() and not origen.is_file():
            raise ErrorValidacion("La ruta persistida no corresponde a un archivo.")
        return RetiroArchivo(origen)

    def validar_ruta_persistida(self, ruta: Path) -> Path:
        return self._validar_destino(ruta)

    def relativa(self, destino: Path) -> str:
        raiz = self.raiz_scripts if self._esta_dentro(destino, self.raiz_scripts) else self.raiz_env
        return (Path(raiz.name) / destino.resolve().relative_to(raiz)).as_posix()

    @staticmethod
    def hash(contenido: bytes) -> str:
        return hashlib.sha256(contenido).hexdigest()

    def _resolver(self, raiz: Path, *partes: str) -> Path:
        return self._validar_destino(raiz.joinpath(*partes))

    def _validar_destino(self, destino: Path) -> Path:
        destino = destino.resolve(strict=False)
        if not (self._esta_dentro(destino, self.raiz_scripts) or self._esta_dentro(destino, self.raiz_env)):
            raise ErrorValidacion("La ruta solicitada queda fuera del almacenamiento autorizado.")
        for padre in (destino, *destino.parents):
            if padre.exists() and padre.is_symlink():
                raise ErrorValidacion("No se permiten enlaces simbolicos en el almacenamiento.")
            if padre in {self.raiz_scripts, self.raiz_env}:
                break
        return destino

    @staticmethod
    def _esta_dentro(ruta: Path, raiz: Path) -> bool:
        try:
            ruta.resolve(strict=False).relative_to(raiz.resolve())
            return True
        except ValueError:
            return False
