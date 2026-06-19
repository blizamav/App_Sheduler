document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.dataset.app = "app-scheduler";

    const cuerpo = document.body;
    const botonesSidebar = document.querySelectorAll("[data-sidebar-toggle]");
    const cierresSidebar = document.querySelectorAll("[data-sidebar-cerrar]");
    const botonesLogs = document.querySelectorAll("[data-panel-logs-toggle]");
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
    let formularioPendiente = null;
    let envioConfirmado = false;

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

    const abrirModalConfirmacion = (configuracion, formulario = null) => {
        if (!modalConfirmacion) {
            return;
        }

        formularioPendiente = formulario || configuracion.closest?.("form") || null;
        const dataset = configuracion.dataset || configuracion;
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

    confirmables.forEach((elemento) => {
        elemento.addEventListener("click", (evento) => {
            evento.preventDefault();
            abrirModalConfirmacion(elemento, elemento.closest("form"));
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
            cerrarModalConfirmacion();
        });
    }

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && modalConfirmacion?.classList.contains("abierto")) {
            cerrarModalConfirmacion();
        }
    });

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
});
