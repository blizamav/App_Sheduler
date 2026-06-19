# UI/UX

## Lineamientos visuales

Estilo moderno, sobrio, corporativo y futurista moderado. La interfaz debe sentirse como una herramienta interna de control TI: clara, rapida de escanear, con jerarquia visual y sin efectos que reduzcan legibilidad.

## Mensajes de duplicados

Desde Fase 12A.2 los formularios de usuarios, mantenedores, tareas y scripts deben mostrar mensajes claros cuando un duplicado exista fuera o dentro de Papelera Operativa.

Mensajes esperados:

* Registro activo: informar que ya existe un registro activo con esos datos.
* Registro inactivo: sugerir activar o editar el registro existente.
* Registro en Papelera Operativa: sugerir restaurar o eliminar permanentemente antes de crear otro.
* Error de integridad SQL por duplicado: mostrar mensaje generico seguro, sin `pyodbc`, nombre de constraint ni traceback.

La UI no debe abrir `alert()`, `window.confirm()` ni `prompt()` para resolver duplicados. La accion de restaurar o eliminar permanentemente sigue perteneciendo a `/papelera`.

## Auditoria

Desde Fase 12B, `/auditoria` debe mostrar con claridad:

* Resultado `OK`, `ERROR` o `BLOQUEADO` mediante badge.
* Accion normalizada en mayusculas y con guion bajo.
* Entidad, modulo, usuario, ruta y metodo HTTP cuando existan.
* Valores antes/despues formateados sin romper layout.

No se implementan exportaciones en Fase 12B.

## Paleta de colores

Variables CSS principales definidas en `app/static/css/estilos.css`:

* `--color-fondo: #eef3f8`: fondo general claro.
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

La UI ya cubre modulos operativos principales: panel, usuarios, mantenedores, tareas, scripts, ejecuciones, consola, historial, feriados, sincronizacion, configuracion del programador, panel operativo, eventos del programador y auditoria.

Desde Fase 12B.1D, el app shell mejora su comportamiento responsive: el sidebar tiene scroll interno, puede colapsarse en desktop, opera como off-canvas en tablet/mobile y se cierra al seleccionar una opcion en vista compacta. La topbar mantiene el boton de menu visible; en desktop colapsa el sidebar y en vistas compactas abre el menu lateral.

Tambien desde Fase 12B.1D, tablas y listados usan overflow horizontal interno con ancho minimo controlado para evitar scroll horizontal global. Las grillas de filtros, formularios, tarjetas y ejecuciones degradan a dos columnas o una columna segun el ancho disponible.

Desde Fase 12B.1E, el shell reemplaza la numeracion del sidebar por iconos textuales de modulo y etiquetas con elipsis controlada. La topbar elimina el bloque redundante `Ambiente local`, usa una marca compacta `APP Scheduler` y conserva el titulo de pantalla, logs y usuario en una sola franja. En escritorio, el sidebar colapsado queda como carril de iconos; en tablet/mobile mantiene el comportamiento off-canvas con etiquetas completas.

Desde Fase 12B.1F, el sidebar corrige su distribucion vertical y su dependencia del contenido: el aside queda fijo en desktop, usa `100dvh`, header y footer quedan fuera del scroll y la navegacion pasa a ser la region flexible con scroll interno independiente. El contenido principal usa margen izquierdo equivalente al ancho del sidebar. Esto evita cortes cuando la pagina tiene poco contenido, zoom alto o pantallas bajas.

Tambien desde Fase 12B.1F, la topbar global deja de renderizar titulo o marca repetida. Queda como una barra compacta integrada al flujo del contenido: toggle del sidebar a la izquierda y acciones de sistema a la derecha. El titulo del modulo vive dentro del contenido de cada vista.

Tambien desde Fase 12B.1F, botones, cards, contenedores, tablas, formularios y badges reciben un tratamiento visual premium: bordes mas finos, sombras sobrias, foco visible, hover/active mas pulidos y microinteracciones ligeras sin cambiar la semantica ni los permisos. Las tablas reemplazan el efecto de raya/borde celeste por hover suave de fila completa.

Desde Fase 11I, el historial de ejecuciones y la consola muestran un badge discreto `Snapshot historico` cuando la ejecucion ya no tiene maestro operativo asociado por eliminacion permanente.

Desde Fase 12A.1, el detalle de auditoria muestra bloques separados para accion, usuario, entidad, descripcion y valores antes/despues. Los valores largos o JSON usan bloques con scroll y corte de palabra controlado para no romper el layout.

Desde Fase 12B.1B, la consola de ejecucion sincroniza visualmente el estado desde el polling JSON. El badge superior, el titulo de estado, el indicador de consola, fecha de termino, duracion, codigo de salida y acciones disponibles se actualizan sin recarga completa. Al pasar a `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE`, se muestra un toast no bloqueante una sola vez.

Pendientes visuales asociados al roadmap:

* Fase 12C: trazabilidad extendida de Auditoria cuando se autorice.
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

## Modal Fase 11G - Eliminar permanentemente

Implementado en Fase 11G.

La accion `Eliminar permanentemente` desde `/papelera` debe usar modal corporativo fuerte, no `alert()`, `window.confirm()` ni `prompt()`.

Texto exacto:

```text
Advertencia: esta acción eliminará permanentemente el registro de las tablas operativas. Ya no aparecerá en mantenedores, papelera, selects ni paneles operativos. El historial de ejecuciones, logs, eventos del programador y snapshots históricos se conservará. Esta acción no se puede deshacer desde la aplicación.
```

Botones:

* `Cancelar`.
* `Eliminar permanentemente`.

Si el backend bloquea la eliminacion por dependencias operativas no historicas, la UI debe mostrar: `No fue posible eliminar permanentemente este registro porque aún existen dependencias operativas no históricas. El registro seguirá en papelera y oculto de la operación normal.`

## Modal Fase 12B.1D-Papelera - Eliminar permanentemente todo

La accion masiva `Eliminar permanentemente todo` en `/papelera` debe mantener una friccion mayor que la accion individual:

* Boton visual `danger` con texto explicito.
* Visible solo para sesiones con `PAPELERA_ELIMINAR_PERMANENTE` o permisos totales.
* Deshabilitado cuando el total real de Papelera es `0`.
* Modal corporativo, no `alert()`, `window.confirm()` ni `prompt()`.
* Resumen previo por entidad y total real de Papelera.
* Checkbox obligatorio antes de habilitar `Eliminar permanentemente todo`.
* Mensaje debe explicar que los bloqueados quedan en Papelera y que historial, logs, eventos, auditoria y snapshots se conservan.
* Despues del proceso, la vista muestra resumen de encontrados, eliminados, no eliminados, errores y motivos seguros.

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
* Mostrar termino de ejecucion desde consola: `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE`.
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
