# Changelog

## 2026-06-17 - Correccion preview Fase 10B

### Corregido

* Se corrigio error en `feriados/sincronizar.html` causado por `preview.items`.
* La estructura `preview` ahora usa la clave `feriados_preview` para evitar conflicto con `dict.items` de Python/Jinja.
* La aplicacion de sincronizacion tambien usa `preview["feriados_preview"]`.

### Validado

* `python -m compileall app scheduler_worker.py`.
* Render de vista previa de sincronizacion con feriados simulados.
* Aplicacion simulada de sincronizacion con insercion `API_NAGER`.
* Validacion real en la app: `/feriados/sincronizar` carga correctamente.
* Consulta real desde la app para `2026 / CL` sin `TypeError`.
* Vista previa renderizada correctamente usando `preview.feriados_preview`.
* Feriados retornados por Nager.Date visibles en pantalla.
* Aplicar sincronizacion validado correctamente desde la app.
* No se duplican fecha + pais.
* Sin referencias a Nager.Date o `requests` desde `scheduler_worker.py`.
* Sin `alert()`, `window.confirm()` ni `prompt()`.

## 2026-06-17 - Fase 10B sincronizacion Nager.Date

### Agregado

* Migracion `database/migrations/013_crear_reglas_feriados_irrenunciables.sql`.
* Seed `database/seeds/009_reglas_irrenunciables_chile.sql`.
* Seed `database/seeds/010_permisos_sincronizacion_feriados.sql`.
* Dependencia `requests`.
* Cliente `app/servicios/cliente_nager_date.py`.
* Servicio `app/servicios/servicio_sincronizacion_feriados.py`.
* Repositorio `app/repositorios/repositorio_reglas_feriados.py`.
* Rutas `/feriados/sincronizar`, `/feriados/sincronizar/preview` y `/feriados/sincronizar/confirmar`.
* Template `app/templates/feriados/sincronizar.html`.

### Validado

* `python -m compileall app scheduler_worker.py`.
* Rutas `/feriados/sincronizar`, `/feriados/sincronizar/preview` y `/feriados/sincronizar/confirmar`.
* Render de pantalla de sincronizacion.
* Consulta real a Nager.Date para `2026/CL`, con 17 feriados retornados.
* Calculo de irrenunciable por regla local simulado.
* Clasificacion `NUEVO`, `MANUAL_NO_SOBRESCRIBE`, `ACTUALIZAR` y `SIN_CAMBIOS`.
* Busqueda sin `alert()`, `window.confirm()` ni `prompt()`.
* Verificacion de que `scheduler_worker.py` no importa ni consulta Nager.Date.

### Cambiado

* `/feriados` agrega boton `Sincronizar feriados`.
* `repositorio_feriados.py` soporta buscar por fecha + pais, insertar `API_NAGER` y actualizar feriados `API_NAGER`.
* Documentacion actualizada para Nager.Date, reglas locales, prioridad `MANUAL` y permiso `FERIADOS_SINCRONIZAR`.

### No implementado

* No se implemento sincronizacion automatica programada.
* No se conecto Nager.Date al scheduler.
* No se implementaron notificaciones.
* No se avanzo a Fase 10C.

## 2026-06-16 - Fase 10A calendario local de feriados

### Validado localmente

* Se ejecuto `database/migrations/012_crear_calendario_feriados.sql` en SQL Server local.
* Se ejecuto `database/seeds/008_permisos_feriados.sql` en SQL Server local.
* La tabla `feriados` fue creada correctamente.
* Los permisos `FERIADOS_*` fueron insertados.
* `/feriados` carga correctamente.
* Se valido crear, editar, activar y desactivar feriados manuales.
* Se valido bloqueo de duplicado para fecha + pais activa.
* `servicio_calendario.es_feriado` retorna `True` con feriado activo y `False` sin feriado activo.
* El scheduler omite tareas automaticas en feriado cuando `ejecutar_en_feriados = 0`.
* El scheduler permite ejecutar en feriado cuando `ejecutar_en_feriados = 1`.
* La ejecucion manual no se bloquea por feriados.

