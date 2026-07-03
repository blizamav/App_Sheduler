# Contrato de evidencia por stdout

## Proposito

Este documento formaliza la Fase 15A.1: contrato de evidencia estructurada emitida por scripts Python hacia APP Scheduler.

La evidencia no se guarda como archivo JSON fisico persistente y no se almacena completa en base de datos. El script define una variable estructurada, imprime un bloque JSON por `stdout` entre delimitadores oficiales, y la app lo capturara en una fase posterior para validarlo y usarlo en el envio de reportes por Microsoft Graph.

Esta fase es documental. No implementa capturador, envio Graph, UI, migraciones ni cambios funcionales.

El modelo minimo de datos propuesto para Fase 15B queda documentado en `docs/MODELO_NOTIFICACIONES_EVIDENCIAS.md`.

Desde Fase 15D existe backend minimo para configurar notificaciones por tarea. Esta configuracion no ejecuta validacion estatica del script todavia y no envia correos.

## Decision aceptada

* La evidencia se emite por `stdout`.
* El bloque real viaja entre delimitadores literales.
* La app debe validar estaticamente el script antes de permitir activar `Enviar evidencia`.
* La ejecucion automatica o manual debe capturar el bloque real emitido por el proceso.
* Si la opcion esta activa y el bloque no aparece en ejecucion, se debe generar alerta interna y no se debe enviar correo al cliente.
* No se guarda el JSON completo en BD.
* No se crea archivo JSON persistente.

## Declaraciones obligatorias en el script

El script compatible debe declarar:

```python
APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"
```

Tambien debe contener los textos literales:

```text
###APP_SCHEDULER_EVIDENCIA_INICIO###
###APP_SCHEDULER_EVIDENCIA_FIN###
```

La validacion estatica solo revisa la version activa del script sin ejecutarla.

## Helper recomendado para scripts

```python
import json

APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"


def emitir_evidencia_scheduler(evidencia):
    print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
    print(json.dumps(evidencia, ensure_ascii=False))
    print("###APP_SCHEDULER_EVIDENCIA_FIN###")
```

## Estructura JSON version 1.0

Campos obligatorios:

| Campo | Tipo | Uso |
|---|---|---|
| `version_contrato` | string | Debe ser `"1.0"`. |
| `estado` | string | Resultado declarado por el script: `EXITOSO`, `ERROR` o `ADVERTENCIA`. |
| `tipo_evidencia` | string | Categoria del reporte, por ejemplo `CARGA_AUDIOS`, `PROCESO_SQL`, `VALIDACION`. |
| `titulo` | string | Titulo humano del reporte. |
| `resumen` | array | Lista dinamica de pares `{ "campo": "...", "valor": "..." }`. |

Campos opcionales:

| Campo | Tipo | Uso |
|---|---|---|
| `asunto_sugerido` | string | Asunto recomendado para correo. |
| `mensaje_introductorio` | string | Texto inicial del reporte. |
| `fecha_proceso` | string | Fecha del proceso en formato ISO o fecha operativa. |
| `adjuntos` | array | Adjuntos declarados por el script. |
| `problemas` | array | Problemas detectados por el script. |
| `metadata` | object | Datos tecnicos no sensibles. |
| `observaciones` | array | Notas humanas. |
| `links` | array | Enlaces autorizados. |
| `secciones` | array | Bloques descriptivos. |
| `tablas` | array | Tablas simples para el cuerpo del correo. |

Formato recomendado de `resumen`:

```json
[
  { "campo": "Cliente", "valor": "BECS" },
  { "campo": "Registros procesados", "valor": 1200 },
  { "campo": "Registros con error", "valor": 0 }
]
```

Formato recomendado de `adjuntos`:

```json
[
  {
    "nombre": "reporte.xlsx",
    "ruta": "salidas/reporte.xlsx",
    "obligatorio": true
  }
]
```

## Ejemplo de stdout esperado

