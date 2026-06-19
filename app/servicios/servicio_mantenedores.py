import unicodedata

from app.repositorios.repositorio_mantenedores import (
    actualizar,
    asegurar_snapshots_mantenedor,
    buscar_duplicado_nombre_normalizado,
    cambiar_estado,
    contar_dependencias,
    contar_tareas_activas,
    crear,
    listar,
    marcar_eliminado_operativo,
    obtener_por_id,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_duplicados import (
    MENSAJE_DUPLICADO_SQL,
    es_error_duplicado_sql,
    registrar_bloqueo_duplicado,
    validar_sin_duplicado,
)


CONFIG_MANTENEDORES = {
    "clientes": {
        "singular": "cliente",
        "titulo": "Clientes",
        "permiso": "CLIENTES",
        "modulo_log": "CLIENTES",
    },
    "categorias": {
        "singular": "categoria",
        "titulo": "Categorias",
        "permiso": "CATEGORIAS",
        "modulo_log": "CATEGORIAS",
    },
    "tipos": {
        "singular": "tipo",
        "titulo": "Tipos",
        "permiso": "TIPOS",
        "modulo_log": "TIPOS",
    },
}


def obtener_config_mantenedor(entidad):
    return CONFIG_MANTENEDORES[entidad]


def normalizar_nombre(nombre):
    texto = unicodedata.normalize("NFKD", nombre.strip())
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return " ".join(texto.upper().split())


def listar_mantenedor(entidad, filtros=None):
    return listar(entidad, filtros)


def obtener_mantenedor(entidad, id_registro):
    return obtener_por_id(entidad, id_registro)


def _validar(entidad, datos, id_registro=None, usuario_accion=None):
    errores = []
    nombre = datos.get("nombre", "").strip()

    if not nombre:
        errores.append("El nombre es obligatorio.")
        return errores

    nombre_normalizado = normalizar_nombre(nombre)
    mensaje = validar_sin_duplicado(
        buscar_duplicado_nombre_normalizado(entidad, nombre_normalizado, id_registro),
        entidad,
        usuario_accion,
        valores={"nombre_normalizado": nombre_normalizado},
        modulo=obtener_config_mantenedor(entidad)["modulo_log"],
    )
    if mensaje:
        errores.append(mensaje)

    return errores


def crear_mantenedor(entidad, datos, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    errores = _validar(entidad, datos, usuario_accion=usuario_accion)
    if errores:
        return False, errores, None

    datos_bd = {
        "nombre": datos["nombre"].strip(),
        "nombre_normalizado": normalizar_nombre(datos["nombre"]),
        "descripcion": datos.get("descripcion", "").strip() or None,
        "usuario_accion": usuario_accion,
    }
    try:
        id_registro = crear(entidad, datos_bd)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                entidad,
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                nombre_entidad=datos_bd["nombre"],
                valores={"nombre_normalizado": datos_bd["nombre_normalizado"]},
                modulo=config["modulo_log"],
            )
            return False, [MENSAJE_DUPLICADO_SQL], None
        raise
    registrar_log_sistema(
        f"{config['permiso']}_CREADO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} creado: {datos_bd['nombre']}.",
        usuario=usuario_accion,
        valor_nuevo=datos_bd["nombre"],
    )
    registrar_auditoria(
        "CREAR",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=datos_bd["nombre"],
        descripcion=f"{config['singular'].capitalize()} creado: {datos_bd['nombre']}.",
        valores_despues=datos_bd,
        modulo=config["modulo_log"],
        usuario=usuario_accion,
    )
    return True, [f"{config['singular'].capitalize()} creado correctamente."], id_registro


def actualizar_mantenedor(entidad, id_registro, datos, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    actual = obtener_por_id(entidad, id_registro)
    if not actual:
        return False, ["Registro no encontrado."]

    errores = _validar(entidad, datos, id_registro, usuario_accion)
    if errores:
        return False, errores

    datos_bd = {
        "nombre": datos["nombre"].strip(),
        "nombre_normalizado": normalizar_nombre(datos["nombre"]),
        "descripcion": datos.get("descripcion", "").strip() or None,
        "usuario_accion": usuario_accion,
    }
    try:
        actualizar(entidad, id_registro, datos_bd)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                entidad,
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                id_entidad=id_registro,
                nombre_entidad=actual["nombre"],
                valores={"nombre_normalizado": datos_bd["nombre_normalizado"]},
                modulo=config["modulo_log"],
            )
            return False, [MENSAJE_DUPLICADO_SQL]
        raise
    registrar_log_sistema(
        f"{config['permiso']}_EDITADO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} editado: {datos_bd['nombre']}.",
        usuario=usuario_accion,
        valor_anterior=str(actual),
        valor_nuevo=str(datos_bd),
    )
    registrar_auditoria(
        "EDITAR",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=datos_bd["nombre"],
        descripcion=f"{config['singular'].capitalize()} editado: {datos_bd['nombre']}.",
        valores_antes=actual,
        valores_despues=datos_bd,
        modulo=config["modulo_log"],
        usuario=usuario_accion,
    )
    return True, [f"{config['singular'].capitalize()} actualizado correctamente."]


def cambiar_estado_mantenedor(entidad, id_registro, activo, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    actual = obtener_por_id(entidad, id_registro)
    if not actual:
        return False, "Registro no encontrado."

    cambiar_estado(entidad, id_registro, activo, usuario_accion)
    accion = "ACTIVADO" if activo else "DESACTIVADO"
    registrar_log_sistema(
        f"{config['permiso']}_{accion}",
        config["modulo_log"],
        f"{config['singular'].capitalize()} {accion.lower()}: {actual['nombre']}.",
        usuario=usuario_accion,
        valor_anterior=str(actual["activo"]),
        valor_nuevo=str(1 if activo else 0),
    )
    registrar_auditoria(
        "ACTIVAR" if activo else "DESACTIVAR",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=actual["nombre"],
        descripcion=f"{config['singular'].capitalize()} {accion.lower()}: {actual['nombre']}.",
        valores_antes={"activo": actual["activo"]},
        valores_despues={"activo": 1 if activo else 0},
        modulo=config["modulo_log"],
        usuario=usuario_accion,
    )
    if activo:
        return True, f"{config['singular'].capitalize()} activado correctamente."
    return True, f"{config['singular'].capitalize()} desactivado correctamente."


def eliminar_mantenedor(entidad, id_registro, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    actual = obtener_por_id(entidad, id_registro)
    if not actual:
        return False, "Registro no encontrado."

    tareas_activas = contar_tareas_activas(entidad, id_registro)
    if tareas_activas > 0:
        registrar_log_sistema(
            f"{config['permiso']}_BORRADO_BLOQUEADO_TAREAS_ACTIVAS",
            config["modulo_log"],
            f"Intento bloqueado de borrar {config['singular']} con tareas activas asociadas: {actual['nombre']}.",
            usuario=usuario_accion,
            valor_anterior=str({"id": id_registro, "tareas_activas": tareas_activas}),
            nivel="WARNING",
        )
        registrar_auditoria(
            "BLOQUEO_BORRADO_CON_DEPENDENCIAS",
            entidad,
            id_entidad=id_registro,
            nombre_entidad=actual["nombre"],
            descripcion="Intento bloqueado de borrar mantenedor con tareas activas asociadas.",
            valores_antes={"id": id_registro, "tareas_activas": tareas_activas},
            resultado="BLOQUEADO",
            modulo=config["modulo_log"],
            usuario=usuario_accion,
        )
        return False, "No puedes eliminar este registro porque tiene tareas activas asociadas. Primero desactiva o elimina esas tareas."

    dependencias = contar_dependencias(entidad, id_registro)
    asegurar_snapshots_mantenedor(entidad, id_registro)
    marcar_eliminado_operativo(
        entidad,
        id_registro,
        usuario_accion,
        "Borrado operativo seguro. Eliminacion permanente disponible solo desde Papelera operativa.",
    )
    registrar_log_sistema(
        f"{config['permiso']}_BORRADO_OPERATIVO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} retirado de operacion conservando historial: {actual['nombre']}.",
        usuario=usuario_accion,
        valor_anterior=str({"id": id_registro, "dependencias_tareas": dependencias}),
    )
    registrar_auditoria(
        "BORRAR_OPERATIVO",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=actual["nombre"],
        descripcion=f"{config['singular'].capitalize()} retirado de operacion conservando historial: {actual['nombre']}.",
        valores_antes={"registro": actual, "dependencias_tareas": dependencias},
        valores_despues={"eliminado_operativo": 1, "activo": 0},
        modulo=config["modulo_log"],
        usuario=usuario_accion,
    )
    return True, f"{config['singular'].capitalize()} borrado de la operacion y enviado a Papelera operativa. El historial se conserva."
