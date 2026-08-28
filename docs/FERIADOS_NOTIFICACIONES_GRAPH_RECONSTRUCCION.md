# Feriados, notificaciones y Microsoft Graph v1.0.0

## Feriados

`dbo.feriados` es la fuente de verdad del Scheduler. La ejecucion manual no se
bloquea por calendario. La automatica respeta `ejecutar_en_feriados` y consulta
solo SQL Server.

La sincronizacion con Nager.Date es una accion manual autorizada con preview.
Usa endpoint fijo, timeout y validacion de esquema. Nunca ocurre dentro del
ciclo Scheduler. Un registro `MANUAL` tiene prioridad, un inactivo no se
reactiva automaticamente y la aplicacion evita duplicar fecha/pais activos.

Los irrenunciables se calculan mediante reglas locales SQL.

## Notificaciones por tarea

La politica separa:

* `notificar_exito_activa`: correo estandar al estado `EXITOSA`;
* `alerta_error_activa`: alerta interna al estado `ERROR`;
* `enviar_evidencia`: contenido Evidencia 1.0 opcional dentro del correo de
  exito; exige notificacion de exito.

Destinatarios TO/CC/BCC se validan, normalizan y reemplazan transaccionalmente.
El resultado del correo no modifica el estado final de la ejecucion.

## Evidencia stdout

El script declara soporte y emite un JSON entre delimitadores impresos. La
validacion estatica usa AST/tokenizacion y no ejecuta ni importa el script. El
Worker captura y valida el bloque real; la BD conserva metadata/hash, no el JSON
completo. Si la evidencia requerida no aparece, se omite el correo al cliente y
se registra alerta interna.

## Microsoft Graph

La disponibilidad efectiva requiere simultaneamente:

* `GRAPH_MAIL_ENABLED=true`;
* `GRAPH_CLIENT_SECRET` presente en el entorno;
* identificadores Graph completos;
* fila SQL global `MAIL_GRAPH` activa.

El cliente usa OAuth client credentials, endpoints fijos, TLS y timeout. El
secret no vive en SQL ni se muestra en UI. Antes del HTTP se reserva una fila en
`notificaciones_envios`; una reserva existente impide un segundo despacho. No
hay retry automatico.

## Gate real Hito 14

Se proceso exclusivamente una ejecucion autorizada. Microsoft Graph acepto una
sola `NOTIFICACION_EXITOSA` con HTTP 202 y request id, usando el template
canonico, un unico TO y sin CC, BCC, evidencia o adjuntos. No se documenta el
destinatario ni identificadores sensibles.

Una segunda evaluacion devolvio `OMITIDO` antes de llamar Graph, demostrando
at-most-once. Al terminar, la configuracion SQL se deshabilito mediante la Web;
Graph efectivo quedo OFF sin editar archivos de entorno.

## Limites v1.0.0

* sincronizacion Nager.Date solo manual;
* sin retry automatico de notificaciones;
* sin upload session para adjuntos grandes;
* adjuntos permitidos solo bajo la carpeta de la version y con limite
  conservador; se rechazan `.env`, `.py`, enlaces y rutas externas.
