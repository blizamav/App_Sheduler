# Uso de .env por scripts

## Que es el .env por script

El `.env` por script permite definir variables de entorno especificas para una version de script cargada en APP Scheduler.

Sirve para que el script lea parametros como servidor, base de datos, usuario tecnico, host SFTP, puerto o limites de trabajo sin dejar esos valores quemados en el codigo Python.

## Donde se configura

Se configura en:

```text
Tareas > Scripts > Versiones > boton .env
```

La configuracion es por version. Una tarea puede tener hasta 3 versiones de script y cada version puede tener su propio estado `.env`.

Estados visibles:

* `.env: No requiere`
* `.env: Pendiente .env`
* `.env: Asociado`

## Flujo actual

1. Abrir la tarea.
2. Entrar a `Scripts`.
3. Subir o seleccionar una version.
4. Abrir el panel `.env` de esa version.
5. Marcar `Este script requiere archivo .env` si corresponde.
6. Pegar contenido en `Contenido .env` o adjuntar un archivo `.env`.
7. Guardar.
8. Ejecutar la tarea.

APP Scheduler carga ese archivo e inyecta sus variables al proceso Python.

## Contenido pegado desde la app

Desde Fase 16B se puede pegar contenido `.env` directamente en la app, ademas de adjuntar archivo.

El usuario no deberia copiar manualmente archivos dentro de:

```text
scripts/.../v1/.env
scripts/.../v2/.env
scripts/.../v3/.env
```

APP Scheduler guarda la configuracion en su carpeta segura de `env_scripts/` y la asocia a la version correspondiente usando los campos existentes de `scripts_versiones`.

Si se pega contenido y tambien se adjunta archivo en el mismo envio, la app rechaza la operacion para evitar ambiguedad.

## Formato correcto

Formato simple:

```env
KEY=VALUE
OTRA_KEY=OTRO_VALOR
```

Reglas aplicadas:

* las lineas vacias se ignoran;
* las lineas que empiezan con `#` se ignoran;
* cada linea util debe tener `KEY=VALUE`;
* `KEY` no puede venir vacio;
* `VALUE` puede venir vacio;
* `VALUE` puede contener espacios;
* `VALUE` puede contener backslash;
* `VALUE` puede contener rutas UNC;
* `VALUE` puede contener simbolos;
* no se deben exigir comillas;
* si vienen comillas simples o dobles, el valor no debe romperse.

Ejemplo sin secretos reales:

```env
SQL_SERVER=SERVIDOR\INSTANCIA
SQL_DATABASE=BASE_DATOS
SQL_USERNAME=usuario
SQL_PASSWORD=********
SFTP_HOST=192.168.0.150
SFTP_USERNAME=usuario_sftp
SFTP_PASSWORD=********
SFTP_PORT=22
MAX_WORKERS=4
```

## Como debe leer variables el script

El script debe usar `os.getenv()`:

```python
import os

sql_server = os.getenv("SQL_SERVER")
sql_database = os.getenv("SQL_DATABASE")
sftp_host = os.getenv("SFTP_HOST")
max_workers = int(os.getenv("MAX_WORKERS", "1"))
```

Si falta una variable obligatoria, el script debe fallar con un mensaje claro, sin imprimir secretos:

```python
if not sql_server:
    raise RuntimeError("Falta variable requerida: SQL_SERVER")
```

## Ayuda visible en la app

Desde Fase 16C, el panel `Variables de entorno del script` incluye una ayuda desplegable dentro de:

```text
Tareas > Scripts > Versiones > boton .env
```

La ayuda muestra:

* que APP Scheduler carga el `.env` antes de ejecutar la version;
* que el script debe leer valores con `os.getenv()`;
* que el script no debe exigir un `.env` fisico local junto al `.py`;
* ejemplo corto de script compatible;
* ejemplo de formato `.env` sin secretos reales;
* ejemplo de carga local opcional para scripts que tambien se ejecutan fuera de APP Scheduler.

La ayuda no muestra secretos reales y mantiene el contenido guardado oculto.

## Que no hacer

No declarar passwords, tokens ni secretos directamente en el codigo Python.

No imprimir secretos:

```python
print(os.getenv("SQL_PASSWORD"))
```

No depender obligatoriamente de un `.env` fisico junto al `.py`:

```python
load_dotenv(".env")
```

Si un script antiguo necesita cargar `.env` local para ejecucion fuera de APP Scheduler, debe hacerlo de forma opcional:

```python
from pathlib import Path
from dotenv import load_dotenv

env_local = Path(__file__).with_name(".env")
if env_local.exists():
    load_dotenv(env_local, override=False)
```

Luego debe leer siempre con `os.getenv()`.

## Seguridad

APP Scheduler no debe mostrar el contenido del `.env` despues de guardar.

Claves sensibles deben enmascararse en cualquier vista o documentacion:

* `PASSWORD`
* `PASS`
* `SECRET`
* `TOKEN`
* `KEY`
* `CLIENT_SECRET`

Los logs esperados son:

```text
.env requerido: Si
.env cargado correctamente
Contenido .env: no mostrado por seguridad.
```

Nunca deben aparecer valores reales de password, token, secret o connection string en logs, changelog o bitacoras.

## Como probar

1. Crear un script de prueba que lea una variable no sensible:

```python
import os

cliente = os.getenv("CLIENTE_PRUEBA")
if not cliente:
    raise RuntimeError("Falta variable requerida: CLIENTE_PRUEBA")

print("Variable CLIENTE_PRUEBA disponible")
```

2. Configurar `.env` de la version:

```env
CLIENTE_PRUEBA=DEMO
```

3. Ejecutar la tarea desde APP Scheduler.
4. Revisar el log de ejecucion.

Resultado esperado:

```text
.env requerido: Si
.env cargado correctamente
Variable CLIENTE_PRUEBA disponible
```

## Mensajes esperados

Si la version no requiere `.env`:

```text
.env requerido: No
.env no requerido
```

Si la version requiere `.env` y esta configurado:

```text
.env requerido: Si
.env cargado correctamente
```

Si la version requiere `.env` y no tiene configuracion, APP Scheduler muestra:

```text
El script requiere .env, pero no tiene variables de entorno configuradas en APP Scheduler.
```

## Regla final

El `.env` de APP Scheduler raiz configura la aplicacion.

El `.env` por script configura solo la ejecucion de una version de script.

No mezclar ambos usos.
