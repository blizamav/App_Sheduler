# APP Scheduler - README del proyecto

## Descripcion general

APP Scheduler sera una aplicacion web corporativa para crear, programar, ejecutar y auditar tareas Python usadas por equipos TI.

## Objetivo

Centralizar la ejecucion controlada de scripts, reducir trabajo manual, mantener trazabilidad completa y preparar despliegues en LOCAL, QA y PRODUCCION.

## Stack tecnologico

* Backend: Python, Flask, Blueprints.
* Frontend: HTML, CSS y JavaScript.
* Base de datos objetivo: SQL Server.
* Configuracion: `.env`.
* Infraestructura objetivo: Docker en QA y PRODUCCION.

## Como levantar el proyecto

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Abrir `http://127.0.0.1:5000`.

## Estructura general

* `app/`: aplicacion Flask.
* `app/templates/`: vistas HTML.
* `app/static/`: CSS y JavaScript.
* `docs/`: documentacion tecnica.
* `run.py`: entrada local.
* `.env.example`: variables requeridas.
* `log_codex.md`: bitacora tecnica.

## Variables de entorno

Las variables obligatorias estan documentadas en `.env.example`. El archivo `.env` real no debe versionarse.

## Comandos utiles

* Instalar dependencias: `pip install -r requirements.txt`
* Ejecutar local: `python run.py`
* Validar sintaxis: `python -m py_compile run.py app\__init__.py app\config.py app\rutas.py`
