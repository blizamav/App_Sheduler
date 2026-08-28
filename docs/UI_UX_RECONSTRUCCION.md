# UI/UX APP Scheduler v1.0.0

## Estado

La interfaz reconstruida es la UI oficial. Usa Bootstrap 5.3.3 local, Jinja,
tokens CSS y JavaScript modular bajo `src/app_scheduler/presentacion/`. El
runtime historico no define la experiencia vigente.

## Criterios

* herramienta interna sobria, clara y orientada a operacion repetitiva;
* jerarquia compacta, superficies blancas y estados semanticos consistentes;
* azul corporativo con cyan moderado, verde, amarillo y rojo funcionales;
* foco visible, labels persistentes y mensajes controlados;
* sin `alert()`, `window.confirm()` o `prompt()`;
* tablas anchas con scroll local, sin ampliar el viewport;
* acciones criticas mediante modal corporativo con contexto suficiente.

## Layout

El shell contiene topbar, sidebar contraible en escritorio y offcanvas en
movil. La preferencia del sidebar se conserva en el navegador. El contenido usa
todo el ancho util y limita solo las superficies que requieren lectura corta.

Se validaron los viewports de referencia:

* 1440x900;
* 768x900;
* 390x844;
* 844x390.

La navegacion movil, los submenus, filtros, formularios y acciones permanecen
alcanzables en orientacion vertical y horizontal.

## Componentes

* botones Bootstrap y variantes de aplicacion;
* badges de estado;
* alertas y toasts;
* modal reutilizable;
* cards operativas sin anidacion decorativa;
* formularios, switches, selects y ayudas contextuales;
* tablas responsive y paginacion;
* stepper de Tareas;
* consola de ejecucion con polling;
* semaforo Worker y paneles de estado;
* estados vacios y errores publicos coherentes.

## Flujo de tarea

El alta/edicion usa pasos independientes: Datos, Script, Evidencia,
Notificaciones y Programacion. El stepper diferencia pantalla actual de estado
funcional (`Completado`, `En curso`, `Pendiente`, `Requiere ajuste`). Evidencia
es opcional y no bloquea una notificacion estandar de exito.

## Accesibilidad y seguridad visual

La UI usa HTML semantico, foco visible, controles nativos/Bootstrap y
`prefers-reduced-motion`. Los errores de autenticacion no revelan si una cuenta
existe. Los campos sensibles Graph informan presencia y permiten reemplazo sin
reproducir el valor vigente.

## Validacion final

Hitos 12 y 14 revisaron login, Panel, usuarios, tareas, scripts, ejecuciones,
consola, configuracion, operacion y flujos criticos en desktop/tablet/movil. No
se detecto overflow global bloqueante. Los templates compilan y los JavaScript
superan `node --check`.
