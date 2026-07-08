# Diagnostico .env por script/version

## Objetivo

Este diagnostico revisa como APP Scheduler maneja actualmente variables de entorno para scripts versionados y propone la implementacion minima para que el usuario pueda configurarlas desde la app sin copiar archivos manualmente en carpetas fisicas.

## Archivos revisados

* `README.md`
* `docs/CHANGELOG.md`
* `log_codex.md`
* `docs/CONTRATO_EVIDENCIA_STDOUT.md`
* `docs/MODELO_NOTIFICACIONES_EVIDENCIAS.md`
* `docs/VARIABLES_ENTORNO.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/FLUJOS.md`
* `docs/BASE_DATOS.md`
* `app/config.py`
* `app/rutas_scripts.py`
* `app/templates/scripts/listado.html`
* `app/servicios/servicio_scripts.py`
* `app/servicios/servicio_env_scripts.py`
* `app/servicios/servicio_ejecuciones.py`
* `app/servicios/servicio_procesos.py`
* `app/servicios/servicio_archivos.py`
* `app/repositorios/repositorio_scripts.py`
* `app/repositorios/repositorio_ejecuciones.py`
* `database/legacy_pre_release_13B/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`

No se modifico ni se ejecuto SQL. No se toco `database/release/`.

## Resumen ejecutivo

APP Scheduler ya tiene soporte funcional parcial para `.env` por version de script:

* La tabla `scripts_versiones` tiene `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa`.
* La UI de scripts permite marcar si una version requiere `.env`.
* La UI permite adjuntar un archivo `.env` por version.
* El archivo queda guardado bajo `env_scripts/.../vX/.env`.
* Al ejecutar, `servicio_ejecuciones.py` valida si la version activa requiere `.env`.
* Si lo requiere, `servicio_env_scripts.py` carga el archivo con `dotenv_values()`.
* El entorno resultante se inyecta al proceso Python mediante `subprocess.Popen(..., env=entorno)`.

La brecha principal no esta en el motor de ejecucion. Esta en la UX y en el formato de configuracion:

* hoy se debe adjuntar un archivo `.env`;
* no existe textarea para pegar contenido;
* no existe almacenamiento estructurado de variables;
* no existe vista segura de claves configuradas enmascaradas;
* el mensaje de bloqueo cuando falta `.env` es tecnico y habla de archivo fisico.

## Respuestas requeridas

### 1. Existe actualmente soporte para .env por script o version?

Si. Existe soporte por version de script, no por tarea ni por script logico completo.

La asociacion vive en `scripts_versiones` y se administra desde la pantalla `/tareas/<id_tarea>/scripts`.

### 2. Donde se guarda hoy el .env si existe?

Se guarda como archivo fisico dentro del arbol `env_scripts/`, con ruta construida por `app/servicios/servicio_archivos.py`.

El patron actual es:

```text
env_scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vN/.env
```

La base de datos guarda solo rutas, no contenido.

### 3. Esta asociado a tarea, script o version?

Esta asociado a version:

* `scripts` es el contenedor logico del script de una tarea.
* `scripts_versiones` representa cada archivo Python versionado.
* `scripts_versiones.requiere_env`, `ruta_env_fisica` y `ruta_env_relativa` controlan el `.env` de cada version.

### 4. Se carga realmente al ejecutar el subprocess?

Si. El flujo actual es:

1. `servicio_ejecuciones._validar_contexto_ejecucion()` consulta la version activa.
2. Si `requiere_env = 1`, valida que exista `ruta_env_relativa` y que el archivo exista fisicamente.
3. `_ejecutar_en_segundo_plano()` llama `cargar_env_version(ruta_env_relativa)`.
4. `servicio_env_scripts.cargar_env_version()` construye `os.environ.copy()`, carga pares con `dotenv_values()` y sobreescribe/agrega las variables del archivo.
5. `servicio_procesos.iniciar_proceso_python()` ejecuta `subprocess.Popen(..., env=entorno, shell=False)`.

