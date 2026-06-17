/*
Fase 10B - APP Scheduler
Seed: 010_permisos_sincronizacion_feriados.sql
Objetivo: agregar permiso incremental para sincronizacion controlada de feriados.
Nota: ejecutar manualmente en SSMS. No modifica seeds anteriores.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('FERIADOS_SINCRONIZAR', N'feriados', N'sincronizar', N'Sincronizar feriados desde Nager.Date con vista previa.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_010');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_010'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso = 'FERIADOS_SINCRONIZAR'
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN','TI')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
