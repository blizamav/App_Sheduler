from __future__ import annotations

from flask import jsonify

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.errores import ErrorValidacion


def _app(configuracion):
    return crear_aplicacion(
        configuracion,
        ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )


def test_fabrica_registra_hito_3_y_protege_panel(configuracion):
    app = _app(configuracion)
    cliente = app.test_client()

    respuesta = cliente.get("/")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login?next=/")
    reglas = {regla.rule for regla in app.url_map.iter_rules()}
    assert reglas == {
        "/",
        "/login",
        "/logout",
        "/salud",
        "/seguridad/roles-permisos",
        "/static-reconstruccion/<path:filename>",
        "/usuarios/",
        "/usuarios/<int:id_usuario>/editar",
        "/usuarios/<int:id_usuario>/estado",
        "/usuarios/nuevo",
    }


def test_healthcheck_no_requiere_sql(configuracion):
    respuesta = _app(configuracion).test_client().get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "ambiente": "LOCAL",
        "estado": "OK",
        "servicio": "web",
        "version": "hito1-test",
    }


def test_csrf_bloquea_escritura_sin_token(configuracion):
    app = _app(configuracion)

    @app.post("/prueba-escritura")
    def prueba_escritura():
        return jsonify({"estado": "OK"})

    respuesta = app.test_client().post(
        "/prueba-escritura",
        headers={"Accept": "application/json"},
    )

    assert respuesta.status_code == 403
    assert respuesta.get_json()["codigo"] == "AUTORIZACION"


def test_csrf_acepta_token_de_sesion(configuracion):
    app = _app(configuracion)

    @app.post("/prueba-escritura")
    def prueba_escritura():
        return jsonify({"estado": "OK"})

    cliente = app.test_client()
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]

    respuesta = cliente.post("/prueba-escritura", headers={"X-CSRF-Token": token})

    assert respuesta.status_code == 200


def test_error_controlado_entrega_respuesta_segura(configuracion):
    app = _app(configuracion)

    @app.get("/api/error-controlado")
    def error_controlado():
        raise ErrorValidacion(
            "Dato invalido.",
            detalle_tecnico="password=valor-que-no-debe-responder",
        )

    respuesta = app.test_client().get(
        "/api/error-controlado",
        headers={"Accept": "application/json"},
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json() == {
        "codigo": "VALIDACION",
        "estado": "ERROR",
        "mensaje": "Dato invalido.",
    }
    assert b"valor-que-no-debe-responder" not in respuesta.data


def test_cookie_sesion_tiene_hardening_base(configuracion):
    app = _app(configuracion)

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False