### Agregado

* Migracion `database/migrations/012_crear_calendario_feriados.sql`.
* Seed `database/seeds/008_permisos_feriados.sql`.
* Modulo web `/feriados` con listado, filtros, creacion, edicion, activacion/desactivacion y eliminacion controlada.
* Repositorio `app/repositorios/repositorio_feriados.py`.
* Rutas `app/rutas_feriados.py`.
* Templates `app/templates/feriados/listado.html` y `app/templates/feriados/formulario.html`.
* Servicio calendario con `es_feriado`, `obtener_feriado`, `listar_feriados` y `validar_fecha_laboral`.
* Integracion del worker para omitir tareas automaticas en feriado cuando `ejecutar_en_feriados = 0`.

### Cambiado

* Sidebar agrega acceso a Feriados.
* `servicio_scheduler_worker.py` consulta calendario local antes de iniciar ejecuciones automaticas.
* Documentacion actualizada para separar Fase 10A local de Fase 10B externa.

### No implementado

* No se conecto API externa de feriados.
* No se implemento sincronizacion automatica externa.
* No se implementaron notificaciones.
* No se avanzo a Fase 10B.

## 2026-06-16 - Ajuste visual Fase 9D

### Cambiado

* Se elimino de `/ejecuciones` el bloque visual de resumen `Total`, `Exitosas`, `Errores`, `En ejecucion` y `Detenidas`.
* Se mantiene el total discreto en header/paginacion.
* Se mantienen filtros, paginacion, agrupacion ano/mes/dia y accion `Ver consola`.

### No implementado

* No se creo migracion.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9D historial agrupado de ejecuciones

### Agregado

* Vista `/ejecuciones` agrupada por ano, mes y dia.
* Filtros por ID, tarea, origen, estado, ano, mes, dia, fecha desde/hasta, usuario y worker.
* Paginacion server-side con `page` y `per_page`.
* Resumen por filtro: total, exitosas, errores, en ejecucion y detenidas.
* Meses en espanol.

### Cambiado

* `repositorio_ejecuciones.py` agrega consulta paginada, `COUNT` y resumen por estado con los mismos filtros.
* `servicio_ejecuciones.py` valida filtros y agrupa solo la pagina actual.
* `ejecuciones/listado.html` deja de ser tabla plana y pasa a vista historica agrupada.

### No implementado

* No se creo migracion.
* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9C timestamps por linea en logs de ejecucion

### Agregado

* Servicio `app/servicios/servicio_logs_ejecucion.py`.
* Formato estandar por linea: `YYYY-MM-DD HH:mm:ss | NIVEL | mensaje`.
* Timestamps para inicio, origen, tarea, script, version, `.env`, PID, salida de script, codigo de salida, estado final y detencion manual.

### Cambiado

* `servicio_ejecuciones.py` escribe logs de ejecucion usando servicio centralizado.
* Consola y polling muestran las lineas ya formateadas desde el archivo fisico.

### No implementado

* No se creo migracion.
* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9B worker automatico separado

### Agregado

* `scheduler_worker.py` como proceso separado.
* Servicio `servicio_scheduler_worker.py`.
* Servicio `servicio_programador.py` para evaluar programaciones.
* Repositorio `repositorio_scheduler.py`.
* Placeholder `servicio_calendario.py`.
* Migracion `011_agregar_control_scheduler_ejecuciones.sql`.
* Ejecuciones automaticas con `fecha_programada`, `clave_programacion` y `nombre_worker`.
* Listado basico `/ejecuciones`.
* Sidebar con acceso a ejecuciones.

### Cambiado

* `servicio_ejecuciones.py` reutiliza el motor de Fase 8 para ejecuciones automaticas.
* `repositorio_ejecuciones.py` soporta listado y campos opcionales de Fase 9B.
* La consola muestra origen, worker y fecha programada.

