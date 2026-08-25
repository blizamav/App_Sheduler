const exito = document.querySelector("[data-notificar-exito]");
const evidencia = document.querySelector("[data-incluir-evidencia]");
const ayuda = document.querySelector("[data-evidencia-dependencia]");

function sincronizarEvidencia() {
  if (!exito || !evidencia) return;
  const incompatible = evidencia.hasAttribute("data-incompatible");
  evidencia.disabled = incompatible || !exito.checked;
  if (!exito.checked) evidencia.checked = false;
  if (ayuda) {
    ayuda.textContent = exito.checked
      ? "La Evidencia es opcional y se incorporara solo cuando la ejecucion emita un bloque valido."
      : "Activa la notificacion de exito para poder incluir Evidencia.";
  }
}

if (exito && evidencia) {
  if (evidencia.disabled) evidencia.setAttribute("data-incompatible", "");
  exito.addEventListener("change", sincronizarEvidencia);
  sincronizarEvidencia();
}
