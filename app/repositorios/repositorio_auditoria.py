from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def columnas_auditoria():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
            """
        )
        return {fila[0] for fila in cursor.fetchall()}


def registrar_evento_auditoria(evento):
    columnas = columnas_auditoria()
    if not columnas:
        return

    mapeo = {
        "fecha_evento": evento.get("fecha_evento"),
        "usuario": evento.get("usuario"),
        "id_usuario": evento.get("id_usuario"),
        "accion": evento.get("accion"),
        "entidad": evento.get("entidad"),
        "id_entidad": evento.get("id_entidad"),
        "nombre_entidad": evento.get("nombre_entidad"),
        "descripcion": evento.get("descripcion"),
        "valores_antes": evento.get("valores_antes"),
        "valores_despues": evento.get("valores_despues"),
        "ip_origen": evento.get("ip_origen"),
        "user_agent": evento.get("user_agent"),
        "resultado": evento.get("resultado"),
        "modulo": evento.get("modulo"),
        "ruta": evento.get("ruta"),
        "metodo_http": evento.get("metodo_http"),
        "activo": 1,
        "tabla_afectada": evento.get("entidad"),
        "id_registro": evento.get("id_entidad") or "-",
        "valor_anterior": evento.get("valores_antes"),
        "valor_nuevo": evento.get("valores_despues"),
        "ip": evento.get("ip_origen"),
        "fecha_hora": evento.get("fecha_evento"),
    }
    campos = [campo for campo in mapeo if campo in columnas and mapeo[campo] is not None]
    if "usuario" in columnas and "usuario" not in campos:
        campos.append("usuario")
    if "accion" in columnas and "accion" not in campos:
        campos.append("accion")
    if "entidad" in columnas and "entidad" not in campos:
        campos.append("entidad")
    if "tabla_afectada" in columnas and "tabla_afectada" not in campos:
        campos.append("tabla_afectada")
    if "id_registro" in columnas and "id_registro" not in campos:
        campos.append("id_registro")
    if "modulo" in columnas and "modulo" not in campos:
        campos.append("modulo")

    valores = []
    for campo in campos:
        valor = mapeo.get(campo)
        if valor is None:
            if campo in ("usuario",):
                valor = "sistema"
            elif campo in ("accion",):
                valor = "ACCION"
            elif campo in ("entidad", "tabla_afectada", "modulo"):
                valor = "GENERAL"
            elif campo == "id_registro":
                valor = "-"
        valores.append(valor)

    marcadores = ", ".join("?" for _ in campos)
    consulta = f"INSERT INTO dbo.auditoria_cambios ({', '.join(campos)}) VALUES ({marcadores})"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *valores)
        conexion.commit()


def listar_auditoria(filtros=None, page=1, per_page=25):
    filtros = filtros or {}
    columnas = columnas_auditoria()
    expresiones = _expresiones(columnas)
    condiciones, parametros = _condiciones(filtros, columnas, expresiones)
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    offset = (max(1, int(page)) - 1) * int(per_page)
    consulta = f"""
        SELECT
            {expresiones['id_auditoria']} AS id_auditoria,
            {expresiones['fecha_evento']} AS fecha_evento,
            {expresiones['id_usuario']} AS id_usuario,
            {expresiones['usuario']} AS usuario,
            {expresiones['accion']} AS accion,
            {expresiones['entidad']} AS entidad,
            {expresiones['id_entidad']} AS id_entidad,
            {expresiones['nombre_entidad']} AS nombre_entidad,
            {expresiones['descripcion']} AS descripcion,
            {expresiones['resultado']} AS resultado,
            {expresiones['modulo']} AS modulo,
            {expresiones['ruta']} AS ruta,
            {expresiones['metodo_http']} AS metodo_http
        FROM dbo.auditoria_cambios
        {where}
        ORDER BY {expresiones['fecha_evento']} DESC, {expresiones['id_auditoria']} DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *(parametros + [offset, int(per_page)]))
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def contar_auditoria(filtros=None):
    filtros = filtros or {}
    columnas = columnas_auditoria()
    expresiones = _expresiones(columnas)
    condiciones, parametros = _condiciones(filtros, columnas, expresiones)
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    consulta = f"SELECT COUNT(1) FROM dbo.auditoria_cambios {where}"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return int(cursor.fetchone()[0] or 0)


