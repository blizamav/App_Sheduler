from flask import current_app


def _driver_odbc(valor):
    """Escapa el nombre del driver para cadena ODBC."""
    return "{" + str(valor or "").replace("}", "}}") + "}"


def _valor_odbc(valor):
    """Prepara valores simples de cadena ODBC sin exponer credenciales."""
    texto = str(valor or "")
    if ";" in texto:
        raise ValueError("Valor de configuracion ODBC contiene un caracter no permitido.")
    return texto


def _normalizar_bandera_odbc(valor, valor_por_defecto):
    texto = str(valor or valor_por_defecto).strip().lower()
    if texto in {"1", "true", "yes", "si", "y"}:
        return "yes"
    if texto in {"0", "false", "no", "n"}:
        return "no"
    return valor_por_defecto


def _normalizar_timeout_odbc(valor, valor_por_defecto=10):
    try:
        timeout = int(valor)
    except (TypeError, ValueError):
        timeout = valor_por_defecto
    return max(1, timeout)


def obtener_parametros_conexion():
    """Retorna parametros ODBC normalizados desde configuracion."""
    return {
        "driver": current_app.config.get("DB_DRIVER", ""),
        "server": current_app.config.get("DB_SERVER", ""),
        "database": current_app.config.get("DB_DATABASE", ""),
        "user": current_app.config.get("DB_USER", ""),
        "password": current_app.config.get("DB_PASSWORD", ""),
        "encrypt": _normalizar_bandera_odbc(current_app.config.get("DB_ENCRYPT"), "no"),
        "trust_server_certificate": _normalizar_bandera_odbc(
            current_app.config.get("DB_TRUST_SERVER_CERTIFICATE"),
            "yes",
        ),
        "timeout": _normalizar_timeout_odbc(current_app.config.get("DB_TIMEOUT"), 10),
    }


def obtener_resumen_conexion_seguro():
    """Retorna resumen seguro de configuracion ODBC sin exponer secretos."""
    parametros = obtener_parametros_conexion()
    return {
        "driver": parametros["driver"],
        "server": parametros["server"],
        "database": parametros["database"],
        "user": parametros["user"],
        "encrypt": parametros["encrypt"],
        "trust_server_certificate": parametros["trust_server_certificate"],
        "timeout": parametros["timeout"],
    }


def construir_cadena_conexion():
    """Construye la cadena ODBC usando exclusivamente configuracion de entorno."""
    parametros = obtener_parametros_conexion()
    return (
        f"DRIVER={_driver_odbc(parametros['driver'])};"
        f"SERVER={_valor_odbc(parametros['server'])};"
        f"DATABASE={_valor_odbc(parametros['database'])};"
        f"UID={_valor_odbc(parametros['user'])};"
        f"PWD={_valor_odbc(parametros['password'])};"
        f"Encrypt={parametros['encrypt']};"
        f"TrustServerCertificate={parametros['trust_server_certificate']};"
        f"Connection Timeout={parametros['timeout']};"
    )


def validar_configuracion_bd():
    """Valida que existan las variables minimas para conectar a SQL Server."""
    parametros = obtener_parametros_conexion()
    requeridas = {
        "DB_SERVER": parametros["server"],
        "DB_DATABASE": parametros["database"],
        "DB_USER": parametros["user"],
        "DB_PASSWORD": parametros["password"],
        "DB_DRIVER": parametros["driver"],
    }
    faltantes = [clave for clave, valor in requeridas.items() if not str(valor or "").strip()]
    return faltantes


def _registrar_error_conexion(error, origen):
    resumen = obtener_resumen_conexion_seguro()
    current_app.logger.error(
        "SQL | origen=%s | driver=%s | server=%s | database=%s | user=%s | encrypt=%s | trust_cert=%s | timeout=%s | error=%s",
        origen,
        resumen["driver"],
        resumen["server"],
        resumen["database"],
        resumen["user"],
        resumen["encrypt"],
        resumen["trust_server_certificate"],
        resumen["timeout"],
        error.__class__.__name__,
    )


def obtener_conexion():
    """Abre una conexion nueva a SQL Server. El llamador debe cerrarla."""
    import pyodbc

    cadena = construir_cadena_conexion()
    try:
        return pyodbc.connect(cadena)
    except Exception as error:
        _registrar_error_conexion(error, "obtener_conexion")
        raise


def probar_conexion_bd():
    """Prueba la conexion ejecutando SELECT 1 y retorna un resultado seguro."""
    faltantes = validar_configuracion_bd()
    if faltantes:
        return {
            "estado": "ERROR",
            "mensaje": "Faltan variables de entorno para conectar a SQL Server.",
            "detalle": ", ".join(faltantes),
        }

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT 1")
            resultado = cursor.fetchone()
            cursor.close()

        if resultado and resultado[0] == 1:
            return {
                "estado": "OK",
                "mensaje": "Conexion a SQL Server correcta.",
                "detalle": "Consulta de diagnostico ejecutada correctamente.",
            }

        return {
            "estado": "ERROR",
            "mensaje": "La conexion respondio, pero la consulta de diagnostico no retorno el valor esperado.",
            "detalle": "SELECT 1 no retorno 1.",
        }
    except ImportError:
        return {
            "estado": "ERROR",
            "mensaje": "No esta instalada la dependencia pyodbc.",
            "detalle": "Ejecuta pip install -r requirements.txt.",
        }
    except Exception as error:
        _registrar_error_conexion(error, "probar_conexion_bd")
        return {
            "estado": "ERROR",
            "mensaje": "No se pudo conectar a SQL Server. Revisa servidor, base, usuario, driver ODBC, cifrado y red.",
            "detalle": error.__class__.__name__,
        }
