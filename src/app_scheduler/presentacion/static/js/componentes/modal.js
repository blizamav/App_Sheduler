export function prepararModal() {
    const modal = document.querySelector("[data-modal]");
    if (!modal) return;

    const cancelar = modal.querySelector("[data-modal-cancelar]");
    const confirmar = modal.querySelector("[data-modal-confirmar]");
    let accionPendiente = null;

    function cerrar() {
        modal.classList.remove("abierto");
        modal.setAttribute("aria-hidden", "true");
        accionPendiente = null;
    }

    document.addEventListener("click", (evento) => {
        const activador = evento.target.closest("[data-confirmar]");
        if (!activador) return;
        evento.preventDefault();
        accionPendiente = () => {
            if (activador instanceof HTMLButtonElement && activador.form) {
                activador.form.requestSubmit(activador);
            }
        };
        modal.querySelector("[data-modal-titulo]").textContent = activador.dataset.titulo || "Confirmar accion";
        modal.querySelector("[data-modal-mensaje]").textContent = activador.dataset.mensaje || "Confirma si deseas continuar.";
        modal.classList.add("abierto");
        modal.setAttribute("aria-hidden", "false");
        cancelar.focus();
    });

    cancelar.addEventListener("click", cerrar);
    confirmar.addEventListener("click", () => {
        const ejecutar = accionPendiente;
        cerrar();
        ejecutar?.();
    });
    modal.addEventListener("click", (evento) => {
        if (evento.target === modal) cerrar();
    });
    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && modal.classList.contains("abierto")) cerrar();
    });
}
