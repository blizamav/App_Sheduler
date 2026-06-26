/*
Release SQL limpio - APP Scheduler
Script: 002_schema_final.sql
Objetivo: crear el schema final consolidado hasta Fase 13A.

Notas:
- No ejecutar sobre una base con datos existentes sin respaldo y revision.
- No borra tablas, no borra datos y no modifica usuarios SQL.
- Integra el resultado final de migrations/001..018.
*/

USE [$(DB_NAME)];
GO

/* =========================================================
   Catalogos
   ========================================================= */

IF OBJECT_ID(N'dbo.cat_estados_tarea', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_estados_tarea (
        id_estado_tarea int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_estados_tarea_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_estados_tarea_activo DEFAULT 1,
        CONSTRAINT PK_cat_estados_tarea PRIMARY KEY (id_estado_tarea),
        CONSTRAINT UX_cat_estados_tarea_codigo UNIQUE (codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.cat_estados_ejecucion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_estados_ejecucion (
        id_estado_ejecucion int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_estados_ejecucion_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_estados_ejecucion_activo DEFAULT 1,
        CONSTRAINT PK_cat_estados_ejecucion PRIMARY KEY (id_estado_ejecucion),
        CONSTRAINT UX_cat_estados_ejecucion_codigo UNIQUE (codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.cat_tipos_programacion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_tipos_programacion (
        id_tipo_programacion int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_tipos_programacion_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_tipos_programacion_activo DEFAULT 1,
        CONSTRAINT PK_cat_tipos_programacion PRIMARY KEY (id_tipo_programacion),
        CONSTRAINT UX_cat_tipos_programacion_codigo UNIQUE (codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.cat_niveles_log', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_niveles_log (
        id_nivel_log int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_niveles_log_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_niveles_log_activo DEFAULT 1,
        CONSTRAINT PK_cat_niveles_log PRIMARY KEY (id_nivel_log),
        CONSTRAINT UX_cat_niveles_log_codigo UNIQUE (codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.cat_tipos_tarea', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_tipos_tarea (
        id_tipo_tarea int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_tipos_tarea_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_tipos_tarea_activo DEFAULT 1,
        CONSTRAINT PK_cat_tipos_tarea PRIMARY KEY (id_tipo_tarea),
        CONSTRAINT UX_cat_tipos_tarea_codigo UNIQUE (codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.cat_estados_version_script', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.cat_estados_version_script (
        id_estado_version_script int IDENTITY(1,1) NOT NULL,
        codigo varchar(30) NOT NULL,
        nombre nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_cat_estados_version_script_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_cat_estados_version_script_activo DEFAULT 1,
        CONSTRAINT PK_cat_estados_version_script PRIMARY KEY (id_estado_version_script),
        CONSTRAINT UX_cat_estados_version_script_codigo UNIQUE (codigo)
    );
END;
GO

/* =========================================================
   Seguridad
   ========================================================= */

IF OBJECT_ID(N'dbo.usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios (
        id_usuario int IDENTITY(1,1) NOT NULL,
        usuario nvarchar(100) NOT NULL,
        nombre_completo nvarchar(200) NOT NULL,
        email nvarchar(200) NULL,
        password_hash nvarchar(300) NOT NULL,
        debe_cambiar_password bit NOT NULL CONSTRAINT DF_usuarios_debe_cambiar_password DEFAULT 0,
        ultimo_login datetime2(0) NULL,
        intentos_fallidos int NOT NULL CONSTRAINT DF_usuarios_intentos_fallidos DEFAULT 0,
        bloqueado bit NOT NULL CONSTRAINT DF_usuarios_bloqueado DEFAULT 0,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_usuarios_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_usuarios_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_usuarios_activo DEFAULT 1,
        CONSTRAINT PK_usuarios PRIMARY KEY (id_usuario),
        CONSTRAINT UX_usuarios_usuario UNIQUE (usuario)
    );
END;
GO

IF OBJECT_ID(N'dbo.roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles (
        id_rol int IDENTITY(1,1) NOT NULL,
        codigo_rol varchar(50) NOT NULL,
        nombre_rol nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        es_sistema bit NOT NULL CONSTRAINT DF_roles_es_sistema DEFAULT 0,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_roles_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_roles_activo DEFAULT 1,
        CONSTRAINT PK_roles PRIMARY KEY (id_rol),
        CONSTRAINT UX_roles_codigo_rol UNIQUE (codigo_rol)
    );
END;
GO

IF OBJECT_ID(N'dbo.permisos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.permisos (
        id_permiso int IDENTITY(1,1) NOT NULL,
        codigo_permiso varchar(120) NOT NULL,
        modulo nvarchar(80) NOT NULL,
        accion nvarchar(80) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_permisos_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_permisos_activo DEFAULT 1,
        CONSTRAINT PK_permisos PRIMARY KEY (id_permiso),
        CONSTRAINT UX_permisos_codigo_permiso UNIQUE (codigo_permiso),
        CONSTRAINT UX_permisos_modulo_accion UNIQUE (modulo, accion)
    );
END;
GO

IF OBJECT_ID(N'dbo.usuarios_roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios_roles (
        id_usuario_rol int IDENTITY(1,1) NOT NULL,
        id_usuario int NOT NULL,
        id_rol int NOT NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_usuarios_roles_fecha_creacion DEFAULT SYSDATETIME(),
        usuario_creacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_usuarios_roles_activo DEFAULT 1,
        CONSTRAINT PK_usuarios_roles PRIMARY KEY (id_usuario_rol),
        CONSTRAINT UX_usuarios_roles_usuario_rol UNIQUE (id_usuario, id_rol),
        CONSTRAINT FK_usuarios_roles_usuarios FOREIGN KEY (id_usuario) REFERENCES dbo.usuarios(id_usuario),
        CONSTRAINT FK_usuarios_roles_roles FOREIGN KEY (id_rol) REFERENCES dbo.roles(id_rol)
    );
END;
GO

IF OBJECT_ID(N'dbo.roles_permisos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles_permisos (
        id_rol_permiso int IDENTITY(1,1) NOT NULL,
        id_rol int NOT NULL,
        id_permiso int NOT NULL,
        permitido bit NOT NULL CONSTRAINT DF_roles_permisos_permitido DEFAULT 1,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_roles_permisos_fecha_creacion DEFAULT SYSDATETIME(),
        usuario_creacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_roles_permisos_activo DEFAULT 1,
        CONSTRAINT PK_roles_permisos PRIMARY KEY (id_rol_permiso),
        CONSTRAINT UX_roles_permisos_rol_permiso UNIQUE (id_rol, id_permiso),
        CONSTRAINT FK_roles_permisos_roles FOREIGN KEY (id_rol) REFERENCES dbo.roles(id_rol),
        CONSTRAINT FK_roles_permisos_permisos FOREIGN KEY (id_permiso) REFERENCES dbo.permisos(id_permiso)
    );
END;
GO

/* =========================================================
   Maestros y negocio
   ========================================================= */

IF OBJECT_ID(N'dbo.clientes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.clientes (
        id_cliente int IDENTITY(1,1) NOT NULL,
        nombre_cliente nvarchar(150) NOT NULL,
        nombre_normalizado nvarchar(150) NOT NULL,
        descripcion nvarchar(300) NULL,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_clientes_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_clientes_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_clientes_activo DEFAULT 1,
        CONSTRAINT PK_clientes PRIMARY KEY (id_cliente),
        CONSTRAINT UX_clientes_nombre_normalizado UNIQUE (nombre_normalizado)
    );
END;
GO

IF OBJECT_ID(N'dbo.categorias', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.categorias (
        id_categoria int IDENTITY(1,1) NOT NULL,
        nombre_categoria nvarchar(150) NOT NULL,
        nombre_normalizado nvarchar(150) NOT NULL,
        descripcion nvarchar(300) NULL,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_categorias_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_categorias_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_categorias_activo DEFAULT 1,
        CONSTRAINT PK_categorias PRIMARY KEY (id_categoria),
        CONSTRAINT UX_categorias_nombre_normalizado UNIQUE (nombre_normalizado)
    );
END;
GO

IF OBJECT_ID(N'dbo.tipos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tipos (
        id_tipo int IDENTITY(1,1) NOT NULL,
        nombre_tipo nvarchar(150) NOT NULL,
        nombre_normalizado nvarchar(150) NOT NULL,
        descripcion nvarchar(300) NULL,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_tipos_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_tipos_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_tipos_activo DEFAULT 1,
        CONSTRAINT PK_tipos PRIMARY KEY (id_tipo),
        CONSTRAINT UX_tipos_nombre_normalizado UNIQUE (nombre_normalizado)
    );
END;
GO

IF OBJECT_ID(N'dbo.tareas', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tareas (
        id_tarea int IDENTITY(1,1) NOT NULL,
        nombre_tarea nvarchar(200) NOT NULL,
        descripcion nvarchar(1000) NULL,
        observacion_tecnica nvarchar(1000) NULL,
        id_cliente int NOT NULL,
        id_categoria int NOT NULL,
        id_tipo int NOT NULL,
        tipo_tarea varchar(30) NOT NULL,
        estado_tarea varchar(30) NOT NULL,
        ultima_ejecucion datetime2(0) NULL,
        proxima_ejecucion datetime2(0) NULL,
        ultimo_estado_ejecucion varchar(30) NULL,
        permite_ejecucion_manual bit NOT NULL CONSTRAINT DF_tareas_permite_ejecucion_manual DEFAULT 1,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_tareas_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_tareas_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_tareas_activo DEFAULT 1,
        CONSTRAINT PK_tareas PRIMARY KEY (id_tarea),
        CONSTRAINT FK_tareas_clientes FOREIGN KEY (id_cliente) REFERENCES dbo.clientes(id_cliente),
        CONSTRAINT FK_tareas_categorias FOREIGN KEY (id_categoria) REFERENCES dbo.categorias(id_categoria),
        CONSTRAINT FK_tareas_tipos FOREIGN KEY (id_tipo) REFERENCES dbo.tipos(id_tipo),
        CONSTRAINT FK_tareas_cat_tipos_tarea FOREIGN KEY (tipo_tarea) REFERENCES dbo.cat_tipos_tarea(codigo),
        CONSTRAINT FK_tareas_cat_estados_tarea FOREIGN KEY (estado_tarea) REFERENCES dbo.cat_estados_tarea(codigo)
    );
END;
GO

IF OBJECT_ID(N'dbo.programaciones', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.programaciones (
        id_programacion int IDENTITY(1,1) NOT NULL,
        id_tarea int NOT NULL,
        tipo_programacion varchar(30) NOT NULL,
        modo_ejecucion_dia varchar(30) NULL,
        hora_inicio time(0) NULL,
        hora_termino time(0) NULL,
        hora_ejecucion time(0) NULL,
        intervalo_minutos int NULL,
        dias_semana varchar(50) NULL,
        dia_mes tinyint NULL,
        fecha_especifica date NULL,
        fechas_especificas nvarchar(max) NULL,
        configuracion_json nvarchar(max) NULL,
        ejecutar_en_feriados bit NOT NULL CONSTRAINT DF_programaciones_ejecutar_en_feriados DEFAULT 0,
        zona_horaria nvarchar(80) NOT NULL CONSTRAINT DF_programaciones_zona_horaria DEFAULT N'America/Santiago',
        fecha_inicio_vigencia date NULL,
        fecha_fin_vigencia date NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_programaciones_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_programaciones_activo DEFAULT 1,
        CONSTRAINT PK_programaciones PRIMARY KEY (id_programacion),
        CONSTRAINT FK_programaciones_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea),
        CONSTRAINT FK_programaciones_cat_tipos_programacion FOREIGN KEY (tipo_programacion) REFERENCES dbo.cat_tipos_programacion(codigo),
        CONSTRAINT CK_programaciones_intervalo CHECK (intervalo_minutos IS NULL OR intervalo_minutos > 0),
        CONSTRAINT CK_programaciones_dia_mes CHECK (dia_mes IS NULL OR dia_mes BETWEEN 1 AND 31),
        CONSTRAINT CK_programaciones_modo_ejecucion_dia CHECK (modo_ejecucion_dia IS NULL OR modo_ejecucion_dia IN ('UNA_VEZ','INTERVALO'))
    );
END;
GO

IF OBJECT_ID(N'dbo.scripts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scripts (
        id_script int IDENTITY(1,1) NOT NULL,
        id_tarea int NOT NULL,
        nombre_script nvarchar(200) NOT NULL,
        descripcion nvarchar(1000) NULL,
        id_version_activa int NULL,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_scripts_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_scripts_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_scripts_activo DEFAULT 1,
        CONSTRAINT PK_scripts PRIMARY KEY (id_script),
        CONSTRAINT UX_scripts_id_tarea UNIQUE (id_tarea),
        CONSTRAINT FK_scripts_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea)
    );
END;
GO

IF OBJECT_ID(N'dbo.scripts_versiones', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scripts_versiones (
        id_version int IDENTITY(1,1) NOT NULL,
        id_script int NOT NULL,
        numero_version tinyint NOT NULL,
        nombre_archivo nvarchar(255) NOT NULL,
        ruta_fisica nvarchar(500) NOT NULL,
        ruta_relativa nvarchar(500) NOT NULL,
        hash_archivo varchar(128) NOT NULL,
        estado_version varchar(30) NOT NULL,
        es_activa bit NOT NULL CONSTRAINT DF_scripts_versiones_es_activa DEFAULT 0,
        requiere_env bit NOT NULL CONSTRAINT DF_scripts_versiones_requiere_env DEFAULT 0,
        ruta_env_fisica nvarchar(500) NULL,
        ruta_env_relativa nvarchar(500) NULL,
        usuario_carga nvarchar(100) NOT NULL,
        fecha_carga datetime2(0) NOT NULL CONSTRAINT DF_scripts_versiones_fecha_carga DEFAULT SYSDATETIME(),
        observacion nvarchar(1000) NULL,
        eliminado_operativo bit NOT NULL CONSTRAINT DF_scripts_versiones_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_scripts_versiones_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        CONSTRAINT PK_scripts_versiones PRIMARY KEY (id_version),
        CONSTRAINT FK_scripts_versiones_scripts FOREIGN KEY (id_script) REFERENCES dbo.scripts(id_script),
        CONSTRAINT FK_scripts_versiones_cat_estado FOREIGN KEY (estado_version) REFERENCES dbo.cat_estados_version_script(codigo),
        CONSTRAINT CK_scripts_versiones_numero CHECK (numero_version BETWEEN 1 AND 3),
        CONSTRAINT CK_scripts_versiones_estado CHECK (estado_version IN ('ACTIVA','DISPONIBLE','REEMPLAZADA','INACTIVA')),
        CONSTRAINT UX_scripts_versiones_script_numero UNIQUE (id_script, numero_version)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = N'FK_scripts_version_activa'
      AND parent_object_id = OBJECT_ID(N'dbo.scripts')
)
BEGIN
    ALTER TABLE dbo.scripts
    ADD CONSTRAINT FK_scripts_version_activa
    FOREIGN KEY (id_version_activa) REFERENCES dbo.scripts_versiones(id_version);
END;
GO

IF OBJECT_ID(N'dbo.configuracion_sistema', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.configuracion_sistema (
        id_configuracion int IDENTITY(1,1) NOT NULL,
        clave nvarchar(120) NOT NULL,
        valor nvarchar(max) NOT NULL,
        tipo_dato varchar(30) NOT NULL,
        descripcion nvarchar(300) NULL,
        es_sensible bit NOT NULL CONSTRAINT DF_configuracion_sistema_es_sensible DEFAULT 0,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_configuracion_sistema_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_configuracion_sistema_activo DEFAULT 1,
        CONSTRAINT PK_configuracion_sistema PRIMARY KEY (id_configuracion),
        CONSTRAINT UX_configuracion_sistema_clave UNIQUE (clave)
    );
END;
GO

/* =========================================================
   Ejecuciones, logs y auditoria
   ========================================================= */

IF OBJECT_ID(N'dbo.ejecuciones', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ejecuciones (
        id_ejecucion bigint IDENTITY(1,1) NOT NULL,
        id_tarea int NULL,
        id_script int NULL,
        id_version int NULL,
        origen_ejecucion varchar(20) NOT NULL,
        estado_ejecucion varchar(30) NOT NULL,
        fecha_hora_inicio datetime2(0) NOT NULL,
        fecha_hora_termino datetime2(0) NULL,
        duracion_segundos int NULL,
        codigo_salida int NULL,
        mensaje_error nvarchar(max) NULL,
        usuario_ejecucion nvarchar(100) NULL,
        pid_proceso int NULL,
        usuario_detencion nvarchar(100) NULL,
        fecha_hora_detencion datetime2(0) NULL,
        motivo_detencion nvarchar(500) NULL,
        fue_detencion_forzada bit NOT NULL CONSTRAINT DF_ejecuciones_fue_detencion_forzada DEFAULT 0,
        fecha_programada datetime2(0) NULL,
        clave_programacion varchar(200) NULL,
        nombre_worker varchar(100) NULL,
        id_tarea_original int NULL,
        nombre_tarea_snapshot nvarchar(200) NULL,
        cliente_snapshot nvarchar(200) NULL,
        categoria_snapshot nvarchar(200) NULL,
        tipo_snapshot nvarchar(200) NULL,
        nombre_script_snapshot nvarchar(200) NULL,
        nombre_archivo_snapshot nvarchar(255) NULL,
        version_script_snapshot nvarchar(50) NULL,
        usuario_ejecucion_snapshot nvarchar(100) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_ejecuciones_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_ejecuciones PRIMARY KEY (id_ejecucion),
        CONSTRAINT FK_ejecuciones_cat_estados_ejecucion FOREIGN KEY (estado_ejecucion) REFERENCES dbo.cat_estados_ejecucion(codigo),
        CONSTRAINT CK_ejecuciones_origen CHECK (origen_ejecucion IN ('MANUAL','AUTOMATICA')),
        CONSTRAINT CK_ejecuciones_duracion CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.logs_tareas', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.logs_tareas (
        id_log bigint IDENTITY(1,1) NOT NULL,
        id_tarea int NULL,
        id_ejecucion bigint NOT NULL,
        nombre_tarea nvarchar(200) NOT NULL,
        nombre_script nvarchar(255) NOT NULL,
        nombre_archivo_log nvarchar(255) NOT NULL,
        ruta_fisica_log nvarchar(500) NOT NULL,
        ruta_relativa_log nvarchar(500) NOT NULL,
        fecha_hora_inicio datetime2(0) NOT NULL,
        fecha_hora_termino datetime2(0) NULL,
        duracion_segundos int NULL,
        estado_final varchar(30) NOT NULL,
        codigo_salida int NULL,
        mensaje_error nvarchar(max) NULL,
        usuario_ejecucion nvarchar(100) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_logs_tareas_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_logs_tareas PRIMARY KEY (id_log),
        CONSTRAINT FK_logs_tareas_ejecuciones FOREIGN KEY (id_ejecucion) REFERENCES dbo.ejecuciones(id_ejecucion),
        CONSTRAINT FK_logs_tareas_cat_estado_final FOREIGN KEY (estado_final) REFERENCES dbo.cat_estados_ejecucion(codigo),
        CONSTRAINT CK_logs_tareas_duracion CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.logs_sistema', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.logs_sistema (
        id bigint IDENTITY(1,1) NOT NULL,
        usuario nvarchar(100) NULL,
        accion nvarchar(100) NOT NULL,
        modulo nvarchar(100) NOT NULL,
        descripcion nvarchar(max) NOT NULL,
        valor_anterior nvarchar(max) NULL,
        valor_nuevo nvarchar(max) NULL,
        ip varchar(45) NULL,
        user_agent nvarchar(500) NULL,
        fecha_hora datetime2(0) NOT NULL CONSTRAINT DF_logs_sistema_fecha_hora DEFAULT SYSDATETIME(),
        nivel varchar(30) NOT NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_logs_sistema_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_logs_sistema PRIMARY KEY (id),
        CONSTRAINT FK_logs_sistema_cat_niveles_log FOREIGN KEY (nivel) REFERENCES dbo.cat_niveles_log(codigo),
        CONSTRAINT CK_logs_sistema_nivel CHECK (nivel IN ('INFO','WARNING','ERROR','CRITICAL'))
    );
END;
GO

IF OBJECT_ID(N'dbo.auditoria_cambios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.auditoria_cambios (
        id_auditoria bigint IDENTITY(1,1) NOT NULL,
        fecha_evento datetime2(0) NOT NULL CONSTRAINT DF_auditoria_cambios_fecha_evento DEFAULT SYSDATETIME(),
        usuario nvarchar(100) NOT NULL,
        id_usuario int NULL,
        accion nvarchar(100) NOT NULL,
        entidad nvarchar(100) NOT NULL,
        id_entidad nvarchar(100) NULL,
        nombre_entidad nvarchar(255) NULL,
        descripcion nvarchar(max) NULL,
        valores_antes nvarchar(max) NULL,
        valores_despues nvarchar(max) NULL,
        ip_origen nvarchar(100) NULL,
        user_agent nvarchar(max) NULL,
        resultado nvarchar(50) NULL,
        modulo nvarchar(100) NULL,
        ruta nvarchar(255) NULL,
        metodo_http nvarchar(20) NULL,
        activo bit NOT NULL CONSTRAINT DF_auditoria_cambios_activo DEFAULT 1,
        CONSTRAINT PK_auditoria_cambios PRIMARY KEY (id_auditoria)
    );
END;
GO

/* =========================================================
   Programador, heartbeat y eventos
   ========================================================= */

IF OBJECT_ID(N'dbo.configuracion_scheduler', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.configuracion_scheduler (
        id_configuracion int IDENTITY(1,1) NOT NULL,
        scheduler_activo bit NOT NULL CONSTRAINT DF_configuracion_scheduler_activo_scheduler DEFAULT 0,
        intervalo_revision_segundos int NOT NULL CONSTRAINT DF_configuracion_scheduler_intervalo DEFAULT 60,
        max_ejecuciones_concurrentes int NOT NULL CONSTRAINT DF_configuracion_scheduler_max DEFAULT 3,
        permitir_ejecucion_automatica bit NOT NULL CONSTRAINT DF_configuracion_scheduler_permitir DEFAULT 0,
        modo_mantenimiento bit NOT NULL CONSTRAINT DF_configuracion_scheduler_mantenimiento DEFAULT 0,
        nombre_worker_principal varchar(100) NULL,
        descripcion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_configuracion_scheduler_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_configuracion_scheduler_activo DEFAULT 1,
        CONSTRAINT PK_configuracion_scheduler PRIMARY KEY (id_configuracion),
        CONSTRAINT CK_configuracion_scheduler_intervalo CHECK (intervalo_revision_segundos BETWEEN 10 AND 3600),
        CONSTRAINT CK_configuracion_scheduler_max CHECK (max_ejecuciones_concurrentes BETWEEN 1 AND 20)
    );
END;
GO

IF OBJECT_ID(N'dbo.scheduler_worker_heartbeat', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scheduler_worker_heartbeat (
        id_worker int IDENTITY(1,1) NOT NULL,
        nombre_worker varchar(100) NOT NULL,
        estado varchar(30) NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_estado DEFAULT 'INICIADO',
        fecha_inicio datetime2(0) NULL,
        fecha_ultimo_heartbeat datetime2(0) NULL,
        fecha_ultimo_ciclo datetime2(0) NULL,
        resultado_ultimo_ciclo varchar(30) NULL,
        ultimo_error varchar(max) NULL,
        ciclos_ejecutados int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_ciclos DEFAULT 0,
        tareas_evaluadas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_evaluadas DEFAULT 0,
        tareas_ejecutadas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_ejecutadas DEFAULT 0,
        tareas_omitidas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_omitidas DEFAULT 0,
        pid_proceso int NULL,
        host varchar(150) NULL,
        version_app varchar(50) NULL,
        activo bit NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_activo DEFAULT 1,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        CONSTRAINT PK_scheduler_worker_heartbeat PRIMARY KEY (id_worker),
        CONSTRAINT CK_scheduler_worker_heartbeat_estado CHECK (estado IN ('INICIADO','ACTIVO','EN_CICLO','ESPERANDO','ERROR','DETENIDO')),
        CONSTRAINT CK_scheduler_worker_heartbeat_ciclos CHECK (ciclos_ejecutados >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_evaluadas CHECK (tareas_evaluadas_ultimo_ciclo >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_ejecutadas CHECK (tareas_ejecutadas_ultimo_ciclo >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_omitidas CHECK (tareas_omitidas_ultimo_ciclo >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.scheduler_eventos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scheduler_eventos (
        id_evento int IDENTITY(1,1) NOT NULL,
        fecha_evento datetime NOT NULL CONSTRAINT DF_scheduler_eventos_fecha DEFAULT GETDATE(),
        nombre_worker varchar(100) NULL,
        id_tarea int NULL,
        nombre_tarea varchar(200) NULL,
        id_tarea_original int NULL,
        nombre_tarea_snapshot nvarchar(200) NULL,
        cliente_snapshot nvarchar(200) NULL,
        categoria_snapshot nvarchar(200) NULL,
        tipo_snapshot nvarchar(200) NULL,
        id_programacion int NULL,
        fecha_programada datetime NULL,
        clave_programacion varchar(200) NULL,
        tipo_evento varchar(50) NOT NULL,
        decision varchar(50) NOT NULL,
        motivo varchar(100) NULL,
        detalle varchar(max) NULL,
        estado_scheduler varchar(50) NULL,
        ejecutar_en_feriados bit NULL,
        es_feriado bit NULL,
        nombre_feriado varchar(200) NULL,
        origen varchar(50) NOT NULL CONSTRAINT DF_scheduler_eventos_origen DEFAULT 'SCHEDULER',
        activo bit NOT NULL CONSTRAINT DF_scheduler_eventos_activo DEFAULT 1,
        CONSTRAINT PK_scheduler_eventos PRIMARY KEY (id_evento),
        CONSTRAINT CK_scheduler_eventos_tipo CHECK (tipo_evento IN ('CICLO_INICIADO','CICLO_FINALIZADO','TAREA_EVALUADA','TAREA_EJECUTADA','TAREA_OMITIDA','ERROR_SCHEDULER')),
        CONSTRAINT CK_scheduler_eventos_decision CHECK (decision IN ('EJECUTAR','OMITIR','ERROR','INFO')),
        CONSTRAINT CK_scheduler_eventos_origen CHECK (origen IN ('SCHEDULER'))
    );
END;
GO

/* =========================================================
   Feriados
   ========================================================= */

IF OBJECT_ID(N'dbo.feriados', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.feriados (
        id_feriado int IDENTITY(1,1) NOT NULL,
        fecha date NOT NULL,
        nombre varchar(200) NOT NULL,
        tipo varchar(50) NULL,
        pais varchar(10) NOT NULL CONSTRAINT DF_feriados_pais DEFAULT 'CL',
        irrenunciable bit NOT NULL CONSTRAINT DF_feriados_irrenunciable DEFAULT 0,
        activo bit NOT NULL CONSTRAINT DF_feriados_activo DEFAULT 1,
        origen varchar(50) NOT NULL CONSTRAINT DF_feriados_origen DEFAULT 'MANUAL',
        observacion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_feriados_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        CONSTRAINT PK_feriados PRIMARY KEY (id_feriado),
        CONSTRAINT CK_feriados_pais CHECK (LEN(LTRIM(RTRIM(pais))) BETWEEN 1 AND 10),
        CONSTRAINT CK_feriados_origen CHECK (origen IN ('MANUAL','API','API_NAGER','IMPORTACION'))
    );
END;
GO

IF OBJECT_ID(N'dbo.reglas_feriados_irrenunciables', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.reglas_feriados_irrenunciables (
        id_regla int IDENTITY(1,1) NOT NULL,
        pais varchar(10) NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_pais DEFAULT 'CL',
        mes int NOT NULL,
        dia int NOT NULL,
        nombre_referencia varchar(200) NOT NULL,
        irrenunciable bit NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_irrenunciable DEFAULT 1,
        activo bit NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_activo DEFAULT 1,
        observacion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        CONSTRAINT PK_reglas_feriados_irrenunciables PRIMARY KEY (id_regla),
        CONSTRAINT CK_reglas_feriados_irrenunciables_pais CHECK (LEN(LTRIM(RTRIM(pais))) BETWEEN 1 AND 10),
        CONSTRAINT CK_reglas_feriados_irrenunciables_mes CHECK (mes BETWEEN 1 AND 12),
        CONSTRAINT CK_reglas_feriados_irrenunciables_dia CHECK (dia BETWEEN 1 AND 31)
    );
END;
GO

/* =========================================================
   Indices finales
   ========================================================= */

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_usuarios_activo' AND object_id = OBJECT_ID(N'dbo.usuarios'))
    CREATE INDEX IX_usuarios_activo ON dbo.usuarios(activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_usuarios_operativo' AND object_id = OBJECT_ID(N'dbo.usuarios'))
    CREATE INDEX IX_usuarios_operativo ON dbo.usuarios(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_roles_permisos_permiso' AND object_id = OBJECT_ID(N'dbo.roles_permisos'))
    CREATE INDEX IX_roles_permisos_permiso ON dbo.roles_permisos(id_permiso);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_clientes_activo' AND object_id = OBJECT_ID(N'dbo.clientes'))
    CREATE INDEX IX_clientes_activo ON dbo.clientes(activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_clientes_operativo' AND object_id = OBJECT_ID(N'dbo.clientes'))
    CREATE INDEX IX_clientes_operativo ON dbo.clientes(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_categorias_operativo' AND object_id = OBJECT_ID(N'dbo.categorias'))
    CREATE INDEX IX_categorias_operativo ON dbo.categorias(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tipos_operativo' AND object_id = OBJECT_ID(N'dbo.tipos'))
    CREATE INDEX IX_tipos_operativo ON dbo.tipos(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_estado' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_estado ON dbo.tareas(estado_tarea, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_cliente_categoria_tipo' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_cliente_categoria_tipo ON dbo.tareas(id_cliente, id_categoria, id_tipo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_proxima_ejecucion' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_proxima_ejecucion ON dbo.tareas(proxima_ejecucion) WHERE activo = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_nombre_contexto' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_nombre_contexto ON dbo.tareas(nombre_tarea, id_cliente, id_categoria, id_tipo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_operativo' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_operativo ON dbo.tareas(eliminado_operativo, activo, estado_tarea);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_programaciones_tarea_activo' AND object_id = OBJECT_ID(N'dbo.programaciones'))
    CREATE INDEX IX_programaciones_tarea_activo ON dbo.programaciones(id_tarea, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_programaciones_tipo_modo' AND object_id = OBJECT_ID(N'dbo.programaciones'))
    CREATE INDEX IX_programaciones_tipo_modo ON dbo.programaciones(tipo_programacion, modo_ejecucion_dia, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_version_activa' AND object_id = OBJECT_ID(N'dbo.scripts'))
    CREATE INDEX IX_scripts_version_activa ON dbo.scripts(id_version_activa);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_operativo' AND object_id = OBJECT_ID(N'dbo.scripts'))
    CREATE INDEX IX_scripts_operativo ON dbo.scripts(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_scripts_versiones_script_activa' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE UNIQUE INDEX UX_scripts_versiones_script_activa ON dbo.scripts_versiones(id_script) WHERE es_activa = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_script_estado' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_script_estado ON dbo.scripts_versiones(id_script, estado_version);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_hash' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_hash ON dbo.scripts_versiones(hash_archivo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_requiere_env' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_requiere_env ON dbo.scripts_versiones(requiere_env);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_operativo' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_operativo ON dbo.scripts_versiones(eliminado_operativo, estado_version, es_activa);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_tarea_fecha' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_tarea_fecha ON dbo.ejecuciones(id_tarea, fecha_hora_inicio DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_script_version' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_script_version ON dbo.ejecuciones(id_script, id_version);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_estado' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_estado ON dbo.ejecuciones(estado_ejecucion);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_origen_estado' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_origen_estado ON dbo.ejecuciones(origen_ejecucion, estado_ejecucion, fecha_hora_inicio);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_ejecuciones_clave_programacion_automatica' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE UNIQUE INDEX UX_ejecuciones_clave_programacion_automatica ON dbo.ejecuciones(clave_programacion) WHERE origen_ejecucion = 'AUTOMATICA' AND clave_programacion IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_detencion' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_detencion ON dbo.ejecuciones(fecha_hora_detencion, usuario_detencion) WHERE fecha_hora_detencion IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_tareas_ejecucion' AND object_id = OBJECT_ID(N'dbo.logs_tareas'))
    CREATE INDEX IX_logs_tareas_ejecucion ON dbo.logs_tareas(id_ejecucion);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_tareas_tarea_fecha' AND object_id = OBJECT_ID(N'dbo.logs_tareas'))
    CREATE INDEX IX_logs_tareas_tarea_fecha ON dbo.logs_tareas(id_tarea, fecha_creacion DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_sistema_fecha' AND object_id = OBJECT_ID(N'dbo.logs_sistema'))
    CREATE INDEX IX_logs_sistema_fecha ON dbo.logs_sistema(fecha_hora DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_sistema_usuario' AND object_id = OBJECT_ID(N'dbo.logs_sistema'))
    CREATE INDEX IX_logs_sistema_usuario ON dbo.logs_sistema(usuario);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_cambios_fecha_evento' AND object_id = OBJECT_ID(N'dbo.auditoria_cambios'))
    CREATE INDEX IX_auditoria_cambios_fecha_evento ON dbo.auditoria_cambios(fecha_evento DESC, id_auditoria DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_cambios_usuario' AND object_id = OBJECT_ID(N'dbo.auditoria_cambios'))
    CREATE INDEX IX_auditoria_cambios_usuario ON dbo.auditoria_cambios(usuario, fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_cambios_entidad' AND object_id = OBJECT_ID(N'dbo.auditoria_cambios'))
    CREATE INDEX IX_auditoria_cambios_entidad ON dbo.auditoria_cambios(entidad, id_entidad, fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_configuracion_scheduler_activa' AND object_id = OBJECT_ID(N'dbo.configuracion_scheduler'))
    CREATE UNIQUE INDEX UX_configuracion_scheduler_activa ON dbo.configuracion_scheduler(activo) WHERE activo = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_scheduler_worker_heartbeat_nombre_activo' AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat'))
    CREATE UNIQUE INDEX UX_scheduler_worker_heartbeat_nombre_activo ON dbo.scheduler_worker_heartbeat(nombre_worker) WHERE activo = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_worker_heartbeat_nombre' AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat'))
    CREATE INDEX IX_scheduler_worker_heartbeat_nombre ON dbo.scheduler_worker_heartbeat(nombre_worker);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_worker_heartbeat_fecha' AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat'))
    CREATE INDEX IX_scheduler_worker_heartbeat_fecha ON dbo.scheduler_worker_heartbeat(fecha_ultimo_heartbeat);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_worker_heartbeat_estado' AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat'))
    CREATE INDEX IX_scheduler_worker_heartbeat_estado ON dbo.scheduler_worker_heartbeat(estado, fecha_ultimo_heartbeat);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_fecha' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_fecha ON dbo.scheduler_eventos(fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_tarea' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_tarea ON dbo.scheduler_eventos(id_tarea);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_tipo' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_tipo ON dbo.scheduler_eventos(tipo_evento);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_clave' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_clave ON dbo.scheduler_eventos(clave_programacion);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_decision' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_decision ON dbo.scheduler_eventos(decision, fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_motivo' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_motivo ON dbo.scheduler_eventos(motivo, fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_worker' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_worker ON dbo.scheduler_eventos(nombre_worker, fecha_evento DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scheduler_eventos_fecha_programada' AND object_id = OBJECT_ID(N'dbo.scheduler_eventos'))
    CREATE INDEX IX_scheduler_eventos_fecha_programada ON dbo.scheduler_eventos(fecha_programada, id_tarea);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_feriados_fecha_pais_activo' AND object_id = OBJECT_ID(N'dbo.feriados'))
    CREATE UNIQUE INDEX UX_feriados_fecha_pais_activo ON dbo.feriados(fecha, pais) WHERE activo = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_feriados_fecha' AND object_id = OBJECT_ID(N'dbo.feriados'))
    CREATE INDEX IX_feriados_fecha ON dbo.feriados(fecha);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_feriados_pais' AND object_id = OBJECT_ID(N'dbo.feriados'))
    CREATE INDEX IX_feriados_pais ON dbo.feriados(pais, fecha);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_feriados_activo' AND object_id = OBJECT_ID(N'dbo.feriados'))
    CREATE INDEX IX_feriados_activo ON dbo.feriados(activo, fecha);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_reglas_feriados_irrenunciables_pais_mes_dia_activo' AND object_id = OBJECT_ID(N'dbo.reglas_feriados_irrenunciables'))
    CREATE UNIQUE INDEX UX_reglas_feriados_irrenunciables_pais_mes_dia_activo ON dbo.reglas_feriados_irrenunciables(pais, mes, dia) WHERE activo = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_reglas_feriados_irrenunciables_busqueda' AND object_id = OBJECT_ID(N'dbo.reglas_feriados_irrenunciables'))
    CREATE INDEX IX_reglas_feriados_irrenunciables_busqueda ON dbo.reglas_feriados_irrenunciables(pais, mes, dia, activo);
GO
