# UI/UX

## Lineamientos visuales

Estilo moderno, sobrio, corporativo y futurista moderado. La interfaz debe sentirse como una herramienta interna de control TI: clara, rapida de escanear, con jerarquia visual y sin efectos que reduzcan legibilidad.

## Paleta de colores

Variables CSS principales definidas en `app/static/css/estilos.css`:

* `--color-fondo: #f4f7fb`: fondo general claro.
* `--color-superficie: #ffffff`: tarjetas, paneles y formularios.
* `--color-azul: #0f4cbd`: acciones primarias e informacion relevante.
* `--color-azul-oscuro: #071b35`: sidebar y paneles de alto contraste.
* `--color-cyan: #18a8d8`: acentos futuristas moderados.
* `--color-verde: #138a4b`: estados activos/exitosos.
* `--color-rojo: #c53a3a`: errores o estados criticos.
* `--color-amarillo: #b87503`: advertencias o pendientes.
* `--color-gris: #7b8798`: estados inactivos o secundarios.
* `--color-borde: #d9e2ef`: separadores suaves.

## Tipografias sugeridas

`Segoe UI`, Arial o sans-serif del sistema para mantener rendimiento y compatibilidad en Windows y Linux.

## Componentes creados

* Login corporativo centrado con fondo tecnico sutil.
* Sidebar responsive con navegacion principal.
* Topbar con usuario logueado, avatar textual y salida.
* Botones primarios y secundarios.
* Botones iconicos para menu y cierre.
* Cards de metricas.
* Badges de estado: activo, inactivo, error, advertencia e informativo.
* Alertas visuales para mensajes Flask.
* Modal global de confirmacion para acciones criticas.
* Contenedores base.
* Formularios con foco visible.
* Tabla base preparada para listados futuros.
* Panel lateral visual preparado para logs.

## Layout

Aplicacion con sidebar fijo en escritorio, topbar persistente y contenido en grillas responsivas. En pantallas menores el sidebar queda oculto y se abre con toggle. El panel lateral de logs se despliega desde la derecha como preparacion visual para Fase 9.

## Estados visuales

* Activo/exitoso: verde.
* Inactivo/pendiente: gris.
* Error: rojo.
* Advertencia: amarillo/naranjo.
* Informativo/en preparacion: azul.

Los estados son visuales en Fase 2; su alimentacion real vendra desde tareas, ejecuciones y logs en fases posteriores.

## Reglas de experiencia

* Acciones criticas deben confirmar con modal propio del sistema, no con `alert()`, `confirm()` ni `prompt()` nativos.
* Errores deben ser claros y accionables.
* Los paneles deben permitir escaneo rapido.
* Las pantallas operativas deben evitar etiquetas internas de fase y usar lenguaje de operacion.
* La interfaz debe ser responsive sin ocultar acciones principales.
* Los efectos visuales deben ser suaves y no deben competir con la lectura.

## Modernizacion Fase 11C

Se aplico una modernizacion visual general sin cambiar logica funcional:

* Sidebar con espaciado, hover y estado activo mas claro.
* Topbar, tarjetas y contenedores con sombras sutiles y mejor separacion.
* Botones primarios/secundarios con foco accesible, hover consistente y sin subrayado cuando son enlaces de accion.
* Tablas con encabezados, hover de filas y scroll mas pulido.
* Formularios y filtros con inputs mas limpios y foco visible.
* Modal y toast con apariencia mas profesional.
* Consola de ejecucion con estilo terminal mejorado, manteniendo formato y polling.
* Historial de ejecuciones agrupado con tarjetas mas claras.
* Textos visibles normalizados: `Scheduler` se presenta como `Programador`, `Worker` como `Proceso programador` y `Heartbeat` como `Senal de vida`.

No se modificaron rutas, permisos, reglas de negocio, consultas SQL, scheduler, heartbeat, feriados ni sincronizacion.

## Estado visual actual

La UI ya cubre modulos operativos principales: panel, usuarios, mantenedores, tareas, scripts, ejecuciones, consola, historial, feriados, sincronizacion, configuracion del programador, panel operativo y eventos del programador.

Pendientes visuales asociados al roadmap:

* Fase 11G: vista de papelera operativa y restauracion.
* Fase 11H: flujo de confirmacion fuerte para purga controlada.
* Fase 12: modulo Auditoria con filtros, detalle y trazabilidad.
* Fase 14: exportaciones, notificaciones, reportes y dashboard avanzado.

## Modal de confirmacion

Desde Fase 4.2 existe un modal global reutilizable definido en `base.html`, controlado desde `app.js` y estilizado en `estilos.css`.

Uso esperado:

* El boton que requiere confirmacion usa clase `requiere-confirmacion`.
* El texto se configura con atributos `data-confirm-title`, `data-confirm-message`, `data-confirm-ok`, `data-confirm-cancel` y `data-confirm-type`.
* Tipos visuales soportados: `danger`, `warning`, `info` y `success`.
* Al cancelar, no se ejecuta ninguna accion.
* Al confirmar, se envia el formulario asociado.
* ESC y clic en overlay cierran el modal.
* Los formularios completos pueden usar `requiere-confirmacion-form` para interceptar el submit antes de guardar.
* En usuarios, el modal cambia automaticamente si detecta cambio de rol, cambio de contrasena o ambos.

El componente queda preparado para acciones futuras como reemplazar script, cambiar version activa, ejecutar tarea manual, suspender tarea o cambios criticos de configuracion.

## Resumen de confirmacion de tareas

Desde Fase 6.1 el modal global puede mostrar un bloque de resumen para formularios de tareas.

Reglas visuales:

* Mostrar una ficha ordenada con datos generales y programacion.
* Usar etiquetas claras y valores legibles.
* Mostrar nombres visibles de cliente, categoria y tipo.
* Mantener el resumen dentro del modal con scroll si el contenido crece.
* No usar `alert()`, `confirm()` ni `prompt()`.

El resumen se genera desde JavaScript con nodos DOM y `textContent`, no con HTML libre.

## Toast del sistema

Desde el ajuste visual de Fase 6.2 existe un componente `toast` flotante para avisos ligeros.

Uso actual:

* Mostrar `No hay cambios para guardar.` cuando el usuario intenta guardar una tarea sin cambios.
* Evitar alertas incrustadas dentro del formulario.
* Evitar `alert()` nativo del navegador.

Caracteristicas:

* Posicion flotante superior derecha en escritorio.
* Adaptacion a ancho disponible en mobile.
* Animacion suave de aparicion y salida.
* Autocierre despues de unos segundos.
* Boton de cierre manual.
* Variantes preparadas para `info`, `success`, `warning` y `error`.

## Decisiones visuales tomadas en Fase 2

* Se mantuvo una paleta clara con sidebar oscuro para dar jerarquia corporativa.
* Se agrego un fondo tecnico sutil al login sin imagenes pesadas ni dependencias externas.
* Se preparo un panel lateral de logs solo visual, sin lectura real de archivos.
* Se agregaron componentes reutilizables antes de crear modulos funcionales.
* No se implementaron tareas, base de datos, usuarios avanzados ni scheduler.
