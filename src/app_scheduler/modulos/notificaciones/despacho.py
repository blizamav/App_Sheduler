"""Despacho post-ejecucion con reserva durable y llamada Graph fuera de SQL."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.notificaciones.cliente_graph import ClienteMicrosoftGraph, ErrorGraph
from app_scheduler.modulos.notificaciones.seguridad import normalizar_email, sanitizar_texto_externo
from app_scheduler.persistencia.repositorio_notificaciones import RepositorioNotificaciones
from app_scheduler.persistencia.repositorio_operacion import RepositorioLogsSistema


MAX_ADJUNTOS = 5
MAX_TOTAL_ADJUNTOS_BYTES = 2 * 1024 * 1024
EXTENSIONES_BLOQUEADAS = frozenset({".env", ".py", ".pyc", ".pyo", ".exe", ".dll", ".bat", ".cmd", ".ps1"})


class ErrorAdjunto(RuntimeError):
    pass


class ServicioDespachoNotificaciones:
    def __init__(self, proveedor, servicio_graph_config, *, cliente_graph=None,
                 fabrica_uow=UnidadTrabajoSQL, repositorio=RepositorioNotificaciones,
                 repositorio_logs=RepositorioLogsSistema, entorno_jinja=None):
        self.proveedor = proveedor
        self.servicio_graph_config = servicio_graph_config
        self.cliente_graph = cliente_graph or ClienteMicrosoftGraph()
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_logs = repositorio_logs
        self.entorno_jinja = entorno_jinja or Environment(
            loader=FileSystemLoader(Path(__file__).resolve().parents[2] / "presentacion" / "templates"),
            autoescape=select_autoescape(("html", "xml")),
        )

    def procesar(self, id_ejecucion: int, evidencia: dict | None = None) -> str:
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            contexto = repo.obtener_contexto_envio(id_ejecucion)
            config = repo.obtener_configuracion_tarea(contexto["id_tarea"]) if contexto and contexto["id_tarea"] else None
        if contexto is None or config is None:
            return "NO_REQUERIDO"
        tipo = self._evento(contexto, config)
        if tipo is None:
            return "NO_REQUERIDO"
        destinatarios = self._destinatarios(tipo, config)
        if tipo == "ALERTA_INTERNA" and not destinatarios["TO"] and config.usar_alerta_global:
            estado_graph = self.servicio_graph_config.obtener()
            destinatarios["TO"] = self._emails_globales(
                estado_graph["efectiva"].get("alertas_destinatarios_default")
            )
        if not destinatarios["TO"]:
            self._log("GRAPH_ENVIO_ERROR", id_ejecucion,
                      "Notificacion omitida: no existen destinatarios TO.", "WARNING")
            return "OMITIDO"
        evidencia_incluida = self._evidencia_incluida(tipo, contexto, config, evidencia)
        if tipo == "NOTIFICACION_EXITOSA" and config.enviar_evidencia and not evidencia_incluida:
            motivo = contexto.get("error_evidencia") or "La ejecucion no emitio una evidencia 1.0 valida."
            self._log(
                "EVIDENCIA_OMITIDA", id_ejecucion,
                "La notificacion de exito se enviara sin evidencia: "
                + sanitizar_texto_externo(motivo, 500),
                "WARNING",
            )
        adjuntos = []
        if evidencia_incluida and config.adjuntar_archivos_declarados:
            try:
                adjuntos = preparar_adjuntos(
                    evidencia or {}, Path(str(contexto["ruta_script_fisica"])).parent
                )
            except ErrorAdjunto as error:
                self._log(
                    "EVIDENCIA_OMITIDA", id_ejecucion,
                    "La notificacion de exito se enviara sin evidencia ni adjuntos: "
                    + sanitizar_texto_externo(error, 500),
                    "WARNING",
                )
                evidencia_incluida = False
                adjuntos = []
        asunto = self._asunto(tipo, contexto, config, evidencia_incluida)
        cuerpo = self._cuerpo(tipo, contexto, evidencia if evidencia_incluida else None)
        id_evidencia = contexto.get("id_evidencia") if evidencia_incluida else None
        return self._despachar(
            tipo, contexto, asunto, destinatarios, cuerpo, adjuntos,
            id_evidencia=id_evidencia,
        )

    def _despachar(self, tipo, contexto, asunto, destinatarios, cuerpo, adjuntos,
                   *, id_evidencia=None):
        serializados = {canal: ";".join(valores) or None for canal, valores in destinatarios.items()}
        with self.fabrica_uow(self.proveedor) as uow:
            id_envio = self.tipo_repositorio(uow.obtener_conexion()).reservar_envio(
                int(contexto["id_ejecucion"]), id_evidencia, tipo,
                asunto, serializados,
            )
            uow.confirmar()
        if id_envio is None:
            return "OMITIDO"
        config_graph = self.servicio_graph_config.efectiva()
        if config_graph is None:
            self._cerrar(id_envio, "OMITIDO", error="Microsoft Graph no esta habilitado o completo.")
            self._log("GRAPH_ENVIO_ERROR", contexto["id_ejecucion"],
                      "Notificacion omitida: Microsoft Graph no esta disponible.", "WARNING")
            return "OMITIDO"
        mensaje = construir_mensaje_graph(asunto, cuerpo, destinatarios, adjuntos)
        self._log("GRAPH_ENVIO_INICIO", contexto["id_ejecucion"],
                  f"Inicio de envio {tipo} por Microsoft Graph.")
        try:
            resultado = self.cliente_graph.enviar(config_graph, mensaje)
        except ErrorGraph as error:
            detalle = sanitizar_texto_externo(str(error), 1000)
            self._cerrar(id_envio, "FALLIDO", status_code=error.status_code,
                         request_id=error.request_id, error=detalle)
            self._log("GRAPH_ENVIO_ERROR", contexto["id_ejecucion"], detalle, "ERROR")
            return "FALLIDO"
        self._cerrar(id_envio, "ENVIADO", status_code=resultado.status_code,
                     request_id=resultado.request_id)
        self._log("GRAPH_ENVIO_OK", contexto["id_ejecucion"],
                  f"Notificacion {tipo} aceptada por Microsoft Graph.")
        return "ENVIADO"

    def _cerrar(self, id_envio, estado, **datos):
        with self.fabrica_uow(self.proveedor) as uow:
            self.tipo_repositorio(uow.obtener_conexion()).finalizar_envio(
                id_envio, estado, **datos
            )
            uow.confirmar()

    def _log(self, accion, id_ejecucion, descripcion, nivel="INFO"):
        with self.fabrica_uow(self.proveedor) as uow:
            self.tipo_logs(uow.obtener_conexion()).registrar(
                accion=accion, modulo="MAIL_GRAPH", descripcion=descripcion,
                nivel=nivel, usuario="sistema",
                valor_nuevo=f"id_ejecucion={int(id_ejecucion)}",
            )
            uow.confirmar()

    @staticmethod
    def _evento(contexto, config):
        if contexto["estado_ejecucion"] == "ERROR" and config.alerta_error_activa:
            return "ALERTA_INTERNA"
        if contexto["estado_ejecucion"] == "EXITOSA" and config.notificar_exito_activa:
            return "NOTIFICACION_EXITOSA"
        return None

    @staticmethod
    def _evidencia_incluida(tipo, contexto, config, evidencia):
        return bool(
            tipo in {"NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE"}
            and config.enviar_evidencia
            and contexto.get("estado_evidencia") == "VALIDADA"
            and isinstance(evidencia, dict)
        )

    @staticmethod
    def _destinatarios(tipo, config):
        clase = "EVIDENCIA" if tipo in {"NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE"} else "ALERTA"
        resultado = {"TO": [], "CC": [], "BCC": []}
        for item in config.destinatarios:
            if item.tipo_destinatario == clase:
                resultado[item.canal].append(item.email)
        return resultado

    @staticmethod
    def _emails_globales(texto):
        resultado = []
        for bruto in str(texto or "").replace(",", ";").split(";"):
            if not bruto.strip():
                continue
            try: email = normalizar_email(bruto)
            except ValueError: continue
            if email not in resultado: resultado.append(email)
        return resultado

    @staticmethod
    def _asunto(tipo, contexto, config, evidencia_incluida=False):
        if tipo in {"NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE"}:
            if config.asunto_personalizado:
                return sanitizar_texto_externo(config.asunto_personalizado, 255)
            if (evidencia_incluida and config.usar_asunto_sugerido_script
                    and contexto.get("asunto_sugerido")):
                return sanitizar_texto_externo(contexto["asunto_sugerido"], 255)
            return sanitizar_texto_externo(
                f"Ejecucion exitosa | {contexto['nombre_tarea']}", 255
            )
        return sanitizar_texto_externo(f"Alerta APP Scheduler | {contexto['nombre_tarea']}", 255)

    def _cuerpo(self, tipo, contexto, evidencia):
        plantilla = (
            "correos/exito.html"
            if tipo in {"NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE"}
            else "correos/alerta.html"
        )
        seguro = {
            clave: sanitizar_texto_externo(valor, 2000) if isinstance(valor, str) else valor
            for clave, valor in contexto.items()
        }
        datos_evidencia = _sanitizar_estructura(evidencia or {})
        return self.entorno_jinja.get_template(plantilla).render(
            ejecucion=seguro, evidencia=datos_evidencia,
        )


def preparar_adjuntos(evidencia: dict, raiz_version: Path) -> list[dict]:
    declarados = evidencia.get("adjuntos", []) if isinstance(evidencia, dict) else []
    if not isinstance(declarados, list):
        raise ErrorAdjunto("La declaracion de adjuntos no es valida.")
    if len(declarados) > MAX_ADJUNTOS:
        raise ErrorAdjunto(f"Se permiten hasta {MAX_ADJUNTOS} adjuntos por correo.")
    raiz = raiz_version.resolve()
    resultado = []
    total = 0
    for item in declarados:
        if not isinstance(item, dict) or not item.get("ruta"):
            raise ErrorAdjunto("Existe un adjunto sin ruta valida.")
        candidata = raiz / str(item["ruta"])
        for elemento in (candidata, *candidata.parents):
            if elemento.exists() and elemento.is_symlink():
                raise ErrorAdjunto("No se permiten enlaces simbolicos como adjuntos.")
            if elemento == raiz:
                break
        ruta = candidata.resolve()
        try: ruta.relative_to(raiz)
        except ValueError as error: raise ErrorAdjunto("El adjunto esta fuera de la version ejecutada.") from error
        if not ruta.is_file():
            if str(item.get("obligatorio", "")).lower() in {"1", "true", "si", "yes"} or item.get("obligatorio") is True:
                raise ErrorAdjunto("Falta un adjunto obligatorio.")
            continue
        if ruta.suffix.lower() in EXTENSIONES_BLOQUEADAS or ruta.name.lower().startswith(".env"):
            raise ErrorAdjunto("El tipo de archivo declarado no esta autorizado.")
        tamano = ruta.stat().st_size
        total += tamano
        if total > MAX_TOTAL_ADJUNTOS_BYTES:
            raise ErrorAdjunto("Los adjuntos superan el limite seguro de correo directo.")
        contenido = base64.b64encode(ruta.read_bytes()).decode("ascii")
        resultado.append({"@odata.type": "#microsoft.graph.fileAttachment",
                          "name": ruta.name,
                          "contentType": mimetypes.guess_type(ruta.name)[0] or "application/octet-stream",
                          "contentBytes": contenido})
    return resultado


def construir_mensaje_graph(asunto, cuerpo_html, destinatarios, adjuntos):
    def direcciones(canal):
        return [{"emailAddress": {"address": email}} for email in destinatarios[canal]]
    mensaje = {"subject": asunto, "body": {"contentType": "HTML", "content": cuerpo_html},
               "toRecipients": direcciones("TO"), "ccRecipients": direcciones("CC"),
               "bccRecipients": direcciones("BCC")}
    if adjuntos:
        mensaje["attachments"] = adjuntos
    return mensaje


def _sanitizar_estructura(valor):
    if isinstance(valor, dict):
        return {str(k): _sanitizar_estructura(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_sanitizar_estructura(v) for v in valor[:100]]
    if isinstance(valor, str):
        return sanitizar_texto_externo(valor, 2000)
    return valor if valor is None or isinstance(valor, (int, float, bool)) else str(valor)
