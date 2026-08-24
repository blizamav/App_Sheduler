from __future__ import annotations

import re
from pathlib import Path

from app_scheduler import crear_aplicacion


RAIZ = Path(__file__).resolve().parents[2]
PRESENTACION = RAIZ / "src/app_scheduler/presentacion"
TEMPLATES = PRESENTACION / "templates"
STATIC = PRESENTACION / "static"


def _app(configuracion):
    return crear_aplicacion(
        configuracion,
        ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )


def test_bootstrap_esta_versionado_y_no_depende_de_cdn():
    css = STATIC / "vendor/bootstrap/bootstrap.min.css"
    js = STATIC / "vendor/bootstrap/bootstrap.bundle.min.js"
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")

    assert css.stat().st_size > 200_000
    assert js.stat().st_size > 70_000
    assert "vendor/bootstrap/bootstrap.min.css" in base
    assert "vendor/bootstrap/bootstrap.bundle.min.js" in base
    assert "cdn.jsdelivr" not in base
    assert "unpkg.com" not in base


def test_todos_los_templates_jinja_compilan(configuracion):
    app = _app(configuracion)

    with app.app_context():
        for nombre in app.jinja_env.list_templates():
            app.jinja_env.get_template(nombre)


def test_botones_declaran_tipo_y_post_incluye_csrf():
    errores_tipo = []
    errores_csrf = []
    for ruta in TEMPLATES.rglob("*.html"):
        contenido = ruta.read_text(encoding="utf-8")
        for boton in re.findall(r"<button\b[^>]*>", contenido, flags=re.IGNORECASE):
            if not re.search(r"\btype\s*=", boton, flags=re.IGNORECASE):
                errores_tipo.append(f"{ruta.relative_to(RAIZ)}: {boton}")
        for formulario in re.findall(
            r"<form\b[^>]*method=[\"']post[\"'][^>]*>.*?</form>",
            contenido,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            if 'name="csrf_token"' not in formulario:
                errores_csrf.append(str(ruta.relative_to(RAIZ)))

    assert errores_tipo == []
    assert errores_csrf == []


def test_confirmacion_no_depende_del_click_y_no_inyecta_html():
    modal = (STATIC / "js/componentes/modal.js").read_text(encoding="utf-8")
    formularios = (STATIC / "js/componentes/formularios.js").read_text(encoding="utf-8")

    assert 'addEventListener("submit"' in modal
    assert 'document.addEventListener("click"' not in modal
    assert "requestSubmit" in modal
    assert "textContent" in modal
    assert "innerHTML" not in modal + formularios
    assert "eval(" not in modal + formularios


def test_respuestas_incluyen_cabeceras_owasp(configuracion):
    respuesta = _app(configuracion).test_client().get("/login")
    csp = respuesta.headers["Content-Security-Policy"]

    assert respuesta.status_code == 200
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-inline'" not in csp
    assert "'unsafe-eval'" not in csp
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_shell_usa_componentes_bootstrap_accesibles():
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    layout = (STATIC / "css/layout.css").read_text(encoding="utf-8")
    core = (STATIC / "js/core.js").read_text(encoding="utf-8")
    estado_sidebar = (STATIC / "js/estado-sidebar.js").read_text(encoding="utf-8")
    componentes = (STATIC / "css/componentes.css").read_text(encoding="utf-8")

    assert 'class="sidebar offcanvas-lg offcanvas-start"' in base
    assert 'data-bs-target="#sidebarPrincipal"' in base
    assert "data-sidebar-contraer" in base
    assert "sidebar-contraido" in layout
    assert "background-color: var(--color-primario-oscuro) !important" in layout
    assert "appScheduler.sidebarContraido" in core + estado_sidebar
    assert "estado-sidebar.js" in base
    assert base.index("estado-sidebar.js") < base.index("bootstrap.min.css")
    assert "document.documentElement.classList.add" in estado_sidebar
    assert "show.bs.dropdown" in core
    assert ".tabla-contenedor.menu-desplegado" in componentes
    assert "z-index: var(--bs-offcanvas-zindex, 1045)" in layout
    assert "height: 100dvh" in layout
    assert "max-width: none" in layout
    assert "orientation: landscape" in layout
    assert ".barra-filtros.tareas-filtros" in componentes
    assert "flex-wrap: nowrap" in layout
    assert "overflow-x: hidden" in layout
    assert ".navegacion-grupo," in layout
    assert 'class="modal fade"' in base
    assert 'aria-labelledby="modalTitulo"' in base
    assert 'data-bs-toggle="dropdown"' in base


def test_vistas_operativas_no_limitan_el_ancho_disponible():
    hojas = (
        "tareas-scripts.css",
        "catalogos.css",
        "seguridad.css",
        "programaciones.css",
    )
    for nombre in hojas:
        contenido = (STATIC / "css/modulos" / nombre).read_text(encoding="utf-8")
        assert "max-width: none" in contenido