def obtener_auditoria(id_auditoria):
    columnas = columnas_auditoria()
    expresiones = _expresiones(columnas)
    consulta = f"""
        SELECT
            {expresiones['id_auditoria']} AS id_auditoria,
            {expresiones['fecha_evento']} AS fecha_evento,
            {expresiones['usuario']} AS usuario,
            {expresiones['accion']} AS accion,
            {expresiones['entidad']} AS entidad,
            {expresiones['id_entidad']} AS id_entidad,
            {expresiones['nombre_entidad']} AS nombre_entidad,
            {expresiones['descripcion']} AS descripcion,
            {expresiones['valores_antes']} AS valores_antes,
            {expresiones['valores_despues']} AS valores_despues,
            {expresiones['ip_origen']} AS ip_origen,
            {expresiones['user_agent']} AS user_agent,
            {expresiones['resultado']} AS resultado,
            {expresiones['modulo']} AS modulo,
            {expresiones['ruta']} AS ruta,
            {expresiones['metodo_http']} AS metodo_http
        FROM dbo.auditoria_cambios
        WHERE {expresiones['id_auditoria']} = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_auditoria)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def _expresiones(columnas):
    return {
        "id_auditoria": "id_auditoria",
        "fecha_evento": "fecha_evento" if "fecha_evento" in columnas else "fecha_hora",
        "id_usuario": "id_usuario" if "id_usuario" in columnas else "CAST(NULL AS int)",
        "usuario": "usuario",
        "accion": "accion",
        "entidad": "entidad" if "entidad" in columnas else "tabla_afectada",
        "id_entidad": "id_entidad" if "id_entidad" in columnas else "id_registro",
        "nombre_entidad": "nombre_entidad" if "nombre_entidad" in columnas else "CAST(NULL AS nvarchar(255))",
        "descripcion": "descripcion" if "descripcion" in columnas else "CAST(NULL AS nvarchar(max))",
        "valores_antes": "valores_antes" if "valores_antes" in columnas else "valor_anterior",
        "valores_despues": "valores_despues" if "valores_despues" in columnas else "valor_nuevo",
        "ip_origen": "ip_origen" if "ip_origen" in columnas else "CONVERT(nvarchar(100), ip)",
        "user_agent": "user_agent",
        "resultado": "resultado" if "resultado" in columnas else "CAST('OK' AS nvarchar(50))",
        "modulo": "modulo",
        "ruta": "ruta" if "ruta" in columnas else "CAST(NULL AS nvarchar(255))",
        "metodo_http": "metodo_http" if "metodo_http" in columnas else "CAST(NULL AS nvarchar(20))",
        "activo": "activo" if "activo" in columnas else "CAST(1 AS bit)",
    }


def _condiciones(filtros, columnas, expresiones):
    condiciones = []
    parametros = []
    if "activo" in columnas:
        condiciones.append("activo = 1")
    if filtros.get("fecha_desde"):
        condiciones.append(f"{expresiones['fecha_evento']} >= ?")
        parametros.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        condiciones.append(f"{expresiones['fecha_evento']} < DATEADD(day, 1, CAST(? AS date))")
        parametros.append(filtros["fecha_hasta"])
    if filtros.get("usuario"):
        condiciones.append(f"{expresiones['usuario']} LIKE ?")
        parametros.append(f"%{filtros['usuario']}%")
    if filtros.get("accion"):
        condiciones.append(f"{expresiones['accion']} LIKE ?")
        parametros.append(f"%{filtros['accion']}%")
    if filtros.get("entidad"):
        condiciones.append(f"{expresiones['entidad']} LIKE ?")
        parametros.append(f"%{filtros['entidad']}%")
    if filtros.get("resultado") and "resultado" in columnas:
        condiciones.append(f"{expresiones['resultado']} = ?")
        parametros.append(filtros["resultado"])
    if filtros.get("modulo"):
        condiciones.append(f"{expresiones['modulo']} LIKE ?")
        parametros.append(f"%{filtros['modulo']}%")
    if filtros.get("texto"):
        condiciones.append(
            f"({expresiones['accion']} LIKE ? OR {expresiones['entidad']} LIKE ? OR "
            f"{expresiones['id_entidad']} LIKE ? OR {expresiones['descripcion']} LIKE ?)"
        )
        texto = f"%{filtros['texto']}%"
        parametros.extend([texto, texto, texto, texto])
    return condiciones, parametros