Por lo tanto, el script ejecutado puede leer esas variables con `os.getenv("NOMBRE_VARIABLE")`.

### 5. El log ".env cargado correctamente" corresponde a variables disponibles para el script?

Si. Ese log se escribe despues de llamar a `cargar_env_version()` y antes de iniciar `subprocess.Popen()` con el entorno resultante.

Ese mensaje no muestra contenido del `.env`; solo confirma que la plataforma preparo el entorno del proceso.

### 6. Por que un script puede seguir buscando un .env fisico en la carpeta v1/v2/v3?

Porque el codigo del script puede tener logica propia, por ejemplo:

```python
from dotenv import load_dotenv
load_dotenv(".env")
```

o una funcion local `cargar_env()` que busca un archivo junto al `.py`.

APP Scheduler inyecta variables al proceso. No copia el `.env` dentro de `scripts/.../vN/`. Por eso un script antiguo que depende obligatoriamente de un `.env` fisico al lado del archivo puede fallar aunque APP Scheduler haya cargado correctamente las variables.

La regla recomendada es que los scripts lean `os.getenv()` y que cualquier carga local de `.env` sea opcional.

### 7. Que archivos participan en la ejecucion de scripts?

* `app/rutas_ejecuciones.py`: endpoint de ejecucion manual.
* `app/servicios/servicio_ejecuciones.py`: validacion, creacion de ejecucion, log, hilo de monitoreo y cierre.
* `app/repositorios/repositorio_ejecuciones.py`: contexto de tarea/script/version y persistencia de ejecuciones.
* `app/servicios/servicio_env_scripts.py`: carga segura del `.env` por version.
* `app/servicios/servicio_procesos.py`: `subprocess.Popen()` con `env`.
* `app/servicios/servicio_logs_ejecucion.py`: escritura normalizada de salida.
* `scheduler_worker.py`: dispara ejecuciones automaticas mediante el motor comun, pero no requiere cambios para el soporte actual.

### 8. Que tablas/campos participan?

Tablas principales:

* `tareas`
* `scripts`
* `scripts_versiones`
* `ejecuciones`
* `logs_tareas`
* `logs_sistema`
* `auditoria_cambios`

Campos relevantes en `scripts_versiones`:

* `id_version`
* `id_script`
* `numero_version`
* `nombre_archivo`
* `ruta_fisica`
* `ruta_relativa`
* `estado_version`
* `es_activa`
* `requiere_env`
* `ruta_env_fisica`
* `ruta_env_relativa`

No existe tabla `variables_entorno` ni tabla `env_scripts` en SQL Server. `env_scripts` es carpeta fisica.

### 9. Que falta para que el usuario pueda pegar o adjuntar un .env desde la app?

Adjuntar archivo ya existe.

Falta permitir pegar contenido desde un textarea y guardarlo de forma segura. La opcion minima es:

* agregar textarea `contenido_env` en el panel `.env` de cada version;
* validar formato `KEY=VALUE`;
* crear internamente un archivo `.env` bajo la misma ruta `env_scripts/.../vX/.env`;
* seguir guardando solo `ruta_env_fisica` y `ruta_env_relativa` en `scripts_versiones`;
* nunca mostrar el contenido despues de guardar;
* mostrar solo estado y, opcionalmente, nombres de claves enmascaradas.

### 10. Se requiere migracion o ya existe estructura suficiente?

Para la implementacion minima recomendada no se requiere migracion.

La estructura actual ya permite asociar un `.env` a una version mediante rutas. Si el contenido pegado se convierte en archivo `.env` dentro de `env_scripts/`, se reutilizan `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa`.

Una migracion solo seria necesaria si se decide guardar variables estructuradas en BD. Esa alternativa no es la minima y aumenta el riesgo por manejo de secretos.

### 11. Riesgos detectados

