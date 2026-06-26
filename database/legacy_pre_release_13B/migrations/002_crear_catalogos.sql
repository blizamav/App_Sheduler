/*
Fase 3B - APP Scheduler
Script: 002_crear_catalogos.sql
Objetivo: crear catalogos base del sistema.
*/

USE APP_SCHEDULER_QA;
GO

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
