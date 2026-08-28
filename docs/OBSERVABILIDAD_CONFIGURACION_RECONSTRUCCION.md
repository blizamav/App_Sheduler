# Observabilidad y configuracion v1.0.0

## Fuentes

La interfaz operativa lee datos reales de SQL Server y filesystem controlado:

* `scheduler_worker_heartbeat`: vida y ciclo del Worker;
* `configuracion_scheduler`: switches, intervalo y concurrencia;
* `ejecuciones`: cola, estados y actividad;
* `scheduler_eventos`: decisiones y omisiones automaticas;
* `logs_sistema`: eventos tecnicos y funcionales;
* `logs_tareas`: metadata del log de cada ejecucion;
* `configuracion_sistema`: parametros globales no secretos;
* `runtime_control/`: lock y estado de Factory Reset.

No se infiere que un Worker esta activo solo porque Scheduler este habilitado.
Configuracion y proceso son señales distintas.

## Semaforo Worker

| Estado | Significado |
|---|---|
| `OPERATIVO` | Heartbeat reciente y estado saludable |
| `ATENCION` | Señal degradada, vencida o cola pendiente que requiere revision |
| `DETENIDO` | Detencion explicita o proceso no operativo confirmado |
| `DESCONOCIDO` | No existe señal suficiente para clasificar |

El healthcheck Docker valida el heartbeat del hostname del contenedor. No crea
Scheduler, no reclama ejecuciones y no reemplaza el diagnostico de la pantalla
**Estado del sistema**.

## Configuracion

* Variables de ambiente: infraestructura, rutas, credenciales y kill switches.
* `configuracion_scheduler`: comportamiento operativo editable con permisos.
* `configuracion_mail_graph`: configuracion global no secreta y activacion SQL.
* `configuracion_sistema`: matriz de lectura para parametros globales.

Graph esta disponible solo si el kill switch ENV, el secret y la fila SQL
global estan habilitados. La UI nunca muestra el secret.

## Logs

`/logs/` pagina `logs_sistema` con filtros seguros. La consola de ejecucion
consulta el archivo confinado asociado a `logs_tareas`. Cada linea de plataforma
usa timestamp y nivel. La salida de un script sigue siendo responsabilidad del
script: no debe imprimir secretos.

El detalle de errores publicos se limita a mensajes controlados; la diagnostica
tecnica va al logger sanitizado. Heartbeats normales no generan un evento por
ciclo para evitar ruido.

## Operacion

Si existen solicitudes `PENDIENTE`:

1. revisar **Estado del sistema**;
2. distinguir Worker detenido de Scheduler o mantenimiento deshabilitados;
3. revisar heartbeat y logs del Worker;
4. usar `--queue-only` cuando se necesite consumir cola sin crear automaticas;
5. no cambiar estados mediante SQL manual.

## Validacion v1.0.0

Hito 14 valido Web/Worker Docker, heartbeat, recuperacion de cola, ejecucion
automatica unica, logs y consola. Al cierre Scheduler quedo OFF, no quedaron
ejecuciones pendientes/en curso y el Worker temporal fue detenido.
