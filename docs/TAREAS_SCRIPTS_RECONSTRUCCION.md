# Tareas y scripts reconstruidos

## Estado y alcance

Hito 5 esta cerrado en el runtime aislado `src/app_scheduler/`.
Hito 6 agrega programaciones y reserva automatica sin alterar las reglas de
scripts. Hito 7 ejecuta la version congelada con un motor unico; el runtime
historico sigue activo y no existe cutover.

El ajuste post-Hito 10 agrega un flujo guiado no transaccional: Datos, Script,
Evidencia, Notificaciones y Programacion. `Guardar` crea la tarea y vuelve al
listado; `Guardar y continuar` crea la misma tarea y abre su panel de Script.
Una tarea puede existir sin script y un script sin Evidencia 1.0 sigue siendo
ejecutable y apto para notificaciones estandar de exito o error.

Para manuales se usa exclusivamente `scripts.id_version_activa`, como en el
contrato historico. La version, ruta y snapshots se congelan al reservar. El
motor valida nuevamente que la ruta fisica persista dentro del root autorizado,
pero no cambia a una version que se active despues.

## Contrato SQL

`tareas` conserva nombre, descripcion, observacion tecnica, cliente, categoria,
tipo, `tipo_tarea`, `estado_tarea`, permiso manual, fechas, auditoria tecnica,
Papelera y `activo`. Hito 5 crea `tipo_tarea = MANUAL`; los estados operativos
aceptados son `ACTIVA`, `INACTIVA` y `SUSPENDIDA`.

`scripts` es un contenedor logico 1:1 con tarea por `UNIQUE(id_tarea)` y guarda
`id_version_activa`. `scripts_versiones` guarda slot 1-3, archivo, rutas, SHA-256,
estado, bandera activa, metadata `.env`, actor y fechas. El esquema refuerza:

* `CHECK(numero_version BETWEEN 1 AND 3)`;
* `UNIQUE(id_script, numero_version)`;
* indice unico filtrado por `es_activa = 1`;
* estados `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA` e `INACTIVA`.

## Politica de tres slots

La primera carga crea el contenedor, v1 y la deja activa. Con uno o dos slots
ocupados se usa el menor slot libre. Con tres slots no existe v4. El operador
debe elegir explicitamente un slot no activo. El reemplazo se bloquea si
`ejecuciones.id_version` contiene referencias; no se elimina historia para
liberar espacio. En el esquema limpio no existe otra referencia funcional
directa hacia `scripts_versiones.id_version`.

Activar una version actualiza la anterior, la nueva y `scripts.id_version_activa`
en una sola UoW. Solo `DISPONIBLE` o `INACTIVA` pueden activarse. La version
activa no se desactiva ni reemplaza.

## Filesystem y compensacion

Estructura vigente:

```text
scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vN/archivo.py
env_scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vN/.env
```

Los roots provienen de `RUTA_BASE_SCRIPTS` y `RUTA_BASE_ENV_SCRIPTS`. Los
segmentos se normalizan, la ruta canonica debe quedar dentro del root y cualquier
symlink inseguro falla cerrado. El navegador nunca proporciona rutas.

La carga valida extension, tamano, UTF-8 y sintaxis con AST sin importar o
ejecutar codigo. `.env` valida tamano y `KEY=VALUE`; su contenido no se guarda
en SQL, logs ni auditoria. SQL conserva solo rutas y metadata.

Cada escritura se prepara como temporal en el mismo volumen. Antes del commit
se promueve atomicamente y el archivo anterior, si existe, se mueve a respaldo.
Si falla filesystem, SQL no confirma. Si falla SQL o auditoria, se restaura el
archivo anterior y se retiran temporal/nuevo. Tras commit se elimina el respaldo.

## Rutas y permisos

| Ruta | Metodo | Permiso |
| --- | --- | --- |
| `/tareas/` | GET | `TAREAS_VER` |
| `/tareas/nueva` | GET/POST | `TAREAS_CREAR` |
| `/tareas/<id>/editar` | GET/POST | `TAREAS_EDITAR` |
| `/tareas/<id>/estado` | POST | `TAREAS_ESTADO` |
| `/scripts` | GET | `SCRIPTS_VER` |
| `/tareas/<id>/scripts` | GET | `SCRIPTS_VER` |
| `/tareas/<id>/scripts/versiones` | POST | `SCRIPTS_VERSIONAR` |
| `.../<id_version>/reemplazar` | POST | `SCRIPTS_REEMPLAZAR` |
| `.../<id_version>/activar` | POST | `SCRIPTS_ACTIVAR_VERSION` |
| `.../<id_version>/desactivar` | POST | `SCRIPTS_DESACTIVAR` |
| `.../<id_version>/env` | POST | `SCRIPTS_ENV_GESTIONAR` |
| `.../<id_version>/env/quitar` | POST | `SCRIPTS_ENV_GESTIONAR` |
| `.../<id_version>/descargar` | GET | `SCRIPTS_VER` |