### No implementado

* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado del scheduler.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9A validada localmente

### Validado

* Se ejecuto `database/migrations/010_crear_configuracion_scheduler.sql` en SQL Server local.
* Se ejecuto `database/seeds/007_permisos_scheduler.sql` en SQL Server local.
* La tabla `configuracion_scheduler` fue creada correctamente.
* Existe un registro inicial activo con defaults seguros.
* `scheduler_activo` quedo apagado por defecto.
* `permitir_ejecucion_automatica` quedo deshabilitado por defecto.
* `intervalo_revision_segundos` quedo en 60.
* `max_ejecuciones_concurrentes` quedo en 3.
* `modo_mantenimiento` quedo desactivado.
* Los permisos `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR` fueron insertados.
* La ruta `/scheduler/configuracion` carga correctamente.
* La pantalla permite editar configuracion.
* Guardar cambios muestra modal corporativo con resumen.
* Guardar sin cambios muestra toast.
* Las validaciones bloquean valores fuera de rango.
* Los cambios quedan registrados en `logs_sistema`.

### No implementado

* No se implemento worker automatico.
* No se ejecutan tareas automaticas.
* No se conecto API de feriados.
* No se avanzo a Fase 9B.

## 2026-06-15 - Fase 9A configuracion scheduler

### Agregado

* Modulo `/scheduler/configuracion`.
* Migracion `010_crear_configuracion_scheduler.sql`.
* Seed `007_permisos_scheduler.sql`.
* Tabla `configuracion_scheduler` con defaults seguros.
* Pantalla para ver y editar scheduler activo, ejecucion automatica, intervalo, maximo concurrentes, modo mantenimiento, worker y descripcion.
* Modal corporativo con resumen de cambios.
* Toast `No hay cambios para guardar.` cuando no hay diferencias.
* Logs de sistema para cambios.

### No implementado

* No se implemento worker automatico.
* No se ejecutan tareas automaticas.
* No se conecto API de feriados.
* No se avanzo a Fase 9B.

## 2026-06-15 - Fase 8 validada localmente

### Validado

* Se ejecuto `database/seeds/006_permisos_ejecuciones.sql` en SQL Server local.
* Los permisos `EJECUCIONES_*` fueron insertados correctamente.
* La ejecucion manual de tarea con script activo funciona.
* La consola muestra stdout y el polling actualiza el log.
* La ejecucion finaliza como `EXITOSA` cuando el script termina bien.
* La detencion manual deja la ejecucion en `DETENIDA_MANUALMENTE`.
* Se registra `pid_proceso`.
* Se genera archivo de log en `logs_tareas/`.
* Se valido ejecucion sin `.env` y con `.env` de prueba usando `os.getenv()`.
* No se mostraron secretos.

### No implementado

* No se implemento scheduler automatico.
* No se conecto API de feriados.
* No se avanzo a Fase 9.

## 2026-06-15 - Fase 8 ejecucion manual con consola

### Agregado

* Modulo de ejecuciones manuales.
* Boton `Ejecutar ahora` en tareas y scripts.
* Validaciones previas de tarea, script, version activa, archivo `.py`, `.env` requerido y ejecucion simultanea.
* Registro en `ejecuciones` con origen `MANUAL`, estado y `pid_proceso`.
* Archivo de log por ejecucion en `logs_tareas/AAAA/MM/DD/`.
* Vista `/ejecuciones/<id_ejecucion>` con consola visual.
* Polling HTTP cada 3 segundos en `/ejecuciones/<id_ejecucion>/log`.
* Boton `Detener ejecucion` con modal corporativo.
* Seed incremental `database/seeds/006_permisos_ejecuciones.sql`.

### Seguridad

* No se muestra contenido de `.env`.
* No se usa `shell=True`.
* No se implemento scheduler automatico.
* No se conecto API de feriados.
* No se avanzo a Fase 9.

