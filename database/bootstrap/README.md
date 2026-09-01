# Bootstrap limpio APP Scheduler

Esta carpeta define el bootstrap vigente para una base nueva. El orden ejecutable esta en `manifest.json`; el script SQLCMD `000_ejecutar_bootstrap_completo.sql` refleja exactamente ese manifiesto.

El bootstrap reutiliza `database/release/001-006` como base publicada e inmutable y agrega definiciones limpias y seeds para las funcionalidades posteriores. Esto evita copiar el esquema base de 885 lineas y mantiene separado el release historico del bootstrap actual.

Desde Fase 19C, `011_seed_permiso_factory_reset.sql` agrega `FACTORY_RESET_EJECUTAR` exclusivamente a `SUPER_ADMIN`. El bootstrap vigente queda en version `19C.1`, con 52 permisos activos y canales independientes `EXITO`, `EVIDENCIA` y `ALERTA`. Este seed solo prepara autorizacion; no implementa ni ejecuta un Factory Reset.

## Ejecucion

1. Confirmar que el nombre destino corresponde a una base nueva y desechable.
2. Abrir `000_ejecutar_bootstrap_completo.sql` desde la raiz del repositorio.
3. Habilitar SQLCMD Mode.
4. Cambiar solamente `DB_NAME`.
5. Ejecutar el script completo y comprobar que `100_validacion_bootstrap_actual.sql` finalice en `OK`.

No ejecutar sobre `APP_SCHEDULER_QA` ni sobre una base con datos. El bootstrap es determinista para una base nueva; no se define como reparador de drift en bases existentes.

`database/migrations/021_consolidar_configuracion_mail_graph_qa.sql` esta excluida: elimina IDs concretos y corrige datos de QA, por lo que no corresponde a una instalacion limpia ni al futuro Factory Reset.
