import re

from app.repositorios.repositorio_notificaciones import (
    desactivar_configuracion_notificacion,
    guardar_configuracion_notificacion,
    listar_destinatarios_config as listar_destinatarios_config_repo,
    obtener_configuracion_notificacion,
    obtener_tarea_notificaciones,
    reemplazar_destinatarios_config as reemplazar_destinatarios_config_repo,
)
from app.servicios.servicio_evidencias import validar_soporte_evidencia_script_por_tarea
from app.servicios.servicio_logs_sistema import registrar_log_sistema


PLANTILLAS_EVIDENCIA = {"STDOUT_V1"}
TIPOS_DESTINATARIO = {"EVIDENCIA", "ALERTA"}
CANALES_DESTINATARIO = {"TO", "CC", "BCC"}
EMAIL_BASICO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def obtener_config_notificacion_tarea(id_tarea):
    tarea = obtener_tarea_notificaciones(id_tarea)
    if not tarea:
        return False, "Tarea no encontrada.", None

    config = obtener_configuracion_notificacion(id_tarea)
    if not config:
        config = _config_default(id_tarea)
    else:
        config = _serializar_config(config)
    return True, "Configuracion de notificaciones obtenida correctamente.", config


def guardar_config_notificacion_tarea(id_tarea, datos_config, destinatarios=None, usuario=None):
    tarea = obtener_tarea_notificaciones(id_tarea)
    if not tarea:
        return False, ["Tarea no encontrada."], None

    entrada = datos_config or {}
    datos = _normalizar_config(entrada)
    destinatarios_norm = normalizar_lista_destinatarios(destinatarios or entrada.get("destinatarios") or [])
    errores = validar_configuracion_notificacion(datos, destinatarios_norm)
    if datos.get("enviar_evidencia"):
        soporte = validar_soporte_evidencia_script_por_tarea(id_tarea)
        if not soporte.get("soporta_evidencia"):
            errores.append(
                "No se puede activar Enviar evidencia. El script asociado no contiene la declaracion y delimitadores requeridos por el contrato stdout."
            )
            errores.extend(soporte.get("errores") or [])
    if errores:
        registrar_log_sistema(
            "NOTIFICACIONES_VALIDACION_ERROR",
            "NOTIFICACIONES",
            "Error controlado al validar configuracion de notificaciones.",
            usuario=usuario,
            valor_nuevo="; ".join(errores),
            nivel="WARNING",
        )
        return False, errores, None

    try:
        id_config = guardar_configuracion_notificacion(id_tarea, datos, destinatarios_norm)
    except Exception as error:
        registrar_log_sistema(
            "NOTIFICACIONES_GUARDAR_ERROR",
            "NOTIFICACIONES",
            "Error controlado al guardar configuracion de notificaciones.",
            usuario=usuario,
            valor_nuevo=error.__class__.__name__,
            nivel="ERROR",
        )
        raise

    registrar_log_sistema(
        "NOTIFICACIONES_CONFIG_GUARDADA",
        "NOTIFICACIONES",
        f"Configuracion de notificaciones guardada para tarea {id_tarea}.",
        usuario=usuario,
        valor_nuevo=f"id_config_notificacion={id_config}",
    )
    ok, _, config = obtener_config_notificacion_tarea(id_tarea)
    return ok, ["Configuracion de notificaciones guardada correctamente."], config


def desactivar_config_notificacion_tarea(id_tarea, usuario=None):
    tarea = obtener_tarea_notificaciones(id_tarea)
    if not tarea:
        return False, "Tarea no encontrada."
    filas = desactivar_configuracion_notificacion(id_tarea)
    registrar_log_sistema(
        "NOTIFICACIONES_CONFIG_DESACTIVADA",
        "NOTIFICACIONES",
        f"Configuracion de notificaciones desactivada para tarea {id_tarea}.",
        usuario=usuario,
        valor_nuevo=f"filas={filas}",
    )
    return True, "Configuracion de notificaciones desactivada correctamente."


def listar_destinatarios_config(id_config_notificacion):
    return listar_destinatarios_config_repo(id_config_notificacion)


def reemplazar_destinatarios_config(id_config_notificacion, destinatarios):
    destinatarios_norm = normalizar_lista_destinatarios(destinatarios)
    errores = _validar_destinatarios(destinatarios_norm)
    if errores:
        return False, errores
    reemplazar_destinatarios_config_repo(id_config_notificacion, destinatarios_norm)
    return True, []


def validar_email_basico(email):
    return bool(EMAIL_BASICO_RE.match(str(email or "").strip()))


def normalizar_lista_destinatarios(destinatarios):
    normalizados = []
    for item in destinatarios or []:
        if not isinstance(item, dict):
            continue
        email = str(item.get("email") or "").strip().lower()
        tipo = str(item.get("tipo_destinatario") or "").strip().upper()
        canal = str(item.get("canal") or "").strip().upper()
        nombre = str(item.get("nombre") or "").strip()
        if not email and not tipo and not canal and not nombre:
            continue
        normalizados.append(
            {
                "tipo_destinatario": tipo,
                "canal": canal,
                "email": email,
                "nombre": nombre or None,
            }
        )
    return _quitar_duplicados_destinatarios(normalizados)


