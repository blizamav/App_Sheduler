const contenedor = document.querySelector("[data-ejecucion]");

if (contenedor) {
    const consola = document.querySelector("[data-consola]");
    const estado = document.querySelector("[data-estado]");
    const resultado = document.querySelector("[data-resultado]");
    const worker = document.querySelector("[data-worker]");
    const pid = document.querySelector("[data-pid]");
    const duracion = document.querySelector("[data-duracion]");
    const codigoSalida = document.querySelector("[data-codigo-salida]");
    const estadoEvidencia = document.querySelector("[data-estado-evidencia]");
    const seccionNotificaciones = document.querySelector("[data-notificaciones-seccion]");
    const listaNotificaciones = document.querySelector("[data-notificaciones-lista]");
    const polling = document.querySelector("[data-polling]");
    const autoscroll = document.querySelector("[data-autoscroll]");
    const texto = (etiqueta, valor) => {
        const grupo = document.createElement("div");
        const termino = document.createElement("dt");
        const detalle = document.createElement("dd");
        termino.textContent = etiqueta;
        detalle.textContent = valor;
        grupo.append(termino, detalle);
        return grupo;
    };
    const renderizarNotificaciones = (items = []) => {
        if (!seccionNotificaciones || !listaNotificaciones) return;
        seccionNotificaciones.hidden = items.length === 0;
        listaNotificaciones.replaceChildren(...items.map((item) => {
            const card = document.createElement("article");
            card.className = "notificacion-ejecucion-card";
            const cabecera = document.createElement("div");
            cabecera.className = "notificacion-ejecucion-cabecera";
            const titulo = document.createElement("h3");
            const badge = document.createElement("span");
            titulo.textContent = item.tipo;
            badge.className = `badge ${item.clase}`;
            badge.textContent = item.estado;
            cabecera.append(titulo, badge);
            const explicacion = document.createElement("p");
            explicacion.textContent = item.explicacion;
            const detalles = document.createElement("dl");
            detalles.append(
                texto("Evidencia incluida", item.evidencia_incluida ? "Si" : "No"),
                texto("Adjuntos seguros", String(item.cantidad_adjuntos)),
            );
            card.append(cabecera, explicacion, detalles);
            return card;
        }));
    };
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
            worker.textContent = datos.nombre_worker || "Pendiente de worker";
            pid.textContent = datos.pid_proceso ?? "-";
            duracion.textContent = datos.duracion_segundos == null
                ? "En progreso"
                : `${datos.duracion_segundos} segundos`;
            codigoSalida.textContent = datos.codigo_salida ?? "-";
            estadoEvidencia.textContent = datos.estado_evidencia;
            renderizarNotificaciones(datos.notificaciones);
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
