# Logs de ejecucion en tiempo real

## Flujo

APP Scheduler ejecuta el Python de cada version con `-u` y fuerza `PYTHONUNBUFFERED=1`. `stdout` se captura mediante `PIPE`, `stderr` se combina con `stdout` y el monitor consume el flujo linea por linea mientras el proceso permanece activo.

Cada linea se escribe inmediatamente en el archivo controlado de `logs_tareas`. La consola consulta el endpoint protegido `GET /ejecuciones/<id_ejecucion>/log` cada 1,5 segundos y detiene automaticamente el polling cuando la ejecucion llega a un estado final.

El frontend solo envia `id_ejecucion`; nunca recibe ni envia la ruta fisica del log. El endpoint mantiene el permiso `EJECUCIONES_LOG_VER`.

## Salida de los scripts

Los `print()` y mensajes de `logging` terminados en salto de linea se muestran progresivamente. Aunque APP Scheduler ejecuta Python sin buffer, para procesos largos se recomienda expresar el progreso de forma clara y usar `flush=True` cuando una salida critica deba publicarse inmediatamente:

```python
print("Descargando audio 1/100", flush=True)
```

El modulo `logging` normalmente descarga cada registro mediante su handler. Se recomienda incluir nivel, timestamp y un mensaje que no contenga credenciales ni secretos.

## Consola

La consola reemplaza su contenido con el estado actual del log, por lo que los refrescos no duplican lineas. Sigue automaticamente el final solo si el usuario ya estaba cerca de la ultima linea; si el usuario sube para revisar contenido anterior, el refresco no fuerza el scroll hacia abajo.

Mientras el proceso esta activo muestra `Actualizando en vivo`. Al recibir un estado final muestra `Ejecucion finalizada` y deja de consultar automaticamente.

El archivo fisico conserva todas las lineas escritas. La respuesta visual mantiene el limite operativo existente de los ultimos 120 KB para evitar respuestas excesivas.

## Evidencia stdout

La captura de evidencia conserva el flujo vigente. Las lineas comprendidas entre:

```text
###APP_SCHEDULER_EVIDENCIA_INICIO###
###APP_SCHEDULER_EVIDENCIA_FIN###
```

se acumulan para su procesamiento y, al mismo tiempo, se escriben completas en el log visible. No se ocultan los delimitadores ni el JSON emitido, no se cambia el contrato y no se guarda el JSON completo en base de datos.

## Compatibilidad

La ejecucion manual y la automatica llaman al mismo monitor y al mismo iniciador de procesos, por lo que ambas reciben salida no bufferizada. El comportamiento es compatible con Windows, Linux y los servicios web/worker de Docker porque utiliza el mismo interprete de Python del proceso actual y no depende de una terminal del sistema operativo.
