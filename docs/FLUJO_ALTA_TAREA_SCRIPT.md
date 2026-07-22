# Flujo alta de tarea con script inicial

## Objetivo

Fase 17A agrega una via opcional para crear una tarea y dejar cargada su version inicial de script desde la misma pantalla.

No reemplaza el modulo `Scripts`. Solo reduce pasos cuando el usuario ya tiene el archivo Python y, opcionalmente, el `.env` de ejecucion.

## Alta de tarea sin script

1. Entrar a `Tareas > Nueva tarea`.
2. Completar datos generales y programacion.
3. No marcar `Configurar script inicial ahora`.
4. Guardar.

Resultado: la tarea se crea como antes y el script puede configurarse luego desde el modulo `Scripts`.

## Alta de tarea con script inicial

1. Entrar a `Tareas > Nueva tarea`.
2. Completar datos generales y programacion.
3. Marcar `Configurar script inicial ahora`.
4. Adjuntar un archivo Python `.py`.
5. Guardar.

Resultado: APP Scheduler crea el contenedor logico de script, carga la version `v1`, la deja activa y guarda el archivo bajo la estructura existente de `scripts/`.

## Alta de tarea con script inicial y .env

1. Marcar `Configurar script inicial ahora`.
2. Adjuntar el archivo Python `.py`.
3. Marcar `Este script requiere archivo .env`.
4. Pegar contenido `.env` o adjuntar archivo `.env`.
5. Guardar.

Resultado: APP Scheduler guarda el `.env` bajo `env_scripts/`, actualiza `scripts_versiones.requiere_env`, `ruta_env_fisica` y `ruta_env_relativa`, y la version `v1` queda lista para ejecucion.

## Reglas

* No se piden rutas fisicas al usuario.
* No se copia el `.env` junto al `.py`; se guarda en `env_scripts/`.
* No se permite pegar contenido `.env` y adjuntar archivo `.env` al mismo tiempo.
* Si una version requiere `.env`, debe informarse durante el alta o guardarse luego desde `Scripts`.
* El contenido del `.env` no se muestra despues de guardar.
* El script debe leer variables con `os.getenv()`.

Ejemplo:

```python
import os

ambiente = os.getenv("AMBIENTE")
```

## Seguridad

No escribir secretos reales en documentacion, logs, capturas ni tickets.

No declarar passwords, tokens ni claves dentro del script Python.

No imprimir variables sensibles en stdout/stderr.

## Riesgo conocido

La creacion combina base de datos y archivos fisicos. La app valida archivo `.py` y `.env` antes de crear la tarea para reducir inconsistencias. Si ocurre un error posterior no previsto al guardar el archivo o la metadata, la tarea puede quedar creada sin script inicial y el usuario debe corregirlo desde el modulo `Scripts`.
