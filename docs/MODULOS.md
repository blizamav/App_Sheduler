# Modulos

## Implementados

* Login inicial desde `.env`.
* Panel principal base.
* Layout corporativo inicial.
* Diseno UI/UX base responsive de Fase 2.
* Propuesta de modelo SQL Server inicial en Fase 3, sin implementacion fisica.
* Ajuste documental Fase 3A para versionamiento controlado de scripts con maximo 3 versiones.
* Scripts SQL Server versionados de Fase 3B creados en `database/`, sin ejecucion automatica.

## Modulos pendientes

* Gestion de tareas.
* Gestion de scripts.
* Gestion de clientes.
* Gestion de categorias.
* Gestion de tipos.
* Gestion de usuarios.
* Roles y permisos.
* Scheduler.
* Ejecucion manual.
* Ejecucion automatica.
* Logs de tareas.
* Logs de sistema.
* Auditoria.
* Configuracion.
* Calendario laboral y feriados.
* Dashboard ejecutivo.
* Notificaciones.

## Estado de implementacion

La aplicacion esta en Fase 3B: scripts SQL versionados creados, no ejecutados. Aun no existen conexion real Flask-SQL Server, CRUD, scheduler ni usuarios en base de datos.

## Impacto del versionamiento de scripts

* Gestion de scripts debe permitir cargar version 1, 2 o 3.
* Gestion de scripts debe impedir una cuarta version directa.
* Gestion de scripts debe permitir reemplazar una version existente con auditoria.
* Ejecucion manual debe permitir elegir version disponible.
* Ejecucion automatica debe usar la version activa.
* Logs y auditoria deben permitir reconstruir que version se ejecuto.
