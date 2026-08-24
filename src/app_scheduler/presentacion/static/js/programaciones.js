function actualizarCampos(formulario) {
    const tipo = formulario.querySelector("[data-tipo-programacion]")?.value;
    const modo = formulario.querySelector("[data-modo-programacion]")?.value;
    formulario.querySelectorAll("[data-campo-tipo]").forEach((campo) => {
        const oculto = campo.dataset.campoTipo !== tipo;
        campo.hidden = oculto;
        campo.setAttribute("aria-hidden", String(oculto));
        campo.querySelectorAll("input, select, textarea").forEach((control) => {
            control.disabled = oculto;
        });
    });
    formulario.querySelectorAll("[data-campo-modo]").forEach((campo) => {
        const oculto = campo.dataset.campoModo !== modo;
        campo.hidden = oculto;
        campo.setAttribute("aria-hidden", String(oculto));
        campo.querySelectorAll("input, select, textarea").forEach((control) => {
            control.disabled = oculto;
        });
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
