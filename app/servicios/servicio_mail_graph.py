import json
import os
import re

from app.repositorios.repositorio_mail_graph import (
    crear_configuracion_mail_graph_default,
    guardar_configuracion_mail_graph,
    obtener_configuracion_mail_graph,
)
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema


GRAPH_SCOPE_DEFAULT = "https://graph.microsoft.com/.default"
EMAIL_BASICO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def obtener_mail_graph_config(usuario=None):
    config = obtener_configuracion_mail_graph()
    if not config:
        crear_configuracion_mail_graph_default(usuario or "sistema")
        config = obtener_configuracion_mail_graph()
    return _serializar_config(config)


def guardar_mail_graph_config(datos_entrada, usuario=None):
    datos_originales = dict(datos_entrada or {})
    if _contiene_secret(datos_originales):
        registrar_log_sistema(
            "MAIL_GRAPH_SECRET_RECHAZADO",
            "MAIL_GRAPH",
            "Payload rechazo campo secreto para configuracion Mail Graph.",
            usuario=usuario,
            nivel="WARNING",
        )
        return False, ["No se acepta client_secret por API ni formulario. Debe configurarse por entorno."], None

    actual = obtener_mail_graph_config(usuario)
    datos = _normalizar(datos_originales)
    errores = validar_configuracion_mail_graph(datos)
    if errores:
        registrar_log_sistema(
            "MAIL_GRAPH_VALIDACION_ERROR",
            "MAIL_GRAPH",
            "; ".join(errores),
            usuario=usuario,
            nivel="WARNING",
        )
        registrar_auditoria(
            "EDITAR_CONFIG_MAIL_GRAPH",
            "configuracion_mail_graph",
            id_entidad=actual.get("id_config_mail"),
            descripcion="Error controlado al validar configuracion Mail Graph.",
            valores_antes=_snapshot(actual),
            valores_despues={"errores": errores},
            resultado="ERROR",
            modulo="MAIL_GRAPH",
            usuario=usuario,
        )
        return False, errores, actual

    cambios = _calcular_cambios(actual, datos)
    if not cambios:
        return False, ["No hay cambios para guardar."], actual

    id_config = guardar_configuracion_mail_graph(actual["id_config_mail"], datos, usuario)
    nuevo = obtener_mail_graph_config(usuario)
    registrar_log_sistema(
        "MAIL_GRAPH_CONFIG_GUARDADA",
        "MAIL_GRAPH",
        "Configuracion global Mail Graph actualizada.",
        usuario=usuario,
        valor_anterior=json.dumps({c["campo"]: c["anterior"] for c in cambios}, ensure_ascii=False),
        valor_nuevo=json.dumps({c["campo"]: c["nuevo"] for c in cambios}, ensure_ascii=False),
    )
    registrar_auditoria(
        "EDITAR_CONFIG_MAIL_GRAPH",
        "configuracion_mail_graph",
        id_entidad=id_config,
        nombre_entidad=datos.get("send_mail_user"),
        descripcion="Configuracion global Mail Graph actualizada.",
        valores_antes={c["campo"]: c["anterior"] for c in cambios},
        valores_despues={c["campo"]: c["nuevo"] for c in cambios},
        modulo="MAIL_GRAPH",
        usuario=usuario,
    )
    return True, ["Configuracion Mail Graph guardada correctamente."], nuevo


def validar_configuracion_mail_graph(datos):
    errores = []
    if datos["activo"] and not datos.get("tenant_id"):
        errores.append("Tenant ID es obligatorio para activar Mail Graph.")
    if datos["activo"] and not datos.get("client_id"):
        errores.append("Client ID es obligatorio para activar Mail Graph.")
    if datos["activo"] and not datos.get("send_mail_user"):
        errores.append("Buzon remitente es obligatorio para activar Mail Graph.")
    if datos.get("send_mail_user") and not validar_email_basico(datos["send_mail_user"]):
        errores.append("Buzon remitente debe tener formato de email valido.")
    if datos["activo"] and not datos.get("graph_scope"):
        errores.append("Scope Graph es obligatorio para activar Mail Graph.")
    if datos.get("graph_scope") and not _scope_valido(datos["graph_scope"]):
        errores.append("Scope Graph debe ser https://graph.microsoft.com/.default o una URL de Microsoft Graph.")
    if datos.get("alertas_destinatarios_default"):
        invalidos = [
            email
            for email in _emails_desde_texto(datos["alertas_destinatarios_default"])
            if not validar_email_basico(email)
        ]
        if invalidos:
            errores.append("Destinatarios globales de alerta contiene emails invalidos.")
    if datos["activo"] and not client_secret_configurado():
        errores.append("GRAPH_CLIENT_SECRET no esta configurado en entorno. No se puede activar Mail Graph.")
    return errores


