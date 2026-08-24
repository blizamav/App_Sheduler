(function aplicarEstadoInicialSidebar() {
    try {
        if (window.localStorage.getItem("appScheduler.sidebarContraido") === "1") {
            document.documentElement.classList.add("sidebar-contraido");
        }
    } catch (_error) {
        document.documentElement.classList.remove("sidebar-contraido");
    }
}());
