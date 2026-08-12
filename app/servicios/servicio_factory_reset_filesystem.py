import hashlib
import os
import shutil
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR
from app.servicios.servicio_factory_reset import ROOTS_FILESYSTEM


class ErrorFactoryResetFilesystem(RuntimeError):
    pass


def preparar_roots_factory_reset(id_operacion):
    sufijo = _sufijo_operacion(id_operacion)
    control = _resolver_control()
    backup_base = control / "factory_backups" / sufijo
    if backup_base.exists():
        raise ErrorFactoryResetFilesystem("Ya existe una cuarentena para esta operacion.")
    operaciones = []
    for nombre, clave, defecto in ROOTS_FILESYSTEM:
        root = _resolver_root(clave, defecto)
        if control == root or control in root.parents or root in control.parents:
            raise ErrorFactoryResetFilesystem("El root de control no puede mezclarse con runtime.")
        if root.is_symlink() or (root.exists() and not root.is_dir()):
            raise ErrorFactoryResetFilesystem(f"Root no regular rechazado: {nombre}.")
        if root.exists():
            _validar_arbol_sin_symlinks(root)
        operaciones.append({"nombre": nombre, "root": root, "backup": backup_base / nombre, "aplicada": False})
    _validar_roots_independientes(operaciones)
    return operaciones


