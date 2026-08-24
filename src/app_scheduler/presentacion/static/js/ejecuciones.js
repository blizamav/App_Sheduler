const contenedor = document.querySelector("[data-ejecucion]");

if (contenedor) {
    const consola = document.querySelector("[data-consola]");
    const estado = document.querySelector("[data-estado]");
    const resultado = document.querySelector("[data-resultado]");
    const polling = document.querySelector("[data-polling]");
    const autoscroll = document.querySelector("[data-autoscroll]");
    const consultar = async () => {
        try {
            const respuesta = await fetch(contenedor.dataset.logUrl, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            if (!respuesta.ok) throw new Error("respuesta_no_disponible");
            const datos = await respuesta.json();
            consola.textContent = datos.log;
            estado.textContent = datos.estado.replaceAll("_", " ");
            resultado.textContent = datos.mensaje_error || "Sin error registrado";
            if (autoscroll?.checked) consola.scrollTop = consola.scrollHeight;
            if (datos.es_final) {
                polling.textContent = "Finalizada";
                polling.className = `badge ${datos.estado === "EXITOSA" ? "activo" : "advertencia"}`;
                return;
            }
            window.setTimeout(consultar, 1500);
        } catch (_error) {
            polling.textContent = "Reintentando";
            window.setTimeout(consultar, 3000);
        }
    };
    consultar();
}
