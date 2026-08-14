import { prepararModal } from "./componentes/modal.js";

function prepararSidebar() {
    const cuerpo = document.body;
    document.querySelector("[data-sidebar-abrir]")?.addEventListener("click", () => {
        cuerpo.classList.add("sidebar-abierto");
    });
    document.querySelector("[data-sidebar-cerrar]")?.addEventListener("click", () => {
        cuerpo.classList.remove("sidebar-abierto");
    });
}

function prepararAlertas() {
    document.querySelectorAll("[data-alerta]").forEach((alerta) => {
        alerta.querySelector("[data-alerta-cerrar]")?.addEventListener("click", () => alerta.remove());
    });
}

export function tokenCsrf() {
    return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

document.addEventListener("DOMContentLoaded", () => {
    prepararSidebar();
    prepararAlertas();
    prepararModal();
});
