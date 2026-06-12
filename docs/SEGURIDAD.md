# Seguridad

## Manejo de sesiones

Fase 1 usa sesiones Flask protegidas por `APP_SECRET_KEY`.

## Roles y permisos

Fase 4 incorpora control inicial de roles y permisos desde SQL Server sin eliminar el acceso inicial desde `.env`.

Flujo vigente:

1. El login valida primero `USUARIO_ADMIN_DEFECTO` y `PASSWORD_ADMIN_DEFECTO` desde `.env`.
2. Si coincide, la sesion queda como `SUPER_ADMIN_ENV` con permisos totales.
3. Si no coincide, se valida contra la tabla `usuarios`.
4. Solo pueden iniciar sesion usuarios activos, no bloqueados y con contrasena valida.
5. Los permisos se cargan desde `usuarios_roles`, `roles`, `roles_permisos` y `permisos`.

El permiso funcional inicial para administrar usuarios es `USUARIOS_ADMIN`.

## Contrasenas

Las contrasenas de usuarios de base de datos se guardan usando hash seguro de Werkzeug:

* `generate_password_hash()` al crear o cambiar contrasena.
* `check_password_hash()` al iniciar sesion.

La aplicacion no muestra contrasenas en formularios ni respuestas.

## Administracion de usuarios

Fase 4 habilita `/usuarios` para usuarios con `USUARIOS_ADMIN` o administrador de `.env`.

Permitido:

* Listar usuarios.
* Filtrar usuarios por estado, rol y busqueda general.
* Crear usuarios.
* Editar nombre, email, rol, estado y contrasena opcional.
* Activar o desactivar usuarios.

No permitido:

* Eliminacion fisica de usuarios desde la app.
* Crear automaticamente el usuario `blizama` en base de datos.
* Exponer credenciales o hashes en pantalla.

Fase 4.2 usa modal corporativo propio antes de activar o desactivar usuarios. Si el administrador cancela, no se envia el formulario y no se registra evento como cambio realizado.

El formulario de edicion advierte cuando se cambia el rol o se ingresa una nueva contrasena. Estas advertencias no bloquean la accion, pero refuerzan claridad antes de guardar.

Las acciones criticas deben usar confirmacion explicita del sistema. No se deben usar `alert()`, `confirm()` ni `prompt()` nativos del navegador para acciones operativas.

Cambios de usuario que requieren confirmacion explicita:

* Crear usuario.
* Editar usuario.
* Cambiar rol.
* Cambiar estado activo/inactivo.
* Cambiar contrasena.
* Activar usuario.
* Deshabilitar usuario.

El cambio de contrasena se registra como evento sin guardar ni mostrar el valor de la contrasena ni su hash.

## Variables de entorno

Credenciales, servidores, rutas y secret keys deben vivir en `.env`. El archivo real se excluye con `.gitignore`.

Reglas obligatorias:

* `.env` contiene credenciales sensibles y configuracion privada por ambiente.
* `.env` nunca debe subirse a Git.
* `.env` nunca debe sobrescribirse automaticamente si ya existe.
* `.env.example` es solo una plantilla sin credenciales reales.
* Las credenciales reales deben configurarse manualmente por ambiente.
* No usar `copy .env.example .env` sobre un archivo `.env` existente.
* Usar comandos seguros, por ejemplo PowerShell: `if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }`.
* Si faltan variables criticas, la app debe mostrar advertencia controlada sin exponer valores.

## Validacion de archivos

Pendiente para Fase 7. Los scripts deberan validar extension `.py`, nombre seguro y rutas internas.

## Variables sensibles por script

Fase 4.3 define que cada script/version podra tener un `.env` propio bajo `env_scripts/`.

Reglas:

* No mostrar secretos en pantalla.
* No guardar secretos en base de datos.
* No registrar secretos en logs.
* No subir `.env` principal ni `.env` de scripts a Git.
* Separar `.env` principal de la app y `.env` de scripts.
* Guardar en base solo rutas fisicas/relativas del `.env` de script.
* Validar rutas para evitar path traversal.
* Solo usuarios autorizados podran cargar o modificar `.env` de scripts.
* Si una version requiere `.env` y falta el archivo, la ejecucion debe fallar controladamente antes de iniciar el proceso.

## Detencion de ejecuciones

Solo usuarios autorizados podran detener ejecuciones. Toda detencion debe:

* Pedir confirmacion mediante modal corporativo.
* Registrar usuario, fecha/hora y motivo cuando aplique.
* Registrar evento en `logs_sistema`.
* Registrar resultado en `logs_tareas`.
* Actualizar `ejecuciones`.
* No exponer datos sensibles del proceso ni variables de entorno.

## Eliminacion fisica de scripts

En la primera version del sistema no debe existir eliminacion fisica de scripts ni versiones desde la app. Las versiones deben gestionarse por estado:

* `ACTIVA`
* `DISPONIBLE`
* `REEMPLAZADA`
* `INACTIVA`

Toda inactivacion o reemplazo debe registrarse en auditoria y logs de sistema. Cualquier limpieza fisica futura debera ser una funcionalidad posterior, restringida, confirmada y auditable.

## Validacion de rutas

No se deben quemar rutas absolutas. Toda ruta operativa debe venir desde `.env`.

## Logs seguros

Fase 4 agrega registro inicial en `logs_sistema` para:

* Login exitoso.
* Login fallido.
* Login bloqueado por usuario inactivo o bloqueado.
* Creacion de usuario.
* Edicion de usuario.
* Activacion o desactivacion de usuario.
* Cambio de rol de usuario.

Los logs no deben exponer passwords, hashes ni credenciales de conexion.

## Recomendaciones

Cambiar `APP_SECRET_KEY` y `PASSWORD_ADMIN_DEFECTO` antes de ejecutar en entornos compartidos.
