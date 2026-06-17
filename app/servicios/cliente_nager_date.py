import requests


URL_BASE_NAGER = "https://date.nager.at/api/v3"
TIMEOUT_SEGUNDOS = 10


class ErrorNagerDate(Exception):
    pass


def consultar_nager_feriados(anio, pais):
    url = f"{URL_BASE_NAGER}/PublicHolidays/{anio}/{pais}"
    try:
        respuesta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
    except requests.Timeout as error:
        raise ErrorNagerDate("La consulta a Nager.Date excedio el tiempo de espera.") from error
    except requests.RequestException as error:
        raise ErrorNagerDate("No fue posible conectar con Nager.Date.") from error

    if respuesta.status_code == 204:
        return []
    if respuesta.status_code == 400:
        raise ErrorNagerDate("Nager.Date rechazo la solicitud. Revisa ano y pais.")
    if respuesta.status_code == 404:
        raise ErrorNagerDate("Nager.Date no reconoce el pais informado.")
    if not respuesta.ok:
        raise ErrorNagerDate(f"Nager.Date respondio con estado HTTP {respuesta.status_code}.")

    try:
        datos = respuesta.json()
    except ValueError as error:
        raise ErrorNagerDate("Nager.Date retorno una respuesta invalida.") from error

    if not isinstance(datos, list):
        raise ErrorNagerDate("Nager.Date retorno una estructura inesperada.")
    return datos
