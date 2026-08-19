function actualizarCampos(formulario) {
    const tipo = formulario.querySelector("[data-tipo-programacion]")?.value;
    const modo = formulario.querySelector("[data-modo-programacion]")?.value;
    formulario.querySelectorAll("[data-campo-tipo]").forEach((campo) => {
        campo.hidden = campo.dataset.campoTipo !== tipo;
    });
    formulario.querySelectorAll("[data-campo-modo]").forEach((campo) => {
        campo.hidden = campo.dataset.campoModo !== modo;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.querySelector("[data-programacion-form]");
    if (!formulario) return;
    formulario.addEventListener("change", (evento) => {
        if (evento.target.matches("[data-tipo-programacion], [data-modo-programacion]")) {
            actualizarCampos(formulario);
        }
    });
    actualizarCampos(formulario);
});