```text
Inicio del proceso
Procesando datos...
###APP_SCHEDULER_EVIDENCIA_INICIO###
{"version_contrato":"1.0","estado":"EXITOSO","tipo_evidencia":"CARGA_AUDIOS","titulo":"Carga de audios finalizada","resumen":[{"campo":"Cliente","valor":"BECS"},{"campo":"Audios cargados","valor":250}]}
###APP_SCHEDULER_EVIDENCIA_FIN###
Proceso finalizado
```

## Validacion estatica antes de activar Enviar evidencia

Antes de permitir activar `Enviar evidencia`, la app debera revisar el archivo de la version activa sin ejecutarlo.

Estado actual: pendiente para fase posterior. Fase 15D solo guarda configuracion y destinatarios.

Reglas:

1. Debe existir `APP_SCHEDULER_EVIDENCIA = True`.
2. Debe existir `APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"`.
3. Debe existir el literal `###APP_SCHEDULER_EVIDENCIA_INICIO###`.
4. Debe existir el literal `###APP_SCHEDULER_EVIDENCIA_FIN###`.

Si falla una regla, la app debe bloquear la activacion y mostrar un mensaje controlado:

```text
No se puede activar el envio de evidencia para este script. El archivo no cumple el contrato APP Scheduler de evidencia por stdout. Debe declarar APP_SCHEDULER_EVIDENCIA=True, version 1.0 y emitir el bloque JSON entre los delimitadores oficiales.
```

## Captura en ejecucion

El capturador futuro debe leer `stdout` linea por linea sin romper el log existente.

Estado recomendado:

* `fuera_bloque`: cada linea se registra normalmente en el log.
* `capturando_bloque`: las lineas se acumulan como posible JSON.
* `bloque_cerrado`: se parsea, valida y queda listo para flujo de notificacion.

Reglas:

* El bloque debe tener inicio y fin.
* Debe existir como maximo un bloque valido por ejecucion en la primera version.
* El JSON debe ser valido.
* `version_contrato` debe ser `"1.0"`.
* `estado` debe ser coherente con el resultado real del proceso.
* Los adjuntos obligatorios deben existir dentro de rutas permitidas.
* No se deben incluir secretos, passwords, tokens ni connection strings.

## Prioridad de decision

La decision final debe respetar este orden:

1. Codigo de salida del proceso.
2. Estado declarado en el JSON de evidencia.
3. Resultado de validacion del bloque de evidencia.
4. Resultado del envio por Microsoft Graph.

Casos:

| Caso | Resultado |
|---|---|
| Exit code distinto de 0 y JSON `EXITOSO` | No enviar a cliente; generar alerta interna. |
| Exit code 0 y JSON `ERROR` | No enviar a cliente; generar alerta interna. |
| Exit code 0 y bloque ausente con evidencia activa | No enviar a cliente; generar alerta interna. |
| Exit code 0 y JSON invalido | No enviar a cliente; generar alerta interna. |
| Exit code 0, JSON valido, estado `EXITOSO` y sin problemas | Candidato a envio al cliente. |

## Regla de envio al cliente

Solo se envia correo al cliente cuando:

* La tarea tiene `Enviar evidencia` activo.
* El script cumple validacion estatica.
* La ejecucion termina con codigo de salida exitoso.
* El bloque de evidencia aparece en `stdout`.
* El JSON es valido.
* `version_contrato` es compatible.
* `estado` es `EXITOSO`.
* No existen `problemas` bloqueantes.
* Los adjuntos obligatorios declarados existen y pasan validacion.
* Microsoft Graph responde correctamente.

## Regla de alerta interna

Se debe generar alerta interna cuando:

* El proceso falla.
* El proceso termina con codigo distinto de 0.
* La opcion de evidencia esta activa pero el bloque no aparece.
* El bloque aparece pero el JSON es invalido.
* El JSON declara `ERROR`.
* Existen problemas bloqueantes.
* Falta un adjunto obligatorio.
* Microsoft Graph falla.
* Ocurre una validacion controlada que impide enviar al cliente.

Destinatario futuro recomendado: `alertas.reportes@soex.cl`, configurable por ambiente.

## Persistencia minima permitida

