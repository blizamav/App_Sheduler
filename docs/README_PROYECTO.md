# APP Scheduler - README del proyecto

## Descripcion general

APP Scheduler es una aplicacion web corporativa para crear, programar, ejecutar, monitorear y preparar auditoria de tareas Python usadas por equipos TI.

## Objetivo

Centralizar la ejecucion controlada de scripts, reducir trabajo manual, mantener trazabilidad completa y preparar despliegues en LOCAL, QA y PRODUCCION.

## Stack tecnologico

* Backend: Python, Flask, Blueprints.
* Frontend: HTML, CSS y JavaScript.
* Base de datos objetivo: SQL Server.
* Configuracion: `.env`.
* Infraestructura objetivo: Docker Compose o systemd en QA y PRODUCCION, pendiente para Fase 13.

## Estado actual

Estado: Fase 11F implementada.

Incluye login hibrido, usuarios/roles/permisos, mantenedores, tareas programables, scripts versionados, `.env` por version, ejecucion manual, consola, detencion manual, historial, scheduler automatico, configuracion del programador, worker separado, heartbeat, feriados locales, sincronizacion Nager.Date, eventos del programador, control de ejecuciones huerfanas y borrado operativo seguro con snapshots.

El roadmap formal esta en `docs/ROADMAP.md`.

## Como levantar el proyecto

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
python run.py
```

Abrir `http://127.0.0.1:5000`.

## Estructura general

* `app/`: aplicacion Flask.
* `app/templates/`: vistas HTML.
* `app/static/`: CSS y JavaScript.
* `docs/`: documentacion tecnica.
* `docs/ROADMAP.md`: roadmap formal vigente.
* `run.py`: entrada local.
* `.env.example`: variables requeridas.
* `log_codex.md`: bitacora tecnica.

## Variables de entorno

Las variables obligatorias estan documentadas en `.env.example`. El archivo `.env` real no debe versionarse.

## Comandos utiles

* Instalar dependencias: `pip install -r requirements.txt`
* Ejecutar local: `python run.py`
* Validar sintaxis base: `python -m compileall app scheduler_worker.py`