## 2026-06-15 - Migracion 009 validada localmente

### Validado

* Se ejecuto `009_corregir_nombre_script_contenedor.sql` en SQL Server local sin errores.
* La migracion afecto 0 filas porque no existian scripts antiguos con `nombre_script` terminado en `.py`.
* Este resultado es correcto para el ambiente local actual.
* La nueva logica aplica para los proximos scripts cargados.

### No implementado

* No se avanzo a Fase 8.
* No se ejecutan scripts.
* No se implemento scheduler.

## 2026-06-15 - Fase 7.5 contenedor de script y archivo versionado

### Corregido

* Al asociar el primer archivo `.py`, `scripts.nombre_script` deja de tomar el nombre del archivo cargado.
* El contenedor `scripts` ahora usa nombre descriptivo `Script de {nombre_tarea}`.
* Los nombres reales de archivos `.py` quedan exclusivamente en `scripts_versiones.nombre_archivo`.
* La vista de scripts mantiene como protagonista el archivo activo real desde la version activa.
* Se agrega migracion correctiva `009_corregir_nombre_script_contenedor.sql` para registros antiguos cuyo `nombre_script` termine en `.py`.

### No implementado

* La migracion 009 no se ejecuto automaticamente desde Codex; fue ejecutada manualmente y validada localmente.
* No se modifico SQL ya ejecutado.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.4 eliminacion clara de scripts y versiones

### Corregido

* El boton superior ahora dice `Eliminar script completo` para aclarar que afecta el contenedor de script y todas sus versiones.
* El modal de script completo advierte que la accion afecta todas las versiones cargadas.
* En la tabla, los botones ahora dicen `Activar version`, `Desactivar version` y `Eliminar version`.
* El modal de `Eliminar version` aclara que solo afecta la version seleccionada y no las demas.
* La eliminacion de version activa se bloquea y pide activar otra version antes.
* La eliminacion de la unica version se bloquea y sugiere usar `Eliminar script completo`.
* Los bloqueos y eliminaciones quedan diferenciados en `logs_sistema`.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.3 simplificacion de script activo

### Corregido

* El bloque superior de `Scripts de tarea` deja de mostrar el nombre logico del script.
* La vista principal muestra solo el archivo activo real, version activa, estado `.env` y estado del script.
* El nombre logico se mantiene internamente en base de datos y servicios, sin exponerse por defecto al usuario operativo.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.2 script activo visible

### Corregido

* El bloque superior de `Scripts de tarea` ahora muestra el archivo activo real desde `scripts_versiones`.
* El nombre logico del script se mantenia como dato secundario hasta Fase 7.3.
* Se muestra version activa, estado `.env` y estado del script en badges.
* Si no hay script asociado, el bloque indica `Sin script asociado todavia`.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.1 mensajes contextuales de scripts

### Corregido

* Cuando una tarea no tiene script, el formulario ahora indica `Asociar script` y el modal explica que se creara v1 activa.
* Cuando ya existe v1 o v2, el modal indica que se creara v2 o v3 segun corresponda.
* Cuando ya existen tres versiones, la pantalla indica que se debe reemplazar una version existente y no sugiere crear v4.
* Los modales de reemplazo de version, cambio de version activa y gestion de `.env` usan textos contextuales.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7 gestion de scripts versiones y env

### Agregado

* Modulo de scripts por tarea en `/tareas/<id_tarea>/scripts`.
* Carga segura de archivos `.py` dentro de `scripts/`.
* Versionamiento v1, v2 y v3 por script logico.
* Bloqueo de cuarta version directa; se debe reemplazar una existente.
* Cambio de version activa con modal corporativo.
* Reemplazo, desactivacion y eliminacion controlada de versiones.
* Gestion de `.env` por version dentro de `env_scripts/`, sin mostrar contenido.
* Seed incremental `database/seeds/005_permisos_scripts.sql`.

### Seguridad

