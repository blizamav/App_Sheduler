# UI/UX APP Scheduler v1.0.1

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

Si una tarea tiene correos activos y Graph no esta disponible, el paso de
Notificaciones y el modal de ejecucion explican que el proceso continuara sin
correo. Solo usuarios con `CONFIGURACION_ADMIN` reciben el enlace de
administracion. El detalle de ejecucion separa visualmente resultado del script
y estado de notificacion (`ENVIADA`, `OMITIDA`, `ERROR` o `PENDIENTE`), y el
polling actualiza ambas areas sin requerir recarga manual.

La configuracion muestra tres bloques autonomos: Exito operacional, Error
operacional y Evidencia al cliente. Cada uno posee TO/CC/BCC propios. Evidencia
no depende del switch de Exito; si ambos estan activos, una ayuda informa que
la ejecucion puede generar dos correos independientes. La compatibilidad
estatica se denomina `Contrato Evidencia 1.0 declarado`, mientras el payload se
presenta como validado solamente durante la ejecucion.

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
