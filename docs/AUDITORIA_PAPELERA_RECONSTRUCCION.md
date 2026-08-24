# Auditoria y Papelera de la reconstruccion

## Estado y alcance

Hito 9, cerrado, reconstruye la consulta inmutable de `auditoria_cambios` y la Papelera
operativa dentro de `src/app_scheduler/`. El runtime historico sigue siendo el
oficial y no existe cutover. No se modifica el DDL, los seeds, QA ni
`database/release/`.

Papelera no equivale a desactivar. `activo = 0` conserva el registro dentro de
la operacion con estado inactivo; `eliminado_operativo = 1` lo retira de flujos
normales; la eliminacion permanente es excepcional, exige permiso separado y
solo retira recursos operativos que no tengan historia incompatible.

## Contrato de auditoria

La UI usa exclusivamente la semantica canonica:

`fecha_evento`, `usuario`, `id_usuario`, `accion`, `entidad`, `id_entidad`,
`nombre_entidad`, `descripcion`, `valores_antes`, `valores_despues`,
`ip_origen`, `user_agent`, `resultado`, `modulo`, `ruta` y `metodo_http`.

La QA historica conserva seis columnas legacy `NOT NULL`. El repositorio
detecta ese contrato y usa `COALESCE` hacia `fecha_hora`, `tabla_afectada`,
`id_registro`, `valor_anterior`, `valor_nuevo` e `ip`. Estas columnas son
aliases de compatibilidad, no campos adicionales para la UI. La base limpia
continua usando solo el contrato canonico.

| Ruta | Metodo | Permiso | Mutacion |
| --- | --- | --- | --- |
| `/auditoria/` | GET | `AUDITORIA_VER` | No |
| `/auditoria/<id>` | GET | `AUDITORIA_DETALLE` | No |

El listado pagina de 25 en 25 mediante `OFFSET/FETCH`, usa orden fijo por fecha
e ID descendentes y filtra por fecha, usuario, accion, entidad, identificador y
busqueda. Todos los datos usan parametros `?`; no se permite ordenar por valores
del request. Antes/despues se formatea como JSON cuando es valido y siempre se
renderiza como texto autoescapado dentro de `pre`.

No existe ruta para editar, borrar, desactivar o reescribir auditoria.

## Matriz contractual de Papelera

| Entidad | Tabla | Retiro | Restauracion | Eliminacion permanente | Referencias y bloqueo | Filesystem | Permiso de retiro |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Usuarios | `usuarios` | Si; bloquea sesion actual y ultimo administrador | Inactivo, desbloqueado, sin reactivar roles | Si, salvo usuario actual o ultimo administrador | `usuarios_roles`; referencias historicas textuales se preservan | No | `USUARIOS_ADMIN` |
| Clientes | `clientes` | Si | Inactivo; bloquea clave duplicada | Solo sin tareas asociadas | FK entrante desde `tareas` | No | `CLIENTES_ESTADO` |
| Categorias | `categorias` | Si | Inactiva; bloquea clave duplicada | Solo sin tareas asociadas | FK entrante desde `tareas` | No | `CATEGORIAS_ESTADO` |
| Tipos | `tipos` | Si | Inactivo; bloquea clave duplicada | Solo sin tareas asociadas | FK entrante desde `tareas` | No | `TIPOS_ESTADO` |
| Tareas | `tareas` | Si; retira tambien script/versiones y bloquea ejecucion en curso | Inactiva; exige maestros operativos y no restaura hijos | Solo sin ejecuciones historicas ni en curso | Programaciones, scripts, ejecuciones, logs, eventos y notificaciones | `.py` y `.env` de sus versiones, solo al purgar | `TAREAS_ELIMINAR` |
| Scripts | `scripts` | Si; retira versiones | Inactivo; exige tarea operativa | Solo con tarea retirada, cero versiones operativas y sin ejecuciones historicas | Versiones, version activa y ejecuciones | `.py` y `.env` de sus versiones, solo al purgar | `SCRIPTS_ELIMINAR` |
| Versiones | `scripts_versiones` | Si; desactiva el slot y desvincula version activa | `INACTIVA`; exige script operativo, metadata y archivos existentes | Solo si no es activa y no tiene ejecuciones historicas | Script activo y ejecuciones | `.py` y `.env` del slot, solo al purgar | `SCRIPTS_ELIMINAR` |

No son entidades de Papelera: `programaciones`, `ejecuciones`, `logs_tareas`,
`logs_sistema`, `scheduler_eventos`, `auditoria_cambios`,
`evidencias_ejecucion` y `notificaciones_envios`. Son dependencias operativas o
historia protegida.

## Reglas de retiro y restauracion

El envio a Papelera se resuelve por ID y entidad allowlist en backend. El
request no controla tabla, estado interno, actor ni ruta fisica. El servicio
vuelve a cargar la fila con `UPDLOCK, HOLDLOCK`, revalida dependencias, actualiza
estado, registra auditoria y confirma una sola UoW.

Una tarea retirada queda `INACTIVA`, y sus scripts/versiones quedan fuera de
operacion. Scheduler, ejecucion manual, selectores y repositorios normales ya
exigen `eliminado_operativo = 0`. El envio no borra programaciones ni archivos.

Restaurar siempre devuelve el recurso inactivo. No reactiva automaticamente
tareas, scripts, versiones ni programaciones. Una tarea requiere cliente,
categoria y tipo operativos; un script requiere su tarea; una version requiere
su script y archivos confinados. Las claves funcionales se vuelven a validar
para evitar colisiones con registros creados despues del retiro.

## Eliminacion permanente e historia