El detalle de script muestra el estado ejecutable de la version activa, el
estado independiente de Evidencia (`Compatible 1.0`, `No implementada` o
`Requiere ajuste`) y el acceso a Notificaciones. El stepper enlaza las cinco
etapas sin introducir SPA ni una transaccion gigante.

`SUPER_ADMIN` y `ADMIN` reciben todos estos permisos. `TI` recibe tareas
operativas, carga/versionado/activacion/reemplazo y `.env`, pero bootstrap no le
asigna `SCRIPTS_DESACTIVAR`. `TERCERO` recibe solo `TAREAS_VER`,
`TAREAS_EJECUTAR` y `SCRIPTS_VER`; la ejecucion manual existe desde Hito 7 y
requiere `EJECUCIONES_EJECUTAR` en la matriz efectiva del usuario.

## Auditoria

Altas, ediciones, estados, cargas, reemplazos, activaciones, desactivaciones y
cambios `.env` comparten UoW con `auditoria_cambios`. Se registra actor, entidad,
ID, contexto HTTP y metadata sanitizada. No se audita codigo completo ni valores
de entorno.

## Usuario ejecutor

`dbo.tareas` no posee `id_usuario_ejecutor` ni campo equivalente. Hito 6 confirma
que una automatica tampoco inventa ese usuario: reserva con
`ejecuciones.usuario_ejecucion = NULL` y conserva el actor tecnico en
`nombre_worker`. La version activa se resuelve al disparar y se congela mediante
`ejecuciones.id_script` e `id_version`. La seleccion de usuario para una futura
ejecucion manual pertenece al Hito 7.

## Pruebas y deuda legitima

La cobertura automatizada incluye reglas de tarea, permisos, CSRF, mass
assignment, validacion `.py`/`.env`, slots 0-3, v4 bloqueada, activa/historial,
compensacion, colisiones, rutas confinadas, secretos y repositorios sin commit.

Resultado de cierre: 32 casos nuevos y 123 pruebas reconstruidas aprobadas; la
suite completa aprueba 149. Una prueba de symlink se omite en Windows porque el
host no permite crearlo, pero el mismo escenario se valido correctamente en un
contenedor Linux efimero. La cobertura incluye cambio v1-v2, unica activa,
transiciones invalidas, rollback y descargas negativas. Compose es valido y las
imagenes `web` y `worker` se construyeron correctamente el 2026-08-19.
La inspeccion responsive automatizada sigue pendiente por un fallo del conector
de navegador, sin dejar servidor temporal activo.

Deuda deliberada: falta prueba de integracion contra SQL Server/QA y validacion
manual visual con datos reales; no se realizan en Hito 5 sin autorizacion. La
clave funcional de tarea no tiene UNIQUE fisico y se controla en servicio.

## Acceso transversal desde el Hito 7

El indice global `/scripts` permite buscar por script, tarea o cliente, filtrar
por estado y version activa, y paginar resultados. Cada resultado muestra
estado, version activa, slots ocupados, cantidad de versiones con `.env` y
ultima actualizacion. No muestra rutas ni valores de entorno.

La accion `Administrar` reutiliza `/tareas/<id_tarea>/scripts`; al entrar desde
el hub, breadcrumb y retorno vuelven a `Scripts`. El detalle representa siempre
v1, v2 y v3, incluidos los slots vacios. Crear un script sigue requiriendo una
tarea: el hub no ofrece alta independiente ni altera la relacion 1:1.

## Flujo guiado definitivo post-Hito 10

El onboarding no es una transaccion unica: cada paso persiste su propio estado.
Datos permite guardar o guardar y continuar. Script ofrece `Cargar version`, la
alternativa explicita `Omitir Script por ahora`, `Activar Vn` cuando corresponde
y `Continuar a Evidencia` una vez que la version activa esta lista.

Evidencia dispone de una ruta y pantalla propias para analizar el contrato 1.0
sin duplicar campos editables de Datos. Notificaciones mantiene independientes
Exito, Error y el contenido adicional opcional de Evidencia. Programacion
permite configurar una agenda o finalizar explicitamente sin programacion.

Las rutas de Evidencia y Notificaciones conservan autorizacion backend y CSRF
en mutaciones. El bloqueo global de mantenimiento se consulta mediante el
control runtime fail-closed; ocultar o deshabilitar una accion en UI nunca
reemplaza esa validacion.
