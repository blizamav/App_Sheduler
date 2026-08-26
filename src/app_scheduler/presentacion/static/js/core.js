import { prepararModal } from "./componentes/modal.js";
import { prepararFormularios } from "./componentes/formularios.js";
import { prepararEstadoWorker } from "./componentes/estado-worker.js";

function prepararSidebar() {
    const sidebar = document.querySelector("#sidebarPrincipal");
    if (!sidebar || !window.bootstrap?.Offcanvas) return;
    const botonContraer = document.querySelector("[data-sidebar-contraer]");
    const clave = "appScheduler.sidebarContraido";
    const aplicarEstado = (contraido) => {
        document.documentElement.classList.toggle("sidebar-contraido", contraido);
        botonContraer?.setAttribute("aria-pressed", String(contraido));
        botonContraer?.setAttribute("aria-label", contraido ? "Expandir navegacion" : "Contraer navegacion");
        botonContraer?.setAttribute("title", contraido ? "Expandir navegacion" : "Contraer navegacion");
    };
    aplicarEstado(document.documentElement.classList.contains("sidebar-contraido"));
    botonContraer?.addEventListener("click", () => {
        const contraido = !document.documentElement.classList.contains("sidebar-contraido");
        aplicarEstado(contraido);
        try { window.localStorage.setItem(clave, contraido ? "1" : "0"); } catch (_error) { /* Estado solo de conveniencia. */ }
    });
    sidebar.querySelectorAll("a.nav-link").forEach((enlace) => {
        enlace.addEventListener("click", () => {
            if (window.innerWidth >= 992) return;
            window.bootstrap.Offcanvas.getInstance(sidebar)?.hide();
        });
    });
}

function prepararMenusEnTablas() {
    document.addEventListener("show.bs.dropdown", (evento) => {
        evento.target.closest(".tabla-contenedor")?.classList.add("menu-desplegado");
    });
    document.addEventListener("hidden.bs.dropdown", (evento) => {
        evento.target.closest(".tabla-contenedor")?.classList.remove("menu-desplegado");
    });
}

function prepararAlertas() {
    document.querySelectorAll("[data-alerta]").forEach((alerta) => {
        window.setTimeout(() => window.bootstrap?.Alert.getOrCreateInstance(alerta).close(), 6000);
    });
}

function prepararTooltips() {
    if (!window.bootstrap?.Tooltip) return;
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((elemento) => window.bootstrap.Tooltip.getOrCreateInstance(elemento));
}

export function tokenCsrf() {
    return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

document.addEventListener("DOMContentLoaded", () => {
    prepararSidebar();
    prepararAlertas();
    prepararModal();
    prepararFormularios();
    prepararTooltips();
    prepararMenusEnTablas();
    prepararEstadoWorker();
});