La eliminacion permanente requiere `PAPELERA_ELIMINAR_PERMANENTE`. No elimina
ejecuciones, logs, evidencias, eventos ni auditoria. Para tareas, scripts y
versiones, cualquier ejecucion historica o en curso bloquea la purga. No se
nulifican `ejecuciones.id_tarea`, `id_script` o `id_version`; continúan
representando exactamente el recurso usado. Solo un recurso sin ejecuciones
puede eliminar sus programaciones, configuracion de notificaciones y recursos
script/version operativos correspondientes.

Clientes, categorias y tipos con tareas no pueden purgarse. No se alteran tareas
para liberar sus FK. La auditoria nunca se elimina desde este modulo.

## Coordinacion SQL y filesystem

| Operacion | SQL | Filesystem | Orden | Compensacion |
| --- | --- | --- | --- | --- |
| Enviar a Papelera | Marca retiro e inactividad | Sin cambios | SQL + auditoria + commit | Rollback UoW |
| Restaurar | Valida y quita retiro, queda inactivo | Solo valida archivos de version | Validar FS, SQL + auditoria + commit | Rollback UoW |
| Purga sin archivos | DELETE operativo condicionado | Sin cambios | SQL + auditoria + commit | Rollback UoW |
| Purga con archivos | Validar ausencia de historia y DELETE operativo | Rename temporal `.bak` | Validar todas las rutas, aplicar cuarentena, SQL, commit, borrar respaldos | Ante fallo previo al commit, revertir renames en orden inverso |

Las rutas salen exclusivamente de SQL, nunca del request. Se resuelven contra
`RUTA_BASE_SCRIPTS` o `RUTA_BASE_ENV_SCRIPTS`, se valida canonical path y se
rechazan escapes y enlaces simbolicos. Los archivos de evidencia y logs no
pertenecen a este cleanup. Tras confirmar se podan solo directorios vacios bajo
las roots autorizadas.

Deuda legitima: no existe transaccion distribuida. Un fallo del sistema
operativo al borrar el respaldo despues del commit puede dejar un `.bak`; no
revierte SQL ya confirmado. Debe tratarse mediante housekeeping observado, sin
borrar a ciegas.

## Permisos y rutas

| Accion | Ruta | Metodo | Permiso | CSRF |
| --- | --- | --- | --- | --- |
| Ver Papelera | `/papelera/` | GET | `PAPELERA_VER` | No aplica |
| Retirar usuario | `/papelera/usuarios/<id>/retirar` | POST | `USUARIOS_ADMIN` | Si |
| Retirar catalogo | `/papelera/<clientes|categorias|tipos>/<id>/retirar` | POST | permiso `*_ESTADO` correspondiente | Si |
| Retirar tarea | `/papelera/tareas/<id>/retirar` | POST | `TAREAS_ELIMINAR` | Si |
| Retirar script/version | `/papelera/<scripts|scripts_versiones>/<id>/retirar` | POST | `SCRIPTS_ELIMINAR` | Si |
| Restaurar | `/papelera/<entidad>/<id>/restaurar` | POST | `PAPELERA_RESTAURAR` | Si |
| Eliminar permanentemente | `/papelera/<entidad>/<id>/eliminar-permanente` | POST | `PAPELERA_ELIMINAR_PERMANENTE` | Si |

Roles del bootstrap vigente: `SUPER_ADMIN` recibe todos los permisos; `ADMIN`
puede consultar auditoria, ver y restaurar Papelera; `TI` puede consultar
auditoria y ver Papelera. La purga permanente queda reservada al permiso
dedicado, sin hardcodear nombres de rol. `SUPER_ADMIN_ENV` usa la misma
evaluacion de permisos privilegiada aprobada.

## Trazabilidad de acciones

Las acciones humanas se registran en la misma UoW:

* `ENVIADO_A_PAPELERA`;
* `ENVIO_PAPELERA_BLOQUEADO`;
* `RESTAURADO`;
* `RESTAURACION_BLOQUEADA`;
* `ELIMINADO_PERMANENTEMENTE`;
* `ELIMINACION_PERMANENTE_BLOQUEADA`.

La metadata incluye actor, entidad, ID, nombre, resultado y contexto HTTP. No
incluye contenido de scripts, `.env`, passwords, rutas de archivos ni secretos.

## UI y controles de seguridad

Auditoria y Papelera usan Bootstrap 5.3.3 local, CSS modular, filtros
responsive, paginacion, badges, estados vacios y el modal corporativo global.
No usan `window.confirm`, JavaScript inline ni HTML no escapado.

Controles revisados, sin declarar certificacion OWASP:

* autorizacion por ruta y accion, no solo visibilidad de botones;
* CSRF global para toda mutacion;
* entidad allowlist e identificador vuelto a cargar para reducir IDOR/BOLA;
* SQL parametrizado y orden fijo;
* autoescape Jinja y JSON como texto;
* mass assignment bloqueado por casos de uso explicitos;
* rutas confinadas y symlink escape rechazado;
* auditoria inmutable y permisos de lectura separados;
* errores publicos sin SQL, parametros, paths ni secretos.

## Validacion del hito

Las pruebas de `tests/reconstruccion/test_auditoria_papelera_hito9.py` cubren
contrato canonico/legacy, filtros parametrizados, paginacion, XSS, permisos,
CSRF, entidades allowlist, bloqueos, restauracion inactiva, preservacion de IDs
historicos, compensacion de archivos, path traversal, operacion
repetida y regresiones de scheduler/ejecucion manual. La validacion final se
registra en `docs/CHANGELOG.md` y `log_codex.md`: 28 pruebas focales, 246 de
reconstruccion y 272 totales aprobadas, con un unico skip conocido de symlink en
Windows.