* Validacion de extension, tamano y rutas internas.
* No se ejecutan scripts cargados.
* No se lee ni muestra contenido de `.env`.
* No se guardan secretos en base de datos; solo rutas.

### No implementado

* No se implemento scheduler.
* No se implemento ejecucion real.
* No se implemento consola en vivo.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 6.2 ajuste visual de aviso sin cambios

### Cambiado

* El aviso `No hay cambios para guardar.` deja de mostrarse incrustado dentro del formulario.
* Se agrega componente `toast` corporativo flotante para avisos ligeros del sistema.
* El toast aparece sin recargar la pagina, con animacion suave, cierre manual y autocierre.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6.2 deteccion de cambios reales en tareas

### Corregido

* Al editar una tarea sin modificar datos ya no se muestra modal de confirmacion.
* El formulario no se envia si no existen cambios reales.
* Se muestra mensaje visual: `No hay cambios para guardar.`
* El backend tambien detecta POST sin cambios y evita `UPDATE`, logs de edicion y cambio de `fecha_actualizacion`.

### Tecnico

* Comparacion normalizada de textos, selects, booleanos, programacion y dias de semana.
* La deteccion aplica solo a edicion; la creacion sigue mostrando resumen siempre.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6.1 resumen de confirmacion de tareas

### Agregado

* Modal de confirmacion enriquecido al crear y editar tareas.
* Resumen previo con datos generales, programacion, feriados y estado.
* Validacion frontend previa para no mostrar resumen con programacion incompleta.
* Soporte reutilizable en el modal global para contenido de resumen generado por JS.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6 tareas con programacion base

### Agregado

* Modulo `/tareas` con listado, filtros, creacion, edicion, activacion, desactivacion y eliminacion controlada.
* Programacion base declarativa: `MANUAL`, `DIARIA`, `SEMANAL`, `MENSUAL` y `FECHA_ESPECIFICA`.
* Modos del dia `UNA_VEZ` e `INTERVALO`.
* Campo `ejecutar_en_feriados` como dato declarativo.
* Migracion propuesta `database/migrations/008_ajustar_tareas_y_programaciones_base.sql`.
* Seed incremental `database/seeds/004_permisos_tareas.sql`.

### Seguridad

* Permisos `TAREAS_VER`, `TAREAS_CREAR`, `TAREAS_EDITAR`, `TAREAS_ESTADO` y `TAREAS_ELIMINAR`.
* Eliminacion fisica de tareas solo si no existen scripts, ejecuciones ni logs asociados.
* Acciones criticas protegidas con modal corporativo reutilizable.

### No implementado

* No se implemento scheduler real.
* No se ejecutan scripts.
* No se implemento carga/versionamiento funcional de scripts.
* No se avanzo a Fase 7.

## 2026-06-13 - Fase 5.1 eliminacion controlada en mantenedores

### Agregado

* Eliminacion fisica controlada para clientes, categorias y tipos.
* Validacion de dependencias contra `tareas` antes de eliminar.
* Modal corporativo fuerte para eliminacion definitiva.
* Bloqueo con mensaje amigable cuando existen dependencias.
* Logs de sistema para eliminacion confirmada e intento bloqueado.

### Seguridad

* No se eliminan registros usados por tareas.
* Si hay dependencias, se sugiere desactivar el registro.
* Se usan permisos existentes `CLIENTES_ESTADO`, `CATEGORIAS_ESTADO` y `TIPOS_ESTADO`.

### Validado

* `python -m compileall app`.
* Rutas `/clientes/<id>/eliminar`, `/categorias/<id>/eliminar` y `/tipos/<id>/eliminar` registradas.
* Login `.env` redirige a `/panel`.
* `/clientes/`, `/categorias/` y `/tipos/` responden 200.

### No implementado

* No se avanzo a Fase 6.
* No se implementaron tareas.
* No se implemento carga de scripts.
* No se implemento scheduler.
* No se modifico SQL.

## 2026-06-12 - Fase 5 mantenedores clientes categorias tipos

### Agregado