No guardar el JSON completo.

Fase 15B recomienda que la persistencia minima se separe en:

* configuracion por tarea;
* destinatarios por configuracion;
* evidencia por ejecucion;
* intentos de envio por Graph o alerta interna.

Datos minimos sugeridos para fases posteriores:

* `id_ejecucion`.
* `estado_evidencia`.
* `version_contrato`.
* `tipo_evidencia`.
* `titulo`.
* `asunto_final`.
* `hash_evidencia`.
* Cantidad de campos de resumen.
* Cantidad de adjuntos.
* Cantidad de problemas.
* `estado_notificacion`.
* Destinatarios.
* Resultado Graph.
* Error controlado si aplica.
* Fechas de creacion, envio y ultimo intento.

## Seguridad

* El script no debe imprimir secretos dentro del bloque.
* No se acepta HTML libre generado por el script en la primera version.
* No se aceptan adjuntos fuera de rutas permitidas.
* No se deben exponer secretos de Graph.
* Si la validacion falla, no se envia correo al cliente.
* La app debe registrar trazabilidad tecnica controlada y sin secretos.
* En fases posteriores se debe evaluar enmascaramiento del bloque en logs visibles si contiene campos sensibles por error del script.

## Ejemplo minimo compatible

```python
import json

APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"

evidencia = {
    "version_contrato": "1.0",
    "estado": "EXITOSO",
    "tipo_evidencia": "VALIDACION",
    "titulo": "Validacion finalizada",
    "resumen": [
        {"campo": "Registros procesados", "valor": 100},
        {"campo": "Registros con error", "valor": 0}
    ]
}

print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
print(json.dumps(evidencia, ensure_ascii=False))
print("###APP_SCHEDULER_EVIDENCIA_FIN###")
```

## Ejemplo carga de audios

```json
{
  "version_contrato": "1.0",
  "estado": "EXITOSO",
  "tipo_evidencia": "CARGA_AUDIOS",
  "titulo": "Carga de audios finalizada",
  "resumen": [
    { "campo": "Cliente", "valor": "BECS" },
    { "campo": "Audios recibidos", "valor": 250 },
    { "campo": "Audios cargados", "valor": 250 },
    { "campo": "Audios rechazados", "valor": 0 }
  ],
  "problemas": []
}
```

## Ejemplo proceso SQL sin SFTP

```json
{
  "version_contrato": "1.0",
  "estado": "EXITOSO",
  "tipo_evidencia": "PROCESO_SQL",
  "titulo": "Proceso SQL terminado",
  "resumen": [
    { "campo": "Base", "valor": "QA" },
    { "campo": "Filas actualizadas", "valor": 830 }
  ],
  "adjuntos": []
}
```

## Casos no habilitantes

Script sin soporte de evidencia:

```python
print("Proceso OK")
```

Resultado esperado: no se puede activar `Enviar evidencia`.

Evidencia activa pero sin bloque emitido en ejecucion:

```python
APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"
print("Proceso OK")
```

Resultado esperado: alerta interna y sin correo al cliente.

JSON invalido:

```text
###APP_SCHEDULER_EVIDENCIA_INICIO###
{estado: EXITOSO}
###APP_SCHEDULER_EVIDENCIA_FIN###
```

Resultado esperado: alerta interna y sin correo al cliente.

## Fases futuras

* Fase 15B: modelo de datos minimo para evidencias y notificaciones.
* Fase 15C: migracion SQL de soporte para notificaciones/evidencias.
* Fase 15D: backend/API de configuracion de notificaciones por tarea.
* Fase 15E: UI minima de configuracion de notificaciones por tarea.
* Fase 15F: configuracion global del origen de correo Mail Automatico Graph, sin envio real.
* Fase posterior: validador estatico del script compatible.
* Fase posterior: capturador de bloque `stdout` y parseo JSON.
* Fase posterior: servicio Microsoft Graph.
* Fase posterior: integracion con worker y ejecuciones.
* Fase posterior: alertas internas, adjuntos, reintentos y trazabilidad.
