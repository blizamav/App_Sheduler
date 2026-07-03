import re
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR
from app.repositorios.repositorio_scripts import listar_versiones, obtener_script_por_tarea
from app.servicios.servicio_archivos import resolver_ruta_segura


DELIMITADOR_INICIO = "###APP_SCHEDULER_EVIDENCIA_INICIO###"
DELIMITADOR_FIN = "###APP_SCHEDULER_EVIDENCIA_FIN###"
VERSION_CONTRATO = "1.0"
RE_DECLARA_EVIDENCIA = re.compile(r"^\s*APP_SCHEDULER_EVIDENCIA\s*=\s*True\s*(?:#.*)?$", re.MULTILINE)
RE_DECLARA_VERSION = re.compile(
    r"^\s*APP_SCHEDULER_EVIDENCIA_VERSION\s*=\s*['\"]1\.0['\"]\s*(?:#.*)?$",
    re.MULTILINE,
)


def obtener_script_evidencia_tarea(id_tarea):
    script = obtener_script_por_tarea(id_tarea)
    if not script:
        return None, "La tarea no tiene script asociado."
    if not script.get("id_version_activa"):
        return None, "La tarea no tiene version activa de script."

    versiones = listar_versiones(script["id_script"])
    version_activa = next(
        (version for version in versiones if version.get("id_version") == script.get("id_version_activa")),
        None,
    )
    if not version_activa:
        return None, "No se encontro la version activa del script."
    if version_activa.get("estado_version") != "ACTIVA" or not bool(version_activa.get("es_activa")):
        return None, "La version activa del script no esta en estado ACTIVA."

    return {
        "script": script,
        "version": version_activa,
        "ruta_relativa": version_activa.get("ruta_relativa"),
        "nombre_archivo": version_activa.get("nombre_archivo"),
    }, None


def validar_soporte_evidencia_script_por_tarea(id_tarea):
    contexto, error = obtener_script_evidencia_tarea(id_tarea)
    if error:
        return _resultado_no_soportado([error])

    try:
        ruta_script = validar_archivo_script_seguro(contexto.get("ruta_relativa"))
        contenido = leer_script_seguro(ruta_script)
        return validar_contenido_script_evidencia(contenido)
    except ValueError as error_validacion:
        return _resultado_no_soportado([str(error_validacion)])


def validar_archivo_script_seguro(ruta_relativa):
    if not ruta_relativa:
        raise ValueError("La version activa no tiene ruta de script registrada.")

    ruta = resolver_ruta_segura(Path(ruta_relativa))
    base_scripts = (BASE_DIR / current_app.config.get("RUTA_BASE_SCRIPTS", "scripts")).resolve()
    if base_scripts not in ruta.parents and ruta != base_scripts:
        raise ValueError("La ruta del script no esta dentro del directorio permitido.")
    if ruta.suffix.lower() != ".py":
        raise ValueError("El archivo activo no es un script Python .py.")
    if not ruta.exists() or not ruta.is_file():
        raise ValueError("El archivo del script activo no existe.")
    return ruta


def leer_script_seguro(ruta_script):
    with open(ruta_script, "r", encoding="utf-8", errors="replace") as archivo:
        return archivo.read()


def validar_contenido_script_evidencia(contenido):
    validaciones = {
        "declara_evidencia": bool(RE_DECLARA_EVIDENCIA.search(contenido or "")),
        "declara_version": bool(RE_DECLARA_VERSION.search(contenido or "")),
        "delimitador_inicio": DELIMITADOR_INICIO in (contenido or ""),
        "delimitador_fin": DELIMITADOR_FIN in (contenido or ""),
    }
    errores = []
    if not validaciones["declara_evidencia"]:
        errores.append("El script no declara APP_SCHEDULER_EVIDENCIA = True.")
    if not validaciones["declara_version"]:
        errores.append('El script no declara APP_SCHEDULER_EVIDENCIA_VERSION = "1.0".')
    if not validaciones["delimitador_inicio"]:
        errores.append("El script no contiene el delimitador de inicio de evidencia.")
    if not validaciones["delimitador_fin"]:
        errores.append("El script no contiene el delimitador de fin de evidencia.")

    return {
        "soporta_evidencia": not errores,
        "version_contrato": VERSION_CONTRATO if not errores else None,
        "validaciones": validaciones,
        "errores": errores,
    }


def _resultado_no_soportado(errores):
    return {
        "soporta_evidencia": False,
        "version_contrato": None,
        "validaciones": {
            "declara_evidencia": False,
            "declara_version": False,
            "delimitador_inicio": False,
            "delimitador_fin": False,
        },
        "errores": errores,
    }
