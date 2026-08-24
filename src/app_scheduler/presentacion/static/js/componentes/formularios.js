function textoProcesando(boton) {
    return boton.dataset.textoProcesando || "Procesando...";
}

export function prepararFormularios() {
    document.querySelectorAll("form").forEach((formulario) => {
        formulario.addEventListener("submit", (evento) => {
            if (!formulario.checkValidity()) {
                evento.preventDefault();
                evento.stopPropagation();
                formulario.classList.add("was-validated");
                formulario.querySelector(":invalid")?.focus();
                return;
            }
            const boton = evento.submitter;
            if (!(boton instanceof HTMLButtonElement)) return;
            window.setTimeout(() => {
                if (evento.defaultPrevented) return;
                boton.disabled = true;
                boton.dataset.textoOriginal = boton.textContent;
                boton.replaceChildren();
                const spinner = document.createElement("span");
                spinner.className = "spinner-border spinner-border-sm";
                spinner.setAttribute("aria-hidden", "true");
                const texto = document.createElement("span");
                texto.textContent = textoProcesando(boton);
                boton.append(spinner, texto);
            }, 0);
        });
    });
}
