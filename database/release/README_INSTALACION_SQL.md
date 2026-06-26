# APP Scheduler - Instalacion SQL release limpio

Este directorio contiene una instalacion limpia de base de datos para `APP_SCHEDULER_TEST_INSTALL`, usada para validar el release desde cero sin tocar la base operativa `APP_SCHEDULER_QA`.

La carpeta `database/migrations/` y `database/seeds/` se conserva como historial de desarrollo. Para una instalacion nueva se debe usar este release consolidado.

## Orden de ejecucion

Ejecutar manualmente en SQL Server Management Studio, en este orden:

1. `001_crear_base_datos.sql`
2. `002_schema_final.sql`
3. `003_seed_roles_permisos.sql`
4. `004_seed_catalogos_base.sql`
5. `005_seed_configuracion_inicial.sql`
6. `006_seed_feriados_base.sql`
7. `099_validacion_instalacion.sql`

Si hubo una ejecucion previa fallida durante Fase 13B, reiniciar la prueba desde una base limpia. No aplicar parches manuales directos sobre tablas: toda correccion debe estar reflejada en estos scripts release.

## Regla critica de Fase 13B

Durante la prueba de instalacion limpia no ejecutar estos scripts sobre `APP_SCHEDULER_QA`.

Los scripts de este paquete apuntan explicitamente a:

```text
APP_SCHEDULER_TEST_INSTALL
```

Si se requiere usar otro nombre de base en un ambiente futuro, cambiarlo de forma controlada en todos los scripts del paquete antes de ejecutar y documentar la decision. No hacer reemplazos parciales.

## Alcance

El release crea la estructura final actual del sistema:

- Seguridad: usuarios, roles, permisos, usuarios_roles y roles_permisos.
- Catalogos base.
- Mantenedores: clientes, categorias y tipos.
- Tareas y programaciones.
- Scripts y versiones con maximo tres versiones logicas.
- Ejecuciones, logs de tareas y logs de sistema.
- Scheduler: configuracion, heartbeat y eventos del programador.
- Feriados locales y reglas de irrenunciables.
- Papelera operativa mediante marcas de eliminado operativo.
- Auditoria de cambios.

## Datos incluidos

Los seeds incluyen:

- Roles base.
- Permisos base y asignaciones por rol.
- Catalogos del sistema.
- Configuracion inicial segura del scheduler, apagada por defecto.
- Reglas locales de feriados irrenunciables para Chile.

## Datos no incluidos

Este release no incluye:

- Usuarios reales.
- Passwords.
- Servidores.
- Rutas locales.
- Tareas de prueba.
- Scripts cargados.
- Ejecuciones.
- Logs historicos.
- Auditoria historica.
- Feriados sincronizados desde API.

## Seguridad

Los scripts no contienen credenciales ni cadenas de conexion. La conexion de la aplicacion se configura por `.env`, que no debe subirse a Git ni sobrescribirse automaticamente.

## Validacion

`099_validacion_instalacion.sql` solo ejecuta consultas `SELECT`. Sirve para revisar conteos, indices criticos, claves foraneas y restricciones `CHECK`.

No ejecuta `INSERT`, `UPDATE`, `DELETE`, `DROP` ni cambios de datos.

## Estado Fase 13B

Codex preparo el paquete para la prueba limpia apuntando a `APP_SCHEDULER_TEST_INSTALL`, pero no ejecuto los scripts SQL. La ejecucion debe realizarse manualmente en SSMS y sus resultados deben registrarse en `log_codex.md` y `docs/CHANGELOG.md`.

## Correccion Fase 13B - seed de roles

Durante la primera ejecucion manual de `003_seed_roles_permisos.sql` se detecto incompatibilidad con el schema final: `dbo.roles.codigo_rol` es obligatorio y el seed no lo informaba.

El seed corregido crea de forma idempotente estos roles base:

- `SUPER_ADMIN`
- `ADMIN`
- `TI`
- `TERCERO`

Las relaciones de `roles_permisos` usan `codigo_rol` para evitar depender del nombre visible del rol.

Si el script `003` fallo antes de insertar roles pero alcanzo a insertar permisos, puede volver a ejecutarse el mismo `003` corregido sobre `APP_SCHEDULER_TEST_INSTALL`; usa `MERGE` y validaciones `NOT EXISTS` para no duplicar permisos ni relaciones.

## Auditoria Fase 13B.1

Se agrego el documento:

```text
database/release/AUDITORIA_RELEASE_SQL.md
```

La auditoria detecto y corrigio inconsistencias adicionales:

- `004_seed_catalogos_base.sql` ahora informa `nombre` en todos los catalogos.
- `cat_tipos_tarea` usa los codigos esperados por la app: `MANUAL` y `PROGRAMADA`.
- `005_seed_configuracion_inicial.sql` usa `descripcion` en `configuracion_scheduler`.
- `configuracion_sistema` recibe `tipo_dato`, requerido por el schema.
- `099_validacion_instalacion.sql` entrega validaciones por secciones.

## Correccion de criterio Fase 13B.1 - roles y permisos reales de QA

La instalacion limpia debe reconstruir fielmente el estado base real de `APP_SCHEDULER_QA`, excluyendo solo datos operativos e historicos.

`APP_SCHEDULER_QA` tiene cuatro roles base: `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`. El rol `OPERADOR` no existe en QA y fue eliminado del release ejecutable.

La matriz esperada de permisos por rol queda:

- `SUPER_ADMIN`: 39 permisos.
- `ADMIN`: 37 permisos.
- `TI`: 31 permisos.
- `TERCERO`: 7 permisos.

`099_validacion_instalacion.sql` valida explicitamente que existan los cuatro roles base, que no existan roles no esperados, que `OPERADOR` no exista y que los conteos de permisos por rol tengan diferencia `0`.
