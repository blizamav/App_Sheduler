document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.dataset.app = "app-scheduler";

    const cuerpo = document.body;
    const botonesSidebar = document.querySelectorAll("[data-sidebar-toggle]");
    const cierresSidebar = document.querySelectorAll("[data-sidebar-cerrar]");
    const enlacesSidebar = document.querySelectorAll(".sidebar .nav-link");
    const botonesLogs = document.querySelectorAll("[data-panel-logs-toggle]");
    const panelLogs = document.querySelector("[data-worker-monitor-panel]");
    const monitorUrl = panelLogs?.dataset.monitorUrl || "";
    const agarreResizePanelLogs = document.querySelector("[data-panel-logs-resize]");
    const indicadorCargaMonitor = document.querySelector("[data-worker-monitor-loading]");
    const actualizadoMonitor = document.querySelector("[data-worker-monitor-updated]");
    const botonActualizarMonitor = document.querySelector("[data-worker-monitor-refresh]");
    const botonPausaMonitor = document.querySelector("[data-worker-monitor-pause]");
    const botonCopiarMonitor = document.querySelector("[data-worker-monitor-copy]");
    const selectorLimiteMonitor = document.querySelector("[data-worker-monitor-limit]");
    const workerStatusText = document.querySelector("[data-worker-status-text]");
    const workerStatusDetail = document.querySelector("[data-worker-status-detail]");
    const programadorEstadoBadge = document.querySelector("[data-programador-estado-badge]");
    const programadorEstadoTexto = document.querySelector("[data-programador-estado-texto]");
    const programadorEstadoDetalle = document.querySelector("[data-programador-estado-detalle]");
    const programadorEstadoExtra = document.querySelector("[data-programador-estado-extra]");
    const schedulerStatusText = document.querySelector("[data-scheduler-status-text]");
    const schedulerStatusDetail = document.querySelector("[data-scheduler-status-detail]");
    const automaticaStatusText = document.querySelector("[data-automatica-status-text]");
    const automaticaStatusDetail = document.querySelector("[data-automatica-status-detail]");
    const heartbeatText = document.querySelector("[data-heartbeat-text]");
    const heartbeatDetail = document.querySelector("[data-heartbeat-detail]");
    const estadoPrincipalMonitor = document.querySelector("[data-monitor-estado-principal]");
    const tarjetasMonitor = {
        worker: document.querySelector("[data-monitor-card='worker']"),
        scheduler: document.querySelector("[data-monitor-card='scheduler']"),
        automatica: document.querySelector("[data-monitor-card='automatica']"),
        senal: document.querySelector("[data-monitor-card='senal']"),
        actividad: document.querySelector("[data-monitor-card='actividad']"),
        eventos: document.querySelector("[data-monitor-card='eventos']"),
        errores: document.querySelector("[data-monitor-card='errores']"),
    };
    const actividadEjecucion = document.querySelector("[data-worker-actividad-ejecucion]");
    const actividadEjecucionDetalle = document.querySelector("[data-worker-actividad-ejecucion-detalle]");
    const actividadEventos = document.querySelector("[data-worker-actividad-eventos]");
    const actividadEventosDetalle = document.querySelector("[data-worker-actividad-eventos-detalle]");
    const actividadErrores = document.querySelector("[data-worker-actividad-errores]");
    const actividadErroresDetalle = document.querySelector("[data-worker-actividad-errores-detalle]");
    const alertasMonitor = document.querySelector("[data-worker-monitor-alerts]");
    const consolaMonitor = document.querySelector("[data-worker-monitor-console]");
    const badgeLineasMonitor = document.querySelector("[data-worker-monitor-lines-badge]");
    const eventosMonitor = document.querySelector("[data-worker-monitor-events]");
    const alertas = document.querySelectorAll(".alerta");
    const confirmables = document.querySelectorAll(".requiere-confirmacion");
    const formulariosConfirmables = document.querySelectorAll(".requiere-confirmacion-form");
    const modalConfirmacion = document.querySelector("#modalConfirmacion");
    const modalTitulo = document.querySelector("[data-modal-titulo]");
    const modalMensaje = document.querySelector("[data-modal-mensaje]");
    const modalTipo = document.querySelector("[data-modal-tipo]");
    const modalIcono = document.querySelector("[data-modal-icono]");
    const modalResumen = document.querySelector("[data-modal-resumen]");
    const modalConfirmar = document.querySelector("[data-modal-confirmar]");
    const modalCancelar = document.querySelector("[data-modal-cancelar]");
    const toastStack = document.querySelector("[data-toast-stack]");
    const selectorRol = document.querySelector("[data-rol-original]");
    const alertaRol = document.querySelector("[data-alerta-rol]");
    const passwordEdicion = document.querySelector("[data-password-edicion='1']");
    const alertaPassword = document.querySelector("[data-alerta-password]");
    const formulariosProgramacion = document.querySelectorAll("[data-programacion-form]");
    const togglesPanelEnv = document.querySelectorAll("[data-panel-env-toggle]");
    const consolaEjecucion = document.querySelector("[data-ejecucion-log]");
    const estadoEjecucion = document.querySelector("[data-ejecucion-estado]");
    const badgeEjecucion = document.querySelector("[data-ejecucion-badge]");
    const terminoEjecucion = document.querySelector("[data-ejecucion-termino]");
    const duracionEjecucion = document.querySelector("[data-ejecucion-duracion]");
    const codigoEjecucion = document.querySelector("[data-ejecucion-codigo]");
    const indicadorEjecucion = document.querySelector("[data-ejecucion-indicador]");
    const accionesEnCursoEjecucion = document.querySelector("[data-ejecucion-accion-en-curso]");
    const formularioDetenerEjecucion = document.querySelector("[data-ejecucion-detener-form]");
    const formularioVerificarEjecucion = document.querySelector("[data-ejecucion-verificar-form]");
    const formularioLimpiezaEventos = document.querySelector("[data-limpieza-eventos-form]");
    const historialEventos = document.querySelector("[data-eventos-historial]");
    const panelNotificacionesTarea = document.querySelector("[data-notificaciones-tarea]");
    const panelMailGraphSensible = document.querySelector("[data-mail-graph-sensible-panel]");
    const botonMailGraphRevelar = document.querySelector("[data-mail-graph-revelar]");
    const botonMailGraphOcultar = document.querySelector("[data-mail-graph-ocultar]");
    const estadoMailGraphSensible = document.querySelector("[data-mail-graph-sensible-estado]");
    const camposMailGraphSensibles = document.querySelectorAll("[data-mail-graph-sensitive]");
    let formularioPendiente = null;
    let accionConfirmadaPendiente = null;
    let temporizadorMailGraphSensible = null;
    let intervaloMailGraphSensible = null;
    let envioConfirmado = false;
    let intervaloMonitorWorker = null;
    let monitorWorkerCargando = false;
    let monitorWorkerPausado = false;

    const esVistaCompacta = () => window.matchMedia("(max-width: 960px)").matches;
    const cerrarSidebarCompacto = () => cuerpo.classList.remove("sidebar-abierto");

    botonesSidebar.forEach((boton) => {
        boton.addEventListener("click", () => {
            if (esVistaCompacta()) {
                cuerpo.classList.add("sidebar-abierto");
                return;
            }
            cuerpo.classList.toggle("sidebar-colapsado");
            localStorage.setItem(
                "appSchedulerSidebar",
                cuerpo.classList.contains("sidebar-colapsado") ? "colapsado" : "expandido"
            );
        });
    });

    cierresSidebar.forEach((boton) => {
        boton.addEventListener("click", () => {
            cerrarSidebarCompacto();
        });
    });

    enlacesSidebar.forEach((enlace) => {
        enlace.addEventListener("click", () => {
            if (esVistaCompacta()) {
                cerrarSidebarCompacto();
            }
        });
    });

    window.addEventListener("resize", () => {
        if (!esVistaCompacta()) {
            cerrarSidebarCompacto();
        }
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") {
            cerrarSidebarCompacto();
            if (cuerpo.classList.contains("panel-logs-abierto")) {
                cerrarPanelLogsWorker();
            }
        }
    });

    togglesPanelEnv.forEach((boton) => {
        boton.addEventListener("click", () => {
            const panel = document.getElementById(boton.dataset.panelEnvToggle);
            panel?.classList.toggle("oculto");
        });
    });

    alertas.forEach((alerta) => {
        setTimeout(() => {
            alerta.classList.add("alerta-saliendo");
        }, 4500);
    });

    const obtenerLimiteMonitor = () => {
        const valor = Number(selectorLimiteMonitor?.value || 100);
        return [50, 100, 200].includes(valor) ? valor : 100;
    };

    const esPanelLogsRedimensionable = () => !window.matchMedia("(max-width: 960px)").matches;

    const anchoPanelLogsSeguro = (valor) => {
        const minimo = 420;
        const maximo = Math.floor(window.innerWidth * 0.85);
        return Math.max(minimo, Math.min(maximo, Number(valor) || 540));
    };

    const aplicarAnchoPanelLogs = (valor, persistir = true) => {
        if (!panelLogs || !esPanelLogsRedimensionable()) {
            panelLogs?.style.removeProperty("--panel-logs-width");
            return;
        }
        const ancho = anchoPanelLogsSeguro(valor);
        panelLogs.style.setProperty("--panel-logs-width", `${ancho}px`);
        if (persistir) {
            localStorage.setItem("appSchedulerPanelLogsWidth", String(ancho));
        }
    };

    const restaurarAnchoPanelLogs = () => {
        const guardado = Number(localStorage.getItem("appSchedulerPanelLogsWidth") || 540);
        aplicarAnchoPanelLogs(guardado, false);
    };

    const formatearTiempoMonitor = (segundos) => {
        if (segundos === null || segundos === undefined || Number.isNaN(Number(segundos))) {
            return "No disponible";
        }
        const total = Math.max(0, Number(segundos));
        if (total < 60) {
            return `${total} segundos`;
        }
        const minutos = Math.floor(total / 60);
        const resto = total % 60;
        if (minutos < 60) {
            return resto ? `${minutos} min ${resto} s` : `${minutos} min`;
        }
        const horas = Math.floor(minutos / 60);
        const minutosResto = minutos % 60;
        return minutosResto ? `${horas} h ${minutosResto} min` : `${horas} h`;
    };

    const obtenerEstadoProgramador = (monitor) => {
        const estadoWorker = monitor?.estado_worker || {};
        const estadoVida = estadoWorker.estado_vida || "NO_DISPONIBLE";

        if (estadoVida === "ERROR") {
            return {
                badge: "error",
                titulo: "ERROR",
                mensaje: "Ocurrio un error al consultar el monitor.",
                detalle: estadoWorker.ultimo_error || "El monitor reporto un error real del proceso programador.",
            };
        }
        if (estadoVida === "DETENIDO") {
            return {
                badge: "inactivo",
                titulo: "DETENIDO",
                mensaje: "El proceso programador fue detenido o finalizo su ejecucion.",
                detalle: estadoWorker.resumen_textual || "El worker reporto una detencion explicita.",
            };
        }
        if (estadoVida === "NO_DISPONIBLE") {
            return {
                badge: "info",
                titulo: "NO DISPONIBLE",
                mensaje: "No hay informacion suficiente para determinar el estado del programador.",
                detalle: estadoWorker.resumen_textual || "El monitor aun no dispone de datos suficientes.",
            };
        }
        if (estadoVida === "ADVERTENCIA") {
            return {
                badge: "advertencia",
                titulo: "ADVERTENCIA",
                mensaje: "La ultima senal esta atrasada. Revisar continuidad del programador.",
                detalle: estadoWorker.resumen_textual || "La ultima senal supera el margen esperado.",
            };
        }
        if (estadoVida === "ACTIVO") {
            return {
                badge: "activo",
                titulo: "OPERATIVO",
                mensaje: "El programador esta enviando senal correctamente.",
                detalle: estadoWorker.resumen_textual || "Senal de vida dentro del margen esperado.",
            };
        }
        if (estadoVida === "SIN_SENAL") {
            return {
                badge: "error",
                titulo: "SIN SENAL",
                mensaje: "No se recibe senal reciente del proceso programador.",
                detalle: estadoWorker.resumen_textual || "No hay senal reciente del programador.",
            };
        }
        return {
            badge: "info",
            titulo: "NO DISPONIBLE",
            mensaje: "No hay informacion suficiente para determinar el estado del programador.",
            detalle: "El monitor aun no dispone de datos suficientes.",
        };
    };

    const nivelBadgeMonitor = (nivel) => {
        const niveles = {
            ACTIVO: "activo",
            ADVERTENCIA: "advertencia",
            ERROR: "error",
            DETENIDO: "inactivo",
            SIN_SENAL: "error",
            NO_DISPONIBLE: "info",
            INACTIVO: "inactivo",
            DESCONOCIDO: "info",
            OPERATIVO: "activo",
            PAUSADO: "advertencia",
            "SIN SENAL": "error",
            EJECUTAR: "activo",
            EJECUCION: "activo",
            EXITOSA: "activo",
            OMITIR: "advertencia",
            FERIADO: "advertencia",
            DESHABILITADA: "advertencia",
            APAGADO: "advertencia",
            INFO: "info",
            CONFIGURACION: "info",
            EVENTO: "info",
            activo: "activo",
            advertencia: "advertencia",
            error: "error",
            inactivo: "inactivo",
            info: "info",
            success: "activo",
            warning: "advertencia",
            paused: "advertencia",
        };
        return niveles[nivel] || "info";
    };

    const obtenerNivelEventoMonitor = (evento = {}) => {
        const decision = (evento.decision || "").toUpperCase();
        const motivo = (evento.motivo || "").toUpperCase();
        const tipoEvento = (evento.tipo_evento || "").toUpperCase();

        if (decision === "ERROR" || motivo === "ERROR" || tipoEvento === "ERROR") {
            return "ERROR";
        }
        if (decision === "OMITIR" || motivo === "FERIADO" || tipoEvento === "FERIADO") {
            return "ADVERTENCIA";
        }
        if (decision === "EJECUTAR") {
            return "ACTIVO";
        }
        return decision || tipoEvento || "INFO";
    };

    const clasesEstadoPanel = ["estado-ok", "estado-advertencia", "estado-error", "estado-info", "estado-neutral"];

    const nivelVisualPanel = (nivel) => {
        const badge = nivelBadgeMonitor(nivel);
        const equivalencias = {
            activo: "estado-ok",
            advertencia: "estado-advertencia",
            error: "estado-error",
            info: "estado-info",
            inactivo: "estado-neutral",
        };
        return equivalencias[badge] || "estado-neutral";
    };

    const aplicarEstadoVisualPanel = (elemento, nivel) => {
        if (!elemento) {
            return;
        }
        elemento.classList.remove(...clasesEstadoPanel);
        elemento.classList.add(nivelVisualPanel(nivel));
    };

    const actualizarIndicadorMonitor = (texto, tipo = "info") => {
        if (!indicadorCargaMonitor) {
            return;
        }
        indicadorCargaMonitor.className = `badge ${nivelBadgeMonitor(tipo)}`;
        indicadorCargaMonitor.textContent = texto;
    };

    const renderizarAlertasMonitor = (alertasOperativas = []) => {
        if (!alertasMonitor) {
            return;
        }
        alertasMonitor.replaceChildren();
        if (!alertasOperativas.length) {
            const vacio = document.createElement("p");
            vacio.className = "estado-vacio";
            vacio.textContent = "Sin alertas operativas.";
            alertasMonitor.appendChild(vacio);
            return;
        }
        alertasOperativas.forEach((alerta) => {
            const item = document.createElement("div");
            item.className = `alerta ${nivelBadgeMonitor(alerta.nivel)} ${nivelVisualPanel(alerta.nivel)}`;
            const mensaje = alerta.mensaje || "Alerta operativa sin detalle.";
            item.textContent = mensaje.replace(/^[^:]+:\s/, "");
            alertasMonitor.appendChild(item);
        });
    };

    const renderizarListaMonitor = (contenedor, items, tipo) => {
        if (!contenedor) {
            return;
        }
        contenedor.replaceChildren();
        if (!items || !items.length) {
            const vacio = document.createElement("p");
            vacio.className = "estado-vacio";
            vacio.textContent = tipo === "eventos"
                ? "Sin eventos recientes del programador."
                : "Sin ejecuciones recientes.";
            contenedor.appendChild(vacio);
            return;
        }

        items.forEach((item) => {
            const fila = document.createElement("article");
            fila.className = "panel-logs-item";

            const encabezado = document.createElement("div");
            encabezado.className = "panel-logs-item-head";

            const nombre = document.createElement("strong");
            nombre.textContent = tipo === "eventos"
                ? (item.nombre_tarea || item.tipo_evento || "Evento")
                : (item.nombre_tarea || `Ejecucion ${item.id_ejecucion || "-"}`);

            const badge = document.createElement("span");
            const estado = tipo === "eventos"
                ? (item.decision || item.tipo_evento || "INFO")
                : (item.estado_ejecucion || "SIN_ESTADO");
            const nivelItem = tipo === "eventos"
                ? obtenerNivelEventoMonitor(item)
                : item.estado_ejecucion;
            if (tipo === "eventos") {
                aplicarEstadoVisualPanel(fila, nivelItem);
            }
            badge.className = `badge ${nivelBadgeMonitor(nivelItem)}`;
            badge.textContent = estado;
            encabezado.append(nombre, badge);

            const meta = document.createElement("p");
            meta.className = "panel-logs-item-meta";
            meta.textContent = tipo === "eventos"
                ? [item.fecha_evento || "Sin fecha", item.motivo || "Sin motivo", item.nombre_worker || "Sin worker"].join(" | ")
                : [item.fecha_hora_inicio || "Sin inicio", item.nombre_worker || "Sin worker", item.codigo_salida ?? "-"].join(" | ");

            const detalle = document.createElement("p");
            detalle.className = "panel-logs-item-detail";
            detalle.textContent = tipo === "eventos"
                ? (item.detalle || "Sin detalle.")
                : (item.mensaje_error || item.clave_programacion || "Sin detalle adicional.");

            fila.append(encabezado, meta, detalle);
            contenedor.appendChild(fila);
        });
    };

    const renderizarEstadoMonitor = (monitor) => {
        const estadoWorker = monitor?.estado_worker || {};
        const estadoScheduler = monitor?.estado_scheduler || {};
        const estadoProgramador = obtenerEstadoProgramador(monitor);

        if (programadorEstadoBadge) {
            programadorEstadoBadge.className = `badge ${estadoProgramador.badge}`;
            programadorEstadoBadge.textContent = estadoProgramador.titulo;
        }
        aplicarEstadoVisualPanel(estadoPrincipalMonitor, estadoProgramador.badge);
        if (programadorEstadoTexto) {
            programadorEstadoTexto.textContent = estadoProgramador.mensaje;
        }
        if (programadorEstadoDetalle) {
            programadorEstadoDetalle.textContent = estadoProgramador.detalle;
        }
        if (programadorEstadoExtra) {
            programadorEstadoExtra.textContent = estadoWorker.nombre_worker
                ? `Detalle: ${estadoWorker.nombre_worker}`
                : "Detalle tecnico no disponible.";
        }

        if (workerStatusText) {
            workerStatusText.textContent = estadoWorker.nombre_worker || "No disponible";
        }
        if (workerStatusDetail) {
            workerStatusDetail.textContent = "Representa la identidad del proceso worker monitorizado.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.worker, estadoWorker.estado_vida || "NO_DISPONIBLE");
        if (schedulerStatusText) {
            schedulerStatusText.textContent = estadoScheduler.scheduler_activo ? "ACTIVO" : "APAGADO";
        }
        if (schedulerStatusDetail) {
            schedulerStatusDetail.textContent = estadoScheduler.scheduler_activo
                ? "La configuracion permite operar el programador."
                : "El programador esta deshabilitado por configuracion.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.scheduler, estadoScheduler.scheduler_activo ? "activo" : "advertencia");
        if (automaticaStatusText) {
            automaticaStatusText.textContent = estadoScheduler.permitir_ejecucion_automatica ? "HABILITADA" : "DESHABILITADA";
        }
        if (automaticaStatusDetail) {
            automaticaStatusDetail.textContent = estadoScheduler.permitir_ejecucion_automatica
                ? "Se permite lanzar ejecuciones automaticas si el programador esta operativo."
                : "No se lanzaran ejecuciones automaticas aunque el programador este operativo.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.automatica, estadoScheduler.permitir_ejecucion_automatica ? "activo" : "advertencia");
        if (heartbeatText) {
            heartbeatText.textContent = estadoWorker.ultimo_heartbeat_local || estadoWorker.ultimo_heartbeat || "Sin registro";
        }
        if (heartbeatDetail) {
            heartbeatDetail.textContent = estadoWorker.estado_vida === "DETENIDO"
                ? "El worker reporto una detencion explicita."
                : estadoWorker.ultimo_heartbeat
                ? `Hace ${formatearTiempoMonitor(estadoWorker.segundos_desde_ultimo_heartbeat)}`
                : "El programador aun no ha emitido senales.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.senal, estadoWorker.estado_vida || "NO_DISPONIBLE");
    };

    const renderizarActividadMonitor = (monitor) => {
        const eventos = monitor?.eventos_recientes || [];
        const resumenEventos = monitor?.resumen_eventos || {};
        const ultimoEvento = eventos[0];
        const totalErrores = Number(resumenEventos.errores_programador || 0);

        if (actividadEjecucion) {
            actividadEjecucion.textContent = ultimoEvento
                ? (ultimoEvento.decision || ultimoEvento.tipo_evento || "EVENTO")
                : "Sin actividad";
        }
        if (actividadEjecucionDetalle) {
            actividadEjecucionDetalle.textContent = ultimoEvento
                ? `${ultimoEvento.nombre_tarea || "Sin tarea"} | ${ultimoEvento.fecha_evento || "Sin fecha"}`
                : "Sin eventos recientes del programador.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.actividad, ultimoEvento ? obtenerNivelEventoMonitor(ultimoEvento) : "info");
        if (actividadEventos) {
            actividadEventos.textContent = String(eventos.length);
        }
        if (actividadEventosDetalle) {
            actividadEventosDetalle.textContent = eventos.length
                ? "Eventos propios del programador visibles en este panel."
                : "Sin eventos recientes del programador.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.eventos, eventos.length ? "activo" : "info");
        if (actividadErrores) {
            actividadErrores.textContent = String(totalErrores);
        }
        if (actividadErroresDetalle) {
            actividadErroresDetalle.textContent = totalErrores > 0
                ? "Se detectaron errores recientes del programador."
                : "Sin errores recientes del programador.";
        }
        aplicarEstadoVisualPanel(tarjetasMonitor.errores, totalErrores > 0 ? "error" : "activo");
    };

    const renderizarConsolaMonitor = (consolaReciente = {}) => {
        const lineas = Array.isArray(consolaReciente.lineas) ? consolaReciente.lineas : [];
        if (badgeLineasMonitor) {
            badgeLineasMonitor.textContent = `${lineas.length} lineas`;
            badgeLineasMonitor.className = `badge ${consolaReciente.archivo_disponible ? "info" : "inactivo"}`;
        }
        if (consolaMonitor) {
            consolaMonitor.textContent = lineas.length
                ? lineas.join("\n")
                : (consolaReciente.mensaje || "Consola del worker no disponible.");
            consolaMonitor.scrollTop = consolaMonitor.scrollHeight;
        }
    };

    const renderizarMonitorWorker = (monitor) => {
        renderizarEstadoMonitor(monitor);
        renderizarAlertasMonitor(monitor?.alertas_operativas || []);
        renderizarActividadMonitor(monitor);
        renderizarConsolaMonitor(monitor?.consola_reciente || {});
        renderizarListaMonitor(eventosMonitor, monitor?.eventos_recientes || [], "eventos");
        if (actualizadoMonitor) {
            actualizadoMonitor.textContent = `Actualizado ${new Date().toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
        }
    };

    const cargarMonitorWorker = async (forzarToast = false) => {
        if (!panelLogs || !monitorUrl || monitorWorkerCargando) {
            return;
        }
        monitorWorkerCargando = true;
        actualizarIndicadorMonitor("Actualizando...", "info");
        try {
            const respuesta = await fetch(`${monitorUrl}?limit=${encodeURIComponent(obtenerLimiteMonitor())}`, {
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "fetch",
                },
            });

            if (!respuesta.ok) {
                const mensaje = respuesta.status === 403
                    ? "No tienes permisos para ver el monitor del worker."
                    : "No fue posible cargar el monitor del worker.";
                actualizarIndicadorMonitor("No se pudo actualizar", "error");
                renderizarAlertasMonitor([{ nivel: "error", mensaje }]);
                if (consolaMonitor) {
                    consolaMonitor.textContent = mensaje;
                }
                if (forzarToast) {
                    mostrarToast(mensaje, "error");
                }
                return;
            }

            const datos = await respuesta.json();
            renderizarMonitorWorker(datos);
            actualizarIndicadorMonitor("Vista actualizada", "info");
            if (forzarToast) {
                mostrarToast("Monitor del worker actualizado.", "info");
            }
        } catch (error) {
            const mensaje = "No fue posible consultar la API de monitoreo del worker.";
            actualizarIndicadorMonitor("No se pudo actualizar", "error");
            renderizarAlertasMonitor([{ nivel: "error", mensaje }]);
            if (consolaMonitor) {
                consolaMonitor.textContent = mensaje;
            }
            if (forzarToast) {
                mostrarToast(mensaje, "error");
            }
        } finally {
            monitorWorkerCargando = false;
        }
    };

    const detenerAutoRefreshWorker = () => {
        if (intervaloMonitorWorker) {
            clearInterval(intervaloMonitorWorker);
            intervaloMonitorWorker = null;
        }
        monitorWorkerPausado = true;
        if (botonPausaMonitor) {
            botonPausaMonitor.dataset.paused = "1";
            botonPausaMonitor.textContent = "Reanudar";
        }
        actualizarIndicadorMonitor("Actualizacion pausada", "advertencia");
    };

    const iniciarAutoRefreshWorker = () => {
        if (!panelLogs || intervaloMonitorWorker) {
            return;
        }
        monitorWorkerPausado = false;
        if (botonPausaMonitor) {
            botonPausaMonitor.dataset.paused = "0";
            botonPausaMonitor.textContent = "Pausar";
        }
        intervaloMonitorWorker = setInterval(() => {
            if (cuerpo.classList.contains("panel-logs-abierto")) {
                cargarMonitorWorker(false);
            }
        }, 5000);
    };

    const abrirPanelLogsWorker = () => {
        cuerpo.classList.add("panel-logs-abierto");
        restaurarAnchoPanelLogs();
        cargarMonitorWorker(false);
        iniciarAutoRefreshWorker();
    };

    const cerrarPanelLogsWorker = () => {
        cuerpo.classList.remove("panel-logs-abierto");
        detenerAutoRefreshWorker();
    };

    botonesLogs.forEach((boton) => {
        boton.addEventListener("click", () => {
            if (cuerpo.classList.contains("panel-logs-abierto")) {
                cerrarPanelLogsWorker();
                return;
            }
            abrirPanelLogsWorker();
        });
    });

    botonActualizarMonitor?.addEventListener("click", () => cargarMonitorWorker(true));

    botonPausaMonitor?.addEventListener("click", () => {
        if (intervaloMonitorWorker) {
            detenerAutoRefreshWorker();
            mostrarToast("Auto-refresh del monitor pausado.", "info");
            return;
        }
        iniciarAutoRefreshWorker();
        cargarMonitorWorker(false);
        mostrarToast("Auto-refresh del monitor reanudado.", "info");
    });

    selectorLimiteMonitor?.addEventListener("change", () => {
        if (cuerpo.classList.contains("panel-logs-abierto")) {
            cargarMonitorWorker(false);
        }
    });

    botonCopiarMonitor?.addEventListener("click", async () => {
        const texto = consolaMonitor?.textContent?.trim() || "";
        if (!texto) {
            mostrarToast("No hay registro visible para copiar.", "warning");
            return;
        }
        try {
            await navigator.clipboard.writeText(texto);
            mostrarToast("Registro visible copiado.", "success");
        } catch (error) {
            mostrarToast("No fue posible copiar el registro visible.", "error");
        }
    });

    if (agarreResizePanelLogs && panelLogs) {
        let arrastrando = false;

        const moverPanelLogs = (evento) => {
            if (!arrastrando || !esPanelLogsRedimensionable()) {
                return;
            }
            const ancho = window.innerWidth - evento.clientX;
            aplicarAnchoPanelLogs(ancho);
        };

        const detenerResizePanelLogs = () => {
            if (!arrastrando) {
                return;
            }
            arrastrando = false;
            cuerpo.classList.remove("panel-logs-redimensionando");
            document.removeEventListener("mousemove", moverPanelLogs);
            document.removeEventListener("mouseup", detenerResizePanelLogs);
        };

        agarreResizePanelLogs.addEventListener("mousedown", (evento) => {
            if (!esPanelLogsRedimensionable()) {
                return;
            }
            arrastrando = true;
            cuerpo.classList.add("panel-logs-redimensionando");
            document.addEventListener("mousemove", moverPanelLogs);
            document.addEventListener("mouseup", detenerResizePanelLogs);
            evento.preventDefault();
        });

        agarreResizePanelLogs.addEventListener("dblclick", () => {
            localStorage.removeItem("appSchedulerPanelLogsWidth");
            aplicarAnchoPanelLogs(540, false);
        });

        window.addEventListener("resize", () => {
            if (esPanelLogsRedimensionable()) {
                restaurarAnchoPanelLogs();
            } else {
                panelLogs.style.removeProperty("--panel-logs-width");
            }
        });
    }

    const abrirModalConfirmacion = (configuracion, formulario = null) => {
        if (!modalConfirmacion) {
            return;
        }

        formularioPendiente = formulario || configuracion.closest?.("form") || null;
        const dataset = configuracion.dataset || configuracion;
        accionConfirmadaPendiente = configuracion.onConfirm || null;
        modalConfirmar.disabled = false;
        const tipo = dataset.confirmType || "info";
        modalConfirmacion.dataset.tipo = tipo;
        modalTitulo.textContent = dataset.confirmTitle || "Confirmar accion";
        modalMensaje.textContent = dataset.confirmMessage || "Confirma si deseas continuar.";
        modalConfirmar.textContent = dataset.confirmOk || "Confirmar";
        modalCancelar.textContent = dataset.confirmCancel || "Cancelar";
        modalTipo.textContent = tipo.toUpperCase();
        modalIcono.textContent = { danger: "!", warning: "!", success: "OK", info: "i" }[tipo] || "i";
        if (modalResumen) {
            modalResumen.replaceChildren();
            modalResumen.classList.add("oculto");
            if (dataset.confirmSummaryNode) {
                modalResumen.appendChild(dataset.confirmSummaryNode);
                modalResumen.classList.remove("oculto");
            }
            if (dataset.confirmRequiresCheck === "1") {
                const contenedorCheck = document.createElement("label");
                contenedorCheck.className = "confirmacion-check";
                const check = document.createElement("input");
                check.type = "checkbox";
                check.addEventListener("change", () => {
                    modalConfirmar.disabled = !check.checked;
                });
                const texto = document.createElement("span");
                texto.textContent = dataset.confirmCheckLabel || "Entiendo y deseo continuar.";
                contenedorCheck.append(check, texto);
                modalResumen.appendChild(contenedorCheck);
                modalResumen.classList.remove("oculto");
                modalConfirmar.disabled = true;
            }
        }
        modalConfirmacion.classList.add("abierto");
        modalConfirmacion.setAttribute("aria-hidden", "false");
        cuerpo.classList.add("modal-abierto");
        modalCancelar.focus();
    };

    const cerrarModalConfirmacion = (mantenerEnvioConfirmado = false) => {
        if (!modalConfirmacion) {
            return;
        }

        modalConfirmacion.classList.remove("abierto");
        modalConfirmacion.setAttribute("aria-hidden", "true");
        cuerpo.classList.remove("modal-abierto");
        formularioPendiente = null;
        accionConfirmadaPendiente = null;
        modalConfirmar.disabled = false;
        if (modalResumen) {
            modalResumen.replaceChildren();
            modalResumen.classList.add("oculto");
        }
        if (!mantenerEnvioConfirmado) {
            envioConfirmado = false;
        }
    };

    const obtenerConfirmacionFormulario = (formulario) => {
        const dataset = formulario.dataset;
        if (dataset.confirmSummary === "tarea") {
            return obtenerConfirmacionTarea(formulario);
        }
        if (dataset.confirmSummary === "scheduler") {
            return obtenerConfirmacionScheduler(formulario);
        }

        if (dataset.formModo === "crear") {
            return dataset;
        }

        const selectorRolFormulario = formulario.querySelector("[data-rol-original]");
        const passwordFormulario = formulario.querySelector("[data-password-edicion='1']");
        const cambioRol = Boolean(
            selectorRolFormulario && selectorRolFormulario.value !== selectorRolFormulario.dataset.rolOriginal
        );
        const cambioPassword = Boolean(passwordFormulario && passwordFormulario.value.length > 0);

        if (cambioRol && cambioPassword) {
            return {
                confirmTitle: "Confirmar cambios criticos",
                confirmMessage: "Estas modificando el rol y la contrasena del usuario. Esto afectara sus permisos y credenciales de acceso. Deseas continuar?",
                confirmOk: "Si, guardar cambios",
                confirmCancel: "Cancelar",
                confirmType: "warning",
            };
        }

        if (cambioRol) {
            return {
                confirmTitle: "Confirmar cambio de rol",
                confirmMessage: "Estas modificando el rol del usuario. Esto puede cambiar sus permisos dentro del sistema. Deseas continuar?",
                confirmOk: "Si, cambiar rol",
                confirmCancel: "Cancelar",
                confirmType: "warning",
            };
        }

        if (cambioPassword) {
            return {
                confirmTitle: "Confirmar cambio de contrasena",
                confirmMessage: "Se actualizara la contrasena del usuario. Deseas continuar?",
                confirmOk: "Si, actualizar contrasena",
                confirmCancel: "Cancelar",
                confirmType: "warning",
            };
        }

        return dataset;
    };

    const crearResumenPapeleraMasiva = (elemento) => {
        const contenedor = document.createElement("div");
        contenedor.className = "resumen-tarea resumen-papelera-masiva";

        const seccion = document.createElement("section");
        const titulo = document.createElement("h3");
        titulo.textContent = "Resumen previo";
        const lista = document.createElement("dl");

        const agregarFila = (etiqueta, valor) => {
            const fila = document.createElement("div");
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");
            dt.textContent = etiqueta;
            dd.textContent = valor;
            fila.append(dt, dd);
            lista.appendChild(fila);
        };

        agregarFila("Total en Papelera", elemento.dataset.totalPapelera || "0");
        [
            ["Usuarios", "total-usuarios"],
            ["Clientes", "total-clientes"],
            ["Categorias", "total-categorias"],
            ["Tipos", "total-tipos"],
            ["Tareas", "total-tareas"],
            ["Scripts", "total-scripts"],
            ["Versiones de scripts", "total-scripts-versiones"],
        ].forEach(([etiqueta, atributo]) => {
            const valor = Number(elemento.getAttribute(`data-${atributo}`) || 0);
            if (valor > 0) {
                agregarFila(etiqueta, String(valor));
            }
        });

        seccion.append(titulo, lista);
        contenedor.appendChild(seccion);
        return contenedor;
    };

    const crearResumenLimpiezaEventos = (elemento) => {
        const formulario = elemento.closest("form");
        const datos = JSON.parse(formulario?.dataset.limpiezaPreview || "{}");
        const contenedor = document.createElement("div");
        contenedor.className = "resumen-tarea resumen-limpieza-eventos";

        const seccion = document.createElement("section");
        const titulo = document.createElement("h3");
        titulo.textContent = "Resumen de limpieza";
        const lista = document.createElement("dl");

        const agregarFila = (etiqueta, valor) => {
            const fila = document.createElement("div");
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");
            dt.textContent = etiqueta;
            dd.textContent = valor;
            fila.append(dt, dd);
            lista.appendChild(fila);
        };

        agregarFila("Periodo", `Mas antiguos que ${datos.dias || "-"} dias`);
        agregarFila("Fecha limite", datos.fecha_limite || "-");
        agregarFila("Total a eliminar", `${datos.total || 0} eventos`);
        agregarFila("Tabla afectada", "Solo scheduler_eventos");
        seccion.append(titulo, lista);
        contenedor.appendChild(seccion);

        const detalle = document.createElement("section");
        const tituloDetalle = document.createElement("h3");
        tituloDetalle.textContent = "Categorias seleccionadas";
        const listaDetalle = document.createElement("dl");
        (datos.detalle || []).forEach((item) => {
            const fila = document.createElement("div");
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");
            dt.textContent = item.nombre || item.clave || "-";
            dd.textContent = `${item.total || 0} eventos`;
            fila.append(dt, dd);
            listaDetalle.appendChild(fila);
        });
        detalle.append(tituloDetalle, listaDetalle);
        contenedor.appendChild(detalle);

        const advertencia = document.createElement("p");
        advertencia.className = "texto-ayuda";
        advertencia.textContent = "Esta accion no se puede deshacer desde la aplicacion. No elimina ejecuciones, logs, auditoria, heartbeat ni datos operativos.";
        contenedor.appendChild(advertencia);
        return contenedor;
    };

    const obtenerConfirmacionElemento = (elemento) => {
        if (elemento.dataset.confirmSummary === "papelera-masiva") {
            return {
                ...elemento.dataset,
                confirmSummaryNode: crearResumenPapeleraMasiva(elemento),
            };
        }
        if (elemento.dataset.confirmSummary === "limpieza-eventos") {
            return {
                ...elemento.dataset,
                confirmSummaryNode: crearResumenLimpiezaEventos(elemento),
            };
        }
        return elemento;
    };

    confirmables.forEach((elemento) => {
        elemento.addEventListener("click", (evento) => {
            evento.preventDefault();
            abrirModalConfirmacion(obtenerConfirmacionElemento(elemento), elemento.closest("form"));
        });
    });

    formulariosConfirmables.forEach((formulario) => {
        formulario.addEventListener("submit", (evento) => {
            if (envioConfirmado) {
                envioConfirmado = false;
                return;
            }

            evento.preventDefault();
            if (formulario.dataset.confirmSummary === "tarea" && !validarFormularioTarea(formulario)) {
                return;
            }
            if (formulario.dataset.confirmSummary === "scheduler" && !formulario.checkValidity()) {
                formulario.reportValidity();
                return;
            }
            if (formulario.dataset.confirmSummary === "scheduler" && !formularioSchedulerTieneCambios(formulario)) {
                mostrarToast("No hay cambios para guardar.", "info");
                return;
            }
            if (
                formulario.dataset.confirmSummary === "tarea" &&
                formulario.dataset.formModo === "editar" &&
                !formularioTareaTieneCambios(formulario)
            ) {
                mostrarToast("No hay cambios para guardar.", "info");
                return;
            }
            abrirModalConfirmacion(obtenerConfirmacionFormulario(formulario), formulario);
        });
    });

    if (modalCancelar) {
        modalCancelar.addEventListener("click", cerrarModalConfirmacion);
    }

    if (modalConfirmacion) {
        modalConfirmacion.addEventListener("click", (evento) => {
            if (evento.target === modalConfirmacion) {
                cerrarModalConfirmacion();
            }
        });
    }

    if (modalConfirmar) {
        modalConfirmar.addEventListener("click", () => {
            const formulario = formularioPendiente;
            if (formulario) {
                envioConfirmado = true;
                cerrarModalConfirmacion(true);
                formulario.requestSubmit();
                return;
            }
            const accion = accionConfirmadaPendiente;
            if (accion) {
                cerrarModalConfirmacion();
                accion();
                return;
            }
            cerrarModalConfirmacion();
        });
    }

    const tiempoAutoOcultarMailGraph = () => {
        const valor = Number(panelMailGraphSensible?.dataset.autoHideMs || 20000);
        return valor > 0 ? valor : 20000;
    };

    const detenerTemporizadoresMailGraph = () => {
        if (temporizadorMailGraphSensible) {
            clearTimeout(temporizadorMailGraphSensible);
            temporizadorMailGraphSensible = null;
        }
        if (intervaloMailGraphSensible) {
            clearInterval(intervaloMailGraphSensible);
            intervaloMailGraphSensible = null;
        }
    };

    const ocultarMailGraphSensible = (mensaje = "Campos sensibles ocultados automaticamente por seguridad.") => {
        detenerTemporizadoresMailGraph();
        camposMailGraphSensibles.forEach((campo) => {
            campo.value = "";
            campo.dataset.original = "";
            campo.disabled = true;
        });
        if (botonMailGraphRevelar) {
            botonMailGraphRevelar.disabled = false;
        }
        botonMailGraphOcultar?.classList.add("oculto");
        if (estadoMailGraphSensible) {
            estadoMailGraphSensible.textContent = mensaje;
        }
    };

    const iniciarAutoOcultamientoMailGraph = () => {
        detenerTemporizadoresMailGraph();
        const duracion = tiempoAutoOcultarMailGraph();
        const inicio = Date.now();
        const actualizarMensaje = () => {
            const restante = Math.max(0, Math.ceil((duracion - (Date.now() - inicio)) / 1000));
            if (estadoMailGraphSensible) {
                estadoMailGraphSensible.textContent = `Campos sensibles visibles temporalmente. Se ocultaran en ${restante} segundos.`;
            }
        };

        actualizarMensaje();
        intervaloMailGraphSensible = setInterval(actualizarMensaje, 1000);
        temporizadorMailGraphSensible = setTimeout(() => {
            ocultarMailGraphSensible("Los campos sensibles fueron ocultados automaticamente por seguridad. Si necesita continuar editando, vuelva a confirmar.");
        }, duracion);
    };

    const revelarMailGraphSensible = async () => {
        const url = panelMailGraphSensible?.dataset.revealUrl;
        if (!url) {
            return;
        }

        if (estadoMailGraphSensible) {
            estadoMailGraphSensible.textContent = "Cargando parametros sensibles...";
        }
        if (botonMailGraphRevelar) {
            botonMailGraphRevelar.disabled = true;
        }

        try {
            const respuesta = await fetch(url, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                },
            });
            const datos = await respuesta.json();
            if (!respuesta.ok || !datos.ok) {
                throw new Error(datos.mensaje || "No fue posible revelar parametros sensibles.");
            }

            camposMailGraphSensibles.forEach((campo) => {
                const clave = campo.dataset.mailGraphSensitive;
                campo.disabled = false;
                campo.value = datos.config?.[clave] || "";
                campo.dataset.original = campo.value;
            });
            if (estadoMailGraphSensible) {
                estadoMailGraphSensible.textContent = "Parametros sensibles visibles temporalmente.";
            }
            botonMailGraphOcultar?.classList.remove("oculto");
            iniciarAutoOcultamientoMailGraph();
        } catch (error) {
            detenerTemporizadoresMailGraph();
            if (estadoMailGraphSensible) {
                estadoMailGraphSensible.textContent = "No fue posible revelar parametros sensibles.";
            }
            if (botonMailGraphRevelar) {
                botonMailGraphRevelar.disabled = false;
            }
        }
    };

    if (botonMailGraphRevelar) {
        botonMailGraphRevelar.addEventListener("click", () => {
            abrirModalConfirmacion({
                dataset: {
                    confirmTitle: "Mostrar parametros sensibles",
                    confirmMessage: "Esta a punto de mostrar parametros sensibles de Microsoft Graph. Solo continue si necesita revisar o modificar esta configuracion.",
                    confirmOk: "Mostrar / editar",
                    confirmCancel: "Cancelar",
                    confirmType: "warning",
                },
                onConfirm: revelarMailGraphSensible,
            });
        });
    }

    if (botonMailGraphOcultar) {
        botonMailGraphOcultar.addEventListener("click", () => {
            ocultarMailGraphSensible("Campos sensibles ocultados manualmente por seguridad.");
        });
    }

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && modalConfirmacion?.classList.contains("abierto")) {
            cerrarModalConfirmacion();
        }
    });

    if (formularioLimpiezaEventos) {
        const botonPreview = formularioLimpiezaEventos.querySelector("[data-limpieza-preview-btn]");
        const botonSubmit = formularioLimpiezaEventos.querySelector("[data-limpieza-submit]");
        const botonTodas = formularioLimpiezaEventos.querySelector("[data-limpieza-todas]");
        const botonRuido = formularioLimpiezaEventos.querySelector("[data-limpieza-ruido]");
        const botonNinguna = formularioLimpiezaEventos.querySelector("[data-limpieza-ninguna]");
        const panelPreview = formularioLimpiezaEventos.querySelector("[data-limpieza-preview]");
        const previewTotal = formularioLimpiezaEventos.querySelector("[data-limpieza-preview-total]");
        const previewFecha = formularioLimpiezaEventos.querySelector("[data-limpieza-preview-fecha]");
        const previewDetalle = formularioLimpiezaEventos.querySelector("[data-limpieza-preview-detalle]");
        const resumenLimpieza = formularioLimpiezaEventos.querySelector("[data-limpieza-resumen]");
        const camposCategorias = formularioLimpiezaEventos.querySelectorAll("[name='categorias']");
        const camposLimpieza = formularioLimpiezaEventos.querySelectorAll("[name='dias_retencion'], [name='categorias']");

        const categoriasSeleccionadas = () =>
            Array.from(formularioLimpiezaEventos.querySelectorAll("[name='categorias']:checked"))
                .map((campo) => campo.value);

        const invalidarPreviewLimpieza = () => {
            formularioLimpiezaEventos.dataset.limpiezaPreview = "";
            botonSubmit.disabled = true;
            panelPreview?.classList.add("oculto");
            actualizarResumenLimpieza();
        };

        const actualizarResumenLimpieza = (datos = null) => {
            const cantidad = categoriasSeleccionadas().length;
            if (resumenLimpieza) {
                const estimado = datos ? `${datos.total || 0} eventos estimados` : "0 eventos estimados";
                let seleccion = "Sin categorias seleccionadas";
                if (cantidad === camposCategorias.length && cantidad > 0) {
                    seleccion = "Todas las categorias seleccionadas";
                } else if (cantidad === 1) {
                    seleccion = "1 categoria seleccionada";
                } else if (cantidad > 1) {
                    seleccion = `${cantidad} categorias seleccionadas`;
                }
                resumenLimpieza.textContent = `Seleccion actual: ${seleccion} - ${estimado}`;
            }
        };

        const marcarCategoriasLimpieza = (claves) => {
            const seleccion = new Set(claves);
            camposCategorias.forEach((campo) => {
                campo.checked = seleccion.has(campo.value);
            });
            invalidarPreviewLimpieza();
        };

        const renderizarPreviewLimpieza = (datos) => {
            formularioLimpiezaEventos.dataset.limpiezaPreview = JSON.stringify(datos);
            if (previewTotal) {
                const total = Number(datos.total || 0);
                const dias = datos.dias || formularioLimpiezaEventos.querySelector("[name='dias_retencion']")?.value || "-";
                previewTotal.textContent = total > 0
                    ? `Se eliminaran ${total} eventos mas antiguos que ${dias} dias.`
                    : "No hay eventos que coincidan con esta seleccion.";
            }
            if (previewFecha) {
                previewFecha.textContent = `Fecha limite: ${datos.fecha_limite || "-"}`;
            }
            if (previewDetalle) {
                previewDetalle.replaceChildren();
                (datos.detalle || []).forEach((item) => {
                    const fila = document.createElement("li");
                    const categoria = document.createElement("span");
                    const total = document.createElement("strong");
                    categoria.textContent = item.nombre || item.clave || "-";
                    total.textContent = `${item.total || 0} eventos`;
                    fila.append(categoria, total);
                    previewDetalle.appendChild(fila);
                });
            }
            panelPreview?.classList.remove("oculto");
            botonSubmit.disabled = Number(datos.total || 0) <= 0;
            actualizarResumenLimpieza(datos);
        };

        camposLimpieza.forEach((campo) => {
            campo.addEventListener("change", invalidarPreviewLimpieza);
        });

        botonTodas?.addEventListener("click", () => {
            marcarCategoriasLimpieza(Array.from(camposCategorias).map((campo) => campo.value));
        });

        botonRuido?.addEventListener("click", () => {
            marcarCategoriasLimpieza(
                Array.from(camposCategorias)
                    .filter((campo) => campo.dataset.ruidoOperativo === "1")
                    .map((campo) => campo.value)
            );
        });

        botonNinguna?.addEventListener("click", () => {
            marcarCategoriasLimpieza([]);
        });

        botonPreview?.addEventListener("click", async () => {
            const categorias = categoriasSeleccionadas();
            if (categorias.length === 0) {
                mostrarToast("Selecciona al menos una categoria para previsualizar.", "warning");
                invalidarPreviewLimpieza();
                return;
            }
            botonPreview.disabled = true;
            try {
                const respuesta = await fetch(formularioLimpiezaEventos.dataset.previewUrl, {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                        "X-Requested-With": "fetch",
                    },
                    body: JSON.stringify({
                        dias_retencion: formularioLimpiezaEventos.querySelector("[name='dias_retencion']")?.value,
                        categorias,
                    }),
                });
                const datos = await respuesta.json();
                if (!respuesta.ok || !datos.ok) {
                    mostrarToast(datos.mensaje || "No fue posible previsualizar la limpieza.", "error");
                    invalidarPreviewLimpieza();
                    return;
                }
                renderizarPreviewLimpieza(datos);
                mostrarToast("Previsualizacion de limpieza actualizada.", "info");
            } catch (error) {
                mostrarToast("No fue posible previsualizar la limpieza.", "error");
                invalidarPreviewLimpieza();
            } finally {
                botonPreview.disabled = false;
            }
        });

        formularioLimpiezaEventos.addEventListener("submit", (evento) => {
            if (envioConfirmado) {
                return;
            }
            if (!formularioLimpiezaEventos.dataset.limpiezaPreview || botonSubmit.disabled) {
                evento.preventDefault();
                mostrarToast("Previsualiza la limpieza antes de continuar.", "warning");
            }
        });

        actualizarResumenLimpieza();
    }

    if (historialEventos) {
        const cargarHistorialEventos = async (url, actualizarUrl = true) => {
            historialEventos.classList.add("cargando");
            try {
                const respuesta = await fetch(url, {
                    headers: {
                        Accept: "text/html",
                        "X-Requested-With": "fetch",
                    },
                });
                if (!respuesta.ok) {
                    throw new Error("Respuesta no valida");
                }
                historialEventos.innerHTML = await respuesta.text();
                if (actualizarUrl) {
                    window.history.pushState({ eventosSchedulerUrl: url }, "", url);
                }
            } catch (error) {
                mostrarToast("No fue posible actualizar la paginacion de eventos.", "error");
            } finally {
                historialEventos.classList.remove("cargando");
            }
        };

        historialEventos.addEventListener("click", (evento) => {
            const enlace = evento.target.closest("[data-eventos-paginacion] a");
            if (!enlace || enlace.classList.contains("deshabilitado")) {
                return;
            }
            evento.preventDefault();
            cargarHistorialEventos(enlace.href);
        });

        window.addEventListener("popstate", () => {
            if (window.location.pathname.endsWith("/scheduler/eventos")) {
                cargarHistorialEventos(window.location.href, false);
            }
        });
    }

    if (selectorRol && alertaRol) {
        selectorRol.addEventListener("change", () => {
            const cambioRol = selectorRol.value !== selectorRol.dataset.rolOriginal;
            alertaRol.classList.toggle("oculto", !cambioRol);
        });
    }

    if (passwordEdicion && alertaPassword) {
        passwordEdicion.addEventListener("input", () => {
            alertaPassword.classList.toggle("oculto", passwordEdicion.value.length === 0);
        });
    }

    if (consolaEjecucion?.dataset.logUrl) {
        const estadosFinales = new Set(["EXITOSA", "ERROR", "DETENIDA_MANUALMENTE", "CANCELADA"]);
        let estadoVisualActual = estadoEjecucion?.textContent?.trim() || "";
        let toastFinalMostrado = estadosFinales.has(estadoVisualActual);

        const claseBadgeEstado = (estado) => {
            if (estado === "EXITOSA") {
                return "activo";
            }
            if (estado === "ERROR") {
                return "error";
            }
            if (estado === "EN_EJECUCION" || estado === "PENDIENTE" || estado === "DETENIDA_MANUALMENTE") {
                return "advertencia";
            }
            return "inactivo";
        };

        const mensajeToastFinal = (estado) => {
            const mensajes = {
                EXITOSA: ["Ejecucion finalizada correctamente. La tarea termino con estado EXITOSA.", "success"],
                ERROR: ["La ejecucion termino con error. Revisa el log para mas detalles.", "error"],
                DETENIDA_MANUALMENTE: ["Ejecucion detenida. La ejecucion fue detenida manualmente.", "warning"],
            };
            return mensajes[estado] || [`Ejecucion finalizada con estado ${estado}.`, "info"];
        };

        const actualizarEstadoVisual = (datos, permitirToast = true) => {
            const estado = datos.estado_actual || datos.estado || "";
            const esFinal = Boolean(datos.estado_es_final ?? datos.es_final);
            if (!estado) {
                return esFinal;
            }

            if (estadoEjecucion) {
                estadoEjecucion.textContent = estado;
            }
            if (badgeEjecucion) {
                badgeEjecucion.textContent = estado;
                badgeEjecucion.className = `badge ${claseBadgeEstado(estado)}`;
            }
            if (terminoEjecucion) {
                terminoEjecucion.textContent = datos.fecha_hora_termino || datos.fecha_hora_fin || "-";
            }
            if (duracionEjecucion) {
                duracionEjecucion.textContent = datos.duracion_segundos ?? "-";
            }
            if (codigoEjecucion) {
                codigoEjecucion.textContent = datos.codigo_salida ?? "-";
            }
            if (indicadorEjecucion) {
                indicadorEjecucion.textContent = esFinal ? "Finalizada" : estado === "PENDIENTE" ? "Pendiente" : "En ejecucion...";
                indicadorEjecucion.className = `badge ${esFinal ? claseBadgeEstado(estado) : "advertencia"}`;
            }
            if (accionesEnCursoEjecucion) {
                accionesEnCursoEjecucion.classList.toggle("oculto", esFinal);
                accionesEnCursoEjecucion.querySelectorAll("button").forEach((boton) => {
                    boton.disabled = esFinal;
                });
            }

            if (permitirToast && esFinal && !toastFinalMostrado && estadoVisualActual !== estado) {
                const [mensaje, tipo] = mensajeToastFinal(estado);
                mostrarToast(mensaje, tipo);
                toastFinalMostrado = true;
            }
            estadoVisualActual = estado;
            return esFinal;
        };

        const actualizarConsola = async () => {
            try {
                const respuesta = await fetch(consolaEjecucion.dataset.logUrl, {
                    headers: { Accept: "application/json" },
                });
                if (!respuesta.ok) {
                    return true;
                }
                const datos = await respuesta.json();
                consolaEjecucion.textContent = datos.log || "";
                consolaEjecucion.scrollTop = consolaEjecucion.scrollHeight;
                return actualizarEstadoVisual(datos);
            } catch (error) {
                return false;
            }
        };

        const intervalo = setInterval(async () => {
            const finalizada = await actualizarConsola();
            if (finalizada) {
                clearInterval(intervalo);
            }
        }, 3000);
        actualizarConsola().then((finalizada) => {
            if (finalizada) {
                clearInterval(intervalo);
            }
        });

        if (formularioDetenerEjecucion) {
            formularioDetenerEjecucion.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                const boton = formularioDetenerEjecucion.querySelector("button[type='submit']");
                if (boton) {
                    boton.disabled = true;
                }
                try {
                    const respuesta = await fetch(formularioDetenerEjecucion.action, {
                        method: "POST",
                        headers: {
                            Accept: "application/json",
                            "X-Requested-With": "fetch",
                        },
                    });
                    const datos = await respuesta.json();
                    if (datos.estado) {
                        actualizarEstadoVisual(datos.estado, false);
                    }
                    mostrarToast(datos.mensaje || "Solicitud de detencion procesada.", respuesta.ok ? "warning" : "error");
                    await actualizarConsola();
                } catch (error) {
                    mostrarToast("No fue posible detener la ejecucion.", "error");
                    if (boton) {
                        boton.disabled = false;
                    }
                }
            });
        }

        if (formularioVerificarEjecucion) {
            formularioVerificarEjecucion.addEventListener("submit", async (evento) => {
                evento.preventDefault();
                const boton = formularioVerificarEjecucion.querySelector("button[type='submit']");
                if (boton) {
                    boton.disabled = true;
                }
                try {
                    const respuesta = await fetch(formularioVerificarEjecucion.action, {
                        method: "POST",
                        headers: {
                            Accept: "application/json",
                            "X-Requested-With": "fetch",
                        },
                    });
                    const datos = await respuesta.json();
                    if (datos.estado) {
                        actualizarEstadoVisual(datos.estado, false);
                    }
                    mostrarToast(datos.mensaje || "Verificacion procesada.", respuesta.ok ? "info" : "error");
                    await actualizarConsola();
                } catch (error) {
                    mostrarToast("No fue posible verificar la ejecucion.", "error");
                } finally {
                    if (boton && !accionesEnCursoEjecucion?.classList.contains("oculto")) {
                        boton.disabled = false;
                    }
                }
            });
        }
    }

    const alternarGrupo = (formulario, selector, visible) => {
        formulario.querySelectorAll(selector).forEach((elemento) => {
            elemento.classList.toggle("oculto", !visible);
        });
    };

    const valorCampo = (formulario, selector) => formulario.querySelector(selector)?.value?.trim() || "";

    const normalizarTexto = (valor) => (valor || "").trim().replace(/\s+/g, " ");

    const textoSeleccionado = (formulario, selector) => {
        const campo = formulario.querySelector(selector);
        return campo?.selectedOptions?.[0]?.textContent?.trim() || "";
    };

    const normalizarEtiqueta = (valor) => {
        const etiquetas = {
            MANUAL: "Manual",
            DIARIA: "Diaria",
            SEMANAL: "Semanal",
            MENSUAL: "Mensual",
            FECHA_ESPECIFICA: "Fecha especifica",
            UNA_VEZ: "Una vez",
            INTERVALO: "Intervalo",
        };
        return etiquetas[valor] || valor || "-";
    };

    const diasSeleccionados = (formulario) => {
        const nombres = {
            LUNES: "lunes",
            MARTES: "martes",
            MIERCOLES: "miercoles",
            JUEVES: "jueves",
            VIERNES: "viernes",
            SABADO: "sabado",
            DOMINGO: "domingo",
        };
        return Array.from(formulario.querySelectorAll("input[name='dias_semana']:checked"))
            .map((campo) => nombres[campo.value] || campo.value.toLowerCase());
    };

    const codigosDiasSeleccionados = (formulario) => Array.from(formulario.querySelectorAll("input[name='dias_semana']:checked"))
        .map((campo) => campo.value)
        .sort();

    const unirLista = (valores) => {
        if (valores.length <= 1) {
            return valores[0] || "";
        }
        return `${valores.slice(0, -1).join(", ")} y ${valores[valores.length - 1]}`;
    };

    const resumirProgramacionFormulario = (formulario) => {
        const tipo = valorCampo(formulario, "[data-tipo-programacion]") || "MANUAL";
        const modo = valorCampo(formulario, "[data-modo-programacion]") || "UNA_VEZ";
        const hora = valorCampo(formulario, "[name='hora_ejecucion']");
        const intervalo = valorCampo(formulario, "[name='intervalo_minutos']");
        const inicio = valorCampo(formulario, "[name='hora_inicio_intervalo']");
        const fin = valorCampo(formulario, "[name='hora_fin_intervalo']");
        const diaMes = valorCampo(formulario, "[name='dia_mes']");
        const fecha = valorCampo(formulario, "[name='fecha_especifica']");
        const dias = unirLista(diasSeleccionados(formulario));

        if (tipo === "MANUAL") {
            return "Manual";
        }

        const prefijos = {
            DIARIA: "Diaria",
            SEMANAL: `Semanal ${dias}`,
            MENSUAL: `Mensual dia ${diaMes}`,
            FECHA_ESPECIFICA: `Fecha especifica ${fecha}`,
        };
        const prefijo = prefijos[tipo] || normalizarEtiqueta(tipo);

        if (modo === "INTERVALO") {
            return `${prefijo} cada ${intervalo} minutos entre ${inicio} y ${fin}`;
        }
        return `${prefijo} a las ${hora}`;
    };

    const obtenerEstadoTareaFormulario = (formulario) => {
        const tipo = valorCampo(formulario, "[data-tipo-programacion]") || "MANUAL";
        const modo = tipo === "MANUAL" ? "" : valorCampo(formulario, "[data-modo-programacion]");
        return {
            nombre_tarea: normalizarTexto(valorCampo(formulario, "[name='nombre_tarea']")),
            descripcion: normalizarTexto(valorCampo(formulario, "[name='descripcion']")),
            id_cliente: valorCampo(formulario, "[name='id_cliente']"),
            id_categoria: valorCampo(formulario, "[name='id_categoria']"),
            id_tipo: valorCampo(formulario, "[name='id_tipo']"),
            observacion_tecnica: normalizarTexto(valorCampo(formulario, "[name='observacion_tecnica']")),
            activo: Boolean(formulario.querySelector("[name='activo']")?.checked),
            tipo_programacion: tipo,
            modo_ejecucion_dia: modo,
            hora_ejecucion: modo === "UNA_VEZ" ? valorCampo(formulario, "[name='hora_ejecucion']") : "",
            dias_semana: tipo === "SEMANAL" ? codigosDiasSeleccionados(formulario) : [],
            dia_mes: tipo === "MENSUAL" ? valorCampo(formulario, "[name='dia_mes']") : "",
            fecha_especifica: tipo === "FECHA_ESPECIFICA" ? valorCampo(formulario, "[name='fecha_especifica']") : "",
            intervalo_minutos: modo === "INTERVALO" ? valorCampo(formulario, "[name='intervalo_minutos']") : "",
            hora_inicio_intervalo: modo === "INTERVALO" ? valorCampo(formulario, "[name='hora_inicio_intervalo']") : "",
            hora_fin_intervalo: modo === "INTERVALO" ? valorCampo(formulario, "[name='hora_fin_intervalo']") : "",
            ejecutar_en_feriados: tipo === "MANUAL" ? false : Boolean(formulario.querySelector("[name='ejecutar_en_feriados']")?.checked),
        };
    };

    const formularioTareaTieneCambios = (formulario) => {
        if (!formulario.dataset.estadoOriginal) {
            return true;
        }
        return JSON.stringify(obtenerEstadoTareaFormulario(formulario)) !== formulario.dataset.estadoOriginal;
    };

    const mostrarToast = (mensaje, tipo = "info") => {
        if (!toastStack) {
            return;
        }

        const toast = document.createElement("div");
        const icono = document.createElement("span");
        const texto = document.createElement("p");
        const cerrar = document.createElement("button");
        toast.className = `toast-sistema ${tipo}`;
        toast.setAttribute("role", "status");
        icono.className = "toast-icono";
        icono.textContent = { success: "OK", error: "!", warning: "!", info: "i" }[tipo] || "i";
        texto.textContent = mensaje;
        cerrar.type = "button";
        cerrar.className = "toast-cerrar";
        cerrar.setAttribute("aria-label", "Cerrar notificacion");
        cerrar.textContent = "x";
        toast.append(icono, texto, cerrar);
        toastStack.appendChild(toast);

        requestAnimationFrame(() => toast.classList.add("visible"));

        const cerrarToast = () => {
            toast.classList.remove("visible");
            toast.addEventListener("transitionend", () => toast.remove(), { once: true });
        };
        cerrar.addEventListener("click", cerrarToast);
        setTimeout(cerrarToast, 3200);
    };

    const emailBasicoValido = (email) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(String(email || "").trim());

    const crearSelectCanalNotificacion = (valor = "TO") => {
        const select = document.createElement("select");
        select.dataset.destinatarioCampo = "canal";
        ["TO", "CC", "BCC"].forEach((canal) => {
            const opcion = document.createElement("option");
            opcion.value = canal;
            opcion.textContent = canal;
            opcion.selected = canal === valor;
            select.appendChild(opcion);
        });
        return select;
    };

    const crearFilaDestinatario = (tipo, datos = {}) => {
        const fila = document.createElement("tr");
        fila.dataset.tipoDestinatario = tipo;

        const celdaEmail = document.createElement("td");
        const email = document.createElement("input");
        email.type = "email";
        email.placeholder = "correo@empresa.cl";
        email.value = datos.email || "";
        email.dataset.destinatarioCampo = "email";
        celdaEmail.appendChild(email);

        const celdaNombre = document.createElement("td");
        const nombre = document.createElement("input");
        nombre.type = "text";
        nombre.placeholder = "Opcional";
        nombre.value = datos.nombre || "";
        nombre.dataset.destinatarioCampo = "nombre";
        celdaNombre.appendChild(nombre);

        const celdaCanal = document.createElement("td");
        celdaCanal.appendChild(crearSelectCanalNotificacion(datos.canal || "TO"));

        const celdaAcciones = document.createElement("td");
        const quitar = document.createElement("button");
        quitar.type = "button";
        quitar.className = "btn secundario compacto";
        quitar.textContent = "Quitar";
        quitar.addEventListener("click", () => fila.remove());
        celdaAcciones.appendChild(quitar);

        fila.append(celdaEmail, celdaNombre, celdaCanal, celdaAcciones);
        return fila;
    };

    const destinatariosNotificaciones = (panel, tipo) =>
        Array.from(panel.querySelectorAll(`[data-destinatarios-lista='${tipo}'] tr`)).map((fila) => ({
            tipo_destinatario: tipo,
            canal: fila.querySelector("[data-destinatario-campo='canal']")?.value || "TO",
            email: normalizarTexto(fila.querySelector("[data-destinatario-campo='email']")?.value || "").toLowerCase(),
            nombre: normalizarTexto(fila.querySelector("[data-destinatario-campo='nombre']")?.value || "") || null,
        })).filter((item) => item.email || item.nombre);

    const obtenerPayloadNotificaciones = (panel) => ({
        enviar_evidencia: Boolean(panel.querySelector("[data-notif-campo='enviar_evidencia']")?.checked),
        plantilla_evidencia: "STDOUT_V1",
        asunto_personalizado: normalizarTexto(panel.querySelector("[data-notif-campo='asunto_personalizado']")?.value || "") || null,
        usar_asunto_sugerido_script: Boolean(panel.querySelector("[data-notif-campo='usar_asunto_sugerido_script']")?.checked),
        adjuntar_archivos_declarados: Boolean(panel.querySelector("[data-notif-campo='adjuntar_archivos_declarados']")?.checked),
        adjuntar_log_tecnico: Boolean(panel.querySelector("[data-notif-campo='adjuntar_log_tecnico']")?.checked),
        alerta_error_activa: Boolean(panel.querySelector("[data-notif-campo='alerta_error_activa']")?.checked),
        usar_alerta_global: Boolean(panel.querySelector("[data-notif-campo='usar_alerta_global']")?.checked),
        destinatarios: [
            ...destinatariosNotificaciones(panel, "EVIDENCIA"),
            ...destinatariosNotificaciones(panel, "ALERTA"),
        ],
    });

    const tieneDestinatarioTo = (destinatarios, tipo) =>
        destinatarios.some((item) => item.tipo_destinatario === tipo && item.canal === "TO" && emailBasicoValido(item.email));

    const validarPayloadNotificaciones = (payload) => {
        const errores = [];
        payload.destinatarios.forEach((item) => {
            if (!item.email || !emailBasicoValido(item.email)) {
                errores.push("Ingresa emails validos para los destinatarios.");
            }
        });
        if (payload.enviar_evidencia && !tieneDestinatarioTo(payload.destinatarios, "EVIDENCIA")) {
            errores.push("Para enviar evidencia agrega al menos un destinatario EVIDENCIA en canal TO.");
        }
        if (payload.alerta_error_activa && !payload.usar_alerta_global && !tieneDestinatarioTo(payload.destinatarios, "ALERTA")) {
            errores.push("Si no usas alerta global agrega al menos un destinatario ALERTA en canal TO.");
        }
        return [...new Set(errores)];
    };

    const limpiarDestinatariosNotificaciones = (panel) => {
        panel.querySelectorAll("[data-destinatarios-lista]").forEach((lista) => lista.replaceChildren());
    };

    const renderizarConfigNotificaciones = (panel, config = {}) => {
        const defaults = {
            enviar_evidencia: false,
            usar_asunto_sugerido_script: true,
            asunto_personalizado: "",
            adjuntar_archivos_declarados: true,
            adjuntar_log_tecnico: false,
            alerta_error_activa: true,
            usar_alerta_global: true,
            destinatarios: [],
        };
        const datos = { ...defaults, ...config };
        Object.entries(datos).forEach(([clave, valor]) => {
            const campo = panel.querySelector(`[data-notif-campo='${clave}']`);
            if (!campo) {
                return;
            }
            if (campo.type === "checkbox") {
                campo.checked = Boolean(valor);
            } else {
                campo.value = valor || "";
            }
        });

        limpiarDestinatariosNotificaciones(panel);
        (datos.destinatarios || []).forEach((destinatario) => {
            const tipo = destinatario.tipo_destinatario === "ALERTA" ? "ALERTA" : "EVIDENCIA";
            panel.querySelector(`[data-destinatarios-lista='${tipo}']`)?.appendChild(crearFilaDestinatario(tipo, destinatario));
        });
        actualizarEstadoAlertaNotificaciones(panel);
    };

    const actualizarEstadoAlertaNotificaciones = (panel) => {
        const usarGlobal = Boolean(panel.querySelector("[data-notif-campo='usar_alerta_global']")?.checked);
        const grupoAlerta = panel.querySelector("[data-destinatarios-grupo='ALERTA']");
        grupoAlerta?.classList.toggle("notificaciones-destinatarios-atenuado", usarGlobal);
    };

    const mensajeErroresApi = (datos) => {
        if (Array.isArray(datos?.errores) && datos.errores.length) {
            return datos.errores.join(" ");
        }
        return datos?.mensaje || "No fue posible completar la accion.";
    };

    const leerRespuestaJsonNotificaciones = async (respuesta) => {
        const contentType = respuesta.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
            return { ok: false, mensaje: "La sesion puede haber expirado o la API no respondio JSON." };
        }
        return respuesta.json();
    };

    const renderizarSoporteEvidencia = (panel, datos = {}) => {
        panel.dataset.evidenciaSoportada = datos.soporta_evidencia ? "1" : "0";
        const contenedor = panel.querySelector("[data-evidencia-soporte-panel]");
        const texto = panel.querySelector("[data-evidencia-soporte-texto]");
        const badge = panel.querySelector("[data-evidencia-soporte-badge]");
        const lista = panel.querySelector("[data-evidencia-soporte-errores]");
        if (!contenedor || !texto || !badge || !lista) {
            return;
        }
        lista.replaceChildren();
        contenedor.classList.toggle("info", Boolean(datos.soporta_evidencia));
        contenedor.classList.toggle("advertencia", !datos.soporta_evidencia);
        badge.className = `badge ${datos.soporta_evidencia ? "activo" : "advertencia"}`;
        badge.textContent = datos.soporta_evidencia ? "Compatible" : "No compatible";
        texto.textContent = datos.soporta_evidencia
            ? "Script compatible con evidencia stdout."
            : "El script actual no declara soporte de evidencia.";
        (datos.errores || []).forEach((error) => {
            const item = document.createElement("li");
            item.textContent = error;
            lista.appendChild(item);
        });
    };

    const validarSoporteEvidenciaUi = async (panel) => {
        if (!panel.dataset.urlValidarEvidencia) {
            return;
        }
        try {
            const respuesta = await fetch(panel.dataset.urlValidarEvidencia, { headers: { Accept: "application/json" } });
            const datos = await leerRespuestaJsonNotificaciones(respuesta);
            if (!respuesta.ok || !datos.ok) {
                throw new Error(datos.mensaje || "No fue posible validar evidencia.");
            }
            renderizarSoporteEvidencia(panel, datos);
        } catch (error) {
            renderizarSoporteEvidencia(panel, {
                soporta_evidencia: false,
                errores: ["No fue posible validar el soporte de evidencia del script."],
            });
        }
    };

    const inicializarNotificacionesTarea = (panel) => {
        if (!panel) {
            return;
        }
        const estado = panel.querySelector("[data-notificaciones-estado]");
        const botonGuardar = panel.querySelector("[data-notificaciones-guardar]");
        const botonDesactivar = panel.querySelector("[data-notificaciones-desactivar]");

        panel.querySelectorAll("[data-agregar-destinatario]").forEach((boton) => {
            boton.addEventListener("click", () => {
                const tipo = boton.dataset.agregarDestinatario;
                panel.querySelector(`[data-destinatarios-lista='${tipo}']`)?.appendChild(crearFilaDestinatario(tipo));
            });
        });

        panel.querySelector("[data-notif-campo='usar_alerta_global']")?.addEventListener("change", () => {
            actualizarEstadoAlertaNotificaciones(panel);
        });

        panel.querySelector("[data-notif-campo='enviar_evidencia']")?.addEventListener("change", (evento) => {
            if (evento.target.checked && panel.dataset.evidenciaSoportada === "0") {
                evento.target.checked = false;
                mostrarToast("No se puede activar Enviar evidencia. El script asociado no contiene la declaracion y delimitadores requeridos por el contrato stdout.", "warning");
            }
        });

        const setEstado = (mensaje) => {
            if (estado) {
                estado.textContent = mensaje;
            }
        };

        const cargar = async () => {
            setEstado("Cargando configuracion...");
            try {
                const respuesta = await fetch(panel.dataset.urlObtener, { headers: { Accept: "application/json" } });
                const datos = await leerRespuestaJsonNotificaciones(respuesta);
                if (!respuesta.ok || !datos.ok) {
                    throw new Error(mensajeErroresApi(datos));
                }
                renderizarConfigNotificaciones(panel, datos.config);
                setEstado("Configuracion cargada.");
            } catch (error) {
                setEstado("No fue posible cargar la configuracion.");
                mostrarToast(error.message || "No fue posible cargar notificaciones.", "error");
            }
        };

        botonGuardar?.addEventListener("click", async () => {
            const payload = obtenerPayloadNotificaciones(panel);
            const errores = validarPayloadNotificaciones(payload);
            if (errores.length) {
                mostrarToast(errores[0], "warning");
                return;
            }
            if (payload.enviar_evidencia && panel.dataset.evidenciaSoportada !== "1") {
                mostrarToast("No se puede activar Enviar evidencia. El script asociado no contiene la declaracion y delimitadores requeridos por el contrato stdout.", "warning");
                return;
            }
            botonGuardar.disabled = true;
            try {
                const respuesta = await fetch(panel.dataset.urlGuardar, {
                    method: "PUT",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                        "X-Requested-With": "fetch",
                    },
                    body: JSON.stringify(payload),
                });
                const datos = await leerRespuestaJsonNotificaciones(respuesta);
                if (!respuesta.ok || !datos.ok) {
                    throw new Error(mensajeErroresApi(datos));
                }
                renderizarConfigNotificaciones(panel, datos.config);
                setEstado("Configuracion guardada.");
                mostrarToast("Configuracion de notificaciones guardada.", "success");
            } catch (error) {
                mostrarToast(error.message || "No fue posible guardar notificaciones.", "error");
            } finally {
                botonGuardar.disabled = false;
            }
        });

        botonDesactivar?.addEventListener("click", async () => {
            botonDesactivar.disabled = true;
            try {
                const respuesta = await fetch(panel.dataset.urlDesactivar, {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                        "X-Requested-With": "fetch",
                    },
                });
                const datos = await leerRespuestaJsonNotificaciones(respuesta);
                if (!respuesta.ok || !datos.ok) {
                    throw new Error(mensajeErroresApi(datos));
                }
                await cargar();
                mostrarToast("Configuracion de notificaciones desactivada.", "success");
            } catch (error) {
                mostrarToast(error.message || "No fue posible desactivar notificaciones.", "error");
            } finally {
                botonDesactivar.disabled = false;
            }
        });

        cargar();
        validarSoporteEvidenciaUi(panel);
    };

    const limpiarValidezTarea = (formulario) => {
        formulario.querySelectorAll("input, select, textarea").forEach((campo) => campo.setCustomValidity(""));
    };

    const marcarInvalido = (campo, mensaje) => {
        if (!campo) {
            return false;
        }
        campo.setCustomValidity(mensaje);
        campo.reportValidity();
        return false;
    };

    const validarFormularioTarea = (formulario) => {
        limpiarValidezTarea(formulario);
        const tipo = valorCampo(formulario, "[data-tipo-programacion]") || "MANUAL";
        const modo = valorCampo(formulario, "[data-modo-programacion]") || "UNA_VEZ";
        const tipoCampo = formulario.querySelector("[data-tipo-programacion]");
        const modoCampo = formulario.querySelector("[data-modo-programacion]");

        if (!formulario.checkValidity()) {
            formulario.reportValidity();
            return false;
        }

        if (tipo === "MANUAL") {
            return true;
        }

        if (!["UNA_VEZ", "INTERVALO"].includes(modo)) {
            return marcarInvalido(modoCampo, "Selecciona un modo de ejecucion valido.");
        }

        if (tipo === "SEMANAL" && diasSeleccionados(formulario).length === 0) {
            return marcarInvalido(tipoCampo, "Selecciona al menos un dia para la programacion semanal.");
        }

        if (tipo === "MENSUAL") {
            const diaMes = Number(valorCampo(formulario, "[name='dia_mes']"));
            if (!diaMes || diaMes < 1 || diaMes > 31) {
                return marcarInvalido(formulario.querySelector("[name='dia_mes']"), "Ingresa un dia del mes entre 1 y 31.");
            }
        }

        if (tipo === "FECHA_ESPECIFICA" && !valorCampo(formulario, "[name='fecha_especifica']")) {
            return marcarInvalido(formulario.querySelector("[name='fecha_especifica']"), "Ingresa una fecha especifica.");
        }

        if (modo === "UNA_VEZ" && !valorCampo(formulario, "[name='hora_ejecucion']")) {
            return marcarInvalido(formulario.querySelector("[name='hora_ejecucion']"), "Ingresa la hora de ejecucion.");
        }

        if (modo === "INTERVALO") {
            const intervalo = Number(valorCampo(formulario, "[name='intervalo_minutos']"));
            const inicio = valorCampo(formulario, "[name='hora_inicio_intervalo']");
            const fin = valorCampo(formulario, "[name='hora_fin_intervalo']");
            if (!intervalo || intervalo <= 0) {
                return marcarInvalido(formulario.querySelector("[name='intervalo_minutos']"), "Ingresa un intervalo mayor a 0.");
            }
            if (!inicio) {
                return marcarInvalido(formulario.querySelector("[name='hora_inicio_intervalo']"), "Ingresa la hora inicio del intervalo.");
            }
            if (!fin) {
                return marcarInvalido(formulario.querySelector("[name='hora_fin_intervalo']"), "Ingresa la hora fin del intervalo.");
            }
            if (inicio >= fin) {
                return marcarInvalido(formulario.querySelector("[name='hora_inicio_intervalo']"), "La hora inicio debe ser menor que la hora fin.");
            }
        }

        return true;
    };

    const agregarFilaResumen = (lista, etiqueta, valor) => {
        if (!valor) {
            return;
        }
        const fila = document.createElement("div");
        const titulo = document.createElement("dt");
        const contenido = document.createElement("dd");
        titulo.textContent = etiqueta;
        contenido.textContent = valor;
        fila.append(titulo, contenido);
        lista.appendChild(fila);
    };

    const crearSeccionResumen = (tituloSeccion, filas) => {
        const seccion = document.createElement("section");
        const titulo = document.createElement("h3");
        const lista = document.createElement("dl");
        titulo.textContent = tituloSeccion;
        filas.forEach(([etiqueta, valor]) => agregarFilaResumen(lista, etiqueta, valor));
        seccion.append(titulo, lista);
        return seccion;
    };

    const crearResumenTarea = (formulario) => {
        const resumen = document.createElement("div");
        resumen.className = "resumen-tarea";
        const tipo = valorCampo(formulario, "[data-tipo-programacion]") || "MANUAL";
        const modo = tipo === "MANUAL" ? "No aplica" : normalizarEtiqueta(valorCampo(formulario, "[data-modo-programacion]"));
        const descripcion = valorCampo(formulario, "[name='descripcion']");
        const observacion = valorCampo(formulario, "[name='observacion_tecnica']");
        const feriados = formulario.querySelector("[name='ejecutar_en_feriados']")?.checked ? "Si" : "No";
        const estado = formulario.querySelector("[name='activo']")?.checked ? "Activa" : "Inactiva";

        resumen.appendChild(crearSeccionResumen("Datos generales", [
            ["Nombre", valorCampo(formulario, "[name='nombre_tarea']")],
            ["Descripcion", descripcion],
            ["Cliente", textoSeleccionado(formulario, "[name='id_cliente']")],
            ["Categoria", textoSeleccionado(formulario, "[name='id_categoria']")],
            ["Tipo", textoSeleccionado(formulario, "[name='id_tipo']")],
            ["Estado", estado],
            ["Observacion tecnica", observacion],
        ]));
        resumen.appendChild(crearSeccionResumen("Programacion", [
            ["Tipo", normalizarEtiqueta(tipo)],
            ["Modo del dia", modo],
            ["Resumen", resumirProgramacionFormulario(formulario)],
            ["Ejecuta en feriados", feriados],
        ]));
        return resumen;
    };

    const obtenerConfirmacionTarea = (formulario) => ({
        confirmTitle: formulario.dataset.confirmTitle,
        confirmMessage: formulario.dataset.confirmMessage,
        confirmOk: formulario.dataset.confirmOk,
        confirmCancel: formulario.dataset.confirmCancel,
        confirmType: formulario.dataset.confirmType,
        confirmSummaryNode: crearResumenTarea(formulario),
    });

    const valorSchedulerCampo = (campo) => {
        if (campo.type === "checkbox") {
            return campo.checked ? "Si" : "No";
        }
        return normalizarTexto(campo.value);
    };

    const valorSchedulerOriginal = (campo) => {
        if (campo.type === "checkbox") {
            return campo.dataset.original === "1" ? "Si" : "No";
        }
        return normalizarTexto(campo.dataset.original || "");
    };

    const cambiosScheduler = (formulario) =>
        Array.from(formulario.querySelectorAll("[data-original]"))
            .map((campo) => ({
                etiqueta: campo.dataset.label || campo.name,
                anterior: valorSchedulerOriginal(campo),
                nuevo: valorSchedulerCampo(campo),
            }))
            .filter((cambio) => cambio.anterior !== cambio.nuevo);

    const formularioSchedulerTieneCambios = (formulario) => cambiosScheduler(formulario).length > 0;

    const crearResumenScheduler = (formulario) => {
        const resumen = document.createElement("div");
        resumen.className = "resumen-tarea";
        const filas = cambiosScheduler(formulario).map((cambio) => [
            cambio.etiqueta,
            `${cambio.anterior || "-"} -> ${cambio.nuevo || "-"}`,
        ]);
        resumen.appendChild(crearSeccionResumen("Cambios", filas));
        return resumen;
    };

    const obtenerConfirmacionScheduler = (formulario) => ({
        confirmTitle: formulario.dataset.confirmTitle,
        confirmMessage: formulario.dataset.confirmMessage,
        confirmOk: formulario.dataset.confirmOk,
        confirmCancel: formulario.dataset.confirmCancel,
        confirmType: formulario.dataset.confirmType,
        confirmSummaryNode: crearResumenScheduler(formulario),
    });

    const actualizarProgramacion = (formulario) => {
        const tipo = formulario.querySelector("[data-tipo-programacion]")?.value || "MANUAL";
        const modo = formulario.querySelector("[data-modo-programacion]")?.value || "UNA_VEZ";
        const esManual = tipo === "MANUAL";

        alternarGrupo(formulario, "[data-campo-programacion]", !esManual);
        alternarGrupo(formulario, "[data-campo-modo]", !esManual);
        alternarGrupo(formulario, "[data-campo-hora]", !esManual && modo === "UNA_VEZ");
        alternarGrupo(formulario, "[data-campo-intervalo]", !esManual && modo === "INTERVALO");
        alternarGrupo(formulario, "[data-campo-semanal]", !esManual && tipo === "SEMANAL");
        alternarGrupo(formulario, "[data-campo-mensual]", !esManual && tipo === "MENSUAL");
        alternarGrupo(formulario, "[data-campo-fecha]", !esManual && tipo === "FECHA_ESPECIFICA");
    };

    formulariosProgramacion.forEach((formulario) => {
        actualizarProgramacion(formulario);
        if (formulario.dataset.formModo === "editar") {
            formulario.dataset.estadoOriginal = JSON.stringify(obtenerEstadoTareaFormulario(formulario));
        }
        formulario.querySelectorAll("[data-tipo-programacion], [data-modo-programacion]").forEach((selector) => {
            selector.addEventListener("change", () => actualizarProgramacion(formulario));
        });
    });

    inicializarNotificacionesTarea(panelNotificacionesTarea);
});
