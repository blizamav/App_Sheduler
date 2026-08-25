"""Cliente central Microsoft Graph con autenticacion client credentials."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import requests

from app_scheduler.modulos.notificaciones.seguridad import sanitizar_texto_externo


URL_TOKEN = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
URL_SENDMAIL = "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"


class ErrorGraph(RuntimeError):
    def __init__(self, mensaje: str, *, status_code=None, request_id=None):
        super().__init__(mensaje)
        self.status_code = status_code
        self.request_id = request_id


@dataclass(frozen=True, slots=True)
class ResultadoGraph:
    status_code: int
    request_id: str | None


class ClienteMicrosoftGraph:
    def __init__(self, *, sesion=None, timeout_token=20.0, timeout_envio=30.0):
        self.sesion = sesion or requests.Session()
        self.timeout_token = timeout_token
        self.timeout_envio = timeout_envio

    def enviar(self, configuracion, mensaje: dict) -> ResultadoGraph:
        token = self._obtener_token(configuracion)
        url = URL_SENDMAIL.format(sender=quote(configuracion["send_mail_user"], safe=""))
        try:
            respuesta = self.sesion.post(
                url,
                json={"message": mensaje, "saveToSentItems": configuracion["save_to_sent_items"]},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=self.timeout_envio,
            )
        except requests.Timeout as error:
            raise ErrorGraph("Microsoft Graph no respondio dentro del tiempo esperado.") from error
        except requests.RequestException as error:
            raise ErrorGraph("No fue posible conectar con Microsoft Graph.") from error
        request_id = respuesta.headers.get("request-id") or respuesta.headers.get("client-request-id")
        if respuesta.status_code != 202:
            detalle = sanitizar_texto_externo(getattr(respuesta, "text", ""), 500)
            raise ErrorGraph(
                f"Microsoft Graph rechazo el envio (HTTP {respuesta.status_code}). {detalle}".strip(),
                status_code=respuesta.status_code, request_id=request_id,
            )
        return ResultadoGraph(respuesta.status_code, request_id)

    def _obtener_token(self, configuracion) -> str:
        url = URL_TOKEN.format(tenant=quote(configuracion["tenant_id"], safe=""))
        try:
            respuesta = self.sesion.post(
                url,
                data={"client_id": configuracion["client_id"],
                      "client_secret": configuracion["client_secret"],
                      "scope": configuracion["graph_scope"],
                      "grant_type": "client_credentials"},
                headers={"Accept": "application/json"}, timeout=self.timeout_token,
            )
        except requests.Timeout as error:
            raise ErrorGraph("Microsoft Graph no entrego token dentro del tiempo esperado.") from error
        except requests.RequestException as error:
            raise ErrorGraph("No fue posible autenticar con Microsoft Graph.") from error
        if respuesta.status_code != 200:
            raise ErrorGraph(
                f"Microsoft Graph rechazo la autenticacion (HTTP {respuesta.status_code}).",
                status_code=respuesta.status_code,
                request_id=respuesta.headers.get("request-id"),
            )
        try:
            datos = respuesta.json()
        except (ValueError, TypeError) as error:
            raise ErrorGraph("Microsoft Graph entrego una respuesta de token invalida.") from error
        token = datos.get("access_token") if isinstance(datos, dict) else None
        if not isinstance(token, str) or not token:
            raise ErrorGraph("Microsoft Graph no entrego un token utilizable.")
        return token
