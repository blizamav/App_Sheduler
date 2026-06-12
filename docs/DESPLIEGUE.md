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

## Ejecucion manual de scripts SQL Server

Los scripts de Fase 3B se encuentran en `database/` y deben ejecutarse manualmente desde SQL Server Management Studio cuando se apruebe crear la base fisicamente.

Orden:

1. `database/migrations/001_crear_base_datos.sql`
2. `database/migrations/002_crear_catalogos.sql`
3. `database/migrations/003_crear_tablas_seguridad.sql`
4. `database/migrations/004_crear_tablas_negocio.sql`
5. `database/migrations/005_crear_tablas_ejecucion_logs.sql`
6. `database/migrations/006_crear_indices.sql`
7. `database/seeds/001_datos_iniciales_catalogos.sql`
8. `database/seeds/002_roles_permisos_iniciales.sql`

Consideraciones:

* No ejecutar contra produccion sin respaldo y aprobacion.
* No modificar scripts para incluir claves, usuarios o servidores reales.
* El usuario inicial de aplicacion sigue validandose desde `.env`; los seeds no crean usuario `blizama`.
* La conexion Flask-SQL Server queda pendiente para una fase posterior.

## Docker

Pendiente para Fase 11.

## Volumenes

* Scripts: `RUTA_BASE_SCRIPTS`
* Logs de tareas: `RUTA_BASE_LOGS_TAREAS`
* Logs de sistema: `RUTA_BASE_LOGS_SISTEMA`

## Consideraciones de seguridad

No subir secretos, logs reales, scripts productivos ni configuraciones privadas.
