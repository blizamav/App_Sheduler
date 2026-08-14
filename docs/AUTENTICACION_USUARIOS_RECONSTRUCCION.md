# Autenticacion y usuarios de la reconstruccion

## Estado y alcance

Hito 3 esta cerrado en `src/app_scheduler/`. El runtime historico sigue activo y no existe cutover. Hito 4 se cerro posteriormente reutilizando esta seguridad; Hito 5 no fue iniciado.

Incluye login, logout, sesion, identidad, autorizacion, usuarios, asignacion de rol, consulta de roles/permisos y auditoria de seguridad. No incluye mantenedores, tareas, scripts, scheduler, Graph, papelera ni Factory Reset.

## Login y sesion

1. `/login` valida entradas y compara primero `USUARIO_ADMIN_DEFECTO`/`PASSWORD_ADMIN_DEFECTO` con comparacion constante.
2. Si coinciden, crea identidad `SUPER_ADMIN_ENV` con permiso efectivo total. La credencial no se persiste ni se registra.
3. Si no coinciden, consulta `usuarios`, exige cuenta activa, no bloqueada y no retirada, y verifica el hash con Werkzeug.
4. Un login SQL correcto carga roles/permisos, actualiza `ultimo_login` y registra auditoria dentro de una UoW.
5. La sesion se limpia antes de guardar solo tipo, ID y login. No contiene password, hash ni la matriz completa.
6. En cada request protegido, una identidad SQL recarga usuario, roles y permisos. Una desactivacion invalida la sesion en el siguiente request.
7. `/logout` registra auditoria cuando es posible y limpia completamente la sesion.

Los errores de usuario inexistente, password incorrecto, usuario inactivo, bloqueado o retirado usan el mismo mensaje. Los destinos `next` externos se rechazan.

`SUPER_ADMIN_ENV` puede autenticar aunque SQL Server no permita escribir auditoria. Esto conserva el acceso de recuperacion, pero no convierte en disponibles las operaciones que necesitan SQL.

## Usuarios

* Listado paginado con busqueda, estado y rol, sin exponer `password_hash`.
* Alta transaccional de usuario, hash y rol.
* Edicion de nombre, correo, rol y password opcional; un password vacio conserva el hash vigente.
* Activacion/desactivacion sin eliminacion fisica en este hito.
* Un `ADMIN` no puede asignar ni administrar `SUPER_ADMIN`.
* Nadie puede desactivar su propia cuenta SQL desde la sesion actual.
* No se puede quitar o desactivar el ultimo `SUPER_ADMIN` activo.
* El modelo permite asociaciones historicas, pero la UI mantiene un rol operativo activo por usuario, conforme al comportamiento vigente.

El catalogo de roles/permisos es de solo lectura. Los roles base y sus relaciones siguen siendo responsabilidad del bootstrap; Hito 3 no crea un editor arbitrario.

## Matriz de permisos Hito 3

| Permiso | Descripcion | Ruta/accion | Roles por bootstrap | Impacto |
| --- | --- | --- | --- | --- |
| `PANEL_VER` | Ver panel principal | `GET /` | `SUPER_ADMIN`, `ADMIN`, `TI`, `TERCERO` | Permite entrar al shell autenticado. |
| `USUARIOS_ADMIN` | Administrar usuarios | `/usuarios/*` y `/seguridad/roles-permisos` | `SUPER_ADMIN`, `ADMIN` | Permite listar, crear, editar, cambiar estado/asignar rol y consultar la matriz. |

`SUPER_ADMIN_ENV` no pertenece a la matriz SQL y satisface cualquier permiso como identidad de recuperacion. Los permisos efectivos de usuarios SQL siempre provienen de `usuarios_roles`, `roles`, `roles_permisos` y `permisos`.

| Rol SQL | Permisos aplicables en Hito 3 | Origen |
| --- | --- | --- |
| `SUPER_ADMIN` | `PANEL_VER`, `USUARIOS_ADMIN` | Catalogo y asociaciones de `database/release/003_seed_roles_permisos.sql`, incorporados por el bootstrap vigente. |
| `ADMIN` | `PANEL_VER`, `USUARIOS_ADMIN` | Misma fuente persistida; no existe regla de permiso hardcodeada por etiqueta. |
| `TI` | `PANEL_VER` | Misma fuente persistida. |
| `TERCERO` | `PANEL_VER` | Misma fuente persistida. |

