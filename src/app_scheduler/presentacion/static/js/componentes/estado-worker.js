const REINTENTO_DEFECTO_MS = 30000;
const ESTADOS_NO_DISPONIBLES = new Set(["DETENIDO", "DESCONOCIDO"]);

function pluralPendientes(cantidad) {
    return cantidad === 1 ? "ejecucion pendiente." : "ejecuciones pendientes.";
}

function aplicarIndicadores(estado) {
    const pendientes = Number(estado.pendientes || 0);
    document.querySelectorAll("[data-worker-indicador]").forEach((indicador) => {
        indicador.dataset.estado = estado.codigo;
        indicador.setAttribute("aria-label", estado.aria_label);
        const texto = indicador.querySelector("[data-worker-texto]");
        const antiguedad = indicador.querySelector("[data-worker-antiguedad]");
        if (texto) texto.textContent = estado.texto;
        if (antiguedad) {
            antiguedad.textContent = estado.antiguedad
                + (pendientes ? ` · ${pendientes} pendiente${pendientes === 1 ? "" : "s"}` : "");
        }
    });
}

function aplicarCola(estado) {
    const pendientes = Number(estado.pendientes || 0);
    const mostrar = ESTADOS_NO_DISPONIBLES.has(estado.codigo) && pendientes > 0;
    document.querySelectorAll("[data-worker-cola-aviso]").forEach((aviso) => {
        aviso.hidden = !mostrar;
        const cantidad = aviso.querySelector("[data-worker-pendientes]");
        const texto = aviso.querySelector("[data-worker-pendientes-texto]");
        if (cantidad) cantidad.textContent = String(pendientes);
        if (texto) texto.textContent = pluralPendientes(pendientes);
    });
}

function aplicarConfirmaciones(estado) {
    document.querySelectorAll("[data-worker-confirmacion]").forEach((boton) => {
        const noDisponible = ESTADOS_NO_DISPONIBLES.has(estado.codigo);
        boton.dataset.titulo = noDisponible
            ? "Worker no disponible: reservar igualmente"
            : "Reservar ejecucion manual";
        boton.dataset.mensaje = noDisponible
            ? boton.dataset.mensajeDetenido
            : boton.dataset.mensajeOperativo;
    });
}

function aplicarEstado(estado) {
    aplicarIndicadores(estado);
    aplicarCola(estado);
    aplicarConfirmaciones(estado);
}

function estadoDesconocido() {
    return {
        codigo: "DESCONOCIDO",
        texto: "Estado Worker desconocido",
        antiguedad: "No fue posible consultar el heartbeat",
        pendientes: 0,
        aria_label: "Estado Worker desconocido. No fue posible consultar el heartbeat.",
    };
}

export function prepararEstadoWorker() {
    const endpoint = document.body.dataset.workerEndpoint;
    if (!endpoint || !document.querySelector("[data-worker-indicador]")) return;
    let temporizador = null;
    let controlador = null;

    const programar = (segundos) => {
        window.clearTimeout(temporizador);
        const espera = Number(segundos) > 0 ? Number(segundos) * 1000 : REINTENTO_DEFECTO_MS;
        temporizador = window.setTimeout(actualizar, espera);
    };

    const actualizar = async () => {
        controlador?.abort();
        controlador = new AbortController();
        try {
            const respuesta = await fetch(endpoint, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
                cache: "no-store",
                signal: controlador.signal,
            });
            if (!respuesta.ok) throw new Error("Estado Worker no disponible");
            const datos = await respuesta.json();
            aplicarEstado(datos.estado_worker || estadoDesconocido());
            programar(datos.polling_segundos);
        } catch (error) {
            if (error.name === "AbortError") return;
            aplicarEstado(estadoDesconocido());
            programar();
        }
    };

    window.addEventListener("pagehide", () => {
        window.clearTimeout(temporizador);
        controlador?.abort();
    }, { once: true });
    actualizar();
}
