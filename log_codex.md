# log_codex - Bitacora tecnica del proyecto

## 1. Estado general

* Nombre del proyecto: APP Scheduler
* Descripcion: Aplicacion web corporativa para programar, ejecutar, monitorear y auditar tareas Python de equipos TI.
* Stack actual: Python, Flask, HTML, CSS, JavaScript, python-dotenv, pyodbc, SQL Server.
* Base de datos: SQL Server local `APP_SCHEDULER_QA` creada y validada manualmente; migraciones 001-007 ejecutadas localmente; conexion Flask-SQL Server inicial agregada con diagnostico controlado.
* Estado actual: Fase 8 implementada con ejecucion manual, consola y detencion controlada.
* Ambiente actual: LOCAL Windows.
* Fase actual: Fase 8 - Ejecucion manual con consola y control de detencion.
* Ultima actualizacion: 2026-06-15 00:00

## 2. Decisiones tecnicas vigentes

* Backend: Flask con fabrica `crear_app()` y Blueprint principal.
* Frontend: HTML/CSS/JS sin Streamlit.
* Base de datos: SQL Server local creado con scripts versionados; conexion Flask inicial mediante `pyodbc` y `.env`.
* Autenticacion: Login hibrido; primero `.env`, luego usuarios activos de SQL Server con password hash.
* Scheduler: Pendiente para fase posterior.
* Logs: Logs de tarea para ejecucion manual implementados en Fase 8; logs avanzados pendientes.
* Auditoria: Pendiente para Fase 10.
* Docker: Pendiente para Fase 11.
* Seguridad: Secretos y credenciales fuera del repositorio mediante `.env`.
* Seguridad `.env`: Nunca sobrescribir `.env` si ya existe; usar comandos seguros que copien `.env.example` solo cuando `.env` no existe.
* Versiones de scripts: No existe eliminacion fisica desde la app en primera version; se gestionan por estados `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Diseno UI/UX: Corporativo sobrio, responsive, sidebar oscuro, topbar clara, componentes reutilizables, fondo claro, azul corporativo, cyan moderado y estados por color.

## 3. Estructura actual del proyecto

* Carpetas principales: `app/`, `app/templates/`, `app/static/`, `docs/`, `database/migrations/`, `database/seeds/`.
* Archivos principales: `run.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `log_codex.md`.
* Modulos implementados: Login inicial, panel base visual, layout responsive, configuracion centralizada, modelo SQL Server con versionamiento de scripts, scripts SQL versionados ejecutados manualmente en SQL Server local, modulo inicial de conexion SQL Server, diagnostico local/QA, usuarios/roles/permisos iniciales, mejoras UX Fase 4.1, modal de confirmacion Fase 4.2, definicion tecnica Fase 4.3, mantenedores base Fase 5, eliminacion controlada Fase 5.1, tareas con programacion base Fase 6, resumen de confirmacion Fase 6.1, deteccion de cambios reales Fase 6.2, gestion de scripts/versiones/env Fase 7, mensajes contextuales Fase 7.1, bloque de script activo Fase 7.2, simplificacion visual Fase 7.3, eliminacion diferenciada Fase 7.4, separacion contenedor/archivo Fase 7.5 y ejecucion manual Fase 8.
* Modulos pendientes: Scheduler automatico, ejecucion programada, API feriados, logs avanzados, auditoria, Docker, calendario laboral.

## 4. Reglas del proyecto

* Reglas de codigo: Usar nombres descriptivos en espanol cuando sea razonable, Flask modular y configuracion centralizada.
* Reglas de seguridad: No versionar `.env`, logs reales, scripts cargados por usuarios ni secretos.
* Reglas de documentacion: Toda modificacion debe actualizar `docs/`, `docs/CHANGELOG.md` si aplica y `log_codex.md`.
* Reglas de diseno: UI clara, sobria, responsive, corporativa y futurista moderada.
* Reglas de base de datos: SQL Server con claves primarias, foraneas, indices y auditoria desde Fase 3.
* Reglas de despliegue: Sin rutas absolutas quemadas; usar variables de entorno.

## 5. Pendientes

* Pendiente 1: Resolver/validar conexion OK desde `/diagnostico/bd` en el entorno local del usuario si aparece error de driver/red/cifrado.
* Pendiente 2: Ejecutar seed 006 en SQL Server local para usuarios de base de datos.
* Pendiente 3: Validar ejecucion manual con script exitoso, script con error y detencion manual.

## 6. Historial de cambios

### 2026-06-15 00:00 - Fase 8 / Seed 006 ejecutado y validacion local completada

* Archivos creados: Ninguno.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se registro que `database/seeds/006_permisos_ejecuciones.sql` fue ejecutado correctamente en SQL Server local.
* Validaciones reportadas: Permisos `EJECUCIONES_*` insertados; ejecucion manual con script activo; consola con stdout; polling de log; estado `EXITOSA`; detencion manual con estado `DETENIDA_MANUALMENTE`; `pid_proceso` registrado; archivo de log generado en `logs_tareas/`.
* Pruebas con env: Se valido ejecucion sin `.env` y con `.env` de prueba `AMBIENTE=QA`, leido por el script mediante `os.getenv()`.
* Seguridad: No se mostraron secretos; no se registro contenido sensible del `.env`.
* No implementado: No se implemento scheduler automatico, no se conecto API de feriados y no se avanzo a Fase 9.
* Riesgos detectados: Mantener la regla de que los scripts cargados no deben imprimir secretos, porque stdout/stderr se muestra en consola.
* Proximos pasos: Cerrar validacion funcional de Fase 8 o definir ajustes menores antes de iniciar Fase 9.

### 2026-06-15 00:00 - Fase 8 / Ejecucion manual con consola y detencion

