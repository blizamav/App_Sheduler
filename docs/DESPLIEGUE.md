# Despliegue

## Ejecucion local en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

## QA Ubuntu

Pendiente para Fase 11. Debe ejecutarse idealmente con Docker, `.env` propio y volumenes para scripts y logs.

## Produccion Ubuntu

Pendiente para Fase 11. Debe usar Docker, volumenes persistentes, respaldo de base de datos, respaldo de scripts y respaldo de logs.

## Variables por ambiente

Cada ambiente debe tener su propio `.env`; nunca debe versionarse.

## Docker

Pendiente para Fase 11.

## Volumenes

* Scripts: `RUTA_BASE_SCRIPTS`
* Logs de tareas: `RUTA_BASE_LOGS_TAREAS`
* Logs de sistema: `RUTA_BASE_LOGS_SISTEMA`

## Consideraciones de seguridad

No subir secretos, logs reales, scripts productivos ni configuraciones privadas.
