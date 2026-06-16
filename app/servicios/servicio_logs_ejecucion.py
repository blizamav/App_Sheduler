from datetime import datetime


NIVELES_VALIDOS = {"INFO", "WARN", "ERROR"}


def obtener_timestamp_log():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def formatear_linea_log(mensaje, nivel="INFO"):
    nivel_normalizado = _normalizar_nivel(nivel)
    texto = "" if mensaje is None else str(mensaje).rstrip("\r\n")
    return f"{obtener_timestamp_log()} | {nivel_normalizado:<5} | {texto}"


def normalizar_linea_script(linea):
    if linea is None:
        return ""
    return str(linea).rstrip("\r\n")


def escribir_linea_log(ruta_log, mensaje, nivel="INFO"):
    if not ruta_log:
        return
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_log, "a", encoding="utf-8", errors="replace") as archivo:
        archivo.write(formatear_linea_log(mensaje, nivel))
        archivo.write("\n")


def escribir_lineas_log(ruta_log, lineas, nivel="INFO"):
    for linea in lineas:
        if isinstance(linea, tuple):
            mensaje, nivel_linea = linea
            escribir_linea_log(ruta_log, mensaje, nivel_linea)
        else:
            escribir_linea_log(ruta_log, linea, nivel)


def _normalizar_nivel(nivel):
    nivel_normalizado = str(nivel or "INFO").upper()
    if nivel_normalizado == "WARNING":
        nivel_normalizado = "WARN"
    if nivel_normalizado not in NIVELES_VALIDOS:
        return "INFO"
    return nivel_normalizado
