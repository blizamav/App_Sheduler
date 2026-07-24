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

Despues del cierre de la transaccion se eliminan los archivos `.py` y `.env` asociados. Las rutas se obtienen desde la metadata persistida, nunca desde el frontend, y deben permanecer dentro de los directorios configurados para `scripts` y `env_scripts`.

Un archivo inexistente no impide retirar la tarea. Una ruta absoluta, externa, sospechosa o que no corresponda a un archivo se rechaza y se registra solo mediante conteos seguros, sin exponer la ruta ni el contenido del `.env`.

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
