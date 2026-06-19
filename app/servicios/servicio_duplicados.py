MENSAJE_DUPLICADO_ACTIVO = "Ya existe un registro activo con estos datos."
MENSAJE_DUPLICADO_INACTIVO = "Ya existe un registro inactivo con estos datos. Puedes activarlo o editarlo en lugar de crear uno nuevo."
MENSAJE_DUPLICADO_PAPELERA = "Ya existe un registro con estos datos en Papelera Operativa. Puedes restaurarlo o eliminarlo permanentemente antes de crear uno nuevo."
MENSAJE_DUPLICADO_SQL = "No fue posible guardar porque ya existe un registro con esos datos. Revisa si esta activo, inactivo o en Papelera Operativa."


def clasificar_duplicado(registro):
    if not registro:
        return None
    if bool(registro.get("eliminado_operativo")):
        return "papelera"
    if not bool(registro.get("activo", 1)):
        return "inactivo"
    return "activo"


def mensaje_duplicado(registro):
    estado = clasificar_duplicado(registro)
    if estado == "papelera":
        return MENSAJE_DUPLICADO_PAPELERA
    if estado == "inactivo":
        return MENSAJE_DUPLICADO_INACTIVO
    if estado == "activo":
        return MENSAJE_DUPLICADO_ACTIVO
    return None


def validar_sin_duplicado(registro, entidad, usuario, valores=None, modulo=None, descripcion=None):
    mensaje = mensaje_duplicado(registro)
    if not mensaje:
        return None
    registrar_bloqueo_duplicado(
        entidad,
        usuario,
        descripcion or mensaje,
        id_entidad=registro.get("id"),
        nombre_entidad=registro.get("nombre"),
        valores=valores,
        modulo=modulo,
    )
    return mensaje


def es_error_duplicado_sql(error):
    texto = str(error).lower()
    indicadores = (
        "duplicate key",
        "unique constraint",
        "unique index",
        "violation of unique key",
        "cannot insert duplicate key",
        "2627",
        "2601",
    )
    return any(indicador in texto for indicador in indicadores)


def registrar_bloqueo_duplicado(entidad, usuario, descripcion, id_entidad=None, nombre_entidad=None, valores=None, modulo=None):
    try:
        from app.servicios.servicio_auditoria import registrar_auditoria

        registrar_auditoria(
            "BLOQUEO_DUPLICADO",
            entidad,
            id_entidad=id_entidad,
            nombre_entidad=nombre_entidad,
            descripcion=descripcion,
            valores_despues=valores,
            resultado="BLOQUEADO",
            modulo=modulo or entidad,
            usuario=usuario,
        )
    except Exception:
        pass
