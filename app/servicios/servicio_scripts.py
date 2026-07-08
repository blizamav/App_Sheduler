import re

from app.repositorios.repositorio_scripts import (
    activar_version,
    actualizar_env_version,
    buscar_duplicado_script_tarea,
    buscar_duplicado_version_numero,
    contar_uso_version,
    contar_uso_script,
    crear_script_con_version,
    crear_version,
    desactivar_script,
    desactivar_version,
    listar_versiones,
    listar_versiones_incluyendo_papelera,
    marcar_script_eliminado_operativo,
    marcar_version_eliminada_operativa,
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
    resolver_ruta_segura,
    validar_tamano,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_duplicados import (
    MENSAJE_DUPLICADO_PAPELERA,
    MENSAJE_DUPLICADO_SQL,
    es_error_duplicado_sql,
    registrar_bloqueo_duplicado,
    validar_sin_duplicado,
)
from app.servicios.servicio_tareas import resumir_programacion


def obtener_vista_scripts_tarea(id_tarea):
    tarea = obtener_tarea_contexto(id_tarea)
    if not tarea:
        return None
    tarea["resumen_programacion"] = resumir_programacion(tarea)
    script = obtener_script_por_tarea(id_tarea)
    versiones = listar_versiones(script["id_script"]) if script else []
    versiones_todas = listar_versiones_incluyendo_papelera(script["id_script"]) if script else []
    for version in versiones:
        version["estado_env"] = _estado_env(version)
        version["usada"] = contar_uso_version(version["id_version"]) > 0
    version_activa = _obtener_version_activa(script, versiones)
    return {
        "tarea": tarea,
        "script": script,
        "versiones": versiones,
        "version_activa": version_activa,
        "nombre_archivo_activo": version_activa.get("nombre_archivo") if version_activa else None,
        "numero_version_activa": version_activa.get("numero_version") if version_activa else None,
        "requiere_env_activa": version_activa.get("requiere_env") if version_activa else None,
        "ruta_env_relativa_activa": version_activa.get("ruta_env_relativa") if version_activa else None,
        "estado_env_activa": version_activa.get("estado_env") if version_activa else None,
        "estado_script": "Activo" if script and script.get("activo") else "Pendiente",
        "total_versiones": len(versiones),
        "proxima_version": _siguiente_version(versiones_todas),
        "maximo_versiones": len(versiones_todas) >= 3,
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
        duplicado_script = buscar_duplicado_script_tarea(id_tarea)
        if not script:
            mensaje = validar_sin_duplicado(
                duplicado_script,
                "scripts",
                usuario,
                valores={"id_tarea": id_tarea},
                modulo="SCRIPTS",
            )
            if mensaje:
                return False, mensaje

        versiones = listar_versiones(script["id_script"]) if script else []
        versiones_todas = listar_versiones_incluyendo_papelera(script["id_script"]) if script else []
        numero_version = _siguiente_version(versiones_todas)
        if not numero_version:
            if any(bool(version.get("eliminado_operativo")) for version in versiones_todas):
                registrar_bloqueo_duplicado(
                    "scripts_versiones",
                    usuario,
                    MENSAJE_DUPLICADO_PAPELERA,
                    id_entidad=script.get("id_script") if script else None,
                    nombre_entidad=tarea["nombre_tarea"],
                    valores={"id_tarea": id_tarea},
                    modulo="SCRIPTS",
                )
                return False, MENSAJE_DUPLICADO_PAPELERA
            registrar_auditoria(
                "BLOQUEO_MAXIMO_VERSIONES",
                "scripts_versiones",
                id_entidad=script.get("id_script") if script else None,
                nombre_entidad=tarea["nombre_tarea"],
                descripcion="Carga de version bloqueada por maximo de versiones.",
                valores_despues={"id_tarea": id_tarea, "versiones_existentes": [v.get("numero_version") for v in versiones_todas]},
                resultado="BLOQUEADO",
                modulo="SCRIPTS",
                usuario=usuario,
            )
            return False, "Ya existen 3 versiones para este script. Debes reemplazar una version existente para continuar."

        if script:
            mensaje = validar_sin_duplicado(
                buscar_duplicado_version_numero(script["id_script"], numero_version),
                "scripts_versiones",
                usuario,
                valores={"id_script": script["id_script"], "numero_version": numero_version},
                modulo="SCRIPTS",
            )
            if mensaje:
                return False, mensaje

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
            try:
                crear_version(script["id_script"], version, usuario)
            except Exception as error:
                if es_error_duplicado_sql(error):
                    registrar_bloqueo_duplicado(
                        "scripts_versiones",
                        usuario,
                        MENSAJE_DUPLICADO_SQL,
                        id_entidad=script["id_script"],
                        nombre_entidad=f"v{numero_version}",
                        valores={"id_script": script["id_script"], "numero_version": numero_version},
                        modulo="SCRIPTS",
                    )
                    return False, MENSAJE_DUPLICADO_SQL
                raise
            accion = "SCRIPT_VERSION_CREADA"
        else:
            try:
                crear_script_con_version(
                    id_tarea,
                    _nombre_contenedor_script(tarea),
                    "Contenedor de scripts asociado a tarea.",
                    version,
                    usuario,
                )
            except Exception as error:
                if es_error_duplicado_sql(error):
                    registrar_bloqueo_duplicado(
                        "scripts",
                        usuario,
                        MENSAJE_DUPLICADO_SQL,
                        nombre_entidad=tarea["nombre_tarea"],
                        valores={"id_tarea": id_tarea, "numero_version": numero_version},
                        modulo="SCRIPTS",
                    )
                    return False, MENSAJE_DUPLICADO_SQL
                raise
            accion = "SCRIPT_CREADO"
        registrar_log_sistema(accion, "SCRIPTS", f"Version v{numero_version} cargada para tarea {tarea['nombre_tarea']}.", usuario=usuario)
        registrar_auditoria(
            "SUBIR_VERSION",
            "scripts",
            id_entidad=script.get("id_script") if script else id_tarea,
            nombre_entidad=tarea["nombre_tarea"],
            descripcion=f"Version v{numero_version} cargada para tarea {tarea['nombre_tarea']}.",
            valores_despues={
                "id_tarea": id_tarea,
                "numero_version": numero_version,
                "nombre_archivo": nombre_archivo,
                "hash_archivo": version["hash_archivo"],
                "estado_version": version["estado_version"],
                "es_activa": version["es_activa"],
                "requiere_env": requiere_env,
            },
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return True, f"Version v{numero_version} cargada correctamente."
    except ValueError as error:
        registrar_log_sistema("SCRIPT_CARGA_BLOQUEADA", "SCRIPTS", str(error), usuario=usuario, nivel="WARNING")
        return False, str(error)
    except Exception:
        registrar_log_sistema("SCRIPT_CARGA_ERROR", "SCRIPTS", "Error controlado al guardar archivo de script.", usuario=usuario, nivel="ERROR")
        registrar_auditoria(
            "SUBIR_VERSION",
            "scripts",
            id_entidad=id_tarea,
            descripcion="Error controlado al guardar archivo de script.",
            resultado="ERROR",
            modulo="SCRIPTS",
            usuario=usuario,
        )
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
        registrar_auditoria(
            "REEMPLAZAR_VERSION",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version_actual['numero_version']}",
            descripcion=f"Version v{version_actual['numero_version']} reemplazada.",
            valores_antes=version_actual,
            valores_despues={"nombre_archivo": nombre_archivo, "hash_archivo": calcular_hash_archivo(ruta_fisica)},
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return True, "Version reemplazada correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception:
        registrar_auditoria(
            "REEMPLAZAR_VERSION",
            "scripts_versiones",
            id_entidad=id_version,
            descripcion="Error controlado al reemplazar version.",
            resultado="ERROR",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "No fue posible reemplazar la version."


def activar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    if version["estado_version"] == "INACTIVA":
        registrar_auditoria(
            "BLOQUEO_SCRIPT_NO_EJECUTABLE",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version['numero_version']}",
            descripcion="Intento bloqueado de activar version inactiva.",
            valores_antes=version,
            resultado="BLOQUEADO",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "No se puede activar una version inactiva."
    activar_version(id_version, version["id_script"], usuario)
    registrar_log_sistema("SCRIPT_VERSION_ACTIVA_CAMBIADA", "SCRIPTS", f"Version activa cambiada a v{version['numero_version']}.", usuario=usuario)
    registrar_auditoria(
        "ACTIVAR_VERSION",
        "scripts_versiones",
        id_entidad=id_version,
        nombre_entidad=f"v{version['numero_version']}",
        descripcion=f"Version activa cambiada a v{version['numero_version']}.",
        valores_antes=version,
        valores_despues={"es_activa": 1, "estado_version": "ACTIVA"},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, "Version activa actualizada."


def desactivar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    if version.get("es_activa"):
        registrar_log_sistema("SCRIPT_VERSION_DESACTIVACION_BLOQUEADA_ACTIVA", "SCRIPTS", f"Intento bloqueado de desactivar version activa v{version['numero_version']}.", usuario=usuario, nivel="WARNING")
        registrar_auditoria(
            "BLOQUEO_SCRIPT_NO_EJECUTABLE",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version['numero_version']}",
            descripcion="Intento bloqueado de desactivar version activa.",
            valores_antes=version,
            resultado="BLOQUEADO",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "No puedes desactivar la version activa. Activa otra version primero."
    desactivar_version(id_version)
    registrar_log_sistema("SCRIPT_VERSION_DESACTIVADA", "SCRIPTS", f"Version v{version['numero_version']} desactivada.", usuario=usuario)
    registrar_auditoria(
        "DESACTIVAR_VERSION",
        "scripts_versiones",
        id_entidad=id_version,
        nombre_entidad=f"v{version['numero_version']}",
        descripcion=f"Version v{version['numero_version']} desactivada.",
        valores_antes=version,
        valores_despues={"estado_version": "INACTIVA"},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, "Version desactivada."


def eliminar_version_script(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    versiones = listar_versiones(version["id_script"])
    if len(versiones) <= 1:
        registrar_log_sistema("SCRIPT_VERSION_ELIMINACION_BLOQUEADA_UNICA", "SCRIPTS", f"Intento bloqueado de eliminar unica version v{version['numero_version']}.", usuario=usuario, nivel="WARNING")
        registrar_auditoria(
            "BLOQUEO_SCRIPT_NO_EJECUTABLE",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version['numero_version']}",
            descripcion="Intento bloqueado de eliminar unica version del script.",
            valores_antes=version,
            resultado="BLOQUEADO",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "Esta es la unica version del script. Para quitarla, usa la opcion Eliminar script completo."
    if version.get("es_activa"):
        registrar_log_sistema("SCRIPT_VERSION_ELIMINACION_BLOQUEADA_ACTIVA", "SCRIPTS", f"Intento bloqueado de eliminar version activa v{version['numero_version']}.", usuario=usuario, nivel="WARNING")
        registrar_auditoria(
            "BLOQUEO_SCRIPT_NO_EJECUTABLE",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version['numero_version']}",
            descripcion="Intento bloqueado de eliminar version activa.",
            valores_antes=version,
            resultado="BLOQUEADO",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "No puedes eliminar directamente la version activa. Activa otra version antes de eliminar esta."
    marcar_version_eliminada_operativa(
        id_version,
        usuario,
        "Borrado operativo seguro. Eliminacion permanente disponible solo desde Papelera operativa.",
    )
    registrar_log_sistema("SCRIPT_VERSION_BORRADA_OPERATIVA", "SCRIPTS", f"Version v{version['numero_version']} retirada de operacion conservando historial.", usuario=usuario)
    registrar_auditoria(
        "BORRAR_OPERATIVO",
        "scripts_versiones",
        id_entidad=id_version,
        nombre_entidad=f"v{version['numero_version']}",
        descripcion=f"Version v{version['numero_version']} retirada de operacion conservando historial.",
        valores_antes=version,
        valores_despues={"eliminado_operativo": 1, "activo": 0},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, "Version retirada de la operacion y enviada a Papelera operativa. El historial de ejecuciones se conserva."


PATRON_CLAVE_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def guardar_env_version(id_version, archivo, requiere_env, usuario, contenido_env=None):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    tarea = obtener_tarea_contexto(version["id_tarea"])
    ruta_env_fisica = version.get("ruta_env_fisica")
    ruta_env_relativa = version.get("ruta_env_relativa")
    try:
        contenido_normalizado = validar_contenido_env(contenido_env)
        if archivo and archivo.filename and contenido_normalizado is not None:
            return False, "Usa solo una opcion: adjuntar archivo .env o pegar contenido .env."
        if archivo and archivo.filename:
            validar_tamano(archivo, max_env_bytes())
            nombre_archivo = nombre_archivo_seguro(archivo.filename, ".env")
            ruta_relativa = construir_ruta_relativa("env_scripts", tarea, version["numero_version"], nombre_archivo)
            eliminar_archivo_seguro(ruta_env_relativa)
            ruta_env_fisica, ruta_env_relativa = guardar_archivo(archivo, ruta_relativa)
        elif contenido_normalizado is not None:
            ruta_relativa = construir_ruta_relativa("env_scripts", tarea, version["numero_version"], ".env")
            eliminar_archivo_seguro(ruta_env_relativa)
            ruta_env_fisica, ruta_env_relativa = guardar_contenido_env(ruta_relativa, contenido_normalizado)
        actualizar_env_version(id_version, requiere_env, ruta_env_fisica, ruta_env_relativa)
        registrar_log_sistema("SCRIPT_ENV_ASOCIADO", "SCRIPTS", f"Env actualizado para version v{version['numero_version']}.", usuario=usuario)
        registrar_auditoria(
            "CONFIGURAR_ENV_VERSION",
            "scripts_versiones",
            id_entidad=id_version,
            nombre_entidad=f"v{version['numero_version']}",
            descripcion=f"Metadatos .env actualizados para version v{version['numero_version']}.",
            valores_antes={"requiere_env": version.get("requiere_env"), "tiene_env": bool(version.get("ruta_env_relativa"))},
            valores_despues={"requiere_env": requiere_env, "tiene_env": bool(ruta_env_relativa)},
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return True, ".env actualizado correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception:
        registrar_auditoria(
            "CONFIGURAR_ENV_VERSION",
            "scripts_versiones",
            id_entidad=id_version,
            descripcion="Error controlado al guardar metadatos .env de version.",
            valores_despues={"requiere_env": requiere_env, "tiene_archivo_env": bool(archivo and archivo.filename), "tiene_contenido_env": bool(contenido_env and contenido_env.strip())},
            resultado="ERROR",
            modulo="SCRIPTS",
            usuario=usuario,
        )
        return False, "No fue posible guardar el .env."


def validar_contenido_env(contenido_env):
    if contenido_env is None or not str(contenido_env).strip():
        return None
    texto = str(contenido_env).replace("\r\n", "\n").replace("\r", "\n")
    if len(texto.encode("utf-8")) > max_env_bytes():
        raise ValueError("El contenido .env supera el tamano maximo permitido.")

    lineas_validas = []
    for numero, linea in enumerate(texto.split("\n"), start=1):
        if not linea.strip() or linea.lstrip().startswith("#"):
            lineas_validas.append(linea.rstrip())
            continue
        if "=" not in linea:
            raise ValueError(f"Linea {numero} invalida. Se esperaba formato KEY=VALUE.")
        clave, _valor = linea.split("=", 1)
        clave = clave.strip()
        if not clave:
            raise ValueError(f"Linea {numero} invalida. KEY no puede estar vacio.")
        if not PATRON_CLAVE_ENV.fullmatch(clave):
            raise ValueError(f"Linea {numero} invalida. KEY debe ser compatible con una variable de entorno.")
        lineas_validas.append(linea.rstrip())

    if not any(linea.strip() and not linea.lstrip().startswith("#") for linea in lineas_validas):
        raise ValueError("El contenido .env no contiene variables utiles.")
    return "\n".join(lineas_validas).rstrip() + "\n"


def guardar_contenido_env(ruta_relativa, contenido):
    ruta_fisica = resolver_ruta_segura(ruta_relativa)
    ruta_fisica.parent.mkdir(parents=True, exist_ok=True)
    ruta_fisica.write_text(contenido, encoding="utf-8", newline="\n")
    return str(ruta_fisica), ruta_relativa.as_posix()


def eliminar_env_version(id_version, usuario):
    version = obtener_version(id_version)
    if not version:
        return False, "Version no encontrada."
    eliminar_archivo_seguro(version.get("ruta_env_relativa"))
    actualizar_env_version(id_version, bool(version.get("requiere_env")), None, None)
    registrar_log_sistema("SCRIPT_ENV_ELIMINADO", "SCRIPTS", f"Env eliminado para version v{version['numero_version']}.", usuario=usuario)
    registrar_auditoria(
        "ELIMINAR_ENV_VERSION",
        "scripts_versiones",
        id_entidad=id_version,
        nombre_entidad=f"v{version['numero_version']}",
        descripcion=f".env eliminado para version v{version['numero_version']}.",
        valores_antes={"requiere_env": version.get("requiere_env"), "tiene_env": bool(version.get("ruta_env_relativa"))},
        valores_despues={"requiere_env": bool(version.get("requiere_env")), "tiene_env": False},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, ".env eliminado correctamente."


def desactivar_script_logico(id_script, usuario):
    script = obtener_script(id_script)
    if not script:
        return False, "Script no encontrado.", None
    desactivar_script(id_script, usuario)
    registrar_log_sistema("SCRIPT_COMPLETO_DESACTIVADO", "SCRIPTS", f"Script completo desactivado: {script['nombre_script']}.", usuario=usuario)
    registrar_auditoria(
        "DESACTIVAR",
        "scripts",
        id_entidad=id_script,
        nombre_entidad=script["nombre_script"],
        descripcion=f"Script completo desactivado: {script['nombre_script']}.",
        valores_antes=script,
        valores_despues={"activo": 0},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, "Script desactivado.", script["id_tarea"]


def eliminar_script_logico(id_script, usuario):
    script = obtener_script(id_script)
    if not script:
        return False, "Script no encontrado.", None
    marcar_script_eliminado_operativo(
        id_script,
        usuario,
        "Borrado operativo seguro. Eliminacion permanente disponible solo desde Papelera operativa.",
    )
    registrar_log_sistema("SCRIPT_COMPLETO_BORRADO_OPERATIVO", "SCRIPTS", f"Script retirado de operacion conservando historial: {script['nombre_script']}.", usuario=usuario)
    registrar_auditoria(
        "BORRAR_OPERATIVO",
        "scripts",
        id_entidad=id_script,
        nombre_entidad=script["nombre_script"],
        descripcion=f"Script retirado de operacion conservando historial: {script['nombre_script']}.",
        valores_antes=script,
        valores_despues={"eliminado_operativo": 1, "activo": 0},
        modulo="SCRIPTS",
        usuario=usuario,
    )
    return True, "Script retirado de la operacion y enviado a Papelera operativa. El historial de ejecuciones se conserva.", script["id_tarea"]


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


def _nombre_contenedor_script(tarea):
    return f"Script de {tarea.get('nombre_tarea') or 'tarea'}"
