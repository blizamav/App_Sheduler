# Changelog

## 2026-06-12 - Fase 3D conexion Flask SQL Server

### Agregado

* Dependencia `pyodbc`.
* Modulo `app/database/conexion.py`.
* Funcion `probar_conexion_bd()`.
* Ruta temporal `/diagnostico/bd` disponible solo en `LOCAL` y `QA`.
* Template de diagnostico de conexion.

### Validado

* La app sigue levantando.
* Login desde `.env` sigue funcionando.
* `/panel` sigue funcionando.
* `/diagnostico/bd` responde sin exponer credenciales.

### Pendiente

* Resolver cualquier error local de driver/red/cifrado que aparezca en `/diagnostico/bd`.
* No hay CRUD, usuarios en base de datos ni scheduler.

## 2026-06-12 - Fase 3B scripts SQL versionados

### Validado Manualmente

* Scripts `001` a `006` ejecutados correctamente en SQL Server local.
* Seeds `001` y `002` ejecutados correctamente.
* Base `APP_SCHEDULER_QA` creada.
* Tablas creadas y verificadas.
* Catalogos con datos iniciales cargados.
* Roles, permisos y relaciones iniciales cargados.
* Confirmado que no se creo el usuario `blizama` en base de datos.
* Flask aun no se conecta a SQL Server.

### Revisado

* Revision tecnica previa de scripts SQL antes de ejecucion manual en SSMS.
* Confirmado orden de claves foraneas y FK diferida `scripts.id_version_activa`.
* Ajustada documentacion de `logs_tareas.nombre_archivo_log` y `logs_sistema.nivel varchar(30)`.

### Agregado

* Carpeta `database/migrations/`.
* Carpeta `database/seeds/`.
* Script `001_crear_base_datos.sql`.
* Script `002_crear_catalogos.sql`.
* Script `003_crear_tablas_seguridad.sql`.
* Script `004_crear_tablas_negocio.sql`.
* Script `005_crear_tablas_ejecucion_logs.sql`.
* Script `006_crear_indices.sql`.
* Seed `001_datos_iniciales_catalogos.sql`.
* Seed `002_roles_permisos_iniciales.sql`.

### Incluye

* Tablas catalogo, seguridad, negocio, ejecucion, logs y auditoria.
* `scripts` y `scripts_versiones` con versionamiento controlado.
* Foreign keys desde estados/tipos operativos hacia catalogos.
* `CHECK(numero_version BETWEEN 1 AND 3)`.
* `UNIQUE(id_script, numero_version)`.
* Indice unico filtrado para una sola version activa.
* FK diferida `scripts.id_version_activa` en script de indices por dependencia circular.
* Seeds de catalogos, roles, permisos y roles_permisos.

### No implementado

* No se ejecuto SQL.
* No se conecto Flask a SQL Server.
* No se creo usuario `blizama` en base de datos.
* No se implemento CRUD ni scheduler.

### Documentacion

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/DESPLIEGUE.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 3A ajuste versionamiento scripts

### Aprobado

* Se aprueba mantener `scripts` + `scripts_versiones`.
* Se aprueba mantener `id_version_activa` en `scripts`.
* Versiones `REEMPLAZADA` no cuentan dentro del maximo de 3 versiones disponibles.
* Primera version controla maximo 3 en capa de servicio.
* Base de datos se refuerza con `CHECK(numero_version BETWEEN 1 AND 3)`, `UNIQUE(id_script, numero_version)` e indice unico filtrado para una sola version activa.
* Trigger o procedimiento almacenado queda como mejora futura.
* Se aprueba estructura fisica `v1`, `v2`, `v3`.

### Documentado

* Separacion entre `scripts` como script logico y `scripts_versiones` como archivos versionados.
* Regla de maximo 3 versiones disponibles por script.
* Regla de una sola version activa por script.
* Ejecuciones con `id_script` e `id_version` para trazabilidad exacta.
* Rutas fisicas versionadas con carpetas `v1`, `v2`, `v3`.
* Flujos de carga, activacion, ejecucion manual/automatica, reemplazo y auditoria de versiones.
* Estrategia recomendada: validacion inicial en capa de servicio, con constraints simples e indice filtrado para una version activa.

### No implementado

* No se creo conexion SQL Server.
* No se ejecutaron scripts SQL.
* No se crearon tablas.
* No se modifico logica funcional Flask.

### Archivos modificados

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/FLUJOS.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 3 parte 1

### Documentado

* Propuesta inicial de modelo relacional SQL Server para `APP_SCHEDULER_QA`.
* Tablas criticas y tablas futuras.
* Campos principales, claves primarias, claves foraneas e indices recomendados.
* Estados propuestos para tareas, ejecuciones y programaciones.
* Reglas para rutas fisicas/relativas de scripts y logs.
* Propuesta de auditoria y logs de sistema.

### No implementado

* No se creo conexion SQL Server.
* No se ejecutaron scripts SQL.
* No se crearon tablas.
* No se modifico CRUD ni logica funcional.

### Archivos modificados

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 2

### Mejorado

* Layout base responsive con sidebar, topbar, usuario logueado y panel lateral visual para logs.
* Pantalla de login con diseno corporativo moderno, fondo tecnico sutil y formulario refinado.
* Panel principal con cards de resumen, placeholders claros y secciones preparadas para ejecuciones, errores y scheduler.
* Componentes visuales reutilizables: botones, cards, badges, alertas, contenedores, tabla base y estados visuales.
* CSS reorganizado con variables de color, espaciado, sombras, bordes y transiciones.
* JavaScript base para toggle de sidebar, panel lateral de logs y tratamiento visual de alertas.

### Archivos modificados

* `app/templates/base.html`
* `app/templates/login.html`
* `app/templates/panel.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`
* `README.md`
* `docs/UI_UX.md`
* `docs/ARQUITECTURA.md`
* `log_codex.md`

### Pendientes visuales

* Validar en navegador con datos reales de usuario.
* Refinar iconografia cuando se incorpore libreria de iconos o componentes finales.
* Conectar estados visuales a datos reales en fases posteriores.

## 2026-06-12 - Fase 1

### Agregado

* Estructura inicial Flask.
* Login inicial desde `.env`.
* Panel principal base.
* Layout visual inicial.
* Documentacion tecnica inicial.
* `.gitignore` profesional.
* `.env.example`.
* Bitacora `log_codex.md`.
