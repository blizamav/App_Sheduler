import json
import os
import re
from html import escape

import requests

from app.repositorios.repositorio_notificaciones_envios import (
    existe_envio_exitoso_alerta,
    existe_envio_exitoso_evidencia,
    registrar_envio_alerta,
    registrar_envio_evidencia,
)
from app.repositorios.repositorio_mail_graph import (
    crear_configuracion_mail_graph_default,
    guardar_configuracion_mail_graph,
    obtener_configuracion_mail_graph,
)
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema


GRAPH_SCOPE_DEFAULT = "https://graph.microsoft.com/.default"
EMAIL_BASICO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TOKEN_TIMEOUT_SEGUNDOS = 20
SENDMAIL_TIMEOUT_SEGUNDOS = 30


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


def enviar_evidencia_cliente_graph(id_ejecucion, id_tarea, resultado_evidencia, evidencia, config_notificacion, exit_code=0):
    if int(exit_code or 0) != 0:
        return _registrar_envio_omitido(id_ejecucion, resultado_evidencia, config_notificacion, "Ejecucion con codigo de salida distinto de 0.")
    if not resultado_evidencia or resultado_evidencia.get("estado_evidencia") != "VALIDADA":
        return None
    if not config_notificacion or not bool(config_notificacion.get("enviar_evidencia")):
        return None
    if existe_envio_exitoso_evidencia(id_ejecucion):
        return {
            "estado_envio": "OMITIDO",
            "mensaje_log": "Envio de evidencia omitido: ya existe envio exitoso para esta ejecucion.",
            "registrado": False,
        }

    destinatarios = _destinatarios_evidencia(config_notificacion.get("destinatarios") or [])
    if not destinatarios["TO"]:
        return _registrar_envio_omitido(id_ejecucion, resultado_evidencia, config_notificacion, "No existen destinatarios TO de evidencia.")

    config_graph = obtener_configuracion_mail_graph()
    validacion_graph = _validar_config_graph_envio(config_graph)
    if validacion_graph:
        return _registrar_envio_omitido(id_ejecucion, resultado_evidencia, config_notificacion, validacion_graph, destinatarios)

    asunto = _construir_asunto(config_notificacion, resultado_evidencia, evidencia)
    cuerpo_html = _construir_html_evidencia(evidencia, resultado_evidencia)
    try:
        token = _obtener_token_graph(config_graph)
        respuesta = _enviar_sendmail_graph(config_graph, token, destinatarios, asunto, cuerpo_html)
        estado_envio = "ENVIADO" if 200 <= respuesta.status_code < 300 else "FALLIDO"
        mensaje = None if estado_envio == "ENVIADO" else _mensaje_graph_error(respuesta)
        id_envio = registrar_envio_evidencia(
            _registro_envio(
                id_ejecucion,
                resultado_evidencia,
                estado_envio,
                asunto,
                destinatarios,
                respuesta.status_code,
                _graph_request_id(respuesta),
                mensaje,
            )
        )
        return {
            "id_envio": id_envio,
            "estado_envio": estado_envio,
            "mensaje_log": (
                "Evidencia enviada por Microsoft Graph."
                if estado_envio == "ENVIADO"
                else "No fue posible enviar evidencia por Microsoft Graph. Estado registrado como FALLIDO."
            ),
            "registrado": True,
        }
    except Exception as error:
        id_envio = registrar_envio_evidencia(
            _registro_envio(
                id_ejecucion,
                resultado_evidencia,
                "FALLIDO",
                asunto,
                destinatarios,
                None,
                None,
                f"Error controlado Graph: {error.__class__.__name__}.",
            )
        )
        registrar_log_sistema(
            "MAIL_GRAPH_ENVIO_EVIDENCIA_ERROR",
            "MAIL_GRAPH",
            "Error controlado al enviar evidencia por Microsoft Graph.",
            usuario="sistema",
            valor_nuevo=error.__class__.__name__,
            nivel="ERROR",
        )
        return {
            "id_envio": id_envio,
            "estado_envio": "FALLIDO",
            "mensaje_log": "No fue posible enviar evidencia por Microsoft Graph. Estado registrado como FALLIDO.",
            "registrado": True,
        }


