"""Errores de aplicacion y traduccion segura a HTTP."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request


class ErrorAplicacion(Exception):
    codigo_http = 400
    codigo = "ERROR_APLICACION"
    mensaje_publico = "No fue posible completar la solicitud."

    def __init__(self, mensaje: str | None = None, *, detalle_tecnico: str | None = None):
        super().__init__(detalle_tecnico or mensaje or self.mensaje_publico)
        self.mensaje = mensaje or self.mensaje_publico
        self.detalle_tecnico = detalle_tecnico


class ErrorValidacion(ErrorAplicacion):
    codigo = "VALIDACION"
    mensaje_publico = "Revisa los datos ingresados."


class ErrorAutorizacion(ErrorAplicacion):
    codigo_http = 403
    codigo = "AUTORIZACION"
    mensaje_publico = "No tienes permiso para realizar esta accion."


class ErrorPersistencia(ErrorAplicacion):
    codigo_http = 503
    codigo = "PERSISTENCIA"
    mensaje_publico = "El servicio de datos no esta disponible temporalmente."


class ErrorInfraestructura(ErrorAplicacion):
    codigo_http = 503
    codigo = "INFRAESTRUCTURA"
    mensaje_publico = "Un servicio tecnico no esta disponible temporalmente."


def _solicita_json() -> bool:
    return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"


def _respuesta_error(codigo: str, mensaje: str, estado: int):
    if _solicita_json():
        return jsonify({"estado": "ERROR", "codigo": codigo, "mensaje": mensaje}), estado
    return render_template("errores/error.html", codigo=codigo, mensaje=mensaje), estado


def registrar_manejadores_errores(app: Flask) -> None:
    @app.errorhandler(ErrorAplicacion)
    def manejar_error_aplicacion(error: ErrorAplicacion):
        app.logger.warning(
            "Error controlado: %s",
            error.detalle_tecnico or error.codigo,
            extra={"evento": error.codigo},
        )
        return _respuesta_error(error.codigo, error.mensaje, error.codigo_http)

    @app.errorhandler(404)
    def manejar_no_encontrado(_error):
        return _respuesta_error("NO_ENCONTRADO", "La pagina solicitada no existe.", 404)

    @app.errorhandler(500)
    def manejar_error_inesperado(error):
        app.logger.exception("Error interno no controlado", extra={"evento": "ERROR_INTERNO"})
        return _respuesta_error(
            "ERROR_INTERNO",
            "Ocurrio un error interno. El equipo TI puede revisar el registro tecnico.",
            500,
        )
