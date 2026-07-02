# Checklist de despliegue y validacion de ambiente

## Proposito

Este checklist ordena la instalacion limpia, configuracion y validacion de APP Scheduler en un ambiente nuevo.

Objetivos:

- Validar una instalacion SQL limpia.
- Validar que el ambiente de aplicacion responde correctamente.
- Evitar despliegues improvisados o cambios no trazados.

## Precondiciones

- SQL Server disponible.
- Usuario SQL/Windows con permisos para crear la base destino.
- SQL Server Management Studio instalado.
- `Query > SQLCMD Mode` disponible y activado para ejecutar el release.
- Python instalado.
- Dependencias del proyecto instalables desde `requirements.txt`.
- Repositorio actualizado.
- Archivo `.env` preparado manualmente por ambiente.
- Si Docker necesita escape distinto de `$`, preparar archivo separado basado en `.env.docker.example`.
- Respaldo disponible antes de tocar bases con datos reales.
- Docker y Docker Compose disponibles si se valida el modo contenedorizado de Fase 14E.

No ejecutar sobre bases reales sin respaldo y aprobacion explicita.

## Instalacion SQL limpia

Fuente oficial:

```text
database/release/
```

Punto de entrada oficial:

```text
database/release/000_ejecutar_instalacion_completa.sql
```

Pasos:

1. Abrir SQL Server Management Studio.
2. Activar `Query > SQLCMD Mode`.
3. Abrir `database/release/000_ejecutar_instalacion_completa.sql`.
4. Configurar `DB_NAME` en el script maestro.
5. Ejecutar el script maestro completo.
6. Revisar la salida de `099_validacion_instalacion.sql`.

Validaciones esperadas:

- `base_actual = DB_NAME`.
- `resultado = OK`.
- Roles reales:
  - `ADMIN = 37` permisos.
  - `SUPER_ADMIN = 39` permisos.
  - `TI = 31` permisos.
  - `TERCERO = 7` permisos.
- `OPERADOR = 0`.
- Catalogos con nombres no nulos.
- Configuracion inicial valida.
- Tablas operativas vacias.
- Sin rutas locales.
- Sin secretos.

`database/legacy_pre_release_13B/` es historico y no es fuente operativa para instalaciones nuevas.

## Configuracion .env

- Respaldar `.env` antes de cambiarlo.
- Cambiar solo variables necesarias para el ambiente.
- `DB_DATABASE` debe apuntar a la base instalada con `DB_NAME`.
- No commitear `.env`.
- No documentar secretos reales.
- Validar variables de bootstrap admin.
- Validar conexion SQL desde la app o ruta diagnostica permitida por ambiente.

## Levantamiento de app

Comandos base en Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Validar:

- La app levanta sin error de conexion.
- Login funciona.
- Panel principal carga.
- Si `/panel` muestra `Advertencias tecnicas del panel`, registrar el origen exacto antes de continuar. El login bootstrap desde `.env` no prueba conectividad SQL Server.
- Verificar parametros ODBC efectivos: `DB_DRIVER`, `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE` y `DB_TIMEOUT`.

## Validacion funcional minima

- `/panel` carga.
- Si `/panel` carga con advertencias, el detalle visible debe identificar el bloque fallido (`metricas_panel`, `configuracion_scheduler` o `ejecuciones_recientes`).
- Usuarios carga.
- Tareas carga vacio.
- Scripts carga vacio.
- Ejecuciones carga vacio.
- Scheduler/configuracion carga.
- Scheduler/eventos carga vacio.
- Papelera carga vacia.
- Logs no presentan error critico.
- No hay error 500.

## Validacion scheduler

- Scheduler debe quedar apagado o con ejecucion automatica deshabilitada por defecto.
- Worker no debe arrancar automaticamente sin decision explicita.
- Worker no debe ejecutarse dentro del proceso Flask.
- En desarrollo local, levantar worker en terminal separada solo para prueba controlada.
- En QA/Produccion, usar proceso separado para web y worker.
- Si se usa Docker Compose, confirmar que existan solo dos servicios operativos: `web` y `worker`.
- No levantar dos contenedores `worker` para el mismo ambiente.
- Worker no debe registrar ruido operativo.
- Si se levanta el worker, debe generar `logs/worker_console.log` como buffer visual local y mantener salida visible en terminal.
- Si se levanta el worker y la sesion tiene permiso `SCHEDULER_CONFIG_VER`, `/api/worker/estado` y `/api/worker/consola` deben responder sin exponer secretos.
- Si se prueba worker, debe hacerse con tarea controlada.
- No activar scheduler en produccion sin configuracion revisada.

Validacion opcional Docker Compose:

- `docker compose up -d --build`
- `docker compose ps`
- `docker compose logs -f worker`
- `docker compose stop worker`
- `docker compose up -d worker`

Si Docker requiere un archivo distinto por escape de password:

- crear `.env.docker` desde `.env.docker.example`;
- usar `DOCKER_ENV_FILE=.env.docker`;
- no sobrescribir `.env` local;
- no versionar `.env.docker`.
- validar que `APP_SECRET_KEY` no siga en valor de plantilla;
- validar helper real con `obtener_conexion()` antes de levantar `worker`.

Referencia operativa:

```text
docs/OPERACION_WORKER.md
```

## Validacion SQL posterior a login

Conteos esperados despues de levantar la app y probar login:

- `usuarios` puede tener 1 registro si bootstrap creo admin.
- `tareas = 0`.
- `scripts = 0`.
- `ejecuciones = 0`.
- `scheduler_eventos = 0`, salvo prueba explicita.
- `logs_sistema` y `auditoria_cambios` pueden tener registros minimos por login/bootstrap.

## Criterio de aprobacion

El ambiente queda aprobado solo si:

- SQL instalado OK.
- `099_validacion_instalacion.sql` OK.
- App levanta.
- Login OK.
- Modulos base OK.
- Sin error 500.
- Sin datos operativos reales.
- Sin secretos.
- Scheduler seguro por defecto.

## Rollback

Si la validacion falla:

1. Detener app.
2. Restaurar `.env` original.
3. Borrar solo base de prueba si corresponde.
4. No borrar bases reales sin respaldo.
5. Registrar hallazgos en `log_codex.md`.

## Evidencia sugerida

- Captura o salida de `099_validacion_instalacion.sql`.
- Resultado de login.
- Resultado de modulos base.
- Conteos SQL principales.
- `git status` limpio antes de cerrar despliegue.