def enviar_alerta_interna_graph(id_ejecucion, contexto, estado_final, codigo_salida, mensaje_error, config_notificacion=None, resultado_evidencia=None):
    if estado_final not in {"ERROR", "FALLIDA"} and int(codigo_salida or 0) == 0:
        return None
    if existe_envio_exitoso_alerta(id_ejecucion):
        return {
            "estado_envio": "OMITIDO",
            "mensaje_log": "Alerta interna omitida: ya existe alerta enviada para esta ejecucion.",
            "registrado": False,
        }
    if config_notificacion and not bool(config_notificacion.get("alerta_error_activa")):
        return _registrar_alerta_omitida(id_ejecucion, resultado_evidencia, {}, "Alerta interna desactivada para la tarea.")

    config_graph = obtener_configuracion_mail_graph()
    destinatarios = _destinatarios_alerta(config_notificacion or {}, config_graph or {})
    if not destinatarios["TO"]:
        return _registrar_alerta_omitida(id_ejecucion, resultado_evidencia, destinatarios, "No hay destinatarios de alerta configurados.")

    validacion_graph = _validar_config_graph_envio(config_graph)
    if validacion_graph:
        return _registrar_alerta_omitida(id_ejecucion, resultado_evidencia, destinatarios, validacion_graph)

    asunto = _construir_asunto_alerta(contexto)
    cuerpo_html = _construir_html_alerta(id_ejecucion, contexto, estado_final, codigo_salida, mensaje_error)
    try:
        token = _obtener_token_graph(config_graph)
        respuesta = _enviar_sendmail_graph(config_graph, token, destinatarios, asunto, cuerpo_html)
        estado_envio = "ENVIADO" if 200 <= respuesta.status_code < 300 else "FALLIDO"
        mensaje = None if estado_envio == "ENVIADO" else _mensaje_graph_error(respuesta)
        id_envio = registrar_envio_alerta(
            _registro_envio(
                id_ejecucion,
                resultado_evidencia or {},
                estado_envio,
                asunto,
                destinatarios,
                respuesta.status_code,
                _graph_request_id(respuesta),
                mensaje,
            )
        )
        return {
            "id_envio": id_envio,
            "estado_envio": estado_envio,
            "mensaje_log": (
                "Alerta interna enviada por Microsoft Graph."
                if estado_envio == "ENVIADO"
                else "No fue posible enviar alerta interna por Microsoft Graph. Estado registrado como FALLIDO."
            ),
            "registrado": True,
        }
    except Exception as error:
        id_envio = registrar_envio_alerta(
            _registro_envio(
                id_ejecucion,
                resultado_evidencia or {},
                "FALLIDO",
                asunto,
                destinatarios,
                None,
                None,
                f"Error controlado Graph: {error.__class__.__name__}.",
            )
        )
        registrar_log_sistema(
            "MAIL_GRAPH_ALERTA_INTERNA_ERROR",
            "MAIL_GRAPH",
            "Error controlado al enviar alerta interna por Microsoft Graph.",
            usuario="sistema",
            valor_nuevo=error.__class__.__name__,
            nivel="ERROR",
        )
        return {
            "id_envio": id_envio,
            "estado_envio": "FALLIDO",
            "mensaje_log": "No fue posible enviar alerta interna por Microsoft Graph. Estado registrado como FALLIDO.",
            "registrado": True,
        }


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


def _validar_config_graph_envio(config_graph):
    if not config_graph:
        return "Configuracion Mail Graph no disponible."
    if not bool(config_graph.get("activo")):
        return "Configuracion Mail Graph inactiva."
    if not config_graph.get("tenant_id"):
        return "Configuracion Mail Graph incompleta: tenant_id."
    if not config_graph.get("client_id"):
        return "Configuracion Mail Graph incompleta: client_id."
    if not config_graph.get("send_mail_user"):
        return "Configuracion Mail Graph incompleta: send_mail_user."
    if not config_graph.get("graph_scope"):
        return "Configuracion Mail Graph incompleta: graph_scope."
    if not client_secret_configurado():
        return "GRAPH_CLIENT_SECRET no configurado en entorno."
    return None


