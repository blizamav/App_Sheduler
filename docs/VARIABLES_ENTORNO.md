# Variables de entorno

## Objetivo

Ordenar que archivo de variables usa cada modo del proyecto y dejar trazable para que sirve cada variable, sin exponer secretos.

## Regla central

* `.env` contiene credenciales y valores reales del ambiente.
* `.env` nunca debe versionarse.
* `.env` nunca debe sobrescribirse automaticamente.
* `.env.example` y `.env.docker.example` son solo plantillas.
* Si se necesita otro archivo por ambiente, debe ser plantilla `*.example` versionada y archivo real no versionado.

## Archivos oficiales

| Archivo | Se versiona | Uso |
|---|---|---|
| `.env` | No | Archivo real para ejecucion local y tambien para web/worker fuera de Docker. |
| `.env.example` | Si | Plantilla base para local, QA o produccion sin contenedor. |
| `.env.docker` | No | Archivo real opcional para contenedores cuando Docker requiere valores distintos, por ejemplo escape de `$` en passwords. |
| `.env.docker.example` | Si | Plantilla base para `.env.docker`. |

## Archivos no oficiales

* `.env.prueba` no forma parte del flujo oficial del proyecto y debe considerarse residual.
* `.env.qa` y `.env.prod` no son requeridos por el codigo actual. Si en el futuro se crean, deben permanecer fuera de Git y basarse en una plantilla `*.example`.

## Que archivo usa cada modo

| Modo | Archivo esperado | Observaciones |
|---|---|---|
| Local Windows | `.env` | `app/config.py` carga `BASE_DIR/.env`. |
| QA sin Docker | `.env` | La app web y `scheduler_worker.py` leen variables del proceso y pueden apoyarse en `BASE_DIR/.env`. |
| Docker local o QA | `.env.docker` recomendado | `docker-compose.yml` usa `DOCKER_ENV_FILE`; si no se define, cae a `.env`. |
| Produccion sin Docker | `.env` | Archivo real administrado por el ambiente. |
| Produccion con Docker | `.env.docker` recomendado | Mantiene separadas las necesidades de Docker frente al uso local. |

## Variables vigentes

### Aplicacion

| Variable | Obligatoria | Secreta | Uso | Default actual |
|---|---|---|---|---|
| `APP_ENV` | Si | No | Define ambiente y reglas como diagnosticos solo para `LOCAL` o `QA`. | `LOCAL` |
| `APP_SECRET_KEY` | Si | Si | Firma de sesion Flask. | `CAMBIAR_EN_ENV_REAL` |
| `APP_HOST` | No | No | Host de Flask. En Docker `web` fuerza `0.0.0.0`. | `127.0.0.1` |
| `APP_PORT` | No | No | Puerto de Flask. | `5000` |
| `APP_DEBUG` | No | No | Activa debug de Flask. | `False` en codigo, `True` en `.env.example` |

### SQL Server

| Variable | Obligatoria | Secreta | Uso | Default actual |
|---|---|---|---|---|
| `DB_SERVER` | Si | No | Servidor o instancia SQL Server. | Vacio |
| `DB_DATABASE` | Si | No | Base de datos de la app. | `APP_SCHEDULER_QA` |
| `DB_USER` | Si | Si | Usuario SQL. | Vacio |
| `DB_PASSWORD` | Si | Si | Password SQL. | Vacio |
| `DB_DRIVER` | Si | No | Driver ODBC. | `ODBC Driver 17 for SQL Server` |
| `DB_ENCRYPT` | No | No | Bandera ODBC `Encrypt`. | `no` |
| `DB_TRUST_SERVER_CERTIFICATE` | No | No | Bandera ODBC `TrustServerCertificate`. | `yes` |
| `DB_TIMEOUT` | No | No | `Connection Timeout` ODBC en segundos. | `10` |

### Bootstrap admin

| Variable | Obligatoria | Secreta | Uso | Default actual |
|---|---|---|---|---|
| `USUARIO_ADMIN_DEFECTO` | Si | Si | Usuario bootstrap para login inicial por `.env`. | `blizama` |
| `PASSWORD_ADMIN_DEFECTO` | Si | Si | Password bootstrap para login inicial por `.env`. | Vacio |

### Rutas y limites

| Variable | Obligatoria | Secreta | Uso | Default actual |
|---|---|---|---|---|
| `RUTA_BASE_SCRIPTS` | No | No | Carpeta base de scripts versionados. | `scripts` |
| `RUTA_BASE_ENV_SCRIPTS` | No | No | Carpeta base de `.env` por script/version. | `env_scripts` |
| `RUTA_BASE_LOGS_TAREAS` | No | No | Carpeta base de logs de ejecucion. | `logs_tareas` |
| `RUTA_BASE_LOGS_SISTEMA` | No | No | Carpeta base de logs del sistema. | `logs_sistema` |
| `MAX_SCRIPT_SIZE_MB` | No | No | Tamano maximo de script cargado. | `5` |
| `MAX_ENV_SIZE_KB` | No | No | Tamano maximo de archivo `.env` por version. | `100` |
| `ZONA_HORARIA` | No | No | Zona horaria operativa. | `America/Santiago` |

### Mail Automatico Graph

Fase 15F agrega configuracion global Mail Automatico Graph. Los valores no sensibles se administran desde la UI y base de datos; el `GRAPH_CLIENT_SECRET` debe venir siempre desde entorno.

