# Arquitectura

## Arquitectura general

La Fase 1 define una aplicacion Flask modular con fabrica `crear_app()`, configuracion centralizada y rutas separadas en Blueprint.

## Capas del sistema

* Presentacion: templates HTML y assets CSS/JS.
* Aplicacion: rutas Flask y control de sesion.
* Configuracion: lectura de `.env`.
* Datos: pendiente para Fase 3 con SQL Server.
* Servicios: pendientes para tareas, scripts, logs, auditoria y scheduler.

## Flujo de datos inicial

1. Usuario accede a `/login`.
2. Flask valida credenciales contra variables de entorno.
3. Se crea sesion segura con `APP_SECRET_KEY`.
4. Usuario entra a `/panel`.

## Backend

Backend Python Flask con estructura inicial:

* `app/__init__.py`
* `app/config.py`
* `app/rutas.py`

## Frontend

HTML/CSS/JS sin Streamlit. Desde Fase 2 el layout incluye login corporativo, sidebar responsive, topbar con usuario, tarjetas de metricas, tabla base, badges de estado y panel lateral visual preparado para logs.

La capa visual sigue siendo estatica y no consume base de datos. Los datos del panel son placeholders hasta las fases funcionales.

## Base de datos

SQL Server sera incorporado desde Fase 3. Base objetivo: `APP_SCHEDULER_QA`, configurable por `.env`.

## Scheduler

Pendiente para Fase 8. Debe ejecutarse como servicio separado dentro de la aplicacion.

## Logs

Pendiente para Fase 9. Rutas configurables por `.env`: `logs_tareas` y `logs_sistema`.

## Seguridad

Fase 1 usa login inicial desde `.env`. En fases posteriores se incorporan usuarios, roles, permisos, auditoria y logs de seguridad.

## Docker

Pendiente para Fase 11. La arquitectura ya evita rutas absolutas para facilitar portabilidad.