def validar_configuracion_notificacion(datos_config, destinatarios):
    errores = []
    if datos_config.get("plantilla_evidencia") not in PLANTILLAS_EVIDENCIA:
        errores.append("La plantilla de evidencia no es valida.")

    errores.extend(_validar_destinatarios(destinatarios))

    if datos_config.get("enviar_evidencia") and not _existe_destinatario_to(destinatarios, "EVIDENCIA"):
        errores.append("Para activar envio de evidencia debes agregar al menos un destinatario EVIDENCIA en canal TO.")

    if (
        datos_config.get("alerta_error_activa")
        and not datos_config.get("usar_alerta_global")
        and not _existe_destinatario_to(destinatarios, "ALERTA")
    ):
        errores.append("Si no usas alerta global debes agregar al menos un destinatario ALERTA en canal TO.")

    return errores


def asegurar_config_unica_activa(id_tarea):
    config = obtener_configuracion_notificacion(id_tarea)
    return bool(config)


def _normalizar_config(datos):
    return {
        "enviar_evidencia": _booleano(datos.get("enviar_evidencia")),
        "plantilla_evidencia": str(datos.get("plantilla_evidencia") or "STDOUT_V1").strip().upper(),
        "asunto_personalizado": _texto_opcional(datos.get("asunto_personalizado"), 255),
        "usar_asunto_sugerido_script": _booleano(datos.get("usar_asunto_sugerido_script"), True),
        "adjuntar_archivos_declarados": _booleano(datos.get("adjuntar_archivos_declarados"), True),
        "adjuntar_log_tecnico": _booleano(datos.get("adjuntar_log_tecnico")),
        "alerta_error_activa": _booleano(datos.get("alerta_error_activa"), True),
        "usar_alerta_global": _booleano(datos.get("usar_alerta_global"), True),
    }


def _validar_destinatarios(destinatarios):
    errores = []
    vistos = set()
    for destinatario in destinatarios:
        tipo = destinatario.get("tipo_destinatario")
        canal = destinatario.get("canal")
        email = destinatario.get("email")
        if tipo not in TIPOS_DESTINATARIO:
            errores.append("Tipo de destinatario invalido.")
        if canal not in CANALES_DESTINATARIO:
            errores.append("Canal de destinatario invalido.")
        if not email or not validar_email_basico(email):
            errores.append("Email de destinatario invalido.")
        clave = (tipo, canal, email)
        if clave in vistos:
            errores.append("No se permiten destinatarios duplicados para el mismo tipo, canal y email.")
        vistos.add(clave)
    return errores


def _quitar_duplicados_destinatarios(destinatarios):
    resultado = []
    vistos = set()
    for destinatario in destinatarios:
        clave = (
            destinatario.get("tipo_destinatario"),
            destinatario.get("canal"),
            destinatario.get("email"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(destinatario)
    return resultado


def _existe_destinatario_to(destinatarios, tipo_destinatario):
    return any(
        destinatario.get("tipo_destinatario") == tipo_destinatario
        and destinatario.get("canal") == "TO"
        and validar_email_basico(destinatario.get("email"))
        for destinatario in destinatarios
    )


def _config_default(id_tarea):
    return {
        "id_config_notificacion": None,
        "id_tarea": int(id_tarea),
        "enviar_evidencia": False,
        "plantilla_evidencia": "STDOUT_V1",
        "asunto_personalizado": None,
        "usar_asunto_sugerido_script": True,
        "adjuntar_archivos_declarados": True,
        "adjuntar_log_tecnico": False,
        "alerta_error_activa": True,
        "usar_alerta_global": True,
        "activo": True,
        "destinatarios": [],
    }


def _serializar_config(config):
    resultado = dict(config)
    for campo in (
        "enviar_evidencia",
        "usar_asunto_sugerido_script",
        "adjuntar_archivos_declarados",
        "adjuntar_log_tecnico",
        "alerta_error_activa",
        "usar_alerta_global",
        "activo",
    ):
        resultado[campo] = bool(resultado.get(campo))
    resultado["destinatarios"] = [
        {
            "tipo_destinatario": destinatario.get("tipo_destinatario"),
            "canal": destinatario.get("canal"),
            "email": destinatario.get("email"),
            "nombre": destinatario.get("nombre"),
        }
        for destinatario in resultado.get("destinatarios", [])
    ]
    return resultado


def _booleano(valor, defecto=False):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return bool(defecto)
    return str(valor).strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


def _texto_opcional(valor, largo_maximo):
    texto = str(valor or "").strip()
    if not texto:
        return None
    return texto[:largo_maximo]