* Los archivos `.env` de script contienen secretos; deben seguir excluidos de Git y no aparecer en logs.
* El contenido del `.env` no debe mostrarse de vuelta en UI despues de guardar.
* `dotenv_values()` acepta sintaxis mas amplia que `KEY=VALUE`; si se implementa textarea, conviene validar reglas simples antes de guardar.
* Si un script imprime variables sensibles por stdout, APP Scheduler no puede ocultarlas sin filtrar la salida del script. La regla operativa debe prohibir imprimir secretos.
* Scripts antiguos que cargan `.env` local de forma obligatoria pueden fallar si no existe un archivo al lado del `.py`.
* `ruta_env_fisica` guarda una ruta absoluta del ambiente. Ya existe, pero para portabilidad futura conviene depender operacionalmente de `ruta_env_relativa`.
* Reemplazar una version no cambia hoy su `.env`; esto puede ser correcto o riesgoso segun si el nuevo script espera variables distintas.

## Propuesta minima recomendada

Implementar en una fase posterior una mejora acotada sobre la estructura actual, sin migracion:

1. Mantener `.env` asociado a `scripts_versiones`.
2. Mantener almacenamiento fisico bajo `env_scripts/`.
3. Mantener en BD solo `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa`.
4. Agregar textarea en `app/templates/scripts/listado.html` para pegar contenido `.env`.
5. Mantener input de archivo `.env` como alternativa.
6. En `app/rutas_scripts.py`, pasar `request.form.get("contenido_env")` a `guardar_env_version()`.
7. En `app/servicios/servicio_scripts.py`, aceptar archivo o texto, validando que no vengan ambos con contenido al mismo tiempo salvo decision explicita de prioridad.
8. Crear helper nuevo o funcion interna para validar lineas utiles `KEY=VALUE`.
9. Guardar el texto validado como archivo `.env` usando la misma ruta segura actual.
10. Cambiar el mensaje de bloqueo cuando falta configuracion a:

```text
El script requiere .env, pero no tiene variables de entorno configuradas en APP Scheduler.
```

11. Mostrar en UI:

```text
.env requerido: Si/No
.env configurado: Si/No
Contenido .env: no mostrado por seguridad
```

12. Documentar que los scripts deben usar:

```python
import os
valor = os.getenv("NOMBRE_VARIABLE")
```

## Migracion opcional no recomendada para la primera mejora

Alternativa: crear tabla `scripts_versiones_env_variables` con una fila por clave.

Impacto:

* permitiria mostrar claves individuales y auditar cambios por clave;
* obligaria a definir cifrado/enmascaramiento/rotacion de secretos;
* ampliaria superficie de seguridad;
* requeriria migracion, repositorio nuevo, UI nueva y politicas de borrado;
* aumentaria riesgo de exposicion accidental.

Rollback esperado si se hiciera:

* desactivar lectura desde la tabla;
* volver a usar `ruta_env_relativa`;
* conservar tabla sin mostrar valores;
* borrar valores sensibles solo mediante procedimiento controlado.

Recomendacion: no aplicar esta alternativa hasta que exista decision formal de cifrado de secretos en BD.

## Regla oficial para scripts

Los scripts ejecutados por APP Scheduler deben leer variables desde el entorno:

```python
import os

sql_server = os.getenv("SQL_SERVER")
```

No deben depender obligatoriamente de un archivo `.env` fisico junto al `.py`.

Si un script antiguo tiene funcion `cargar_env()`, debe ser opcional:

```python
from pathlib import Path
from dotenv import load_dotenv

env_local = Path(__file__).with_name(".env")
if env_local.exists():
    load_dotenv(env_local, override=False)
```

Despues de eso, el script debe seguir leyendo con `os.getenv()`.

## Cierre del diagnostico

La plataforma ya carga e inyecta `.env` por version cuando existe archivo asociado. La implementacion minima pendiente es mejorar la UI/servicio para que el usuario pueda pegar contenido `.env` desde la app, con validacion simple, sin exponer secretos y sin requerir copia manual en carpetas fisicas.