def limpiar_roots_factory_reset(operaciones):
    aplicadas = []
    try:
        for item in operaciones:
            root = item["root"]
            backup = item["backup"]
            root.mkdir(parents=True, exist_ok=True)
            _validar_arbol_sin_symlinks(root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(root, backup, copy_function=shutil.copy2)
            if _huella_arbol(root) != _huella_arbol(backup):
                raise ErrorFactoryResetFilesystem(f"La cuarentena no coincide con {item['nombre']}.")
            item["aplicada"] = True
            aplicadas.append(item)
            _limpiar_contenido_root(root)
        return {
            "ok": True,
            "roots_limpios": len(aplicadas),
            "cuarentenas": [str(item["backup"]) for item in aplicadas],
        }
    except Exception as error:
        rollback_roots_factory_reset(aplicadas)
        if isinstance(error, ErrorFactoryResetFilesystem):
            raise
        raise ErrorFactoryResetFilesystem(f"No fue posible limpiar roots: {error.__class__.__name__}.") from error


def rollback_roots_factory_reset(operaciones):
    errores = []
    for item in reversed(list(operaciones)):
        if not item.get("aplicada"):
            continue
        root = item["root"]
        backup = item["backup"]
        try:
            if not backup.is_dir() or backup.is_symlink():
                raise ErrorFactoryResetFilesystem("Cuarentena no disponible.")
            root.mkdir(parents=True, exist_ok=True)
            _limpiar_contenido_root(root)
            shutil.copytree(backup, root, dirs_exist_ok=True, copy_function=shutil.copy2)
            if _huella_arbol(root) != _huella_arbol(backup):
                raise ErrorFactoryResetFilesystem("Restauracion no verificable.")
        except Exception as error:
            errores.append(f"{item['nombre']}:{error.__class__.__name__}")
    return {"ok": not errores, "errores": errores}


def validar_roots_vacios(operaciones):
    for item in operaciones:
        root = item["root"]
        if not root.is_dir() or root.is_symlink():
            return False
        try:
            next(root.iterdir())
            return False
        except StopIteration:
            pass
    return True


def _limpiar_contenido_root(root):
    _validar_arbol_sin_symlinks(root)
    for actual, carpetas, archivos in os.walk(root, topdown=False, followlinks=False):
        actual_path = Path(actual)
        for nombre in archivos:
            archivo = actual_path / nombre
            _validar_descendiente(root, archivo)
            archivo.unlink()
        for nombre in carpetas:
            carpeta = actual_path / nombre
            _validar_descendiente(root, carpeta)
            carpeta.rmdir()


def _huella_arbol(root):
    hasher = hashlib.sha256()
    entradas = []
    for actual, carpetas, archivos in os.walk(root, followlinks=False):
        actual_path = Path(actual)
        for nombre in carpetas:
            carpeta = actual_path / nombre
            _validar_descendiente(root, carpeta)
            entradas.append(("D", carpeta.relative_to(root).as_posix(), carpeta))
        for nombre in archivos:
            archivo = actual_path / nombre
            _validar_descendiente(root, archivo)
            entradas.append(("F", archivo.relative_to(root).as_posix(), archivo))
    total = 0
    for tipo, relativa, ruta in sorted(entradas, key=lambda item: (item[0], item[1])):
        hasher.update((tipo + ":" + relativa).encode("utf-8"))
        if tipo == "F":
            archivo = ruta
            with archivo.open("rb") as stream:
                for bloque in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(bloque)
            total += 1
    return total, hasher.hexdigest()


def _validar_arbol_sin_symlinks(root):
    if root.is_symlink():
        raise ErrorFactoryResetFilesystem("Root symlink rechazado.")
    for actual, carpetas, archivos in os.walk(root, followlinks=False):
        actual_path = Path(actual)
        for nombre in [*carpetas, *archivos]:
            ruta = actual_path / nombre
            if ruta.is_symlink():
                raise ErrorFactoryResetFilesystem("Symlink runtime rechazado.")
            _validar_descendiente(root, ruta)


def _validar_descendiente(root, ruta):
    root_resuelto = root.resolve()
    ruta_resuelta = ruta.resolve()
    if root_resuelto not in ruta_resuelta.parents:
        raise ErrorFactoryResetFilesystem("Ruta fuera del root permitido.")


def _resolver_root(clave, defecto):
    valor = str(current_app.config.get(clave, defecto)).strip() or defecto
    ruta_configurada = Path(valor).expanduser()
    if ".." in ruta_configurada.parts:
        raise ErrorFactoryResetFilesystem(f"Path traversal rechazado: {clave}.")
    if not ruta_configurada.is_absolute():
        ruta_configurada = BASE_DIR / ruta_configurada
    if _contiene_symlink(ruta_configurada):
        raise ErrorFactoryResetFilesystem(f"Root con symlink rechazado: {clave}.")
    ruta = ruta_configurada.resolve()
    if ruta == BASE_DIR or ruta.parent == ruta:
        raise ErrorFactoryResetFilesystem(f"Root peligroso rechazado: {clave}.")
    return ruta


def _resolver_control():
    valor = str(current_app.config.get("RUTA_CONTROL_RUNTIME", "runtime_control")).strip() or "runtime_control"
    ruta = Path(valor).expanduser()
    if ".." in ruta.parts:
        raise ErrorFactoryResetFilesystem("Path traversal rechazado en control runtime.")
    if not ruta.is_absolute():
        ruta = BASE_DIR / ruta
    if _contiene_symlink(ruta):
        raise ErrorFactoryResetFilesystem("Root de control con symlink rechazado.")
    ruta = ruta.resolve()
    if ruta == BASE_DIR or ruta.parent == ruta:
        raise ErrorFactoryResetFilesystem("Root de control peligroso.")
    return ruta


def _contiene_symlink(ruta):
    actual = Path(ruta)
    while actual != actual.parent:
        if actual.exists() and actual.is_symlink():
            return True
        actual = actual.parent
    return False


def _validar_roots_independientes(operaciones):
    roots = [item["root"] for item in operaciones]
    if len(set(roots)) != len(roots):
        raise ErrorFactoryResetFilesystem("Los roots runtime deben ser unicos.")
    for root in roots:
        for otro in roots:
            if root != otro and (root in otro.parents or otro in root.parents):
                raise ErrorFactoryResetFilesystem("Los roots runtime no pueden contenerse entre si.")


def _sufijo_operacion(valor):
    texto = "".join(caracter for caracter in str(valor or "") if caracter.isalnum())[:12]
    if len(texto) < 8:
        raise ErrorFactoryResetFilesystem("Identificador de operacion invalido.")
    return texto.upper()
