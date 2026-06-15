# Modulos

## Implementados

* Login inicial desde `.env`.
* Panel principal base.
* Layout corporativo inicial.
* Diseno UI/UX base responsive de Fase 2.
* Propuesta de modelo SQL Server inicial en Fase 3, sin implementacion fisica.
* Ajuste documental Fase 3A para versionamiento controlado de scripts con maximo 3 versiones.
* Scripts SQL Server versionados de Fase 3B creados en `database/`, sin ejecucion automatica.
* Conexion Flask-SQL Server desde `.env` y diagnostico `/diagnostico/bd`.
* Fase 4 inicial: login hibrido `.env` + SQL Server.
* Fase 4 inicial: administracion basica de usuarios, roles y permisos.
* Fase 4 inicial: logs de sistema para login y cambios de usuarios.
* Fase 4.1: filtros, confirmaciones y mejoras UX del modulo usuarios.
* Fase 4.3: definicion tecnica de ejecucion segura, detencion manual y `.env` por script.
* Fase 5: mantenedores funcionales de clientes, categorias y tipos.
* Fase 5.1: eliminacion fisica controlada en mantenedores solo cuando no existen dependencias.

## Modulos pendientes

* Gestion de tareas.
* Gestion de scripts.
* Scheduler.
* Ejecucion manual.
* Ejecucion automatica.
* Logs de tareas.
* Logs de sistema completos.
* Auditoria.
* Configuracion.
* Calendario laboral y feriados.
* Dashboard ejecutivo.
* Notificaciones.

## Definicion Fase 4.3

Antes de implementar tareas, scripts y scheduler se definio:

* Cada version de script podra indicar si requiere `.env`.
* Los `.env` de scripts viviran en `env_scripts/`, separados del codigo en `scripts/`.
* La base guardara solo rutas de `.env`, no secretos.
* Las ejecuciones registraran `pid_proceso` y datos de detencion manual.
* La interfaz futura debera permitir detener ejecuciones solo si estan `EN_EJECUCION`.
* Toda detencion debe confirmarse con modal corporativo y registrarse en logs.

## Estado de implementacion

La aplicacion esta en Fase 5: usuarios, roles, permisos y mantenedores base conectados a SQL Server. Aun no existen CRUD de tareas, carga real de scripts, scheduler, ejecuciones ni paneles funcionales de logs/auditoria.

## Mantenedores base

Implementado en Fase 5:

* `/clientes`: listar, filtrar, crear, editar, activar y desactivar clientes.
* `/categorias`: listar, filtrar, crear, editar, activar y desactivar categorias.
* `/tipos`: listar, filtrar, crear, editar, activar y desactivar tipos.
* Filtros por estado y busqueda general.
* Contador de resultados.
* Modal corporativo para crear, editar y cambiar estado.
* Validacion de nombre obligatorio y duplicados por nombre normalizado.
* Eliminacion fisica controlada solo si el registro no tiene dependencias en `tareas`.
* Logs en `logs_sistema` para creacion, edicion, activacion y desactivacion.
* Logs en `logs_sistema` para eliminacion definitiva e intento bloqueado por dependencias.

## Modulo de usuarios

Implementado en Fase 4:

* Login hibrido: primero `.env`, luego tabla `usuarios`.
* Usuario `.env` con rol de sesion `SUPER_ADMIN_ENV`.
* Usuarios de base de datos con roles y permisos desde tablas de seguridad.
* Pantalla `/usuarios` para listar, filtrar, crear, editar, activar y desactivar usuarios.
* Filtros por estado, rol y busqueda general.
* Confirmacion antes de activar o desactivar usuarios.
* Advertencias visuales al cambiar rol o contrasena.
* Asignacion de un rol activo por usuario desde el formulario inicial.
* Contrasenas con hash seguro.
* Sin eliminacion fisica de usuarios.
* Eventos principales registrados en `logs_sistema`.

## Impacto del versionamiento de scripts

* Gestion de scripts debe permitir cargar version 1, 2 o 3.
* Gestion de scripts debe impedir una cuarta version directa.
* Gestion de scripts debe permitir reemplazar una version existente con auditoria.
* Gestion de scripts debe manejar versiones por estado: `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Gestion de scripts no debe permitir eliminacion fisica desde la app en la primera version.
* Ejecucion manual debe permitir elegir version disponible.
* Ejecucion automatica debe usar la version activa.
* Logs y auditoria deben permitir reconstruir que version se ejecuto.
