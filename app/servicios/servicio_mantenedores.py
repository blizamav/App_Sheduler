import unicodedata

from app.repositorios.repositorio_mantenedores import (
    actualizar,
    cambiar_estado,
    contar_dependencias,
    crear,
    eliminar,
    existe_nombre_normalizado,
    listar,
    obtener_por_id,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema


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


def _validar(entidad, datos, id_registro=None):
    errores = []
    nombre = datos.get("nombre", "").strip()

    if not nombre:
        errores.append("El nombre es obligatorio.")
        return errores

    nombre_normalizado = normalizar_nombre(nombre)
    if existe_nombre_normalizado(entidad, nombre_normalizado, id_registro):
        errores.append("Ya existe un registro con ese nombre.")

    return errores


def crear_mantenedor(entidad, datos, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    errores = _validar(entidad, datos)
    if errores:
        return False, errores, None

    datos_bd = {
        "nombre": datos["nombre"].strip(),
        "nombre_normalizado": normalizar_nombre(datos["nombre"]),
        "descripcion": datos.get("descripcion", "").strip() or None,
        "usuario_accion": usuario_accion,
    }
    id_registro = crear(entidad, datos_bd)
    registrar_log_sistema(
        f"{config['permiso']}_CREADO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} creado: {datos_bd['nombre']}.",
        usuario=usuario_accion,
        valor_nuevo=datos_bd["nombre"],
    )
    return True, [f"{config['singular'].capitalize()} creado correctamente."], id_registro


def actualizar_mantenedor(entidad, id_registro, datos, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    actual = obtener_por_id(entidad, id_registro)
    if not actual:
        return False, ["Registro no encontrado."]

    errores = _validar(entidad, datos, id_registro)
    if errores:
        return False, errores

    datos_bd = {
        "nombre": datos["nombre"].strip(),
        "nombre_normalizado": normalizar_nombre(datos["nombre"]),
        "descripcion": datos.get("descripcion", "").strip() or None,
        "usuario_accion": usuario_accion,
    }
    actualizar(entidad, id_registro, datos_bd)
    registrar_log_sistema(
        f"{config['permiso']}_EDITADO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} editado: {datos_bd['nombre']}.",
        usuario=usuario_accion,
        valor_anterior=str(actual),
        valor_nuevo=str(datos_bd),
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
    if activo:
        return True, f"{config['singular'].capitalize()} activado correctamente."
    return True, f"{config['singular'].capitalize()} desactivado correctamente."


def eliminar_mantenedor(entidad, id_registro, usuario_accion):
    config = obtener_config_mantenedor(entidad)
    actual = obtener_por_id(entidad, id_registro)
    if not actual:
        return False, "Registro no encontrado."

    dependencias = contar_dependencias(entidad, id_registro)
    if dependencias > 0:
        mensaje = (
            "No se puede eliminar este registro porque ya tiene informacion asociada. "
            "Puedes desactivarlo para que no vuelva a usarse."
        )
        registrar_log_sistema(
            f"{config['permiso']}_ELIMINACION_BLOQUEADA",
            config["modulo_log"],
            f"Intento de eliminar {config['singular']} con dependencias: {actual['nombre']}.",
            usuario=usuario_accion,
            valor_anterior=str({"id": id_registro, "dependencias_tareas": dependencias}),
            nivel="WARNING",
        )
        return False, mensaje

    try:
        eliminar(entidad, id_registro)
    except Exception:
        mensaje = (
            "No se puede eliminar este registro porque ya tiene informacion asociada. "
            "Puedes desactivarlo para que no vuelva a usarse."
        )
        registrar_log_sistema(
            f"{config['permiso']}_ELIMINACION_BLOQUEADA",
            config["modulo_log"],
            f"Eliminacion bloqueada por restriccion de base de datos: {actual['nombre']}.",
            usuario=usuario_accion,
            valor_anterior=str({"id": id_registro}),
            nivel="WARNING",
        )
        return False, mensaje

    registrar_log_sistema(
        f"{config['permiso']}_ELIMINADO",
        config["modulo_log"],
        f"{config['singular'].capitalize()} eliminado definitivamente: {actual['nombre']}.",
        usuario=usuario_accion,
        valor_anterior=str(actual),
    )
    return True, f"{config['singular'].capitalize()} eliminado definitivamente."