La tabla resume solo permisos consumidos por Hito 3; la UI consulta la matriz completa desde SQL y no mantiene una copia independiente. `SUPER_ADMIN` es un rol interno asociado a una fila de `usuarios`. `SUPER_ADMIN_ENV` tiene `id_usuario = None`, no se inserta en `usuarios` y no cuenta al validar el ultimo `SUPER_ADMIN` interno.

## Rutas y controles

| Metodo | Ruta | Autenticacion | Permiso | CSRF | Caso de uso |
| --- | --- | --- | --- | --- | --- |
| `GET`, `POST` | `/login` | Publica hasta autenticar | No aplica | POST si | Login hibrido y establecimiento de sesion. |
| `POST` | `/logout` | Sesion si existe | No aplica | Si | Auditoria y limpieza completa. |
| `GET` | `/` | Obligatoria | `PANEL_VER` | No aplica | Panel reconstruido. |
| `GET` | `/usuarios/` | Obligatoria | `USUARIOS_ADMIN` | No aplica | Listado y filtros. |
| `GET`, `POST` | `/usuarios/nuevo` | Obligatoria | `USUARIOS_ADMIN` | POST si | Alta transaccional usuario + rol. |
| `GET`, `POST` | `/usuarios/<id>/editar` | Obligatoria | `USUARIOS_ADMIN` | POST si | Edicion transaccional y password opcional. |
| `POST` | `/usuarios/<id>/estado` | Obligatoria | `USUARIOS_ADMIN` | Si | Activar/desactivar. |
| `GET` | `/seguridad/roles-permisos` | Obligatoria | `USUARIOS_ADMIN` | No aplica | Consulta de matriz de solo lectura. |

`/salud` permanece como healthcheck tecnico sin SQL y no es una ruta administrativa.

## Auditoria

Eventos implementados: `LOGIN_OK`, `LOGIN_FALLIDO`, `LOGOUT`, `USUARIO_CREADO`, `USUARIO_EDITADO`, `USUARIO_ACTIVADO`, `USUARIO_DESACTIVADO` y `ROLES_USUARIO_MODIFICADOS`.

Se usan `usuario`, `id_usuario`, `accion`, `entidad`, `id_entidad`, `nombre_entidad`, `descripcion`, `valores_antes`, `valores_despues`, `ip_origen`, `user_agent`, `resultado`, `modulo`, `ruta` y `metodo_http`; `fecha_evento` y `activo` conservan defaults del contrato. No se usan las seis columnas legacy.

La serializacion reemplaza valores de claves sensibles por `[PROTEGIDO]`. Passwords y hashes no forman parte de los valores auditados.

## Seguridad y pruebas

* CSRF transversal en todos los formularios mutables.
* Cookie `HttpOnly`, `SameSite` y `Secure` segun configuracion.
* Autorizacion backend en cada ruta administrativa; el sidebar es solo presentacion.
* SQL parametrizado y commit/rollback exclusivamente mediante UoW.
* Respuestas de persistencia sin detalle SQL ni credenciales.
* 69 tests reconstruidos con fakes, sin SQL Server ni datos QA, cubren login valido/invalido/inactivo, recuperacion, sesion, logout, open redirect, CSRF, 403, alta, edicion, estados, jerarquia, rollback, auditoria y sanitizacion. La suite completa alcanza 95 pruebas aprobadas.

Deuda legitima: no existe rate limit distribuido aprobado. Una futura fase de hardening puede definir umbrales/bloqueo temporal sin alterar el contrato de Hito 3.

Las pruebas de cierre demuestran que una sesion SQL previamente valida pierde acceso y se limpia cuando el cargador detecta la cuenta inactiva. Tambien demuestran que la disponibilidad de `SUPER_ADMIN_ENV` no permite desactivar el ultimo `SUPER_ADMIN` interno.