def _obtener_token_graph(config_graph):
    url = f"https://login.microsoftonline.com/{config_graph['tenant_id']}/oauth2/v2.0/token"
    datos = {
        "client_id": config_graph["client_id"],
        "client_secret": os.getenv("GRAPH_CLIENT_SECRET", ""),
        "scope": config_graph.get("graph_scope") or GRAPH_SCOPE_DEFAULT,
        "grant_type": "client_credentials",
    }
    respuesta = requests.post(url, data=datos, timeout=TOKEN_TIMEOUT_SEGUNDOS)
    if not 200 <= respuesta.status_code < 300:
        raise RuntimeError(f"TOKEN_HTTP_{respuesta.status_code}")
    token = (respuesta.json() or {}).get("access_token")
    if not token:
        raise RuntimeError("TOKEN_NO_DISPONIBLE")
    return token


def _enviar_sendmail_graph(config_graph, token, destinatarios, asunto, cuerpo_html):
    url = f"https://graph.microsoft.com/v1.0/users/{config_graph['send_mail_user']}/sendMail"
    payload = {
        "message": {
            "subject": asunto,
            "body": {"contentType": "HTML", "content": cuerpo_html},
            "toRecipients": _recipients_graph(destinatarios["TO"]),
            "ccRecipients": _recipients_graph(destinatarios["CC"]),
            "bccRecipients": _recipients_graph(destinatarios["BCC"]),
        },
        "saveToSentItems": bool(config_graph.get("save_to_sent_items")),
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, headers=headers, json=payload, timeout=SENDMAIL_TIMEOUT_SEGUNDOS)


def _registrar_envio_omitido(id_ejecucion, resultado_evidencia, config_notificacion, motivo, destinatarios=None):
    destinatarios = destinatarios or _destinatarios_evidencia((config_notificacion or {}).get("destinatarios") or [])
    id_envio = registrar_envio_evidencia(
        _registro_envio(
            id_ejecucion,
            resultado_evidencia or {},
            "OMITIDO",
            _construir_asunto(config_notificacion or {}, resultado_evidencia or {}, {}),
            destinatarios,
            None,
            None,
            motivo,
        )
    )
    return {
        "id_envio": id_envio,
        "estado_envio": "OMITIDO",
        "mensaje_log": f"Envio de evidencia omitido: {motivo}",
        "registrado": True,
    }


def _registrar_alerta_omitida(id_ejecucion, resultado_evidencia, destinatarios, motivo):
    id_envio = registrar_envio_alerta(
        _registro_envio(
            id_ejecucion,
            resultado_evidencia or {},
            "OMITIDO",
            "Alerta interna APP Scheduler",
            destinatarios or {"TO": [], "CC": [], "BCC": []},
            None,
            None,
            motivo,
        )
    )
    return {
        "id_envio": id_envio,
        "estado_envio": "OMITIDO",
        "mensaje_log": f"Alerta interna omitida: {motivo}",
        "registrado": True,
    }


def _registro_envio(id_ejecucion, resultado_evidencia, estado_envio, asunto, destinatarios, status_code, request_id, error):
    return {
        "id_ejecucion": id_ejecucion,
        "id_evidencia": resultado_evidencia.get("id_evidencia"),
        "estado_envio": estado_envio,
        "asunto": _texto(asunto, 255),
        "destinatarios_to": _emails_serializados(destinatarios.get("TO")),
        "destinatarios_cc": _emails_serializados(destinatarios.get("CC")),
        "destinatarios_bcc": _emails_serializados(destinatarios.get("BCC")),
        "graph_status_code": status_code,
        "graph_request_id": _texto(request_id, 255),
        "error_controlado": _texto(error, 2000),
    }


