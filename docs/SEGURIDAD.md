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

## Mantenedores base

Clientes, categorias y tipos usan permisos especificos por modulo:

* `CLIENTES_VER`, `CLIENTES_CREAR`, `CLIENTES_EDITAR`, `CLIENTES_ESTADO`
* `CATEGORIAS_VER`, `CATEGORIAS_CREAR`, `CATEGORIAS_EDITAR`, `CATEGORIAS_ESTADO`
* `TIPOS_VER`, `TIPOS_CREAR`, `TIPOS_EDITAR`, `TIPOS_ESTADO`

Desde Fase 5.1 existe eliminacion fisica controlada solo para registros sin dependencias en `tareas`.

Reglas:

* Si el registro no tiene dependencias, puede eliminarse definitivamente con modal `danger`.
* Si tiene dependencias, se bloquea la eliminacion y se sugiere desactivar.
* La eliminacion confirmada se registra en `logs_sistema`.
* El intento bloqueado tambien se registra en `logs_sistema` con nivel `WARNING`.
* Se usan permisos existentes de estado: `CLIENTES_ESTADO`, `CATEGORIAS_ESTADO`, `TIPOS_ESTADO`.
* No se modifican usuarios, tareas, scripts ni trazabilidad historica.

## Tareas

Fase 6 agrega permisos especificos:

* `TAREAS_VER`
* `TAREAS_CREAR`
* `TAREAS_EDITAR`
* `TAREAS_ESTADO`
* `TAREAS_ELIMINAR`

Reglas:

* Solo usuarios autorizados pueden acceder al modulo `/tareas`.
* Crear, editar, activar, desactivar y eliminar usan confirmacion por modal corporativo.
* La eliminacion fisica solo se permite si la tarea no tiene scripts, ejecuciones ni logs asociados.
* Si hay dependencias, se bloquea y se recomienda desactivar.
* No se ejecutan scripts ni procesos desde Fase 6.
* No se manipulan secretos ni `.env` de scripts desde Fase 6.

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

## Scripts y versiones

Fase 7 agrega permisos especificos:

* `SCRIPTS_VER`
* `SCRIPTS_CREAR`
* `SCRIPTS_EDITAR`
* `SCRIPTS_VERSIONAR`
* `SCRIPTS_ACTIVAR_VERSION`
* `SCRIPTS_DESACTIVAR`
* `SCRIPTS_ELIMINAR`
* `SCRIPTS_ENV_GESTIONAR`

Reglas:

* Solo se aceptan archivos `.py` para scripts.
* Solo se aceptan archivos `.env` para variables por version.
* Se valida tamano maximo con `MAX_SCRIPT_SIZE_MB` y `MAX_ENV_SIZE_KB`.
* Los archivos se guardan solo bajo `scripts/` y `env_scripts/`.
* No se permiten rutas absolutas ni path traversal.
* No se ejecutan scripts en Fase 7.
* No se muestra contenido de `.env`.
* No se guardan secretos en base de datos.
* `scripts.nombre_script` es solo un nombre descriptivo de contenedor; no debe contener secretos ni rutas.
* Los nombres reales de archivos `.py` se guardan en `scripts_versiones.nombre_archivo`.
* La eliminacion fisica de versiones se bloquea si la version esta activa o tiene historial.
* La eliminacion de una version unica se bloquea para evitar dejar el contenedor de script sin versiones.
* El boton `Eliminar script completo` es la unica accion visual que puede afectar todo el conjunto de versiones.
* El boton `Eliminar version` solo puede afectar la version de su fila; no elimina otras versiones ni el script completo.
* Todo bloqueo por version activa, version unica o historial se registra en `logs_sistema` con nivel `WARNING`.

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

## Eliminacion controlada de scripts

La eliminacion fisica desde la app solo se permite de forma controlada cuando no existe historial operativo asociado.

Reglas:

* `Eliminar script completo` afecta el contenedor de script y todas sus versiones, solo si no tienen historial.
* `Eliminar version` afecta solo una version especifica y no toca las demas.
* Si una version esta activa, se debe activar otra antes de eliminarla.
* Si una version es la unica del script, se debe usar `Eliminar script completo`.
* Si existe historial en ejecuciones o logs, se bloquea la eliminacion fisica y se recomienda desactivar.
* Al eliminar una version sin historial se eliminan tambien su archivo `.py` y `.env` asociado, si existen.
* No se muestra ni registra contenido de `.env`.

Los estados vigentes para versiones siguen siendo:

* `ACTIVA`
* `DISPONIBLE`
* `REEMPLAZADA`
* `INACTIVA`

Toda eliminacion, inactivacion, reemplazo o bloqueo debe registrarse en logs de sistema.

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
