const exito = document.querySelector("[data-notificar-exito]");
const evidencia = document.querySelector("[data-incluir-evidencia]");
const resumenCorreos = document.querySelector("[data-resumen-correos]");

function sincronizarResumenCorreos() {
  if (!resumenCorreos || !exito || !evidencia) return;
  resumenCorreos.hidden = !(exito.checked && evidencia.checked);
}

if (exito && evidencia) {
  exito.addEventListener("change", sincronizarResumenCorreos);
  evidencia.addEventListener("change", sincronizarResumenCorreos);
  sincronizarResumenCorreos();
}

const flujo = document.querySelector(".flujo-tarea");
const pasoActual = flujo?.querySelector('[aria-current="step"]');
if (flujo && pasoActual) {
  const destino = pasoActual.offsetLeft - (flujo.clientWidth - pasoActual.clientWidth) / 2;
  const reducirMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  flujo.scrollTo({ left: Math.max(0, destino), behavior: reducirMovimiento ? "auto" : "smooth" });
}
