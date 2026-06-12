/*
Fase 3B - APP Scheduler
Script: 004_crear_tablas_negocio.sql
Objetivo: crear tablas maestras y de negocio.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.clientes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.clientes (
        id_cliente int IDENTITY(1,1) NOT NULL,
        nombre_cliente nvarchar(150) NOT NULL,
        nombre_normalizado nvarchar(150) NOT NULL,
        descripcion nvarchar(300) NULL,
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
        id_cliente int NOT NULL,
        id_categoria int NOT NULL,
        id_tipo int NOT NULL,
        tipo_tarea varchar(30) NOT NULL,
        estado_tarea varchar(30) NOT NULL,
        ultima_ejecucion datetime2(0) NULL,
        proxima_ejecucion datetime2(0) NULL,
        ultimo_estado_ejecucion varchar(30) NULL,
        permite_ejecucion_manual bit NOT NULL CONSTRAINT DF_tareas_permite_ejecucion_manual DEFAULT 1,
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
        hora_inicio time(0) NULL,
        hora_termino time(0) NULL,
        hora_ejecucion time(0) NULL,
        intervalo_minutos int NULL,
        dias_semana varchar(50) NULL,
        dia_mes tinyint NULL,
        fechas_especificas nvarchar(max) NULL,
        configuracion_json nvarchar(max) NULL,
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
        CONSTRAINT CK_programaciones_dia_mes CHECK (dia_mes IS NULL OR dia_mes BETWEEN 1 AND 31)
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
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_scripts_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_scripts_activo DEFAULT 1,
        CONSTRAINT PK_scripts PRIMARY KEY (id_script),
        CONSTRAINT UX_scripts_id_tarea UNIQUE (id_tarea),
        CONSTRAINT FK_scripts_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea)
        -- FK id_version_activa se agrega en 006 por dependencia circular con scripts_versiones.
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
        usuario_carga nvarchar(100) NOT NULL,
        fecha_carga datetime2(0) NOT NULL CONSTRAINT DF_scripts_versiones_fecha_carga DEFAULT SYSDATETIME(),
        observacion nvarchar(1000) NULL,
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

-- Futuras tablas consideradas: feriados, calendarios_laborales, notificaciones,
-- parametros_tarea, ambientes y respaldos.