def _destinatarios_evidencia(destinatarios):
    resultado = {"TO": [], "CC": [], "BCC": []}
    for destinatario in destinatarios or []:
        if destinatario.get("tipo_destinatario") != "EVIDENCIA":
            continue
        canal = str(destinatario.get("canal") or "").upper()
        email = str(destinatario.get("email") or "").strip().lower()
        if canal in resultado and validar_email_basico(email):
            resultado[canal].append({"email": email, "nombre": destinatario.get("nombre")})
    return {canal: _unicos_destinatarios(lista) for canal, lista in resultado.items()}


def _destinatarios_alerta(config_notificacion, config_graph):
    if bool((config_notificacion or {}).get("usar_alerta_global", True)):
        return _destinatarios_desde_texto_global((config_graph or {}).get("alertas_destinatarios_default"))
    return _destinatarios_por_tipo((config_notificacion or {}).get("destinatarios") or [], "ALERTA")


def _destinatarios_por_tipo(destinatarios, tipo_destinatario):
    resultado = {"TO": [], "CC": [], "BCC": []}
    for destinatario in destinatarios or []:
        if destinatario.get("tipo_destinatario") != tipo_destinatario:
            continue
        canal = str(destinatario.get("canal") or "").upper()
        email = str(destinatario.get("email") or "").strip().lower()
        if canal in resultado and validar_email_basico(email):
            resultado[canal].append({"email": email, "nombre": destinatario.get("nombre")})
    return {canal: _unicos_destinatarios(lista) for canal, lista in resultado.items()}


def _destinatarios_desde_texto_global(texto):
    return {
        "TO": [{"email": email, "nombre": None} for email in _emails_desde_texto(texto) if validar_email_basico(email)],
        "CC": [],
        "BCC": [],
    }


def _unicos_destinatarios(destinatarios):
    vistos = set()
    resultado = []
    for item in destinatarios:
        email = item["email"]
        if email in vistos:
            continue
        vistos.add(email)
        resultado.append(item)
    return resultado


def _recipients_graph(destinatarios):
    return [{"emailAddress": {"address": item["email"], "name": item.get("nombre") or item["email"]}} for item in destinatarios or []]


def _emails_serializados(destinatarios):
    emails = [item["email"] for item in destinatarios or []]
    return "; ".join(emails) or None


def _construir_asunto(config_notificacion, resultado_evidencia, evidencia):
    if bool((config_notificacion or {}).get("usar_asunto_sugerido_script")) and (evidencia or {}).get("asunto_sugerido"):
        return _texto(evidencia.get("asunto_sugerido"), 255)
    if (config_notificacion or {}).get("asunto_personalizado"):
        return _texto(config_notificacion.get("asunto_personalizado"), 255)
    if (resultado_evidencia or {}).get("titulo"):
        return _texto(resultado_evidencia.get("titulo"), 255)
    if (evidencia or {}).get("titulo"):
        return _texto(evidencia.get("titulo"), 255)
    return "Evidencia proceso APP Scheduler"


def _construir_html_evidencia(evidencia, resultado_evidencia):
    evidencia = evidencia or {}
    titulo = escape(str(evidencia.get("titulo") or resultado_evidencia.get("titulo") or "Evidencia proceso APP Scheduler"))
    intro = escape(str(evidencia.get("mensaje_introductorio") or "Se adjunta resumen de evidencia del proceso ejecutado."))
    fecha = escape(str(evidencia.get("fecha_proceso") or ""))
    filas_resumen = _filas_resumen_html(evidencia.get("resumen"))
    filas_problemas = _filas_problemas_html(evidencia.get("problemas"))
    fecha_html = f"<p><strong>Fecha proceso:</strong> {fecha}</p>" if fecha else ""
    problemas_html = f"<h2>Problemas informados</h2><ul>{filas_problemas}</ul>" if filas_problemas else ""
    return f"""<!doctype html>
<html>
<body style="font-family: Arial, sans-serif; color: #1f2937;">
  <h1 style="color: #0f4c81;">{titulo}</h1>
  <p>{intro}</p>
  {fecha_html}
  <h2>Resumen</h2>
  <table style="border-collapse: collapse; width: 100%;">
    <tbody>
      {filas_resumen or '<tr><td style="padding: 8px; border: 1px solid #d8e2ef;">Sin resumen informado.</td></tr>'}
    </tbody>
  </table>
  {problemas_html}
  <p style="margin-top: 24px; color: #64748b; font-size: 12px;">Correo generado automaticamente por APP Scheduler.</p>
</body>
</html>"""