* Mantenedor `/clientes`.
* Mantenedor `/categorias`.
* Mantenedor `/tipos`.
* Repositorio y servicio generico para mantenedores base.
* Templates reutilizables de listado y formulario.
* Sidebar con accesos a Clientes, Categorias y Tipos.
* Seed incremental `database/seeds/003_permisos_mantenedores.sql`.

### Funcionalidad

* Listar, filtrar, crear, editar, activar y desactivar.
* Filtro por estado y busqueda por nombre/descripcion.
* Validacion de nombre obligatorio.
* Validacion de duplicados por nombre normalizado.
* Sin eliminacion fisica en Fase 5 inicial; ajustado en Fase 5.1 para permitir eliminacion controlada solo sin dependencias.
* Logs de sistema por creacion, edicion, activacion y desactivacion.
* Confirmaciones con modal corporativo.

### Validado

* `python -m compileall app`.
* Login `.env` redirige a `/panel`.
* `/clientes/`, `/clientes/nuevo`, `/categorias/`, `/categorias/nuevo`, `/tipos/`, `/tipos/nuevo` responden 200.
* Filtros de listados responden 200.

### No implementado

* No se avanzo a Fase 6.
* No se implementaron tareas.
* No se implemento carga de scripts.
* No se implemento scheduler.

## 2026-06-12 - Migracion 007 validada localmente

### Validado Manualmente

* Migracion `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql` ejecutada correctamente en SQL Server local.
* Confirmado estado `DETENIDA_MANUALMENTE` en `cat_estados_ejecucion`.
* Confirmados campos `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa` en `scripts_versiones`.
* Confirmados campos `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion` y `fue_detencion_forzada` en `ejecuciones`.

### No implementado

* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.

## 2026-06-12 - Fase 4.3 definiciones de ejecucion segura

### Agregado

* Definicion tecnica para detener ejecuciones en curso.
* Definicion tecnica para `.env` propio por script/version.
* Estructura fisica recomendada `scripts/`, `env_scripts/` y `logs_tareas/`.
* Migracion propuesta `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`.
* Variable de plantilla `RUTA_BASE_ENV_SCRIPTS`.
* Exclusiones `env_scripts/` y `**/.env` en `.gitignore`.

### Base de datos

* `scripts_versiones`: propuesta de `requiere_env`, `ruta_env_fisica`, `ruta_env_relativa`.
* `ejecuciones`: propuesta de `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion`, `fue_detencion_forzada`.
* Catalogo `DETENIDA_MANUALMENTE` para `cat_estados_ejecucion`.

### Seguridad

* No guardar contenido de `.env` de scripts en BD.
* No mostrar ni registrar secretos.
* Separar `.env` principal de `.env` por script.
* Validar rutas para evitar path traversal.
* Detencion de ejecuciones solo para usuarios autorizados y con confirmacion.

### No implementado

* No se implementaron tareas.
* No se implemento scheduler.
* No se implemento carga funcional de scripts.
* No se ejecuto SQL desde Codex.

## 2026-06-12 - Fase 4.2 modal corporativo de confirmacion

### Corregido

* Los formularios de crear y editar usuario ahora tambien requieren modal de confirmacion antes de guardar.
* Edicion de usuario detecta cambio de rol y muestra confirmacion especial.
* Edicion de usuario detecta nueva contrasena y muestra confirmacion especial.
* Si cambian rol y contrasena juntos, se muestra confirmacion de cambios criticos.
* Se registra cambio de contrasena en `logs_sistema` sin valores sensibles.

### Agregado

* Modal global reutilizable de confirmacion en `base.html`.
* Variantes visuales `danger`, `warning`, `info` y `success`.
* Cierre por boton cancelar, clic en overlay y tecla ESC.
* Atributos `data-*` para configurar titulo, mensaje, botones y tipo visual.

### Cambiado

* Activar/deshabilitar usuario ya no usa `window.confirm()`.
* Las acciones de usuarios abren modal propio y solo envian el formulario al confirmar.