* Archivos creados: `app/rutas_ejecuciones.py`, `app/repositorios/repositorio_ejecuciones.py`, `app/servicios/servicio_ejecuciones.py`, `app/servicios/servicio_env_scripts.py`, `app/servicios/servicio_procesos.py`, `app/templates/ejecuciones/consola.html`, `database/seeds/006_permisos_ejecuciones.sql`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/repositorios/repositorio_tareas.py`, `app/templates/base.html`, `app/templates/tareas/listado.html`, `app/templates/scripts/listado.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `docs/DESPLIEGUE.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se implemento ejecucion manual de tareas usando la version activa del script, consola visual con polling, archivo de log por ejecucion y detencion manual.
* Permisos: Se creo seed incremental `006_permisos_ejecuciones.sql` con `EJECUCIONES_VER`, `EJECUCIONES_EJECUTAR`, `EJECUCIONES_DETENER` y `EJECUCIONES_LOG_VER`; debe ejecutarse manualmente en SSMS para usuarios DB.
* Decision tecnica: No se creo migracion 010 porque `ejecuciones` y `logs_tareas` ya contienen los campos necesarios.
* Seguridad: La ejecucion usa `subprocess` sin `shell=True`, carga `.env` por version en el entorno del proceso sin mostrar contenido y bloquea ejecuciones simultaneas por tarea.
* Logs: Se registra `pid_proceso`, salida stdout/stderr en archivo `logs_tareas/AAAA/MM/DD/`, metadatos en `logs_tareas` y eventos en `logs_sistema`.
* Detencion: Se implemento detencion controlada del proceso registrado y cierre forzado por PID si corresponde, actualizando `DETENIDA_MANUALMENTE`.
* Pruebas realizadas: `python -m compileall app`; carga de `crear_app()` y listado de rutas `/tareas/<id_tarea>/ejecutar`, `/ejecuciones/<id_ejecucion>`, `/ejecuciones/<id_ejecucion>/log`, `/ejecuciones/<id_ejecucion>/detener`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`; render de `ejecuciones/consola.html` con datos simulados confirmando consola, log y boton de detencion; verificacion de seed 006 contra columnas reales `codigo_rol` y `codigo_permiso`.
* Riesgos detectados: La detencion de arbol completo depende del sistema operativo; en Windows se usa `taskkill` como respaldo. Los scripts no deben imprimir secretos, porque stdout/stderr se muestra en consola.
* Proximos pasos: Ejecutar seed 006 en SSMS, probar script exitoso, script con error y detencion manual; no avanzar a Fase 9.

### 2026-06-15 00:00 - Fase 7.5 / Migracion 009 ejecutada y validada localmente

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se registro que `009_corregir_nombre_script_contenedor.sql` fue ejecutada manualmente en SQL Server local sin errores.
* Resultado: La migracion afecto 0 filas porque no existian scripts antiguos con `nombre_script` terminado en `.py`.
* Decision: El resultado es correcto y esperado en este ambiente; no habia datos antiguos que corregir.
* Alcance: La nueva logica de Fase 7.5 aplica para los proximos scripts cargados, usando `Script de {nombre_tarea}` como contenedor y `scripts_versiones.nombre_archivo` para el archivo real.
* Pruebas realizadas: Validacion manual reportada por el usuario en SQL Server local.
* Riesgos detectados: En otros ambientes con datos antiguos, la migracion puede afectar filas si existen nombres terminados en `.py`; revisar conteo antes/despues al ejecutar.
* Proximos pasos: Continuar pruebas de carga de scripts sin avanzar a Fase 8 hasta aprobacion.

### 2026-06-15 00:00 - Fase 7.5 / Corregir concepto de script principal y archivo de version