def _construir_asunto_alerta(contexto):
    nombre = (contexto or {}).get("nombre_tarea") or "Tarea sin nombre"
    return _texto(f"[APP Scheduler] Fallo tarea: {nombre}", 255)


def _construir_html_alerta(id_ejecucion, contexto, estado_final, codigo_salida, mensaje_error):
    contexto = contexto or {}
    filas = {
        "Tarea": contexto.get("nombre_tarea"),
        "Script": contexto.get("nombre_script"),
        "Version": f"v{contexto.get('numero_version')}" if contexto.get("numero_version") else None,
        "Origen": contexto.get("origen_ejecucion"),
        "Fecha/hora inicio": contexto.get("fecha_hora_inicio_alerta"),
        "Fecha/hora termino": contexto.get("fecha_hora_termino_alerta"),
        "Estado final": estado_final,
        "Codigo de salida": codigo_salida if codigo_salida is not None else "No disponible",
        "ID ejecucion": id_ejecucion,
        "Mensaje de error": mensaje_error,
        "Log": f"Disponible en APP Scheduler, modulo Ejecuciones, ID ejecucion {id_ejecucion}.",
    }
    filas_html = "\n".join(
        "<tr>"
        f"<th style=\"text-align:left; padding:8px; border:1px solid #d8e2ef; background:#f4f8fc;\">{escape(str(campo))}</th>"
        f"<td style=\"padding:8px; border:1px solid #d8e2ef;\">{escape(str(valor or ''))}</td>"
        "</tr>"
        for campo, valor in filas.items()
    )
    return f"""<!doctype html>
<html>
<body style="font-family: Arial, sans-serif; color: #1f2937;">
  <h1 style="color: #b91c1c;">Falla de ejecucion en APP Scheduler</h1>
  <p>Se detecto una falla tecnica durante la ejecucion de una tarea.</p>
  <table style="border-collapse: collapse; width: 100%;">
    <tbody>
      {filas_html}
    </tbody>
  </table>
  <p style="margin-top: 24px;">Revisar el log de ejecucion en APP Scheduler para mas detalle.</p>
  <p style="margin-top: 24px; color: #64748b; font-size: 12px;">Correo generado automaticamente por APP Scheduler.</p>
</body>
</html>"""


def _filas_resumen_html(resumen):
    if not isinstance(resumen, list):
        return ""
    filas = []
    for indice, item in enumerate(resumen, start=1):
        if isinstance(item, dict):
            campo = item.get("campo") or item.get("nombre") or item.get("titulo") or item.get("label") or f"Item {indice}"
            valor = item.get("valor")
            if valor is None:
                valor = item.get("value") or item.get("descripcion") or item.get("resultado") or ""
        else:
            campo = f"Item {indice}"
            valor = item
        filas.append(
            "<tr>"
            f"<th style=\"text-align:left; padding:8px; border:1px solid #d8e2ef; background:#f4f8fc;\">{escape(str(campo))}</th>"
            f"<td style=\"padding:8px; border:1px solid #d8e2ef;\">{escape(str(valor))}</td>"
            "</tr>"
        )
    return "\n".join(filas)


def _filas_problemas_html(problemas):
    if not isinstance(problemas, list):
        return ""
    return "".join(f"<li>{escape(str(item))}</li>" for item in problemas)


def _mensaje_graph_error(respuesta):
    try:
        datos = respuesta.json() or {}
        codigo = ((datos.get("error") or {}).get("code")) or f"HTTP_{respuesta.status_code}"
    except Exception:
        codigo = f"HTTP_{respuesta.status_code}"
    return f"Microsoft Graph rechazo el envio: {codigo}."


def _graph_request_id(respuesta):
    return (
        respuesta.headers.get("request-id")
        or respuesta.headers.get("client-request-id")
        or respuesta.headers.get("x-ms-request-id")
    )


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
