"""Cliente HTTP minimo para el endpoint publico versionado de Nager.Date."""

from __future__ import annotations

import requests


URL_NAGER = "https://date.nager.at/api/v3/PublicHolidays/{anio}/{pais}"


class ErrorNagerDate(RuntimeError):
    """Fallo externo controlado sin cuerpo remoto ni datos sensibles."""


class ClienteNagerDate:
    def __init__(self, *, sesion=None, timeout_segundos: float = 10.0):
        self.sesion = sesion or requests.Session()
        self.timeout_segundos = timeout_segundos

    def consultar(self, anio: int, pais: str) -> list[dict]:
        url = URL_NAGER.format(anio=anio, pais=pais)
        try:
            respuesta = self.sesion.get(
                url,
                timeout=self.timeout_segundos,
                headers={"Accept": "application/json", "User-Agent": "APP-Scheduler/1.0"},
            )
        except requests.Timeout as error:
            raise ErrorNagerDate("Nager.Date no respondio dentro del tiempo esperado.") from error
        except requests.RequestException as error:
            raise ErrorNagerDate("No fue posible conectar con Nager.Date.") from error
        if respuesta.status_code != 200:
            raise ErrorNagerDate(
                f"Nager.Date respondio con estado HTTP {respuesta.status_code}."
            )
        try:
            datos = respuesta.json()
        except (ValueError, TypeError) as error:
            raise ErrorNagerDate("Nager.Date entrego una respuesta JSON invalida.") from error
        if not isinstance(datos, list):
            raise ErrorNagerDate("Nager.Date entrego una estructura inesperada.")
        return datos