La migracion 020 ya fue ejecutada manualmente en `APP_SCHEDULER_QA`. Con `GRAPH_CLIENT_SECRET` vacio, la pantalla `/configuracion/mail-graph` debe mostrar `Secret: No configurado` y mantener el servicio inactivo por defecto. La app no muestra ni devuelve el valor real del secret.

| Variable | Obligatoria | Secreta | Uso | Estado |
|---|---|---|---|---|
| `GRAPH_CLIENT_SECRET` | Si para activar Mail Graph | Si | Secreto de aplicacion Graph. Nunca se guarda en BD ni se muestra por UI/API. | Implementada como lectura de entorno |
| `GRAPH_SECRET_CONFIG_MODE` | No | No | Origen del secret. V1 soporta `ENV`. | Implementada |
| `GRAPH_TENANT_ID` | No | No | Fallback documental para Tenant ID si se requiere inicializar por entorno. La UI/BD es fuente principal no sensible. | Plantilla |
| `GRAPH_CLIENT_ID` | No | No | Fallback documental para Client ID si se requiere inicializar por entorno. La UI/BD es fuente principal no sensible. | Plantilla |
| `GRAPH_SCOPE` | No | No | Scope por defecto sugerido. | Plantilla |
| `GRAPH_SEND_MAIL_USER` | No | No | Fallback documental para buzon remitente. La UI/BD es fuente principal no sensible. | Plantilla |
| `GRAPH_MAIL_ENABLED` | No | No | Bandera documental para despliegues; activar envio real queda pendiente. | Plantilla |
| `GRAPH_SAVE_TO_SENT_ITEMS` | No | No | Default sugerido para guardar copia en enviados. | Plantilla |
| `GRAPH_ALERTAS_DEFAULT` | No | No | Default sugerido para alertas globales. | Plantilla |

## Como se cargan hoy

* `app/config.py` ejecuta `load_dotenv(BASE_DIR / ".env", override=False)`.
* Si una variable ya viene inyectada por el proceso, `load_dotenv(..., override=False)` no la pisa.
* En Docker, `docker-compose.yml` inyecta variables por `env_file`; por eso `DOCKER_ENV_FILE` resuelve que archivo entra al contenedor.
* En Docker, `TZ` debe alinearse con `ZONA_HORARIA` para que el monitor del worker, los logs y la hora visible del contenedor hablen el mismo huso horario operativo.
* `app/database/conexion.py` usa solo valores ya cargados en `current_app.config`.

## Variables criticas validadas por la app

La validacion actual considera criticas:

* `APP_SECRET_KEY`
* `DB_SERVER`
* `DB_DATABASE`
* `DB_USER`
* `DB_PASSWORD`
* `DB_DRIVER`
* `USUARIO_ADMIN_DEFECTO`
* `PASSWORD_ADMIN_DEFECTO`

Si faltan o siguen con valores de plantilla, la app debe responder con advertencias controladas y sin mostrar secretos.

## Recomendaciones operativas

* No ejecutar `copy .env.example .env` a ciegas.
* En PowerShell, copiar solo si `.env` no existe.
* No reutilizar automaticamente `.env` local para Docker si la password contiene `$`.
* Para levantar contenedores de forma consistente, exportar antes `DOCKER_ENV_FILE=.env.docker` y mantener ese flujo en comandos `docker compose`.
* Mantener separados los archivos reales por ambiente.
* No documentar ni commitear credenciales reales.

## Validacion real Fase 14F.4

Resultado validado en Docker usando:

```powershell
$env:DOCKER_ENV_FILE=".env.docker"
```

Y desde Fase 14F.5:

```powershell
$env:DOCKER_ENV_FILE=".env.docker"
$env:ZONA_HORARIA="America/Santiago"
```

Con ese flujo:

* `web` y `worker` reciben el mismo archivo real de contenedor.
* `TZ` dentro de Docker queda alineado con `ZONA_HORARIA`.
* El monitor del worker evita falsos `SIN_SENAL` por diferencia UTC vs hora local SQL Server.

Confirmado:

* `docker compose config --services` devuelve `web` y `worker`.
* `docker compose run --rm web ...` recibe valores reales de `DB_SERVER`, `DB_USER` y `DB_PASSWORD` sin caer en placeholder.
* La conexion real con `obtener_conexion()` dentro de Docker responde `CONEXION_APP_OK=1`.
* `docker compose up -d web` levanta correctamente la web.
* Login y `/panel` fueron validados desde dentro del contenedor contra `http://127.0.0.1:5000`.

Hallazgo real:

* Ese hallazgo quedo corregido posteriormente en el ambiente real: durante la validacion final Fase 14G `APP_SECRET_KEY_CONFIGURADA=True`.
* Se mantiene la regla de no exponer el valor ni versionarlo.

Regla aplicada:

* `worker` no se levanto en esta fase porque la instruccion vigente exigia autorizacion adicional del usuario despues de validar conexion y web.

## Validacion real Fase 14G

Confirmado en Docker usando:

```powershell
$env:DOCKER_ENV_FILE=".env.docker"
```

Resultado:

* `docker compose config --services` devuelve `web` y `worker`.
* `APP_SECRET_KEY_CONFIGURADA=True`.
* `DB_SERVER_PLACEHOLDER=False`.
* `DB_USER_CONFIGURADO=True`.
* `DB_PASSWORD_LEN > 0`.
* `DB_ENCRYPT=no`.
* `DB_TRUST_SERVER_CERTIFICATE=yes`.
* `DB_TIMEOUT=10`.
* `ZONA_HORARIA=America/Santiago`.
* `TZ=America/Santiago`.
* Usuario SQL dedicado esperado configurado sin exponer su valor real en la documentacion operativa.
