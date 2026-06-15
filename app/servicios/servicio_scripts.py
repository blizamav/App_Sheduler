from pathlib import Path

from app.repositorios.repositorio_scripts import (
    activar_version,
    actualizar_env_version,
    contar_uso_version,
    contar_uso_script,
    crear_script_con_version,
    crear_version,
    desactivar_script,
    desactivar_version,
    eliminar_script,
    eliminar_version,
    listar_versiones,
    obtener_script_por_tarea,
    obtener_script,
    obtener_tarea_contexto,
    obtener_version,
    reemplazar_version,
)
from app.servicios.servicio_archivos import (
    calcular_hash_archivo,
    construir_ruta_relativa,
    eliminar_archivo_seguro,
    guardar_archivo,
    max_env_bytes,
    max_script_bytes,
    nombre_archivo_seguro,
    validar_tamano,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_tareas import resumir_programacion


def obtener_vista_scripts_tarea(id_tarea):
    tarea = obtener_tarea_contexto(id_tarea)
    if not tarea:
        return None
    tarea["resumen_programacion"] = resumir_programacion(tarea)
    script = obtener_script_por_tarea(id_tarea)
    versiones = listar_versiones(script["id_script"]) if script else []
    for version in versiones:
        version["estado_env"] = _estado_env(version)
        version["usada"] = contar_uso_version(version["id_version"]) > 0
    version_activa = _obtener_version_activa(script, versiones)
    return {
        "tarea": tarea,
        "script": script,
        "versiones": versiones,
        "version_activa": version_activa,
        "total_versiones": len(versiones),
        "proxima_version": _siguiente_version(versiones),
        "maximo_versiones": len(versiones) >= 3,
    }


def subir_version(id_tarea, archivo, observacion, requiere_env, usuario):
    tarea = obtener_tarea_contexto(id_tarea)
    if not tarea:
        return False, "Tarea no encontrada."
    if not archivo or not archivo.filename:
        return False, "Debes seleccionar un archivo .py."

    try:
        validar_tamano(archivo, max_script_bytes())
        nombre_archivo = nombre_archivo_seguro(archivo.filename, ".py")
        script = obtener_script_por_tarea(id_tarea)
        versiones = listar_versiones(script["id_script"]) if script else []
        numero_version = _siguiente_version(versiones)
        if not numero_version:
            return False, "Ya existen 3 versiones para este script. Debes reemplazar una version existente para continuar."

        ruta_relativa = construir_ruta_relativa("scripts", tarea, numero_version, nombre_archivo)
        ruta_fisica, ruta_relativa_texto = guardar_archivo(archivo, ruta_relativa)
        version = {
            "numero_version": numero_version,
            "nombre_archivo": nombre_archivo,
            "ruta_fisica": ruta_fisica,
            "ruta_relativa": ruta_relativa_texto,
            "hash_archivo": calcular_hash_archivo(ruta_fisica),
            "estado_version": "ACTIVA" if not versiones else "DISPONIBLE",
            "es_activa": not versiones,
            "observacion": observacion or None,
            "requiere_env": requiere_env,
        }
        if script:
            crear_version(script["id_script"], version, usuario)
            accion = "SCRIPT_VERSION_CREADA"
        else:
            crear_script_con_version(id_tarea, nombre_archivo, "Script asociado a tarea.", version, usuario)
            accion = "SCRIPT_CREADO"
        registrar_log_sistema(accion, "SCRIPTS", f"Version v{numero_version} cargada para tarea {tarea['nombre_tarea']}.", usuario=usuario)
        return True, f"Version v{numero_version} cargada correctamente."
    except ValueError as error:
        registrar_log_sistema("SCRIPT_CARGA_BLOQUEADA", "SCRIPTS", str(error), usuario=usuario, nivel="WARNING")
        return False, str(error)
    except Exception:
        registrar_log_sistema("SCRIPT_CARGA_ERROR", "SCRIPTS", "Error controlado al guardar archivo de script.", usuario=usuario, nivel="ERROR")
        return False, "No fue posible guardar el script."


def reemplazar_version_script(id_version, archivo, observacion, usuario):
    version_actual = obtener_version(id_version)
    if not version_actual:
        return False, "Version no encontrada."
    if contar_uso_version(id_version) > 0:
        return False, "No se puede reemplazar esta version porque ya tiene historial asociado."
    if not archivo or not archivo.filename:
        return False, "Debes seleccionar un archivo .py."

    tarea = obtener_tarea_contexto(version_actual["id_tarea"])
    try:
        validar_tamano(archivo, max_script_bytes())
        nombre_archivo = nombre_archivo_seguro(archivo.filename, ".py")
        ruta_relativa = construir_ruta_relativa("scripts", tarea, version_actual["numero_version"], nombre_archivo)
        eliminar_archivo_seguro(version_actual.get("ruta_relativa"))
        ruta_fisica, ruta_relativa_texto = guardar_archivo(archivo, ruta_relativa)
        reemplazar_version(
            id_version,
            {
                "nombre_archivo": nombre_archivo,
                "ruta_fisica": ruta_fisica,
                "ruta_relativa": ruta_relativa_texto,
                "hash_archivo": calcular_hash_archivo(ruta_fisica),
                "estado_version": "ACTIVA" if version_actual.get("es_activa") else "DISPONIBLE",
                "observacion": observacion or None,
            },
            usuario,
        )
        registrar_log_sistema("SCRIPT_VERSION_REEMPLAZADA", "SCRIPTS", f"Version v{version_actual['numero_version']} reemplazada.", usuario=usuario)
        return True, "Version reemplazada correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception:
        return False, "No fue posible reemplazar la version."


def activar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    if version["estado_version"] == "INACTIVA":
        return False, "No se puede activar una version inactiva."
    activar_version(id_version, version["id_script"], usuario)
    registrar_log_sistema("SCRIPT_VERSION_ACTIVA_CAMBIADA", "SCRIPTS", f"Version activa cambiada a v{version['numero_version']}.", usuario=usuario)
    return True, "Version activa actualizada."


def desactivar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    if version.get("es_activa"):
        return False, "No puedes desactivar la version activa. Activa otra version primero."
    desactivar_version(id_version)
    registrar_log_sistema("SCRIPT_VERSION_DESACTIVADA", "SCRIPTS", f"Version v{version['numero_version']} desactivada.", usuario=usuario)
    return True, "Version desactivada."


def eliminar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    if version.get("es_activa"):
        return False, "No puedes eliminar la version activa. Activa otra version primero."
    if contar_uso_version(id_version) > 0:
        return False, "No se puede eliminar esta version porque ya tiene historial asociado."
    eliminar_archivo_seguro(version.get("ruta_relativa"))
    eliminar_archivo_seguro(version.get("ruta_env_relativa"))
    eliminar_version(id_version)
    registrar_log_sistema("SCRIPT_VERSION_ELIMINADA", "SCRIPTS", f"Version v{version['numero_version']} eliminada fisicamente.", usuario=usuario)
    return True, "Version eliminada definitivamente."


def guardar_env_version(id_version, archivo, requiere_env, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    tarea = obtener_tarea_contexto(version["id_tarea"])
    ruta_env_fisica = version.get("ruta_env_fisica")
    ruta_env_relativa = version.get("ruta_env_relativa")
    try:
        if archivo and archivo.filename:
            validar_tamano(archivo, max_env_bytes())
            nombre_archivo = nombre_archivo_seguro(archivo.filename, ".env")
            ruta_relativa = construir_ruta_relativa("env_scripts", tarea, version["numero_version"], nombre_archivo)
            eliminar_archivo_seguro(ruta_env_relativa)
            ruta_env_fisica, ruta_env_relativa = guardar_archivo(archivo, ruta_relativa)
        actualizar_env_version(id_version, requiere_env, ruta_env_fisica, ruta_env_relativa)
        registrar_log_sistema("SCRIPT_ENV_ASOCIADO", "SCRIPTS", f"Env actualizado para version v{version['numero_version']}.", usuario=usuario)
        return True, ".env actualizado correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception:
        return False, "No fue posible guardar el .env."


def eliminar_env_version(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    eliminar_archivo_seguro(version.get("ruta_env_relativa"))
    actualizar_env_version(id_version, bool(version.get("requiere_env")), None, None)
    registrar_log_sistema("SCRIPT_ENV_ELIMINADO", "SCRIPTS", f"Env eliminado para version v{version['numero_version']}.", usuario=usuario)
    return True, ".env eliminado correctamente."


def desactivar_script_logico(id_script, usuario):
    script = obtener_script(id_script)
    if not script:
        return False, "Script no encontrado.", None
    desactivar_script(id_script, usuario)
    registrar_log_sistema("SCRIPT_DESACTIVADO", "SCRIPTS", f"Script desactivado: {script['nombre_script']}.", usuario=usuario)
    return True, "Script desactivado.", script["id_tarea"]


def eliminar_script_logico(id_script, usuario):
    script = obtener_script(id_script)
    if not script:
        return False, "Script no encontrado.", None
    if contar_uso_script(id_script) > 0:
        return False, "No se puede eliminar este script porque ya tiene historial asociado. Puedes desactivarlo.", script["id_tarea"]
    versiones = listar_versiones(id_script)
    for version in versiones:
        eliminar_archivo_seguro(version.get("ruta_relativa"))
        eliminar_archivo_seguro(version.get("ruta_env_relativa"))
    eliminar_script(id_script)
    registrar_log_sistema("SCRIPT_ELIMINADO", "SCRIPTS", f"Script eliminado fisicamente: {script['nombre_script']}.", usuario=usuario)
    return True, "Script eliminado definitivamente.", script["id_tarea"]


def _siguiente_version(versiones):
    usados = {int(version["numero_version"]) for version in versiones}
    for numero in (1, 2, 3):
        if numero not in usados:
            return numero
    return None


def _estado_env(version):
    if not version.get("requiere_env"):
        return "No requiere"
    if version.get("ruta_env_relativa"):
        return "Asociado"
    return "Pendiente .env"


def _obtener_version_activa(script, versiones):
    if not script or not versiones:
        return None
    for version in versiones:
        if version.get("es_activa"):
            return version
    id_version_activa = script.get("id_version_activa")
    for version in versiones:
        if version.get("id_version") == id_version_activa:
            return version
    return None