* Archivos creados: `database/migrations/009_corregir_nombre_script_contenedor.sql`.
* Archivos modificados: `app/servicios/servicio_scripts.py`, `app/templates/scripts/listado.html`, `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Problema detectado: Al cargar el primer `.py`, `scripts.nombre_script` quedaba con el nombre del archivo, por ejemplo `prueba_1.py`.
* Decision tecnica: `scripts` representa el contenedor asociado a la tarea y `scripts_versiones` representa los archivos `.py` reales.
* Correccion aplicada: Al crear el primer script, `scripts.nombre_script` se guarda como `Script de {nombre_tarea}` y el archivo cargado queda en `scripts_versiones.nombre_archivo`.
* Migracion 009: Corrige registros existentes cuyo `scripts.nombre_script` termine en `.py`, usando `Script de ` + `tareas.nombre_tarea`; no se ejecuto automaticamente.
* Vista: El bloque superior sigue mostrando el archivo activo real desde la version activa y no muestra nombre logico ni contenedor interno.
* Pruebas realizadas: `python -m compileall app`; busqueda sin `script logico`, `Nombre logico`, `alert(`, `window.confirm`, `confirm(` ni `prompt(` en UI; prueba simulada de `subir_version` confirmando `scripts.nombre_script = Script de Pruebaa3` y `scripts_versiones.nombre_archivo = prueba_1.py`; render de `scripts/listado.html` confirmando bloque activo con `prueba_4.py`, sin `Nombre logico` ni `prueba_1.py`.
* Riesgos detectados: Ejecutar migracion 009 manualmente en SSMS antes de seguir probando con registros antiguos.
* Proximos pasos: Ejecutar 009 en SQL Server local, validar que registros antiguos cambien a `Script de {nombre_tarea}` y mantener Fase 8 pendiente.

### 2026-06-15 00:00 - Fase 7.4 / Diferenciar eliminacion de script completo y version

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/scripts/listado.html`, `app/servicios/servicio_scripts.py`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Problema detectado: El boton `Eliminar script` era ambiguo y podia interpretarse como eliminacion del archivo activo, aunque afectaba el script logico completo.
* Decision UX: Renombrar la accion superior a `Eliminar script completo` y usar `Eliminar version` en cada fila de la tabla.
* Correccion aplicada: Los modales explican si la accion afecta todas las versiones o solo una version especifica.
* Reglas aplicadas: La eliminacion de version activa se bloquea; la eliminacion de unica version se bloquea; la version con historial se bloquea; una version eliminada no elimina otras versiones.
* Logs: Se agregaron registros diferenciados para script completo eliminado, eliminacion completa bloqueada por historial, version eliminada y bloqueos por activa, unica o historial.
* Pruebas realizadas: `python -m compileall app`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`; verificacion de textos `Eliminar script completo`, `Activar version`, `Desactivar version` y `Eliminar version`; prueba simulada de `eliminar_version_script` confirmando que v2 no activa elimina solo esa version, version activa se bloquea y unica version se bloquea.
* Riesgos detectados: Validar en navegador con datos reales v1/v2/v3 que los botones largos no rompan la tabla en resoluciones pequenas.
* Proximos pasos: Probar eliminacion de v2 no activa, intento de eliminar activa y unica version; no avanzar a Fase 8 sin aprobacion.

### 2026-06-15 00:00 - Fase 7.3 / Simplificar bloque de script activo

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/scripts/listado.html`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `log_codex.md`.
* Que se corrigio: El bloque superior de scripts ya no muestra `Nombre logico`, para evitar confusion cuando el archivo activo real fue reemplazado.
* Decision visual: Mostrar solo el archivo activo real desde `scripts_versiones`, version activa, estado `.env`, estado del script y texto descriptivo operativo.
* Decision tecnica: Mantener `scripts.nombre_script` internamente sin modificar SQL, modelo, servicios ni registros historicos.
* Pruebas realizadas: `python -m compileall app`; render de `scripts/listado.html` validando que `prueba_4.py` aparece como archivo activo y que no aparecen `Nombre logico` ni `prueba_1.py`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`.
* Riesgos detectados: Validar en navegador que una version activa reemplazada muestre solo el archivo nuevo y que la tabla siga mostrando v1, v2 y v3.
* Proximos pasos: Probar visualmente en `/tareas/<id_tarea>/scripts`; no avanzar a Fase 8 sin aprobacion.

### 2026-06-15 00:00 - Fase 7.2 / Mostrar script activo de forma clara

* Archivos creados: Ninguno.
* Archivos modificados: `app/servicios/servicio_scripts.py`, `app/templates/scripts/listado.html`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `log_codex.md`.
* Problema detectado: El bloque superior mostraba `scripts.nombre_script`, aunque el archivo activo real podia haber cambiado al reemplazar la version activa.
* Decision visual: Mostrar como protagonista el archivo activo obtenido desde `scripts_versiones`; dejar el nombre logico como dato secundario.
* Datos mostrados: Archivo activo, version activa, estado `.env`, estado del script y nombre logico.
* Pruebas realizadas: `python -m compileall app`; render de `scripts/listado.html` en casos sin script, version activa reemplazada y version no activa reemplazada; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`.
* Riesgos detectados: Validar visualmente con reemplazo real de version activa y de version no activa.
* Proximos pasos: Probar en navegador con datos reales y mantener Fase 8 pendiente hasta aprobacion.

### 2026-06-15 00:00 - Fase 7.1 / Mensajes contextuales correctos en gestion de scripts

* Archivos creados: Ninguno.
* Archivos modificados: `app/servicios/servicio_scripts.py`, `app/templates/scripts/listado.html`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `log_codex.md`.
* Que se corrigio: La primera carga de script ya no se presenta como `Subir nueva version`; ahora indica que se asociara el primer script y se creara v1 activa.
* Mensajes contextuales: Primer script, subida de v2/v3, maximo de 3 versiones, reemplazo de version, cambio de version activa, asociacion/reemplazo/eliminacion de `.env`.
* Pruebas realizadas: `python -m compileall app`; render de `scripts/listado.html` en escenarios sin script, con v1 y con v1-v3; listado de rutas Flask de scripts; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`.
* Riesgos detectados: Validar visualmente con datos reales en una tarea sin script, una con v1, una con v1-v2 y una con v1-v3.
* Proximos pasos: Probar en navegador y mantener Fase 8 pendiente hasta aprobacion.

### 2026-06-15 00:00 - Fase 7 / Gestion de scripts, versiones y env por tarea

* Archivos creados: `app/rutas_scripts.py`, `app/repositorios/repositorio_scripts.py`, `app/servicios/servicio_scripts.py`, `app/servicios/servicio_archivos.py`, `app/templates/scripts/listado.html`, `database/seeds/005_permisos_scripts.sql`.
* Archivos modificados: `app/__init__.py`, `app/config.py`, `.env.example`, `.gitignore`, `app/seguridad.py`, `app/templates/base.html`, `app/templates/tareas/listado.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `README.md`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/BASE_DATOS.md`, `docs/SEGURIDAD.md`, `docs/ARQUITECTURA.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Que se hizo: Se implemento gestion de scripts por tarea, carga segura de `.py`, versionamiento v1-v3, version activa, reemplazo/desactivacion/eliminacion controlada de versiones y gestion de `.env` por version.
* Migraciones: No se creo migracion nueva; las tablas existentes y la migracion 007 ya contienen los campos necesarios.
* Seed creado: `database/seeds/005_permisos_scripts.sql` con permisos `SCRIPTS_*`; debe ejecutarse manualmente en SSMS para usuarios DB.
* Seguridad: No se ejecutan scripts, no se importa codigo cargado, no se muestra contenido de `.env`, no se guardan secretos en base y se validan extension, tamano y rutas seguras.
* Decisiones tomadas: Bloquear v4 directa; reemplazo de version solo si no tiene historial; no eliminar version activa; `.env` se guarda separado en `env_scripts/`.
* Pruebas realizadas: `python -m compileall app`; listado de rutas Flask para `/scripts` y `/tareas`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`; render de `scripts/listado.html` con datos simulados.
* Riesgos detectados: Debe ejecutarse seed 005 para roles DB; pruebas funcionales completas requieren base local con migraciones 007/008 aplicadas.
* Proximos pasos: Ejecutar seed 005 en SSMS, probar carga de v1-v3 y mantener Fase 8 pendiente hasta aprobacion.

### 2026-06-15 00:00 - Fase 6.2 / Ajuste visual de aviso sin cambios

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/base.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se cambio: El mensaje `No hay cambios para guardar.` ya no se muestra como bloque inline dentro del formulario.
* Componente implementado: Toast corporativo flotante con icono, cierre manual, autocierre y animacion suave.
* Comportamiento: Al editar una tarea sin cambios, no se envia formulario, no se abre modal y aparece el toast flotante.
* Pruebas realizadas: `python -m compileall app`; GET `/tareas/` y `/tareas/nueva` con sesion admin simulada; busqueda sin `alert(`, `window.confirm`, `confirm(`, `prompt(`, `mensaje-formulario` ni `data-mensaje-formulario`; verificacion de referencias `toast`.
* Riesgos detectados: Validar visualmente en navegador desktop/mobile con una tarea real.
* Proximos pasos: Probar edicion sin cambios en navegador y mantener Fase 7 pendiente hasta aprobacion.

### 2026-06-15 00:00 - Fase 6.2 / Detectar cambios reales antes de guardar tareas

* Archivos creados: Ninguno.
* Archivos modificados: `app/static/js/app.js`, `app/static/css/estilos.css`, `app/servicios/servicio_tareas.py`, `app/rutas_tareas.py`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `log_codex.md`.
* Que se corrigio: Editar una tarea sin modificar datos ya no muestra modal ni envia formulario desde frontend.
* Como se detectan cambios: Se compara una fotografia normalizada del formulario original contra el estado actual; textos se normalizan, checkboxes se comparan como booleanos, selects por `value` y dias de semana como conjunto ordenado.
* Respaldo backend: Si llega un POST sin cambios, el servicio compara contra la tarea actual, no ejecuta `UPDATE`, no recrea programacion, no registra logs y retorna `No hay cambios para guardar.`.
* Pruebas realizadas: `python -m compileall app`; GET `/tareas/` y `/tareas/nueva` con sesion admin simulada; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`; prueba directa de comparacion backend con dias desordenados y cambio de nombre.
* Riesgos detectados: La comparacion visual debe validarse en navegador con datos reales, especialmente fechas/horas devueltas por SQL Server.
* Proximos pasos: Validar edicion sin cambios y con cambios reales en nombre, contexto, programacion y feriados; no avanzar a Fase 7 sin aprobacion.

### 2026-06-15 00:00 - Fase 6.1 / Resumen de confirmacion de tareas

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/base.html`, `app/templates/tareas/formulario.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se hizo: Se amplio el modal corporativo para mostrar un resumen antes de crear o editar tareas.
* Que muestra: Nombre, descripcion, cliente, categoria, tipo, estado, observacion tecnica, tipo de programacion, modo, resumen legible y ejecucion en feriados.
* Decisiones tomadas: Generar el resumen desde datos actuales del formulario; leer nombres visibles de selects; usar nodos DOM y `textContent`; validar programacion antes de abrir el modal.
* Pruebas realizadas: `python -m compileall app`; GET `/tareas/` y `/tareas/nueva` con sesion admin simulada; busqueda sin `window.confirm` ni `confirm(`.
* Riesgos detectados: Las pruebas de confirmacion visual completas deben validarse en navegador con datos reales y migracion 008 ejecutada.
* Proximos pasos: Validar en navegador las variantes manual, diaria, semanal, mensual y fecha especifica; no avanzar a Fase 7 sin aprobacion.

### 2026-06-15 00:00 - Fase 6 / Tareas con programacion base

* Archivos creados: `app/repositorios/repositorio_tareas.py`, `app/servicios/servicio_tareas.py`, `app/rutas_tareas.py`, `app/templates/tareas/listado.html`, `app/templates/tareas/formulario.html`, `database/migrations/008_ajustar_tareas_y_programaciones_base.sql`, `database/seeds/004_permisos_tareas.sql`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/templates/base.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `README.md`, `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/ARQUITECTURA.md`, `log_codex.md`.
* Que se hizo: Se implemento modulo `/tareas` con listado, filtros, creacion, edicion, activacion/desactivacion, eliminacion controlada y programacion declarativa.
* Por que se hizo: Permitir administrar tareas base antes de implementar carga de scripts, ejecucion y scheduler.
* Decisiones tomadas: Programacion activa por tarea; al editar se inactiva la anterior y se crea una nueva; eliminacion fisica solo sin dependencias en scripts, ejecuciones ni logs.
* Pruebas recomendadas: Ejecutar migracion 008 y seed 004 en SSMS; validar login; abrir `/tareas/`; crear una tarea manual y una programada; probar filtros, editar, desactivar y eliminar una tarea sin dependencias.
* Riesgos detectados: El modulo requiere ejecutar migracion 008 para usar los nuevos campos; la validacion real de feriados queda pendiente; no existe scheduler ni ejecucion real.
* Proximos pasos: Ejecutar y validar `008_ajustar_tareas_y_programaciones_base.sql` y `004_permisos_tareas.sql`; no avanzar a Fase 7 sin aprobacion.

### 2026-06-13 14:20 - Fase 5.1 / Eliminacion controlada en mantenedores

* Archivos creados: Ninguno.
* Archivos modificados: `app/repositorios/repositorio_mantenedores.py`, `app/servicios/servicio_mantenedores.py`, `app/rutas_mantenedores.py`, `app/templates/mantenedores/listado.html`, `README.md`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se agrego eliminacion fisica controlada para clientes, categorias y tipos cuando no tienen dependencias en `tareas`.
* Por que se hizo: Permitir corregir registros creados por error sin romper trazabilidad historica cuando ya fueron usados.
* Decisiones tomadas: No crear permisos nuevos ni modificar SQL; usar permisos existentes `CLIENTES_ESTADO`, `CATEGORIAS_ESTADO`, `TIPOS_ESTADO`; validar dependencias directas contra `tareas`, que cubren dependencias indirectas hacia scripts, programaciones y ejecuciones.
* Reglas aplicadas: Si no hay dependencias, modal `danger` y eliminacion definitiva; si hay dependencias, bloqueo, mensaje amigable, sugerencia de desactivar y log de intento bloqueado.
* Pruebas realizadas: `python -m compileall app`; rutas de eliminar registradas; login `.env`; GET `/clientes/`, `/categorias/`, `/tipos/` responden 200.
* Riesgos detectados: La validacion funcional completa debe probarse con un registro sin dependencias y otro usado por una tarea real cuando Fase 6 exista.
* Proximos pasos: Validar en navegador con datos reales; no avanzar a Fase 6 hasta aprobacion.

### 2026-06-12 20:05 - Fase 5 / Mantenedores de clientes, categorias y tipos

* Archivos creados: `app/repositorios/repositorio_mantenedores.py`, `app/servicios/servicio_mantenedores.py`, `app/rutas_mantenedores.py`, `app/templates/mantenedores/listado.html`, `app/templates/mantenedores/formulario.html`, `database/seeds/003_permisos_mantenedores.sql`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/templates/base.html`, `README.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implementaron mantenedores funcionales para clientes, categorias y tipos con listado, filtros, creacion, edicion, activacion/desactivacion logica, modales de confirmacion y logs de sistema.
* Por que se hizo: Clientes, categorias y tipos son datos base requeridos antes de crear tareas y construir rutas fisicas de scripts.
* Permisos: Se creo seed incremental `003_permisos_mantenedores.sql` con permisos `CLIENTES_*`, `CATEGORIAS_*` y `TIPOS_*`. Admin `.env` accede sin ejecutar seed; usuarios DB requieren ejecutar el seed para recibir permisos.
* Decisiones tomadas: No eliminar fisicamente; normalizar nombres para evitar duplicados; usar un modulo generico para reducir duplicacion; no modificar tablas existentes.
* Pruebas realizadas: `python -m compileall app`; listado de rutas Flask; login `.env`; GET `/clientes/`, `/clientes/nuevo`, `/categorias/`, `/categorias/nuevo`, `/tipos/`, `/tipos/nuevo` y filtros responden 200.
* Riesgos detectados: El seed 003 debe ejecutarse manualmente en SQL Server para usuarios DB con roles ADMIN/TI; falta prueba manual de creacion/edicion contra datos reales.
* Proximos pasos: Ejecutar seed 003 en SQL Server local, validar CRUD logico en navegador y no avanzar a Fase 6 hasta aprobacion.

### 2026-06-12 19:35 - Fase 4.3 / Migracion 007 ejecutada y validada localmente

* Archivos creados: Ninguno.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `log_codex.md`.
* Que se hizo: Se registro que la migracion `007_agregar_control_ejecucion_y_env_scripts.sql` fue ejecutada correctamente en SQL Server local.
* Validaciones reportadas: Existe `DETENIDA_MANUALMENTE` en `cat_estados_ejecucion`; `scripts_versiones` tiene `requiere_env`, `ruta_env_fisica`, `ruta_env_relativa`; `ejecuciones` tiene `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion`, `fue_detencion_forzada`.
* Decisiones tomadas: Mantener documentado que la base local ya contiene los campos necesarios para `.env` por script y detencion manual, sin implementar todavia tareas, scripts ni scheduler.
* Pruebas realizadas: Validacion manual reportada por el usuario en SQL Server local.
* Riesgos detectados: La migracion fue validada localmente; QA/produccion requeriran ejecucion controlada con respaldo.
* Proximos pasos: No avanzar a Fase 5 hasta aprobacion explicita; mantener pendiente la implementacion funcional de tareas/scripts/scheduler.

### 2026-06-12 19:25 - Fase 4.3 / Definiciones de ejecucion segura y env por script

* Archivos creados: `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`.
* Archivos modificados: `.gitignore`, `.env.example`, `app/config.py`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/SEGURIDAD.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/CHANGELOG.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Que se hizo: Se definio manejo futuro de detencion manual de procesos, `.env` por script/version, estructura fisica `scripts/`, `env_scripts/`, `logs_tareas/`, y seguridad asociada. Se creo migracion propuesta 007 para campos faltantes.
* Por que se hizo: Antes de implementar tareas, scripts o scheduler era necesario resolver trazabilidad de procesos en ejecucion y manejo seguro de credenciales por script.
* Decisiones tomadas: No guardar secretos en base; guardar solo rutas de `.env`; validar rutas contra path traversal; detener ejecuciones solo con usuario autorizado y modal; no modificar scripts SQL ya ejecutados, sino crear migracion nueva versionada.
* Migracion propuesta: `007_agregar_control_ejecucion_y_env_scripts.sql` agrega `DETENIDA_MANUALMENTE`, campos `requiere_env`/rutas env en `scripts_versiones` y campos de detencion en `ejecuciones`.
* Pruebas realizadas: Revision de scripts SQL existentes; confirmacion de que `pid_proceso` ya existia; verificacion de `.gitignore`; `python -m compileall app`.
* Riesgos detectados: La detencion real dependera del sistema operativo, permisos del proceso hijo y manejo de procesos descendientes; se debe disenar cuidadosamente para no dejar procesos colgados.
* Proximos pasos: Revisar/aprobar migracion 007 y reglas de seguridad antes de iniciar Fase 5; no implementar scheduler ni tareas todavia.

### 2026-06-12 18:45 - Fase 4.2 / Modal corporativo de confirmacion

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/base.html`, `app/templates/usuarios/listado.html`, `app/templates/usuarios/formulario.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `app/rutas_usuarios.py`, `app/servicios/servicio_usuarios.py`, `docs/UI_UX.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se reemplazo `window.confirm()` por un modal global reutilizable con titulo, mensaje, botones, tipo visual y envio del formulario solo al confirmar. Se amplio el modal para interceptar formularios de crear/editar usuario.
* Por que se hizo: Las confirmaciones nativas del navegador no cumplen el estandar visual corporativo definido para la aplicacion.
* Decisiones tomadas: Mantener POST actual del backend; configurar textos por atributos `data-*`; soportar variantes `danger`, `warning`, `info` y `success`; permitir cancelar por boton, overlay o ESC; regla general de usuarios: todo cambio debe pedir confirmacion.
* Confirmaciones agregadas: crear usuario, guardar edicion, cambio de rol, cambio de contrasena y cambios criticos combinados de rol/contrasena.
* Pruebas realizadas: `python -m compileall app`; busqueda sin coincidencias de `window.confirm` ni `confirm(`; login `.env` redirige a `/panel`; GET `/usuarios/` y `/usuarios/nuevo` responden 200; `/usuarios/nuevo` renderiza formulario confirmable.
* Riesgos detectados: Falta validacion visual manual final en navegador con datos reales; el modal queda preparado para futuros modulos pero no se conecto a tareas, scripts ni scheduler.
* Proximos pasos: Validar en navegador crear/editar usuario con cancelar y confirmar; no avanzar a Fase 5 hasta aprobacion.

### 2026-06-12 18:25 - Seguridad / No sobrescribir archivo .env

* Archivos creados: Ninguno.
* Archivos modificados: `README.md`, `docs/DESPLIEGUE.md`, `docs/SEGURIDAD.md`, `docs/README_PROYECTO.md`, `docs/CHANGELOG.md`, `log_codex.md`, `app/config.py`, `app/__init__.py`, `app/rutas.py`, `app/templates/login.html`.
* Que se hizo: Se reemplazaron comandos inseguros `copy .env.example .env` / `Copy-Item .env.example .env` por comandos seguros que no sobrescriben `.env` existente; se documento la regla; se agrego validacion controlada de variables criticas.
* Por que se hizo: El archivo `.env` real fue sobrescrito por la plantilla y se perdieron credenciales locales. La documentacion no debe inducir a repetir ese problema.
* Decisiones tomadas: `.env.example` se mantiene solo como plantilla; `.env` debe reconstruirse manualmente por ambiente; Codex no debe recuperar, inventar ni registrar credenciales reales.
* Pruebas realizadas: Verificacion de `.gitignore`; busqueda de comandos inseguros; `python -m compileall app`; carga de aplicacion con validacion de configuracion.
* Riesgos detectados: El usuario debe restaurar manualmente `APP_SECRET_KEY`, credenciales SQL Server, usuario/password admin y rutas locales si aplica.
* Proximos pasos: Reconstruir `.env` manualmente con valores reales y validar `/diagnostico/bd`; no avanzar a Fase 5.

### 2026-06-12 18:05 - Fase 4.1 / Mejoras UX, filtros y correcciones visuales del modulo usuarios

* Archivos creados: Ninguno.
* Archivos modificados: `app/repositorios/repositorio_usuarios.py`, `app/servicios/servicio_usuarios.py`, `app/rutas.py`, `app/rutas_usuarios.py`, `app/seguridad.py`, `app/templates/usuarios/listado.html`, `app/templates/usuarios/formulario.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `README.md`, `docs/SEGURIDAD.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se agregaron filtros por estado, rol y busqueda general en `/usuarios`; contador de resultados; boton limpiar; confirmaciones antes de activar/deshabilitar; advertencias al cambiar rol o contrasena; visualizacion de rol con nombre amigable sin redundancia.
* Por que se hizo: Para mejorar claridad, seguridad operativa y experiencia de administracion de usuarios antes de cerrar Fase 4.
* Decisiones tomadas: Mantener filtros en backend con query parameters; mantener `USUARIOS_ADMIN`; no agregar permisos nuevos; no modificar SQL; registrar logs solo cuando la accion confirmada llega al backend.
* Pruebas realizadas: `python -m compileall app`; login `.env` redirige a `/panel`; GET `/usuarios/`, `/usuarios/?estado=activo`, `/usuarios/?estado=inactivo`, `/usuarios/?rol=TI`, `/usuarios/?rol=ADMIN`, `/usuarios/?buscar=test` y `/usuarios/nuevo` responden 200.
* Riesgos detectados: La validacion completa de filtros con datos reales y login de usuario DB debe probarse contra SQL Server local del usuario; las confirmaciones usan `window.confirm`, suficiente para esta fase pero reemplazable por modal corporativo futuro.
* Proximos pasos: Cerrar validacion manual de Fase 4.1 en navegador y luego definir la siguiente fase sin avanzar aun a tareas, scripts o scheduler.

### 2026-06-12 17:40 - Fase 4 / Usuarios, roles y permisos iniciales

* Archivos creados: `app/seguridad.py`, `app/rutas_usuarios.py`, `app/repositorios/__init__.py`, `app/repositorios/repositorio_usuarios.py`, `app/repositorios/repositorio_roles.py`, `app/repositorios/repositorio_permisos.py`, `app/repositorios/repositorio_logs_sistema.py`, `app/servicios/__init__.py`, `app/servicios/servicio_usuarios.py`, `app/servicios/servicio_roles.py`, `app/servicios/servicio_permisos.py`, `app/servicios/servicio_logs_sistema.py`, `app/templates/usuarios/listado.html`, `app/templates/usuarios/formulario.html`.
* Archivos modificados: `app/__init__.py`, `app/rutas.py`, `app/templates/base.html`, `app/static/css/estilos.css`, `README.md`, `docs/SEGURIDAD.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/ARQUITECTURA.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento login hibrido, validando primero administrador desde `.env` y luego usuarios activos en SQL Server; se agrego administracion inicial de usuarios en `/usuarios`; se separaron repositorios, servicios y decoradores de seguridad; se agregaron logs de sistema para login y cambios de usuarios.
* Por que se hizo: Para iniciar Fase 4 usando las tablas de seguridad ya creadas, sin avanzar a tareas, scripts, scheduler ni paneles funcionales posteriores.
* Decisiones tomadas: Mantener `blizama` solo desde `.env`; usar `USUARIOS_ADMIN` como permiso inicial de administracion; no permitir eliminacion fisica de usuarios; guardar contrasenas con hash de Werkzeug; dejar el administrador `.env` con permisos totales de sesion.
* Pruebas realizadas: `python -m compileall app`; GET `/login` 200; POST `/login` con credenciales `.env` redirige a `/panel`; GET `/panel` 200; GET `/usuarios/` 200 con sesion `.env`.
* Riesgos detectados: La creacion/login de usuario de base de datos debe validarse manualmente contra SQL Server local con `.env` correctamente configurado; si la conexion falla, `/usuarios` muestra error amigable y no rompe el login `.env`.
* Proximos pasos: Probar creacion de usuario DB, login con usuario DB, permisos por rol y bloqueo por usuario inactivo; no avanzar a CRUD de tareas ni scheduler hasta nueva aprobacion.

### 2026-06-12 17:05 - Documentacion / Actualizacion README principal

* Archivos creados: Ninguno.
* Archivos modificados: `README.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se actualizo el README principal para reflejar el estado real del proyecto hasta Fase 3D.
* Por que se hizo: El README seguia indicando Fase 2 y no reflejaba scripts SQL, base validada ni conexion Flask-SQL Server inicial.
* Decisiones tomadas: Mantener README como resumen ejecutivo y dejar detalle tecnico en `docs/` y `log_codex.md`.
* Pruebas realizadas: Revision documental; no se modifico logica funcional.
* Riesgos detectados: README debe seguir actualizandose al cerrar nuevas fases para evitar divergencia.
* Proximos pasos: No avanzar a Fase 4; continuar solo cuando se solicite la siguiente fase.

### 2026-06-12 16:58 - Fase 3D / Conexion Flask SQL Server y diagnostico

* Archivos creados: `app/database/__init__.py`, `app/database/conexion.py`, `app/templates/diagnostico_bd.html`.
* Archivos modificados: `requirements.txt`, `.env.example`, `app/rutas.py`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se agrego conexion inicial con SQL Server usando `pyodbc`, variables de entorno y ruta `/diagnostico/bd` protegida por sesion y disponible solo en `LOCAL`/`QA`.
* Por que se hizo: Para validar conectividad Flask-SQL Server antes de implementar repositorios, CRUD, usuarios en base de datos o scheduler.
* Decisiones tomadas: Login inicial sigue desde `.env`; no se crea usuario `blizama` en base de datos; no se muestran credenciales ni datos sensibles en diagnostico.
* Pruebas realizadas: `python -m py_compile`; GET `/login` 200; POST `/login` redirige a `/panel`; GET `/panel` 200; GET `/diagnostico/bd` 200 en LOCAL. La prueba real de conexion retorno `OperationalError` amigable sin exponer credenciales en esta sesion.
* Riesgos detectados: El resultado de conexion depende del driver ODBC, red, instancia SQL Server, cifrado y permisos locales.
* Proximos pasos: Corregir configuracion local si `/diagnostico/bd` muestra error; luego crear repositorios base solo cuando se solicite explicitamente.

### 2026-06-12 16:46 - Fase 3B / Decision sin eliminacion fisica de scripts

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se documento oficialmente que en la primera version no existe eliminacion fisica de scripts ni versiones desde la app.
* Por que se hizo: Para asegurar trazabilidad completa y evitar perdida de evidencia de versiones cargadas o reemplazadas.
* Decisiones tomadas: Las versiones se gestionan por estado: `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`; inactivacion y reemplazo deben auditarse.
* Pruebas realizadas: Se verifico que `cat_estados_version_script` y `CK_scripts_versiones_estado` ya incluyen `INACTIVA`; no se modifico SQL.
* Riesgos detectados: Cualquier limpieza fisica futura debe disenarse como funcionalidad separada, restringida y auditable.
* Proximos pasos: Mantener esta regla al implementar modulo de scripts en fases posteriores.

### 2026-06-12 16:38 - Fase 3B / Ejecucion manual validada en SQL Server local

* Archivos creados: Ninguno.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Que se hizo: Se registro que los scripts SQL de Fase 3B fueron ejecutados correctamente de forma manual en SQL Server local.
* Por que se hizo: Para dejar trazabilidad de que la base `APP_SCHEDULER_QA` ya existe localmente y que el modelo fue validado por el motor SQL Server.
* Decisiones tomadas: Mantener pendiente la conexion Flask-SQL Server; no avanzar a CRUD ni Fase 4.
* Pruebas realizadas: Usuario reporto ejecucion exitosa de `001` a `006` y seeds `001` a `002`; valido existencia de tablas, datos de catalogos, roles/permisos y ausencia del usuario `blizama` en base de datos.
* Riesgos detectados: La validacion fue local; QA/produccion requeriran ejecucion controlada, respaldo y revision de variables de entorno.
* Proximos pasos: Preparar conexion Flask-SQL Server y capa de repositorios solo cuando se solicite explicitamente.

### 2026-06-12 16:28 - Fase 3B / Revision tecnica previa de scripts SQL

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se revisaron estaticamente los scripts SQL versionados, dependencias por orden, FKs, CHECKs, indices, seeds idempotentes, ausencia de secretos y trazabilidad de scripts/versiones.
* Por que se hizo: Para detectar errores evidentes antes de ejecutar manualmente en SQL Server Management Studio.
* Decisiones tomadas: No ejecutar SQL ni conectar Flask; corregir solo documentacion menor para alinear `logs_tareas.nombre_archivo_log` y `logs_sistema.nivel varchar(30)` con los scripts.
* Pruebas realizadas: Lectura completa de scripts, chequeo automatico de orden de FKs, busqueda de secretos reales, verificacion de `id_script`/`id_version` en `ejecuciones`, `CHECK(numero_version BETWEEN 1 AND 3)`, `UNIQUE(id_script, numero_version)` e indice unico filtrado de version activa.
* Riesgos detectados: Aun falta validacion real por motor SQL Server; la ejecucion debe hacerse primero en ambiente local/QA y no en produccion.
* Proximos pasos: Ejecutar manualmente en SSMS en el orden documentado, revisar mensajes de SQL Server y reportar cualquier error antes de avanzar a conexion Flask-SQL Server.

### 2026-06-12 16:12 - Fase 3B / Creacion de scripts SQL Server versionados

* Archivos creados: `database/migrations/001_crear_base_datos.sql`, `database/migrations/002_crear_catalogos.sql`, `database/migrations/003_crear_tablas_seguridad.sql`, `database/migrations/004_crear_tablas_negocio.sql`, `database/migrations/005_crear_tablas_ejecucion_logs.sql`, `database/migrations/006_crear_indices.sql`, `database/seeds/001_datos_iniciales_catalogos.sql`, `database/seeds/002_roles_permisos_iniciales.sql`.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se crearon scripts SQL Server versionados para base, catalogos, seguridad, negocio, ejecucion/logs/auditoria, indices y seeds iniciales.
* Por que se hizo: Para preparar la implementacion fisica ordenada del modelo aprobado sin ejecutar SQL ni conectar Flask todavia.
* Decisiones tomadas: Mantener scripts idempotentes cuando sea razonable; agregar FK `scripts.id_version_activa` en `006_crear_indices.sql` por dependencia circular; reforzar estados/tipos con FKs hacia catalogos; no crear usuario `blizama` en seeds.
* Pruebas realizadas: Revision de archivos y estructura; no se ejecutaron scripts SQL por regla de fase.
* Riesgos detectados: Los scripts deben probarse primero en ambiente local/QA; SQL Server validara compatibilidad final de constraints e indices.
* Proximos pasos: Ejecutar manualmente en SSMS solo con aprobacion; luego iniciar fase de conexion Flask-SQL Server si se solicita.

### 2026-06-12 16:03 - Fase 3A / Aprobacion de decisiones de versionamiento

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se registraron las aprobaciones del modelo de versionamiento controlado de scripts.
* Por que se hizo: Para dejar cerradas las decisiones necesarias antes de avanzar a Fase 3B.
* Decisiones tomadas: Se aprueba `scripts` + `scripts_versiones`, `id_version_activa`, maximo 3 controlado por servicio en primera version, refuerzo con `CHECK`, `UNIQUE` e indice filtrado, trigger/procedimiento como mejora futura y estructura fisica `v1`, `v2`, `v3`.
* Pruebas realizadas: Revision documental; no aplica prueba de ejecucion porque no se implemento conexion ni SQL.
* Riesgos detectados: Aun falta definir si al reemplazar una version fisica se preservara copia historica adicional o solo auditoria/hash/ruta previa.
* Proximos pasos: Iniciar Fase 3B solo cuando se solicite, creando scripts SQL versionados y capa de conexion/repositorios sin quemar credenciales.

### 2026-06-12 15:54 - Fase 3A / Ajuste versionamiento controlado de scripts

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se ajusto el modelo propuesto para separar `scripts` como script logico y `scripts_versiones` como versiones fisicas maximo v1-v3; se documento version activa, ejecuciones con `id_script` e `id_version`, rutas versionadas, auditoria y flujos operativos.
* Por que se hizo: Para soportar que cada tarea mantenga hasta 3 versiones de script disponibles y que cada ejecucion sea trazable a una version exacta.
* Decisiones tomadas: Priorizar validacion de maximo 3 versiones en capa de servicio para primera version; proponer constraints simples, indice unico filtrado para una sola version activa y posible trigger/procedimiento como refuerzo futuro.
* Pruebas realizadas: Revision documental; no aplica prueba de ejecucion porque no se implemento conexion, scripts SQL ni cambios funcionales.
* Riesgos detectados: Se debe aprobar si versiones reemplazadas cuentan o no como disponibles y si se requiere blindaje en SQL Server con trigger/procedimiento.
* Proximos pasos: Esperar aprobacion o ajustes; no avanzar a Fase 3B hasta cerrar esta propuesta.

### 2026-06-12 15:35 - Fase 3 parte 1 / Propuesta modelo SQL Server

* Archivos creados: Ninguno.
* Archivos modificados: `docs/BASE_DATOS.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se documento el modelo relacional inicial para SQL Server, incluyendo tablas criticas, tablas futuras, campos, tipos sugeridos, claves primarias, foraneas, indices, estados, rutas de scripts/logs, auditoria y scripts SQL sugeridos como propuesta no ejecutada.
* Por que se hizo: La Fase 3 exige aprobar el modelo antes de implementar conexion, crear tablas o generar scripts finales.
* Decisiones tomadas: Mantener secretos en `.env`; proponer rutas relativas y fisicas para scripts/logs; usar campos estandar de auditoria; mantener tablas futuras fuera de implementacion inicial.
* Pruebas realizadas: Revision documental; no aplica prueba de ejecucion porque no se implemento conexion ni scripts SQL.
* Riesgos detectados: Deben aprobarse convenciones, estados, uso de JSON en programaciones y estrategia de migraciones antes de implementar.
* Proximos pasos: Esperar aprobacion o ajustes del usuario; luego crear scripts SQL versionados y capa de conexion/repositorios sin quemar credenciales.

### 2026-06-12 15:23 - Fase 2 / Diseno UI UX base

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/base.html`, `app/templates/login.html`, `app/templates/panel.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `README.md`, `docs/UI_UX.md`, `docs/CHANGELOG.md`, `docs/ARQUITECTURA.md`, `log_codex.md`.
* Que se hizo: Se mejoro el layout base con sidebar responsive, topbar con usuario, login refinado, panel principal con cards y placeholders, badges de estado, tabla base, alertas, botones reutilizables y panel lateral visual para logs.
* Por que se hizo: Para cerrar la Fase 2 con una interfaz mas profesional, corporativa y preparada para modulos funcionales posteriores sin adelantar base de datos ni scheduler.
* Decisiones tomadas: Mantener HTML/CSS/JS puro sin dependencias externas; dejar datos simulados claramente marcados; preparar componentes visuales reutilizables antes de implementar CRUD o scheduler.
* Pruebas realizadas: `python -m py_compile run.py app\__init__.py app\config.py app\rutas.py`; GET `/login` respondio 200; POST `/login` con credenciales de `.env` redirigio a `/panel`; verificacion en navegador local confirmo topbar, sidebar, 4 metricas, badges, panel lateral de logs, toggle de logs y sidebar responsive a 390px.
* Riesgos detectados: El panel de logs es solo visual; los usuarios pueden interpretarlo como funcional si no se mantiene el texto de pendiente.
* Proximos pasos: Despues de aprobacion, iniciar Fase 3 con propuesta formal de modelo SQL Server antes de crear scripts o conexion.

### 2026-06-12 14:24 - Fase 1 / Base inicial del proyecto

* Archivos creados: `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `run.py`, `app/__init__.py`, `app/config.py`, `app/rutas.py`, `app/templates/base.html`, `app/templates/login.html`, `app/templates/panel.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, documentos en `docs/`.
* Archivos modificados: Ninguno previo; repositorio estaba vacio salvo `.git`.
* Que se hizo: Se creo la base Flask, login inicial desde `.env`, panel principal base, layout visual inicial, documentacion obligatoria y bitacora.
* Por que se hizo: Para cerrar la Fase 1 con una base funcional, documentada y preparada para crecimiento incremental.
* Decisiones tomadas: No implementar base de datos, Docker ni scheduler en Fase 1; se dejan documentados como pendientes segun fases definidas.
* Pruebas realizadas: `python -m py_compile run.py app\__init__.py app\config.py app\rutas.py`; carga de aplicacion con `from app import crear_app`.
* Riesgos detectados: `APP_SECRET_KEY` y `PASSWORD_ADMIN_DEFECTO` deben cambiarse en `.env` real antes de uso compartido.
* Proximos pasos: Probar login en navegador con `.env` real e iniciar Fase 2 solo despues de aprobacion.
