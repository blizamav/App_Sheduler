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

const flujo = document.querySelector(".flujo-tarea");
const pasoActual = flujo?.querySelector('[aria-current="step"]');
if (flujo && pasoActual) {
  const destino = pasoActual.offsetLeft - (flujo.clientWidth - pasoActual.clientWidth) / 2;
  const reducirMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  flujo.scrollTo({ left: Math.max(0, destino), behavior: reducirMovimiento ? "auto" : "smooth" });
}
