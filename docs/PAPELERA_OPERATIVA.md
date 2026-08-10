# Papelera operativa

## Politica

La Papelera separa el dato operativo del historial protegido. La eliminacion permanente retira definitivamente lo necesario para operar una entidad, pero nunca elimina su trazabilidad historica.

## Eliminacion operativa y restauracion

La eliminacion operativa marca el registro con `eliminado_operativo = 1` y lo oculta de listados, selects, scheduler y paneles normales. Mientras siga en Papelera puede restaurarse como inactivo, sujeto a las reglas de integridad existentes.

## Eliminacion permanente de una tarea

Al confirmar la eliminacion permanente de una tarea se eliminan en una transaccion controlada:

* la tarea;
* sus programaciones;
* sus scripts y versiones;
* la configuracion de notificaciones y sus destinatarios;
* las referencias operativas hacia esos registros.

Despues del cierre de la transaccion se eliminan los archivos `.py` y `.env` asociados. Las rutas se obtienen desde la metadata persistida antes de ejecutar los `DELETE`, nunca desde el frontend, y deben permanecer dentro de los directorios configurados para `scripts` y `env_scripts`.

Un archivo inexistente no impide retirar la tarea. Una ruta absoluta, externa, sospechosa o que no corresponda a un archivo se rechaza y se registra solo mediante conteos seguros, sin exponer la ruta ni el contenido del `.env`.

La misma regla aplica para la eliminacion permanente individual de scripts y versiones: antes de borrar registros operativos en BD se capturan `ruta_relativa` y `ruta_env_relativa` de todas las versiones involucradas. Esto evita perder metadata fisica antes de limpiar los archivos.

## Limpieza fisica segura

La limpieza fisica elimina solo archivos conocidos entregados por el repositorio de Papelera:

* scripts Python bajo `scripts/`;
* archivos `.env` bajo `env_scripts/`.

Antes de eliminar se resuelve la ruta real y se valida que siga dentro del root permitido. Se rechazan rutas absolutas, rutas con traversal o cualquier ruta que escape de `scripts/` o `env_scripts/`.

Luego de eliminar un archivo, la app intenta podar solo carpetas padre vacias mediante `rmdir`, deteniendose al llegar a `scripts/` o `env_scripts/`. No se usa borrado recursivo y no se eliminan carpetas que contengan archivos no asociados.

## Auditoria dry-run de huerfanos

Existe un mecanismo interno de dry-run para comparar rutas operativas vigentes de `scripts_versiones` contra archivos fisicos existentes en `scripts/` y `env_scripts/`.

El dry-run no elimina nada. Clasifica archivos como:

* `REFERENCIADO`;
* `HUERFANO`;
* `CARPETA_VACIA`.

La Fase 18D.1 confirmo en ambiente local que, con BD operativa sin tareas, scripts ni versiones, existian residuos fisicos: 14 `.py`, 6 `.env` y 5 carpetas vacias.

La Fase 18D.2 ejecuto la limpieza autorizada despues de repetir el cruce de solo lectura contra la BD. Se eliminaron exclusivamente los 20 archivos clasificados como `HUERFANO` y se podaron 46 carpetas que estaban o quedaron vacias mediante `rmdir`. El dry-run posterior confirmo 0 archivos huerfanos, 0 carpetas vacias y 0 rutas rechazadas; los roots `scripts/` y `env_scripts/` permanecieron intactos.

La Fase 18D.3 valido el flujo completo con una tarea temporal real, dos versiones `.py`, un `.env` por version y una ejecucion exitosa. El borrado operativo conservo los archivos mientras la tarea estuvo en Papelera; la eliminacion permanente retiro exclusivamente sus registros y archivos operativos, podo sus carpetas y mantuvo la ejecucion, el log, la auditoria y los snapshots historicos. El dry-run final permanecio en cero.

## Historial protegido

No se eliminan:

* ejecuciones y logs historicos;
* evidencias capturadas;
* intentos y envios de notificaciones;
* auditoria;
* eventos historicos del scheduler;
* snapshots y nombres historicos.

Antes de eliminar filas operativas, la app completa y valida los snapshots disponibles y nulifica las referencias historicas desacopladas. El historial no bloquea la eliminacion permanente cuando el desacople historico requerido esta aplicado y los snapshots son suficientes.

## Catalogos y configuracion global

Eliminar una tarea no elimina clientes, categorias, tipos, usuarios, roles, permisos, configuracion del sistema ni configuracion global de Microsoft Graph.

## Eliminacion masiva

La eliminacion masiva procesa primero las tareas para que cada una absorba la limpieza de sus scripts, versiones y archivos. Si un script o version tambien figuraba por separado en Papelera, se reconoce como eliminado junto con su tarea y no se trata como error.

## Bloqueos reales

Una ejecucion actualmente en curso sigue bloqueando la eliminacion permanente de su tarea. Tambien se bloquea si falta el desacople historico obligatorio o si los snapshots requeridos no pueden completarse. Estos bloqueos protegen una operacion activa o la trazabilidad; el simple hecho de tener historial finalizado no bloquea.
