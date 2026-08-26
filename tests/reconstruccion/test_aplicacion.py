from __future__ import annotations

from flask import jsonify

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.errores import ErrorValidacion


def _app(configuracion):
    return crear_aplicacion(
        configuracion,
        ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )


def test_fabrica_registra_hito_5_y_protege_panel(configuracion):
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
        "/categorias/",
        "/categorias/<int:id_registro>/editar",
        "/categorias/<int:id_registro>/estado",
        "/categorias/nuevo",
        "/clientes/",
        "/clientes/<int:id_registro>/editar",
        "/clientes/<int:id_registro>/estado",
        "/clientes/nuevo",
        "/seguridad/roles-permisos",
        "/scripts",
        "/static-reconstruccion/<path:filename>",
        "/usuarios/",
        "/usuarios/<int:id_usuario>/editar",
        "/usuarios/<int:id_usuario>/estado",
        "/usuarios/nuevo",
        "/tipos/",
        "/tipos/<int:id_registro>/editar",
        "/tipos/<int:id_registro>/estado",
        "/tipos/nuevo",
        "/tareas/",
        "/tareas/nueva",
        "/tareas/<int:id_tarea>/editar",
        "/tareas/<int:id_tarea>/estado",
        "/tareas/<int:id_tarea>/programaciones/",
        "/tareas/<int:id_tarea>/programaciones/nueva",
        "/tareas/<int:id_tarea>/programaciones/<int:id_programacion>/editar",
        "/tareas/<int:id_tarea>/programaciones/<int:id_programacion>/estado",
        "/tareas/<int:id_tarea>/scripts",
        "/tareas/<int:id_tarea>/scripts/versiones",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/activar",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/desactivar",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/descargar",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/env",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/env/quitar",
        "/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/reemplazar",
        "/ejecuciones/",
        "/ejecuciones/<int:id_ejecucion>",
        "/ejecuciones/<int:id_ejecucion>/log",
        "/ejecuciones/<int:id_ejecucion>/detener",
            "/tareas/<int:id_tarea>/ejecutar",
            "/tareas/<int:id_tarea>/evidencia",
            "/tareas/<int:id_tarea>/notificaciones",
                "/operacion/estado",
                "/operacion/worker",
                "/logs/",
            "/logs/<int:id_log>",
            "/configuracion/",
            "/configuracion/scheduler",
            "/auditoria/",
            "/auditoria/<int:id_auditoria>",
            "/papelera/",
            "/papelera/<entidad>/<int:id_registro>/retirar",
            "/papelera/<entidad>/<int:id_registro>/restaurar",
                "/papelera/<entidad>/<int:id_registro>/eliminar-permanente",
                "/feriados/",
                "/feriados/nuevo",
                "/feriados/<int:id_feriado>/editar",
                "/feriados/<int:id_feriado>/estado",
                "/feriados/<int:id_feriado>/eliminar",
                "/feriados/sincronizar",
                "/feriados/sincronizar/preview",
                "/feriados/sincronizar/aplicar",
                "/configuracion/mail-graph",
                "/administracion/factory-reset",
                "/administracion/factory-reset/preview",
                "/administracion/factory-reset/ejecutar",
                "/administracion/factory-reset/estado",
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
