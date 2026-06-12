# Changelog

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
