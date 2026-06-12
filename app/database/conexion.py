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


def construir_cadena_conexion():
    """Construye la cadena ODBC usando exclusivamente configuracion de entorno."""
    driver = current_app.config.get("DB_DRIVER", "")
    servidor = current_app.config.get("DB_SERVER", "")
    base_datos = current_app.config.get("DB_DATABASE", "")
    usuario = current_app.config.get("DB_USER", "")
    password = current_app.config.get("DB_PASSWORD", "")

    return (
        f"DRIVER={_driver_odbc(driver)};"
        f"SERVER={_valor_odbc(servidor)};"
        f"DATABASE={_valor_odbc(base_datos)};"
        f"UID={_valor_odbc(usuario)};"
        f"PWD={_valor_odbc(password)};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )


def validar_configuracion_bd():
    """Valida que existan las variables minimas para conectar a SQL Server."""
    requeridas = {
        "DB_SERVER": current_app.config.get("DB_SERVER", ""),
        "DB_DATABASE": current_app.config.get("DB_DATABASE", ""),
        "DB_USER": current_app.config.get("DB_USER", ""),
        "DB_PASSWORD": current_app.config.get("DB_PASSWORD", ""),
        "DB_DRIVER": current_app.config.get("DB_DRIVER", ""),
    }
    faltantes = [clave for clave, valor in requeridas.items() if not str(valor or "").strip()]
    return faltantes


def obtener_conexion():
    """Abre una conexion nueva a SQL Server. El llamador debe cerrarla."""
    import pyodbc

    cadena = construir_cadena_conexion()
    return pyodbc.connect(cadena)


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
        return {
            "estado": "ERROR",
            "mensaje": "No se pudo conectar a SQL Server. Revisa servidor, base, usuario, driver ODBC y red.",
            "detalle": error.__class__.__name__,
        }