def validar_email_basico(email):
    return bool(EMAIL_BASICO_RE.match(str(email or "").strip()))


def client_secret_configurado():
    valor = os.getenv("GRAPH_CLIENT_SECRET", "")
    return bool(str(valor or "").strip())


def _normalizar(datos):
    return {
        "activo": _booleano(datos.get("activo")),
        "tenant_id": _texto(datos.get("tenant_id"), 100),
        "client_id": _texto(datos.get("client_id"), 100),
        "graph_scope": _texto(datos.get("graph_scope"), 255) or GRAPH_SCOPE_DEFAULT,
        "send_mail_user": (_texto(datos.get("send_mail_user"), 255) or "").lower() or None,
        "save_to_sent_items": _booleano(datos.get("save_to_sent_items"), True),
        "alertas_destinatarios_default": _normalizar_emails_texto(datos.get("alertas_destinatarios_default")),
        "client_secret_origen": "ENV",
    }


def _serializar_config(config):
    resultado = dict(config or {})
    resultado["activo"] = bool(resultado.get("activo"))
    resultado["save_to_sent_items"] = bool(resultado.get("save_to_sent_items"))
    resultado["graph_scope"] = resultado.get("graph_scope") or GRAPH_SCOPE_DEFAULT
    resultado["client_secret_origen"] = "ENV"
    resultado["client_secret_configurado"] = client_secret_configurado()
    return resultado


def _booleano(valor, defecto=False):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return bool(defecto)
    return str(valor).strip().lower() in {"1", "true", "si", "yes", "on"}


def _texto(valor, maximo):
    texto = str(valor or "").strip()
    if not texto:
        return None
    return texto[:maximo]


def _scope_valido(scope):
    return scope == GRAPH_SCOPE_DEFAULT or scope.startswith("https://graph.microsoft.com/")


def _emails_desde_texto(texto):
    return [item.strip().lower() for item in re.split(r"[;,\n]+", str(texto or "")) if item.strip()]


def _normalizar_emails_texto(texto):
    emails = _emails_desde_texto(texto)
    return "; ".join(dict.fromkeys(emails)) or None


def _contiene_secret(datos):
    return any(str(clave).lower() in {"client_secret", "graph_client_secret", "secret"} for clave in datos.keys())


def _snapshot(config):
    return {
        "activo": bool(config.get("activo")) if config else False,
        "tenant_id": config.get("tenant_id") if config else None,
        "client_id": config.get("client_id") if config else None,
        "graph_scope": config.get("graph_scope") if config else GRAPH_SCOPE_DEFAULT,
        "send_mail_user": config.get("send_mail_user") if config else None,
        "save_to_sent_items": bool(config.get("save_to_sent_items")) if config else True,
        "alertas_destinatarios_default": config.get("alertas_destinatarios_default") if config else None,
        "client_secret_origen": "ENV",
        "client_secret_configurado": client_secret_configurado(),
    }


def _calcular_cambios(actual, datos):
    campos = (
        "activo",
        "tenant_id",
        "client_id",
        "graph_scope",
        "send_mail_user",
        "save_to_sent_items",
        "alertas_destinatarios_default",
        "client_secret_origen",
    )
    cambios = []
    for campo in campos:
        anterior = actual.get(campo)
        nuevo = datos.get(campo)
        if isinstance(anterior, bool) or isinstance(nuevo, bool):
            anterior = bool(anterior)
            nuevo = bool(nuevo)
        if anterior != nuevo:
            cambios.append({"campo": campo, "anterior": anterior, "nuevo": nuevo})
    return cambios
