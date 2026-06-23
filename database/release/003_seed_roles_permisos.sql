/*
Release SQL limpio - APP Scheduler
Script: 003_seed_roles_permisos.sql
Objetivo: cargar roles, permisos y asignaciones base.
No crea usuarios reales ni credenciales.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.roles AS destino
USING (VALUES
    (N'SUPER_ADMIN', N'Administrador total del sistema.'),
    (N'ADMIN', N'Administrador operativo del sistema.'),
    (N'TI', N'Usuario tecnico de TI.'),
    (N'TERCERO', N'Usuario tercero con acceso limitado.')
) AS origen(nombre_rol, descripcion)
ON destino.nombre_rol = origen.nombre_rol
WHEN MATCHED THEN
    UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME(), usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (nombre_rol, descripcion, usuario_creacion)
    VALUES (origen.nombre_rol, origen.descripcion, N'release_seed');
GO

MERGE dbo.permisos AS destino
USING (VALUES
    (N'PANEL_VER', N'panel', N'ver', N'Ver panel principal'),
    (N'TAREAS_VER', N'tareas', N'ver', N'Ver tareas'),
    (N'TAREAS_CREAR', N'tareas', N'crear', N'Crear tareas'),
    (N'TAREAS_EDITAR', N'tareas', N'editar', N'Editar tareas'),
    (N'TAREAS_ACTIVAR', N'tareas', N'activar', N'Activar tareas'),
    (N'TAREAS_SUSPENDER', N'tareas', N'suspender', N'Suspender tareas'),
    (N'TAREAS_ESTADO', N'tareas', N'estado', N'Cambiar estado de tareas'),
    (N'TAREAS_EJECUTAR', N'tareas', N'ejecutar', N'Ejecutar tareas'),
    (N'TAREAS_ELIMINAR', N'tareas', N'eliminar', N'Eliminar tareas de forma controlada'),
    (N'SCRIPTS_VER', N'scripts', N'ver', N'Ver scripts'),
    (N'SCRIPTS_CREAR', N'scripts', N'crear', N'Crear contenedor logico de script'),
    (N'SCRIPTS_EDITAR', N'scripts', N'editar', N'Editar metadatos de script'),
    (N'SCRIPTS_CARGAR', N'scripts', N'cargar', N'Cargar scripts'),
    (N'SCRIPTS_REEMPLAZAR', N'scripts', N'reemplazar', N'Reemplazar scripts'),
    (N'SCRIPTS_VERSIONAR', N'scripts', N'versionar', N'Cargar o reemplazar versiones'),
    (N'SCRIPTS_ACTIVAR_VERSION', N'scripts', N'activar_version', N'Activar version de script'),
    (N'SCRIPTS_DESACTIVAR', N'scripts', N'desactivar', N'Desactivar scripts o versiones'),
    (N'SCRIPTS_ELIMINAR', N'scripts', N'eliminar', N'Eliminar scripts de forma controlada'),
    (N'SCRIPTS_ENV_GESTIONAR', N'scripts', N'env_gestionar', N'Gestionar archivo .env por version'),
    (N'EJECUCIONES_VER', N'ejecuciones', N'ver', N'Ver historial de ejecuciones'),
    (N'EJECUCIONES_EJECUTAR', N'ejecuciones', N'ejecutar', N'Ejecutar tareas manualmente'),
    (N'EJECUCIONES_DETENER', N'ejecuciones', N'detener', N'Detener ejecuciones en curso'),
    (N'EJECUCIONES_LOG_VER', N'ejecuciones', N'log_ver', N'Ver consola y logs de ejecuciones'),
    (N'LOGS_VER', N'logs', N'ver', N'Ver logs'),
    (N'AUDITORIA_VER', N'auditoria', N'ver', N'Ver auditoria'),
    (N'AUDITORIA_DETALLE', N'auditoria', N'detalle', N'Ver detalle de auditoria'),
    (N'USUARIOS_ADMIN', N'usuarios', N'administrar', N'Administrar usuarios'),
    (N'CONFIGURACION_ADMIN', N'configuracion', N'administrar', N'Administrar configuracion general'),
    (N'CLIENTES_VER', N'clientes', N'ver', N'Ver clientes'),
    (N'CLIENTES_CREAR', N'clientes', N'crear', N'Crear clientes'),
    (N'CLIENTES_EDITAR', N'clientes', N'editar', N'Editar clientes'),
    (N'CLIENTES_ESTADO', N'clientes', N'estado', N'Activar o desactivar clientes'),
    (N'CATEGORIAS_VER', N'categorias', N'ver', N'Ver categorias'),
    (N'CATEGORIAS_CREAR', N'categorias', N'crear', N'Crear categorias'),
    (N'CATEGORIAS_EDITAR', N'categorias', N'editar', N'Editar categorias'),
    (N'CATEGORIAS_ESTADO', N'categorias', N'estado', N'Activar o desactivar categorias'),
    (N'TIPOS_VER', N'tipos', N'ver', N'Ver tipos'),
    (N'TIPOS_CREAR', N'tipos', N'crear', N'Crear tipos'),
    (N'TIPOS_EDITAR', N'tipos', N'editar', N'Editar tipos'),
    (N'TIPOS_ESTADO', N'tipos', N'estado', N'Activar o desactivar tipos'),
    (N'SCHEDULER_CONFIG_VER', N'scheduler', N'config_ver', N'Ver configuracion del scheduler'),
    (N'SCHEDULER_CONFIG_EDITAR', N'scheduler', N'config_editar', N'Editar configuracion del scheduler'),
    (N'FERIADOS_VER', N'feriados', N'ver', N'Ver feriados'),
    (N'FERIADOS_CREAR', N'feriados', N'crear', N'Crear feriados'),
    (N'FERIADOS_EDITAR', N'feriados', N'editar', N'Editar feriados'),
    (N'FERIADOS_ESTADO', N'feriados', N'estado', N'Activar o desactivar feriados'),
    (N'FERIADOS_ELIMINAR', N'feriados', N'eliminar', N'Eliminar feriados manuales'),
    (N'FERIADOS_SINCRONIZAR', N'feriados', N'sincronizar', N'Sincronizar feriados desde fuente externa'),
    (N'PAPELERA_VER', N'papelera', N'ver', N'Ver papelera operativa'),
    (N'PAPELERA_RESTAURAR', N'papelera', N'restaurar', N'Restaurar registros desde papelera'),
    (N'PAPELERA_ELIMINAR_PERMANENTE', N'papelera', N'eliminar_permanente', N'Eliminar definitivamente registros permitidos')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN MATCHED THEN
    UPDATE SET modulo = origen.modulo,
               accion = origen.accion,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'release_seed');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, usuario_creacion)
SELECT r.id_rol, p.id_permiso, N'release_seed'
FROM dbo.roles r
CROSS JOIN dbo.permisos p
WHERE r.nombre_rol = N'SUPER_ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, usuario_creacion)
SELECT r.id_rol, p.id_permiso, N'release_seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    N'PANEL_VER', N'TAREAS_VER', N'TAREAS_CREAR', N'TAREAS_EDITAR', N'TAREAS_ACTIVAR', N'TAREAS_SUSPENDER',
    N'TAREAS_ESTADO', N'TAREAS_EJECUTAR', N'TAREAS_ELIMINAR',
    N'SCRIPTS_VER', N'SCRIPTS_CREAR', N'SCRIPTS_EDITAR', N'SCRIPTS_CARGAR', N'SCRIPTS_REEMPLAZAR',
    N'SCRIPTS_VERSIONAR', N'SCRIPTS_ACTIVAR_VERSION', N'SCRIPTS_DESACTIVAR', N'SCRIPTS_ELIMINAR',
    N'SCRIPTS_ENV_GESTIONAR', N'EJECUCIONES_VER', N'EJECUCIONES_EJECUTAR', N'EJECUCIONES_DETENER',
    N'EJECUCIONES_LOG_VER', N'LOGS_VER', N'AUDITORIA_VER', N'AUDITORIA_DETALLE', N'USUARIOS_ADMIN',
    N'CONFIGURACION_ADMIN', N'CLIENTES_VER', N'CLIENTES_CREAR', N'CLIENTES_EDITAR', N'CLIENTES_ESTADO',
    N'CATEGORIAS_VER', N'CATEGORIAS_CREAR', N'CATEGORIAS_EDITAR', N'CATEGORIAS_ESTADO',
    N'TIPOS_VER', N'TIPOS_CREAR', N'TIPOS_EDITAR', N'TIPOS_ESTADO',
    N'SCHEDULER_CONFIG_VER', N'SCHEDULER_CONFIG_EDITAR',
    N'FERIADOS_VER', N'FERIADOS_CREAR', N'FERIADOS_EDITAR', N'FERIADOS_ESTADO', N'FERIADOS_ELIMINAR',
    N'FERIADOS_SINCRONIZAR', N'PAPELERA_VER', N'PAPELERA_RESTAURAR'
)
WHERE r.nombre_rol = N'ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, usuario_creacion)
SELECT r.id_rol, p.id_permiso, N'release_seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    N'PANEL_VER', N'TAREAS_VER', N'TAREAS_CREAR', N'TAREAS_EDITAR', N'TAREAS_ACTIVAR', N'TAREAS_SUSPENDER',
    N'TAREAS_ESTADO', N'TAREAS_EJECUTAR',
    N'SCRIPTS_VER', N'SCRIPTS_CREAR', N'SCRIPTS_EDITAR', N'SCRIPTS_CARGAR', N'SCRIPTS_REEMPLAZAR',
    N'SCRIPTS_VERSIONAR', N'SCRIPTS_ACTIVAR_VERSION', N'SCRIPTS_DESACTIVAR', N'SCRIPTS_ENV_GESTIONAR',
    N'EJECUCIONES_VER', N'EJECUCIONES_EJECUTAR', N'EJECUCIONES_DETENER', N'EJECUCIONES_LOG_VER',
    N'LOGS_VER', N'AUDITORIA_VER', N'AUDITORIA_DETALLE',
    N'CLIENTES_VER', N'CATEGORIAS_VER', N'TIPOS_VER',
    N'SCHEDULER_CONFIG_VER', N'SCHEDULER_CONFIG_EDITAR',
    N'FERIADOS_VER', N'FERIADOS_CREAR', N'FERIADOS_EDITAR', N'FERIADOS_ESTADO', N'FERIADOS_SINCRONIZAR',
    N'PAPELERA_VER'
)
WHERE r.nombre_rol = N'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, usuario_creacion)
SELECT r.id_rol, p.id_permiso, N'release_seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    N'PANEL_VER', N'TAREAS_VER', N'TAREAS_EJECUTAR', N'SCRIPTS_VER',
    N'EJECUCIONES_VER', N'EJECUCIONES_LOG_VER', N'LOGS_VER'
)
WHERE r.nombre_rol = N'TERCERO'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