### Validado

* `python -m compileall app`.
* Busqueda sin coincidencias de `window.confirm` ni `confirm(` en `app/static/js` y `app/templates`.
* Login `.env` redirige a `/panel`.
* `/panel`, `/usuarios/`, `/usuarios/?estado=activo`, `/usuarios/?rol=TI` y `/usuarios/nuevo` responden 200.

### No implementado

* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.
* No se modifico SQL ni permisos.

## 2026-06-12 - Seguridad .env y comandos de configuracion

### Corregido

* Reemplazadas instrucciones inseguras que copiaban `.env.example` sobre `.env`.
* Agregados comandos seguros para PowerShell y CMD que solo crean `.env` si no existe.
* Documentada regla de no sobrescribir `.env` real.
* Agregada validacion controlada de variables criticas de configuracion.
* Login muestra advertencia amigable si `.env` falta o contiene valores de plantilla.

### Seguridad

* `.env` se mantiene excluido por `.gitignore`.
* `.env.example` se mantiene como plantilla.
* No se agregaron credenciales reales a codigo, README, docs ni logs.
* No se modifico `.env`.

## 2026-06-12 - Fase 4.1 mejoras UX modulo usuarios

### Agregado

* Filtros en `/usuarios` por estado, rol y busqueda general.
* Contador de resultados del listado de usuarios.
* Boton para limpiar filtros.
* Confirmacion antes de activar o deshabilitar usuarios.
* Advertencia visual al cambiar rol de usuario.
* Advertencia visual al ingresar nueva contrasena en edicion.

### Mejorado

* Visualizacion de roles con nombre amigable, sin codigo redundante.
* Badges de rol y estado.
* Mensajes amigables de login, permisos y acciones de usuarios.
* Registro separado de cambio de rol en `logs_sistema`.

### Validado

* `python -m compileall app`.
* Login `.env` redirige a `/panel`.
* `/usuarios/` responde 200.
* `/usuarios/?estado=activo` responde 200.
* `/usuarios/?estado=inactivo` responde 200.
* `/usuarios/?rol=TI` responde 200.
* `/usuarios/?rol=ADMIN` responde 200.
* `/usuarios/?buscar=test` responde 200.
* `/usuarios/nuevo` responde 200.

### No implementado

* No se modificaron scripts SQL.
* No se cambio estructura de base de datos.
* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.

## 2026-06-12 - Fase 4 usuarios, roles y permisos iniciales

### Agregado

* Login hibrido: primero `.env`, luego tabla `usuarios`.
* Decoradores `login_requerido` y `permiso_requerido`.
* Sesion con roles y permisos.
* Modulo `/usuarios` para listar, crear, editar, activar y desactivar usuarios.
* Repositorios y servicios para usuarios, roles, permisos y logs de sistema.
* Registro inicial en `logs_sistema` para login y cambios de usuarios.
* Templates `usuarios/listado.html` y `usuarios/formulario.html`.

### Seguridad

* Contrasenas de usuarios de base de datos con `generate_password_hash` y `check_password_hash`.
* Sin eliminacion fisica de usuarios.
* Usuario inicial de `.env` mantiene acceso total y no se crea en base de datos.

### Validado

* `python -m compileall app`.
* GET `/login` responde 200.
* Login por `.env` redirige a `/panel`.
* GET `/panel` responde 200.
* GET `/usuarios/` responde 200 con sesion `.env`.

### No implementado

* CRUD de tareas.
* Carga real de scripts.
* Scheduler.
* Panel funcional de logs/auditoria.

## 2026-06-12 - README actualizado

### Documentado

* README principal actualizado al estado Fase 3D.
* Estado actual, stack, funcionalidades actuales y pendientes.
* Ejecucion local en Windows.
* Variables de entorno principales.
* Ubicacion y orden de scripts SQL.
* Referencias a `docs/` y `log_codex.md`.

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
