document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.dataset.app = "app-scheduler";

    const cuerpo = document.body;
    const botonesSidebar = document.querySelectorAll("[data-sidebar-toggle]");
    const cierresSidebar = document.querySelectorAll("[data-sidebar-cerrar]");
    const botonesLogs = document.querySelectorAll("[data-panel-logs-toggle]");
    const alertas = document.querySelectorAll(".alerta");

    botonesSidebar.forEach((boton) => {
        boton.addEventListener("click", () => {
            cuerpo.classList.add("sidebar-abierto");
        });
    });

    cierresSidebar.forEach((boton) => {
        boton.addEventListener("click", () => {
            cuerpo.classList.remove("sidebar-abierto");
        });
    });

    botonesLogs.forEach((boton) => {
        boton.addEventListener("click", () => {
            cuerpo.classList.toggle("panel-logs-abierto");
        });
    });

    alertas.forEach((alerta) => {
        setTimeout(() => {
            alerta.classList.add("alerta-saliendo");
        }, 4500);
    });
});
