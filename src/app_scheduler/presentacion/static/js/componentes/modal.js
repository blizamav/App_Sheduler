export function prepararModal() {
    const modal = document.querySelector("[data-modal]");
    if (!modal || !window.bootstrap?.Modal) return;

    const confirmar = modal.querySelector("[data-modal-confirmar]");
    const instancia = window.bootstrap.Modal.getOrCreateInstance(modal);
    let pendiente = null;

    document.addEventListener("submit", (evento) => {
        const formulario = evento.target;
        const activador = evento.submitter;
        if (!(formulario instanceof HTMLFormElement) || !(activador instanceof HTMLButtonElement) || !activador.matches("[data-confirmar]")) return;
        if (formulario.dataset.confirmacionLista === "1") {
            delete formulario.dataset.confirmacionLista;
            return;
        }
        evento.preventDefault();
        pendiente = { formulario, activador };
        modal.querySelector("[data-modal-titulo]").textContent = activador.dataset.titulo || "Confirmar accion";
        modal.querySelector("[data-modal-mensaje]").textContent = activador.dataset.mensaje || "Confirma si deseas continuar.";
        confirmar.textContent = activador.dataset.textoConfirmar || "Confirmar";
        confirmar.className = `btn ${activador.classList.contains("peligro") || activador.classList.contains("btn-danger") ? "btn-danger" : "btn-primary"}`;
        instancia.show();
    });

    confirmar.addEventListener("click", () => {
        if (!pendiente) return;
        const { formulario, activador } = pendiente;
        pendiente = null;
        formulario.dataset.confirmacionLista = "1";
        instancia.hide();
        formulario.requestSubmit(activador);
    });

    modal.addEventListener("hidden.bs.modal", () => { pendiente = null; });
}
