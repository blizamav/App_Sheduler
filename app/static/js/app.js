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
    const modalConfirmar = document.querySelector("[data-modal-confirmar]");
    const modalCancelar = document.querySelector("[data-modal-cancelar]");
    const selectorRol = document.querySelector("[data-rol-original]");
    const alertaRol = document.querySelector("[data-alerta-rol]");
    const passwordEdicion = document.querySelector("[data-password-edicion='1']");
    const alertaPassword = document.querySelector("[data-alerta-password]");
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
        if (!mantenerEnvioConfirmado) {
            envioConfirmado = false;
        }
    };

    const obtenerConfirmacionFormulario = (formulario) => {
        const dataset = formulario.dataset;
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
});
