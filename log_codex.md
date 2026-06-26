# log_codex - Bitacora tecnica del proyecto

## 1. Estado general

* Nombre del proyecto: APP Scheduler
* Descripcion: Aplicacion web corporativa para programar, ejecutar, monitorear y auditar tareas Python de equipos TI.
* Stack actual: Python, Flask, HTML, CSS, JavaScript, python-dotenv, pyodbc, SQL Server.
* Base de datos: SQL Server local `APP_SCHEDULER_QA` creada y validada manualmente; historial incremental conservado en `database/migrations/` y `database/seeds/`; release SQL limpio consolidado en `database/release/` para instalaciones desde cero.
* Estado actual: Fase 13B.2 implementada como parametrizacion del nombre de base del release SQL mediante SQLCMD `DB_NAME`; se mantiene la matriz validada de roles/permisos. No se ejecuto SQL desde Codex y no se avanzo a Fase 13C ni Fase 14.
* Ambiente actual: LOCAL Windows.
* Fase actual: Fase 13B.2 - Parametrizacion del nombre de base en release SQL.
* Ultima actualizacion: 2026-06-26

## 2. Decisiones tecnicas vigentes

* Backend: Flask con fabrica `crear_app()` y Blueprint principal.
* Frontend: HTML/CSS/JS sin Streamlit.
* Base de datos: SQL Server local creado con scripts versionados; conexion Flask inicial mediante `pyodbc` y `.env`.
* Autenticacion: Login hibrido; primero `.env`, luego usuarios activos de SQL Server con password hash.
* Scheduler: Worker automatico separado implementado; validacion local de feriados implementada en Fase 10A; Fase 10B sincroniza feriados de forma manual hacia SQL Server; Fase 11A agrega panel operativo solo lectura, sin conectar internet al scheduler; Fase 11B agrega heartbeat en tabla dedicada; Fase 11D agrega eventos y omisiones del programador en tabla dedicada; Fase 11D.1 agrega resumen inteligente y retencion logica manual; Fase 11D.2 agrega historial filtrable de eventos; Fase 11F excluye tareas borradas operativamente de candidatos del scheduler; Fase 13A.1 evita persistir eventos ruidosos y agrega limpieza controlada; Fase 13A.1B agrega limpieza parametrizable con whitelist y previsualizacion.
* Logs: Logs de tarea con timestamp por linea implementados en Fase 9C; logs avanzados pendientes.
* Auditoria: Fase 12A implementa `auditoria_cambios`, `/auditoria` y servicio central `registrar_auditoria(...)`; Fase 12B amplia cobertura con acciones normalizadas, bloqueos `BLOQUEADO`, errores controlados `ERROR` y sanitizacion reforzada.
* Docker/despliegue: Pendiente para Fase 13B y siguientes; Fase 13A deja release SQL limpio para instalacion desde cero.
* Seguridad: Secretos y credenciales fuera del repositorio mediante `.env`.
* Seguridad `.env`: Nunca sobrescribir `.env` si ya existe; usar comandos seguros que copien `.env.example` solo cuando `.env` no existe.
* Versiones de scripts: No existe eliminacion fisica desde la app en primera version; se gestionan por estados `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Diseno UI/UX: Corporativo sobrio, responsive, sidebar oscuro, topbar clara compacta, componentes reutilizables, fondo claro, azul corporativo, cyan moderado y estados por color; Fase 12B.1F corrige el shell visual con sidebar flexible robusto y tratamiento premium de componentes compartidos.

## 3. Estructura actual del proyecto

* Carpetas principales: `app/`, `app/templates/`, `app/static/`, `docs/`, `database/migrations/`, `database/seeds/`.
* Archivos principales: `run.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `log_codex.md`.
* Modulos implementados: Login inicial, panel principal general con metricas reales, layout responsive, configuracion centralizada, modelo SQL Server con versionamiento de scripts, scripts SQL versionados ejecutados manualmente en SQL Server local, modulo inicial de conexion SQL Server, diagnostico local/QA, usuarios/roles/permisos iniciales, mejoras UX Fase 4.1, modal de confirmacion Fase 4.2, definicion tecnica Fase 4.3, mantenedores base Fase 5, eliminacion controlada Fase 5.1, tareas con programacion base Fase 6, resumen de confirmacion Fase 6.1, deteccion de cambios reales Fase 6.2, gestion de scripts/versiones/env Fase 7, mensajes contextuales Fase 7.1, bloque de script activo Fase 7.2, simplificacion visual Fase 7.3, eliminacion diferenciada Fase 7.4, separacion contenedor/archivo Fase 7.5, ejecucion manual Fase 8, configuracion scheduler Fase 9A, worker automatico Fase 9B, timestamps en logs Fase 9C, historial agrupado Fase 9D, calendario local de feriados Fase 10A, sincronizacion Nager.Date controlada Fase 10B, panel operativo scheduler Fase 11A, heartbeat del worker Fase 11B, modernizacion visual Fase 11C, eventos del programador Fase 11D, historial filtrable Fase 11D.2, borrado operativo seguro Fase 11F, papelera operativa Fase 11G, desacople historico Fase 11H, revision post-borrado Fase 11I, disponibilidad visible/diagnosticable de ejecucion manual en `/tareas`, auditoria base Fase 12A, correccion 12A.1 de detalle/roles, validacion transversal de duplicados Fase 12A.2, cobertura ampliada de auditoria Fase 12B, cierre garantizado de ejecucion manual Fase 12B.1A, sincronizacion visual de consola Fase 12B.1B, modernizacion responsive Fase 12B.1D, eliminacion permanente masiva segura en Papelera, rediseno visual profundo del shell Fase 12B.1E, correccion premium del shell Fase 12B.1F, validacion inicial 12B.2 del worker automatico con correcciones acotadas de cierre/heartbeat, release SQL limpio Fase 13A, optimizacion/limpieza de eventos Fase 13A.1 y limpieza parametrizable Fase 13A.1B.
* Modulos pendientes: Fase 12C Auditoria extendida, Fase 13B+ operacion/despliegue y Fase 14 mantenimiento avanzado.

## 4. Reglas del proyecto

* Reglas de codigo: Usar nombres descriptivos en espanol cuando sea razonable, Flask modular y configuracion centralizada.
* Reglas de seguridad: No versionar `.env`, logs reales, scripts cargados por usuarios ni secretos.
* Reglas de documentacion: Toda modificacion debe actualizar `docs/`, `docs/CHANGELOG.md` si aplica y `log_codex.md`.
* Reglas de diseno: UI clara, sobria, responsive, corporativa y futurista moderada.
* Reglas de base de datos: SQL Server con claves primarias, foraneas, indices y auditoria desde Fase 3.
* Reglas de despliegue: Sin rutas absolutas quemadas; usar variables de entorno.

## 5. Pendientes

* Pendiente 1: Resolver/validar conexion OK desde `/diagnostico/bd` en el entorno local del usuario si aparece error de driver/red/cifrado.
* Pendiente 2: Ejecutar migracion 011 en SQL Server local antes de usar ejecuciones automaticas si aun no fue aplicada.
* Pendiente 3: Ejecutar migracion 013 y seeds 009/010 en SQL Server local antes de probar `/feriados/sincronizar` con usuarios de base de datos.
* Pendiente 4: Mantener pruebas controladas del worker antes de uso operativo.

## 6. Historial de cambios

### 2026-06-26 - Fase 13B.2 / Script maestro instalacion SQLCMD

* Archivo creado: `database/release/000_ejecutar_instalacion_completa.sql`.
* Archivos modificados: `database/release/README_INSTALACION_SQL.md`, `database/release/AUDITORIA_RELEASE_SQL.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Problema detectado: ejecutar `000_configuracion_instalacion.sql` en una pestaÃ±a separada de SSMS no garantiza que `DB_NAME` quede disponible en scripts abiertos en otras ventanas.
* Cambio aplicado: se crea un script maestro que define `DB_NAME` una sola vez y ejecuta `001` a `006` y `099` con directivas SQLCMD `:r`.
* Flujo recomendado: abrir `000_ejecutar_instalacion_completa.sql`, activar `Query > SQLCMD Mode`, cambiar solo `DB_NAME` si corresponde y ejecutar el archivo completo.
* Flujo avanzado: los scripts individuales siguen disponibles, pero requieren `DB_NAME` definido en la misma ventana/script SQLCMD.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se conecto a SQL Server, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`, no se cambio backend/frontend/scheduler, no se alteraron roles/permisos/catalogos/configuracion, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B.2 / Parametrizacion DB_NAME release SQL

* Archivo creado: `database/release/000_configuracion_instalacion.sql`.
* Archivos modificados: `database/release/001_crear_base_datos.sql`, `database/release/002_schema_final.sql`, `database/release/003_seed_roles_permisos.sql`, `database/release/004_seed_catalogos_base.sql`, `database/release/005_seed_configuracion_inicial.sql`, `database/release/006_seed_feriados_base.sql`, `database/release/099_validacion_instalacion.sql`, `database/release/README_INSTALACION_SQL.md`, `database/release/AUDITORIA_RELEASE_SQL.md`, `docs/DESPLIEGUE.md`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Objetivo: permitir que el release SQL se instale en distintas bases cambiando una sola variable.
* Cambio aplicado: se agrega SQLCMD variable `DB_NAME` con valor por defecto `APP_SCHEDULER_TEST_INSTALL` para pruebas.
* SQL: `001` usa `CREATE DATABASE [$(DB_NAME)]` y `USE [$(DB_NAME)]`; `002` a `006` y `099` usan `USE [$(DB_NAME)]`.
* Validacion: `099_validacion_instalacion.sql` compara `DB_NAME()` contra `'$(DB_NAME)'`.
* Documentacion: README, auditoria y despliegue indican activar `Query > SQLCMD Mode`, ejecutar `000` primero y cambiar solo `DB_NAME` para otro ambiente.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se conecto a SQL Server, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`, no se cambio backend/frontend/scheduler, no se alteraron roles/permisos/catalogos/configuracion/schema funcional, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B.1 / Correccion matriz real roles-permisos QA

* Archivos modificados: `database/release/003_seed_roles_permisos.sql`, `database/release/099_validacion_instalacion.sql`, `database/release/AUDITORIA_RELEASE_SQL.md`, `database/release/README_INSTALACION_SQL.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Objetivo corregido: el release debe replicar el estado base real de `APP_SCHEDULER_QA`, no redisenar seguridad ni crear roles inexistentes.
* Hallazgo: `APP_SCHEDULER_QA` no tiene rol `OPERADOR`; el release lo estaba creando indebidamente.
* Correccion aplicada: `OPERADOR` fue eliminado del seed ejecutable de roles y de las validaciones esperadas.
* Roles finales del release: `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`.
* Matriz de permisos esperada: `SUPER_ADMIN = 39`, `ADMIN = 37`, `TI = 31`, `TERCERO = 7`.
* `003`: `SUPER_ADMIN` deja de recibir todos los permisos por `CROSS JOIN`; todos los roles usan listas explicitas de permisos equivalentes a QA.
* `099`: se agregan validaciones de roles esperados, roles no esperados, ausencia de `OPERADOR` y diferencias de permisos por rol.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se conecto a SQL Server, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`, no se cambio backend/frontend/scheduler, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B.1 / Correccion de criterio roles base

* Archivos modificados: `database/release/003_seed_roles_permisos.sql`, `database/release/099_validacion_instalacion.sql`, `database/release/AUDITORIA_RELEASE_SQL.md`, `database/release/README_INSTALACION_SQL.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Nota: entrada superada por la correccion posterior de matriz real QA; el release final no crea `OPERADOR`.
* Problema detectado: la correccion anterior del release simplifico indebidamente los roles base a `SUPER_ADMIN`, `ADMIN` y `OPERADOR`, dejando fuera los roles historicos funcionales `TI` y `TERCERO`.
* Criterio corregido: el release limpio debe reconstruir fielmente el estado funcional del sistema, no redisenar ni eliminar roles historicos.
* Correccion aplicada: `003_seed_roles_permisos.sql` restaura `TI` y `TERCERO`; todos los roles informan `codigo_rol` y el `MERGE` usa `codigo_rol`.
* Validacion: `099_validacion_instalacion.sql` agrega `VALIDACION_ROLES_BASE` y `VALIDACION_ROLES_FALTANTES`; se espera `roles_faltantes = 0`.
* Documentacion: README y auditoria del release explican la correccion de criterio y los roles base esperados.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se conecto a SQL Server, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`, no se cambio backend/frontend/scheduler, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B.1 / Auditoria integral release SQL

* Archivos creados: `database/release/AUDITORIA_RELEASE_SQL.md`.
* Archivos modificados: `database/release/004_seed_catalogos_base.sql`, `database/release/005_seed_configuracion_inicial.sql`, `database/release/099_validacion_instalacion.sql`, `database/release/README_INSTALACION_SQL.md`, `docs/DESPLIEGUE.md`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Objetivo: detener parches puntuales y revisar integralmente el release SQL contra schema final, seeds historicos y usos del backend.
* Hallazgo 1: `004_seed_catalogos_base.sql` omitia `nombre` en catalogos con columna `nombre NOT NULL`.
* Hallazgo 2: `cat_tipos_tarea` contenia tipos tecnicos, pero el backend guarda `MANUAL` y `PROGRAMADA`.
* Hallazgo 3: `005_seed_configuracion_inicial.sql` usaba `observacion` en `configuracion_scheduler`, columna inexistente en el schema final.
* Hallazgo 4: `configuracion_sistema.tipo_dato` es obligatorio y no estaba informado por el seed.
* Correcciones: `004` informa `codigo`, `nombre`, `descripcion`; `005` usa columnas reales y `tipo_dato`; `099` queda como reporte de validacion por secciones.
* Auditoria: se documento matriz tabla por tabla, matriz seed por seed, tablas con datos, tablas vacias, columnas NOT NULL, catalogos, roles/permisos, configuracion minima, riesgos y reintento manual.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se conecto a SQL Server, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`, no se cambio backend/frontend/scheduler, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B / Preparacion de prueba de instalacion limpia

* Archivos modificados: `database/release/001_crear_base_datos.sql`, `database/release/002_schema_final.sql`, `database/release/003_seed_roles_permisos.sql`, `database/release/004_seed_catalogos_base.sql`, `database/release/005_seed_configuracion_inicial.sql`, `database/release/006_seed_feriados_base.sql`, `database/release/099_validacion_instalacion.sql`, `database/release/README_INSTALACION_SQL.md`, `docs/DESPLIEGUE.md`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Problema detectado: el paquete release apuntaba a `APP_SCHEDULER_QA`, pero la prueba de Fase 13B debe ejecutarse en una base nueva para no tocar datos reales.
* Cambio aplicado: los scripts release ahora apuntan a `APP_SCHEDULER_TEST_INSTALL` para la prueba limpia manual.
* Documentacion: se reforzo en README de release y despliegue que la ejecucion debe realizarse manualmente en SSMS y que Codex no debe ejecutar SQL.
* Estado de ejecucion: pendiente de ejecucion manual por el usuario en SQL Server Management Studio.
* Pruebas esperadas: ejecutar scripts `001` a `006`, luego `099_validacion_instalacion.sql`, revisar tablas, roles, permisos, relaciones, configuracion, indices, checks y ausencia de datos operativos.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se toco `APP_SCHEDULER_QA`, no se cambio backend/frontend/scheduler/logica funcional, no se hizo commit ni push y no se avanzo a Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13B / Correccion seed roles release

* Error reportado por el usuario en SSMS: `Cannot insert the value NULL into column 'codigo_rol', table 'APP_SCHEDULER_TEST_INSTALL.dbo.roles'; column does not allow nulls`.
* Diagnostico: `database/release/002_schema_final.sql` define `dbo.roles.codigo_rol varchar(50) NOT NULL` y `UX_roles_codigo_rol`, pero `database/release/003_seed_roles_permisos.sql` creaba roles solo con `nombre_rol` y `descripcion`.
* Causa raiz: el `MERGE dbo.roles` del release no incluia `codigo_rol` en el origen ni en el `INSERT`.
* Correccion: el seed ahora usa `codigo_rol`, `nombre_rol`, `descripcion` y `es_sistema`; la clave de emparejamiento del `MERGE` es `codigo_rol`.
* Correccion superada por Fase 13B.1: el release final no crea `OPERADOR`; los roles reales son `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`.
* Relaciones: los inserts de `roles_permisos` ahora filtran por `r.codigo_rol`; se elimino la dependencia de `nombre_rol`.
* Validacion adicional: `099_validacion_instalacion.sql` reporta `roles_codigo_nulo`, que debe ser `0`.
* Estado de ejecucion: pendiente reintento manual del script `003` corregido en SSMS; no avanzar a `004` hasta que `003` termine sin errores.
* Reglas: No se modifico `.env`, no se ejecuto SQL desde Codex, no se toco `APP_SCHEDULER_QA`, no se cambio backend/frontend/scheduler, no se hizo commit ni push y no se avanzo a `004`, Fase 13C ni Fase 14.

### 2026-06-26 - Fase 13A.1B / Paginacion dinamica de eventos scheduler

* Archivos creados: `app/templates/scheduler/_eventos_historial.html`.
* Archivos modificados: `app/rutas_scheduler.py`, `app/templates/scheduler/eventos.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `docs/UI_UX.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Problema detectado: la paginacion del historial en `/scheduler/eventos` recargaba toda la pagina y devolvia al usuario arriba de la vista.
* Cambio aplicado: la tabla de eventos y la paginacion pasan a un parcial reutilizable; la ruta devuelve ese parcial cuando recibe `X-Requested-With: fetch`.
* Frontend: `app.js` intercepta clicks en `Primero`, `Anterior`, `Siguiente` y `Ultimo`, carga el parcial con `fetch` y reemplaza solo `[data-eventos-historial]`.
* UX: no hay scroll automatico ni recarga completa; el bloque de filtros y la limpieza quedan intactos visualmente.
* URL: se usa `history.pushState` para conservar pagina y filtros; `popstate` vuelve a cargar el parcial correspondiente.
* Degradacion segura: los enlaces siguen siendo `href` normales si JavaScript falla o esta desactivado.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se cambio logica de limpieza/scheduler/auditoria/permisos, no se borraron datos y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-26 - Fase 13A.1B / Multiselect visible de limpieza scheduler

* Archivos modificados: `app/templates/scheduler/eventos.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/UI_UX.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Problema detectado: el selector `Alcance` funcionaba como preset principal y ocultaba categorias individuales salvo al elegir `Personalizado`.
* Cambio aplicado: se elimina el selector `Alcance`; las categorias permitidas quedan siempre visibles como checkboxes compactos.
* Atajos disponibles: `Ruido operativo`, `Seleccionar todo` y `Deseleccionar todo`.
* Comportamiento UI: el resumen indica sin categorias, una categoria, varias categorias o todas las categorias seleccionadas; la previsualizacion y limpieza usan las categorias marcadas.
* Backend: no se modifico; se mantiene `request.form.getlist("categorias")`, bloqueo de lista vacia, whitelist de categorias y SQL seguro existente.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se cambiaron permisos/auditoria/scheduler, no se borraron datos y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-23 - Fase 13A.1B / Limpieza parametrizable de eventos scheduler

* Archivos modificados: `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`, `app/rutas_scheduler.py`, `app/templates/scheduler/eventos.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/ARQUITECTURA.md`, `docs/ROADMAP.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Objetivo: permitir limpieza parametrizable por periodo y categorias seleccionadas.
* Backend: se agrego whitelist `CATEGORIAS_LIMPIEZA`, previsualizacion protegida y eliminacion con condiciones SQL internas validadas.
* UI: se agregaron checkboxes de categorias, botones `Seleccionar todas`, `Limpiar solo ruido operativo`, `Previsualizar limpieza` y modal con resumen dinamico.
* Permiso usado: `SCHEDULER_CONFIG_EDITAR`.
* Auditoria: accion `LIMPIAR_EVENTOS_SCHEDULER`, con periodo, categorias, total eliminado y detalle.
* No se creo seed ni migracion; no se modifico `database/release/`.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se borro auditoria/ejecuciones/logs/heartbeat/datos operativos, no se cambio logica de ejecucion y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-23 - Fase 13A.1B / Ajuste visual compacto de limpieza scheduler

* Archivos modificados: `app/templates/scheduler/eventos.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/UI_UX.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Diagnostico visual: la seccion de limpieza parametrizable ocupaba demasiado espacio por tarjetas, textos largos y checkboxes distribuidos como bloque principal antes del historial.
* Cambio aplicado: se compacto el bloque en una barra operativa con periodo, desplegable de categorias, acciones rapidas, resumen discreto y previsualizacion bajo demanda.
* Funcionalidad conservada: whitelist backend, seleccion de categorias, previsualizacion previa, boton deshabilitado hasta validar, modal corporativo con resumen y checkbox obligatorio.
* Decision UI/UX: mantener la limpieza como herramienta secundaria dentro de `/scheduler/eventos`, sin competir visualmente con filtros, paginacion e historial.
* Validaciones recomendadas: abrir `/scheduler/eventos`, seleccionar periodo y categorias, usar acciones rapidas, previsualizar, confirmar modal con checkbox y verificar que no aparezcan `alert()`, `confirm()`, `prompt()` ni recargas forzadas.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se cambiaron repositorios/servicios/rutas en este ajuste visual y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-23 - Fase 13A.1B / Rediseno visual por presets de limpieza scheduler

* Archivos modificados: `app/templates/scheduler/eventos.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/UI_UX.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Problema visual detectado: el selector de categorias seguia abriendo un panel grande, con checkboxes visibles, texto cortado y superposicion sobre la tabla de eventos.
* Cambio aplicado: la limpieza queda como flujo administrativo compacto: seleccionar periodo, elegir preset de alcance, previsualizar impacto y confirmar eliminacion.
* Presets visibles: `Ruido operativo`, `Eventos de ejecucion`, `Errores y bloqueos`, `Calendario y programacion`, `Todas las categorias permitidas` y `Personalizado`.
* Modo personalizado: las categorias individuales se muestran solo si el usuario selecciona `Personalizado`, como lista compacta de checkboxes normales y sin tarjetas.
* Funcionalidad conservada: el frontend sigue enviando claves `categorias`; el backend mantiene whitelist, permisos, auditoria, previsualizacion y confirmacion fuerte sin cambios.
* Decision UI/UX: ocultar complejidad tecnica por defecto y presentar la limpieza como una accion administrativa de alcance claro.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se cambiaron repositorios/servicios/rutas, no se borro informacion y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-23 - Fase 13A.1 / Optimizacion y limpieza controlada de eventos scheduler

* Archivos modificados: `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`, `app/rutas_scheduler.py`, `app/templates/scheduler/eventos.html`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/ARQUITECTURA.md`, `docs/ROADMAP.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Diagnostico: `scheduler_eventos` crecia por eventos normales repetitivos de cada ciclo: inicio, fin y omisiones `FUERA_DE_VENTANA`.
* Politica nueva: no persistir `CICLO_INICIADO`, `CICLO_FINALIZADO` ni `TAREA_OMITIDA/FUERA_DE_VENTANA`; conservar eventos relevantes.
* Limpieza: se agrego `POST /scheduler/eventos/limpiar`, protegido con `SCHEDULER_CONFIG_EDITAR`, para eliminar eventos informativos antiguos de 20, 30, 60 o 90 dias.
* Alcance de limpieza: solo `scheduler_eventos` y solo eventos informativos ruidosos antiguos.
* Protecciones: modal corporativo danger, checkbox obligatorio, validacion de periodos permitidos, auditoria y log de sistema.
* No se creo seed ni migracion; no se actualizo `database/release/` porque se reutiliza permiso existente y no hay cambio de schema.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se borro auditoria/ejecuciones/logs/heartbeat/datos operativos, no se cambio logica de ejecucion y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-23 - Fase 13A / Consolidacion SQL release limpio

* Archivos creados: `database/release/README_INSTALACION_SQL.md`, `database/release/001_crear_base_datos.sql`, `database/release/002_schema_final.sql`, `database/release/003_seed_roles_permisos.sql`, `database/release/004_seed_catalogos_base.sql`, `database/release/005_seed_configuracion_inicial.sql`, `database/release/006_seed_feriados_base.sql`, `database/release/099_validacion_instalacion.sql`.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/DESPLIEGUE.md`, `docs/ROADMAP.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `log_codex.md`.
* Objetivo: consolidar el historial SQL incremental en un release limpio para instalar `APP_SCHEDULER_QA` desde cero.
* Que se hizo: se creo script de base, esquema final, seeds consolidados y validacion solo lectura.
* Modelo incluido: seguridad, mantenedores, tareas, programaciones, scripts versionados, ejecuciones, logs, scheduler, heartbeat, eventos, feriados, reglas irrenunciables, papelera operativa, snapshots y auditoria.
* Seeds incluidos: roles, permisos, roles_permisos, catalogos, configuracion inicial segura y reglas base de feriados irrenunciables.
* Que no se incluyo: usuarios reales, passwords, servidores, rutas locales, datos de prueba, tareas, scripts, ejecuciones, logs historicos, auditoria historica ni feriados sincronizados por API.
* Decisiones: `database/migrations/` y `database/seeds/` quedan como historial; `database/release/` queda como camino recomendado para instalacion limpia.
* Validaciones: revision de orden logico, dependencias, indices filtrados, checks, ausencia de credenciales y `git diff --check`.
* Reglas: No se modifico `.env`, no se ejecuto SQL, no se cambio backend/frontend/scheduler y no se avanzo a Fase 13B ni Fase 14.

### 2026-06-19 - Fase 12B.2 / Validacion real del scheduler_worker

* Archivos modificados: `app/servicios/servicio_ejecuciones.py`, `app/servicios/servicio_worker_heartbeat.py`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `docs/SEGURIDAD.md`, `docs/UI_UX.md`, `docs/DESPLIEGUE.md`, `log_codex.md`.
* Comandos ejecutados: `python scheduler_worker.py --once`; arranque breve de `python scheduler_worker.py` desde wrapper local con detencion controlada; `python -m compileall app scheduler_worker.py`.
* Resultado `--once`: corre sin romper, pero no puede leer configuracion ni registrar heartbeat/eventos por error ODBC local `08001` de cifrado/credenciales SSL.
* Resultado continuo breve: inicia, reporta el mismo error controlado y queda en ciclo de espera; fue detenido por wrapper tras unos segundos. El codigo de salida observado corresponde a la terminacion externa del proceso de prueba.
* Configuracion usada: no pudo leerse desde SQL Server por fallo de conexion. No hubo IDs reales de tarea, ejecucion, eventos ni heartbeat.
* Bug corregido 1: `iniciar_ejecucion_automatica(...)` usaba hilo `daemon=True`; en modo `--once` podia terminar el worker antes del cierre final de la ejecucion automatica. Se cambio a `daemon=False`.
* Bug corregido 2: el cierre garantizado del monitor ahora cubre tambien origen `AUTOMATICA` si una ejecucion queda `EN_EJECUCION`.
* Bug corregido 3: fallos al registrar heartbeat/logs del worker ya no propagan excepcion si SQL Server no esta disponible.
* Validaciones no completadas por entorno: programador inactivo, ejecucion automatica deshabilitada, mantenimiento, tarea elegible, duplicado de slot, concurrencia, feriado, `/scheduler/panel`, `/scheduler/eventos`, `/ejecuciones`, consola y `/panel`.
* Reglas: No se modifico `.env`, no se ejecuto SQL automaticamente, no se crearon migraciones ni seeds, no se borro historial/auditoria/ejecuciones/logs/eventos/snapshots, no se cambio Papelera/roles/duplicados ni ejecucion manual estable, no se implemento Docker/systemd/Celery/Redis y no se avanzo a Fase 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1D-Papelera / Eliminacion permanente masiva segura

* Archivos modificados: `app/rutas_papelera.py`, `app/servicios/servicio_papelera.py`, `app/templates/papelera/listado.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `docs/SEGURIDAD.md`, `docs/UI_UX.md`, `log_codex.md`.
* Objetivo: Agregar una accion masiva segura en `/papelera` para eliminar permanentemente todos los registros eliminados operativamente, sin borrar historial ni cambiar reglas individuales.
* Backend: Se agrego `eliminar_todo_permanente(...)`, que lista Papelera, ordena el procesamiento y llama item por item a `eliminar_registro_permanente(...)`.
* Seguridad: Los bloqueos por dependencias, usuario conectado, ultimo administrador, snapshots insuficientes, migracion pendiente o integridad se mantienen por item. Un item bloqueado no detiene el resto del proceso.
* UI: Se agrego boton `Eliminar permanentemente todo` visible por permiso `PAPELERA_ELIMINAR_PERMANENTE`, modal `danger`, resumen por entidad y checkbox obligatorio antes de confirmar.
* Resultado: La vista muestra resumen de encontrados, eliminados, no eliminados, errores y motivos seguros de los registros no eliminados.
* Auditoria: Se registra accion masiva `ELIMINAR_PERMANENTE_TODO_PAPELERA` y se conservan las auditorias individuales de eliminacion permanente o bloqueo por registro.
* Reglas: No se ejecuto SQL, no se crearon migraciones ni seeds, no se modifico `.env`, no se agrego `DELETE CASCADE`, no se borro historial/auditoria/ejecuciones/logs/eventos/snapshots y no se avanzo a Fase 12B.2, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1F / Correccion profunda del shell visual y modernizacion UI/UX premium

* Archivos modificados: `app/templates/base.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `docs/UI_UX.md`, `log_codex.md`.
* Causa del sidebar cortado: La navegacion tenia overflow, pero no era el hijo flexible principal del sidebar; con zoom alto o pantallas bajas, header, nav y footer podian competir por la altura disponible dentro del aside.
* Causa de redundancia superior: La topbar mostraba marca y titulo (`APP Scheduler` + pantalla actual) mientras cada vista ya presentaba su contexto operativo en el contenido principal.
* Causa del espacio vacio posterior: Al retirar el titulo global, la topbar quedo como zona flotante de acciones; el boton de sidebar quedaba desanclado visualmente y el contenido no aprovechaba bien la composicion superior.
* Solucion sidebar: El aside queda `position: fixed` en desktop, usa `100dvh`, `max-height: 100dvh`, header/footer no flexibles y `.nav` como region flexible con scroll interno. El contenido principal usa margen izquierdo equivalente al sidebar. Se conserva off-canvas mobile, overlay, cierre por enlace, Escape y normalizacion por resize.
* Solucion topbar: Se elimina el titulo global de la topbar; queda como barra compacta en flujo normal, con toggle de sidebar a la izquierda, acciones a la derecha y el titulo del modulo dentro del contenido real de cada vista.
* Tablas: Se elimina el efecto de raya/borde celeste por celda y se reemplaza por hover suave de fila completa.
* Componentes: Se modernizaron botones, icon buttons, cards, contenedores, bloques, formularios, badges, foco, hover, active y microinteracciones sin cambiar clases funcionales ni condiciones de permisos.
* Validacion visual realizada: `/login` probado con viewport 390, 820 y 1280 px sin overflow horizontal global ni errores JavaScript. Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.
* Validaciones tecnicas: `python -m compileall app scheduler_worker.py`; busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` u `ON DELETE CASCADE` en `app` y `database`; `git diff --check`.
* Reglas: No se cambio logica funcional, no se tocaron rutas/servicios/repositorios de negocio, no se ejecuto SQL, no se crearon migraciones ni seeds, no se modifico `.env`, no se agregaron dependencias externas, no se cambio `scheduler_worker.py`, no se avanzo a Fase 12B.2, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1E / Rediseno visual profundo del shell y experiencia UI general

* Archivos modificados: `app/templates/base.html`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `docs/UI_UX.md`, `log_codex.md`.
* Problema detectado: El shell ya era responsive, pero la navegacion seguia dependiendo de numeracion visual y la topbar repetia informacion de ambiente, generando una jerarquia mas pesada que la necesaria.
* Solucion implementada: Se reemplazo la numeracion del sidebar por iconos textuales de modulo con etiquetas controladas, se compacto la topbar con marca `APP Scheduler` y titulo de pantalla, y se ajustaron fondo, ancho del sidebar, espaciados, estados activos y bienvenida para una experiencia mas profesional.
* Responsive: El sidebar colapsado en desktop queda como carril de iconos textuales; en vistas compactas conserva off-canvas con etiquetas completas.
* Validacion visual realizada: `/login` probado con viewport 390, 820 y 1280 px sin overflow horizontal global ni errores JavaScript. Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.
* Validaciones tecnicas: `python -m compileall app scheduler_worker.py`; busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` u `ON DELETE CASCADE` en `app` y `database`; `git diff --check`.
* Reglas: No se cambio logica funcional, no se tocaron rutas/servicios/repositorios de negocio, no se ejecuto SQL, no se crearon migraciones ni seeds, no se modifico `.env`, no se agregaron dependencias externas, no se cambio `scheduler_worker.py`, no se avanzo a Fase 12B.2, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1D / Modernizacion visual general y layout responsive

* Archivos modificados: `app/templates/base.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `docs/UI_UX.md`, `log_codex.md`.
* Problema detectado: El shell era funcional pero podia volverse rigido con zoom alto o anchos intermedios; el sidebar no tenia colapso desktop ni scroll interno robusto y algunas grillas/tablas podian empujar ancho global.
* Solucion implementada: Se agregaron variables de layout (`--sidebar-width`, `--sidebar-width-collapsed`, `--topbar-height`), colapso desktop persistido en `localStorage`, sidebar off-canvas en vistas compactas, scroll interno del menu, cierre al seleccionar opcion en mobile/tablet y tablas con overflow horizontal interno.
* Topbar: El boton de menu queda visible; en desktop colapsa/expande el sidebar y en vistas compactas abre el menu lateral.
* Componentes: Se reforzaron grillas de filtros/formularios/tarjetas/listados para degradar a dos o una columna segun ancho; botones, inputs y contenedores evitan desbordes por min-width; panel de logs tiene scroll propio.
* Validacion visual realizada: `/login` probado con viewport 390, 820 y 1280 px sin overflow horizontal global. Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.
* Validaciones tecnicas: `python -m compileall app scheduler_worker.py`; busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`; `git diff --check`.
* Reglas: No se cambio logica funcional, no se tocaron rutas/servicios/repositorios de negocio, no se ejecuto SQL, no se crearon migraciones, no se modifico `.env`, no se agregaron dependencias externas, no se cambio `scheduler_worker.py`, no se avanzo a Fase 12B.1E, 12B.2, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1C / Validacion operativa de ejecucion manual

* Tipo de fase: Validacion operativa, sin desarrollo funcional grande.
* Objetivo: Probar ejecuciones manuales reales repetidas para confirmar cierre automatico `EXITOSA`, `ERROR` y `DETENIDA_MANUALMENTE`, sincronizacion visual sin reload, toast unico y ausencia de huerfanas normales.
* Resultado en este entorno: Bloqueado para pruebas reales completas. La app local responde en `http://127.0.0.1:5000/`, pero redirige a `/login`; no se leyeron credenciales desde `.env`. La consulta de tareas ejecutables mediante la capa de servicio fallo por `pyodbc.OperationalError` con mensaje de cifrado/credenciales SSL/ODBC Driver 17.
* Pruebas reales no ejecutadas: 5 ejecuciones rapidas exitosas, 2 largas exitosas, 2 con error, 1 detenida manualmente, apertura de ejecucion ya finalizada y verificacion sobre finalizada. No se reportan IDs reales porque no se pudo iniciar ejecuciones contra BD.
* Validaciones tecnicas ejecutadas: `python -m compileall app scheduler_worker.py`; busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`; prueba ligera del contrato de polling para `EXITOSA`, `ERROR` y `DETENIDA_MANUALMENTE`; `git diff --check`.
* Bugs encontrados: Ningun bug nuevo confirmado en codigo durante esta fase; la limitacion fue ambiental/conexion.
* Correcciones aplicadas: Ninguna correccion funcional. No se modifico el cierre garantizado de Fase 12B.1A ni la sincronizacion visual de Fase 12B.1B.
* Pendiente operativo: Repetir la matriz de pruebas reales desde una sesion autenticada y con SQL Server accesible; ejecutar manualmente en SSMS las consultas de validacion documentadas en `docs/FLUJOS.md`.
* Reglas: No se ejecuto SQL automaticamente, no se crearon migraciones, no se modifico `.env`, no se cambio `scheduler_worker.py`, no se borro historial/auditoria/ejecuciones/logs/eventos/snapshots, no se avanzo a Fase 12B.1D, 12B.2, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1B / Sincronizacion visual de consola y notificacion de termino

* Archivos modificados: `app/templates/ejecuciones/consola.html`, `app/static/js/app.js`, `app/servicios/servicio_ejecuciones.py`, `app/rutas_ejecuciones.py`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/UI_UX.md`, `docs/ROADMAP.md`, `log_codex.md`.
* Diagnostico: Fase 12B.1A ya cerraba correctamente la ejecucion manual en backend, pero la consola solo refrescaba el texto del log. El badge superior, titulo de estado, resumen y acciones seguian usando el estado inicial renderizado al cargar la pagina.
* Causa visual: contrato de polling insuficiente y JS parcial; `/ejecuciones/<id>/log` entregaba estado basico, pero el frontend no aplicaba ese estado a todos los componentes visibles ni notificaba el termino.
* Correccion backend: `obtener_estado_log()` ahora devuelve `estado_actual`, `estado_es_final`, `codigo_salida`, `fecha_hora_termino`, alias `fecha_hora_fin`, `duracion_segundos`, `mensaje_error`, `en_ejecucion` y `detener_polling`, manteniendo `estado` y `es_final` por compatibilidad.
* Correccion frontend: la consola actualiza sin reload el titulo de estado, badge superior, indicador de consola, fecha de termino, duracion, codigo de salida y acciones en curso. Al finalizar, oculta/deshabilita acciones de ejecucion en curso y corta polling tras la primera sincronizacion final.
* Toast: se reutiliza el toast del sistema; `EXITOSA`, `ERROR` y `DETENIDA_MANUALMENTE` muestran notificacion no bloqueante una sola vez al detectar transicion desde estado no final.
* Detencion/verificacion: los formularios de detencion y verificacion en consola pueden enviarse por `fetch` y sincronizar respuesta JSON sin refresh completo; el flujo normal por POST queda como fallback.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`; `git diff --check`.
* Reglas: No se ejecuto SQL, no se crearon migraciones, no se modifico `.env`, no se cambio `scheduler_worker.py`, no se borro historial/auditoria/ejecuciones/logs/eventos/snapshots, no se cambio el motor de ejecucion ni el cierre garantizado de Fase 12B.1A, no se avanzo a Fase 12B.1C, 12B.1D, 12C ni Fase 13.

### 2026-06-19 - Fase 12B.1A / Diagnostico y cierre garantizado de ejecucion manual

* Archivos modificados: `app/servicios/servicio_ejecuciones.py`, `app/servicios/servicio_procesos.py`, `docs/CHANGELOG.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/ROADMAP.md`, `log_codex.md`.
* Diagnostico obligatorio:
  * `subprocess.Popen` se lanza en `app/servicios/servicio_procesos.py`, funcion `iniciar_proceso_python()`.
  * La ejecucion manual crea un `threading.Thread` desde `iniciar_ejecucion_manual()` y ejecuta `_ejecutar_en_segundo_plano()`.
  * El hilo usa `app.app_context()` y no depende del objeto request despues de recibir `app`, `id_ejecucion`, `contexto`, ruta de log y usuario.
  * `pid_proceso` se guarda con `actualizar_pid_ejecucion()` despues de iniciar el proceso.
  * stdout/stderr se lee desde `proceso.stdout`; stderr va combinado a stdout por `stderr=subprocess.STDOUT`.
  * `process.wait()` se ejecuta despues de consumir stdout.
  * El estado final se actualiza con `finalizar_ejecucion()` y `actualizar_log_tarea_final()`.
  * Si el script termina rapido, el iterador de stdout termina y luego `wait()` devuelve returncode.
  * Si la lectura de stdout falla, ahora se cierra como `ERROR` por fallo controlado del monitor.
  * Si falla la escritura de logs o una operacion del monitor, ahora existe cierre defensivo para dejar `ERROR` si sigue `EN_EJECUCION`.
  * Antes, una excepcion o finalizacion anomala del monitor podia dejar solo `olvidar_proceso()` en `finally`, sin cierre garantizado.
  * Con Flask debug/reloader, un hilo `daemon=True` puede ser mas vulnerable a cierre abrupto del proceso; se cambio el hilo manual a `daemon=False`.
  * Faltaba un bloque `finally` que verificara si la ejecucion manual seguia `EN_EJECUCION`.
* Causa probable: combinacion de hilo daemon y ausencia de cierre defensivo final; si el monitor terminaba/fallaba antes de ejecutar `finalizar_ejecucion()`, el proceso real podia morir y la fila quedar `EN_EJECUCION` hasta usar `Verificar`.
* Correccion: El hilo manual ya no es daemon; si el proceso finaliza con returncode `0`, cierra `EXITOSA`; con returncode distinto de `0`, cierra `ERROR`; si falla el monitor, intenta terminar el proceso hijo y cierra `ERROR` con mensaje controlado; en `finally`, si sigue `EN_EJECUCION`, cierra `ERROR`.
* Verificacion huerfana: Se mantiene como recuperacion excepcional; no debe ser necesaria para ejecuciones manuales normales.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; simulacion en memoria de cierre manual exitoso `EXITOSA`, cierre con returncode distinto de cero `ERROR` y fallo de monitor `ERROR`; busqueda sin coincidencias de `alert()`, `window.confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`; `git diff --check`.
* Reglas: No se ejecuto SQL, no se crearon migraciones, no se modifico `.env`, no se toco `scheduler_worker.py`, no se cambio el programador automatico, no se borro historial y no se avanzo a Fase 12C ni Fase 13.

### 2026-06-19 - Fase 12B / Cobertura ampliada y consolidacion de Auditoria

* Archivos modificados: `app/servicios/servicio_auditoria.py`, `app/seguridad.py`, `app/servicios/servicio_ejecuciones.py`, `app/rutas_ejecuciones.py`, `app/servicios/servicio_configuracion_scheduler.py`, `app/rutas_scheduler.py`, `app/servicios/servicio_sincronizacion_feriados.py`, `app/servicios/servicio_scripts.py`, `app/servicios/servicio_usuarios.py`, `app/servicios/servicio_mantenedores.py`, `app/servicios/servicio_tareas.py`, `app/servicios/servicio_papelera.py`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/BASE_DATOS.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se hizo: Se consolido la auditoria de acciones humanas criticas con normalizacion central de acciones, entidades, resultados y modulos.
* Acciones nuevas/cubiertas: bloqueos por permisos, bloqueos de ejecucion manual no ejecutable, bloqueos de detencion, restauracion bloqueada en Papelera, bloqueo por maximo de versiones, bloqueos de version activa/unica, previsualizacion de sincronizacion de feriados y errores controlados de configuracion/ejecuciones/scripts.
* Sanitizacion: Se amplio la lista de claves sensibles para ocultar passwords, tokens, secrets, keys, api keys, credentials, cadenas de conexion y valores relacionados; `.env` por script no guarda contenido ni valores.
* Resultado esperado: Acciones exitosas quedan `OK`, bloqueos quedan `BLOQUEADO` y errores controlados quedan `ERROR`.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; prueba ligera de sanitizacion y normalizacion de acciones; render simulado de `auditoria/listado.html` y `auditoria/detalle.html`; busqueda sin coincidencias de `alert()`, `window.confirm()` y `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`; `git diff --check`.
* Reglas: No se ejecuto SQL, no se crearon migraciones, no se modifico `.env`, no se borro historial, no se agrego `DELETE CASCADE`, no se implementaron exportaciones/notificaciones/reportes y no se avanzo a Fase 12C ni Fase 13.

### 2026-06-18 - Fase 12A.2 / Validacion transversal de duplicados con Papelera Operativa

* Archivos creados: `app/servicios/servicio_duplicados.py`.
* Archivos modificados: `app/repositorios/repositorio_usuarios.py`, `app/repositorios/repositorio_mantenedores.py`, `app/repositorios/repositorio_tareas.py`, `app/repositorios/repositorio_scripts.py`, `app/servicios/servicio_usuarios.py`, `app/servicios/servicio_mantenedores.py`, `app/servicios/servicio_tareas.py`, `app/servicios/servicio_scripts.py`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `docs/UI_UX.md`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se agrego validacion transversal para detectar duplicados activos, inactivos o en Papelera antes de guardar usuarios, mantenedores, tareas, scripts y versiones.
* Detalle tecnico: Usuarios valida `usuario` y `email`; mantenedores valida `nombre_normalizado`; tareas valida `nombre_tarea + cliente + categoria + tipo`; scripts valida `id_tarea`; versiones valida `id_script + numero_version` y calcula `v1` a `v3` incluyendo Papelera.
* Auditoria: Los bloqueos registran `BLOQUEO_DUPLICADO` con resultado `BLOQUEADO` cuando auditoria esta disponible.
* UX: Los errores de constraint unica se traducen a mensaje seguro sin `pyodbc`, nombre de constraint ni traceback.
* Pruebas realizadas: `python -m compileall app`; prueba ligera de clasificacion/mensaje de duplicados; `git diff --check`; busqueda sin coincidencias de `alert()`, `window.confirm()`, `prompt()` en `app`; busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`.
* Reglas: No se ejecuto SQL, no se crearon migraciones, no se modifico `.env`, no se borro historial, no se agrego `DELETE CASCADE`, no se cambio Papelera ni Scheduler y no se avanzo a Fase 12B ni Fase 13.

### 2026-06-18 - Fase 12A.1 / Correccion visual Auditoria y roles

* Archivos modificados: `app/repositorios/repositorio_auditoria.py`, `app/servicios/servicio_auditoria.py`, `app/templates/auditoria/detalle.html`, `app/static/css/estilos.css`, `app/rutas_usuarios.py`, `app/repositorios/repositorio_usuarios.py`, `app/servicios/servicio_usuarios.py`, `app/templates/usuarios/formulario.html`, `app/templates/usuarios/listado.html`, `docs/SEGURIDAD.md`, `docs/MODULOS.md`, `docs/UI_UX.md`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se redisenio el detalle de auditoria con bloques legibles y valores antes/despues formateados; se reforzo backend contra escalamiento a `SUPER_ADMIN`.
* Reglas de roles: Solo `SUPER_ADMIN` puede asignar/quitar `SUPER_ADMIN`; `ADMIN` no puede modificar, desactivar ni borrar `SUPER_ADMIN`; no se puede desactivar/borrar el usuario conectado ni el ultimo `SUPER_ADMIN` activo; `SUPER_ADMIN` puede administrar `ADMIN` si queda capacidad administrativa.
* Usuario `.env`: Se mantiene como bootstrap tecnico fuera de BD, sin forzar su creacion ni administrarlo desde `/usuarios`.
* Reglas: No se ejecuto SQL, no se modifico `.env`, no se cambio Papelera ni Scheduler, no se borro historial y no se avanzo a Fase 12B ni Fase 13.

### 2026-06-18 - Fase 12A / Auditoria base

* Archivos creados: `app/repositorios/repositorio_auditoria.py`, `app/servicios/servicio_auditoria.py`, `app/rutas_auditoria.py`, `app/templates/auditoria/listado.html`, `app/templates/auditoria/detalle.html`, `database/migrations/018_crear_o_ajustar_auditoria_cambios.sql`, `database/seeds/012_permisos_auditoria.sql`.
* Archivos modificados: `app/__init__.py`, `app/templates/base.html`, servicios de papelera, usuarios, mantenedores, tareas, scripts, ejecuciones, control de ejecuciones, scheduler, calendario y sincronizacion de feriados, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `docs/UI_UX.md`, `docs/ARQUITECTURA.md`, `log_codex.md`.
* Que se hizo: Se implemento modulo `/auditoria` con filtros, paginacion, detalle, permisos y servicio central `registrar_auditoria(...)`.
* Cobertura inicial: papelera, eliminacion permanente, borrados operativos, usuarios, mantenedores, tareas, scripts/versiones/env, ejecucion manual, detencion, verificacion huerfana, scheduler y feriados.
* Reglas: No se ejecuto SQL, no se modifico `.env`, no se borro historial, no se agrego `DELETE CASCADE`, no se avanzo a Fase 12B ni Fase 13.

### 2026-06-18 - Fase 11I / Revision integral post-borrado y desacople historico

* Archivos creados: `database/diagnostics/004_validacion_post_desacople_historico.sql`.
* Archivos modificados: `app/repositorios/repositorio_ejecuciones.py`, `app/repositorios/repositorio_panel.py`, `app/repositorios/repositorio_panel_scheduler.py`, `app/repositorios/repositorio_scheduler_eventos.py`, `app/templates/ejecuciones/listado.html`, `app/templates/ejecuciones/consola.html`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se hizo: Se revisaron consultas historicas post Fase 11H y se reforzo el uso de snapshots/fallbacks para ejecuciones desacopladas.
* Problemas encontrados: Algunas expresiones historicas podian quedar en `NULL` si el maestro operativo ya no existia; el filtro de usuario no consideraba `usuario_ejecucion_snapshot`; paneles/eventos podian mostrar tarea vacia si el maestro fue eliminado.
* Correcciones: `/ejecuciones`, `/ejecuciones/<id>`, panel principal, panel programador y eventos usan fallback claro; consola/listado muestran badge `Snapshot historico` cuando aplica.
* Validacion reportada por usuario: `id_ejecucion = 14` quedo con `id_tarea`, `id_script` e `id_version` en `NULL` y snapshots completos de `Prueba5`.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; render de `ejecuciones/listado.html` y `ejecuciones/consola.html` con datos simulados de ejecucion 14 desacoplada; busqueda de `INNER JOIN` en repositorios historicos; busqueda de fallbacks historicos.
* No ejecutado: No se ejecuto SQL manual ni scripts de migracion; no se ejecuto `scheduler_worker.py --once` porque escribe heartbeat/eventos; la validacion real de rutas con DB quedo bloqueada por error ODBC local de cifrado/credenciales.
* Reglas: No se borro historial, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-18 - Fase 11H / Desacople historico para eliminacion permanente real

* Archivos creados: `database/migrations/017_desacople_historico_papelera.sql`, `database/diagnostics/003_diagnostico_desacople_historico.sql`.
* Archivos modificados: `app/repositorios/repositorio_papelera.py`, `app/servicios/servicio_papelera.py`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se desacoplaron por diseno las referencias historicas de `ejecuciones` y `logs_tareas` para que la papelera pueda borrar fisicamente registros operativos sin borrar historia.
* Por que se hizo: Las FKs historicas contra `tareas`, `scripts` y `scripts_versiones` impedian la eliminacion permanente real aunque existieran snapshots.
* Decisiones tomadas: Mantener `logs_tareas.id_ejecucion` como FK historica valida; volver anulables solo IDs historicos; no tocar FKs operativas vivas; bloquear `/papelera` si la migracion 017 no esta aplicada o si faltan snapshots.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; busqueda sin `alert()`, `window.confirm()`, `confirm()` ni `prompt()` en `app`; busqueda sin `DELETE CASCADE` en `app` y SQL nuevo; `git diff --check`.
* Riesgos detectados: La migracion 017 debe aplicarse manualmente despues de la 016 y del seed 011; sin esa ejecucion, la UI bloqueara la eliminacion permanente de tareas, scripts y versiones.
* Proximos pasos: Ejecutar manualmente `database/diagnostics/003_diagnostico_desacople_historico.sql`, aplicar `database/migrations/017_desacople_historico_papelera.sql` en SSMS y repetir diagnostico antes de validar `/papelera` con datos reales.

### 2026-06-18 02:25 - Correccion post Fase 11G suma BIT en papelera

* Archivos modificados: `app/repositorios/repositorio_papelera.py`, `docs/CHANGELOG.md`, `log_codex.md`.
* Causa: SQL Server no permite sumar columnas `bit` directamente. `/papelera` fallaba en `_dependencias_tarea()` al sumar `eliminado_operativo` de cliente, categoria y tipo.
* Correccion: Se convirtieron esos `bit` con `CAST(ISNULL(..., 0) AS INT)` antes de sumarlos.
* Alcance: No se cambio la logica funcional de papelera, restauracion ni eliminacion permanente segura.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; busqueda de sumas directas de `eliminado_operativo` en `repositorio_papelera.py`; busqueda sin `alert()`, `window.confirm()`, `confirm()`, `prompt()` ni `DELETE CASCADE` en `app`.
* Reglas: No se ejecuto SQL, no se modifico `.env`, no se borro historial, no se implemento Auditoria y no se avanzo a Fase 11H ni Fase 12A.

### 2026-06-18 02:10 - Fase 11G papelera operativa funcional

* Archivos creados: `app/repositorios/repositorio_papelera.py`, `app/servicios/servicio_papelera.py`, `app/rutas_papelera.py`, `app/templates/papelera/listado.html`, `database/seeds/011_permisos_papelera.sql`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/templates/base.html`, `app/static/css/estilos.css`, `app/servicios/servicio_mantenedores.py`, `app/repositorios/repositorio_mantenedores.py`, `app/servicios/servicio_tareas.py`, `app/servicios/servicio_scripts.py`, `app/servicios/servicio_usuarios.py`, `README.md`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/ROADMAP.md`, `docs/BASE_DATOS.md`, `docs/SEGURIDAD.md`, `docs/ARQUITECTURA.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se hizo: Se implemento funcionalmente `/papelera` con filtros, paginacion simple, restauracion como inactivo y eliminacion permanente segura.
* Sidebar: Se reorganizo por grupos funcionales: Administracion, Operacion, Programador y Control y trazabilidad. Papelera operativa queda dentro de Administracion.
* Entidades soportadas: usuarios, clientes, categorias, tipos, tareas, scripts y scripts_versiones.
* Borrado normal: Usuarios, mantenedores, tareas, scripts y versiones se retiran operativamente; la eliminacion permanente queda solo en Papelera.
* Seguridad: No se borran ejecuciones, logs, eventos del programador, snapshots, `auditoria_cambios` ni archivos historicos.
* Permisos: Se creo seed manual `database/seeds/011_permisos_papelera.sql` para `PAPELERA_VER`, `PAPELERA_RESTAURAR` y `PAPELERA_ELIMINAR_PERMANENTE`.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; verificacion de rutas Flask de papelera; render de `papelera/listado.html` con datos simulados; busqueda de `alert()`, `window.confirm()`, `confirm()` y `prompt()` en app; `git diff --check`.
* Reglas: No se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria, no se avanzo a Fase 11H ni a Fase 12A.

### 2026-06-18 01:20 - Ajuste diseno Fase 11G eliminacion permanente segura

* Archivos modificados: `README.md`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/ROADMAP.md`, `docs/BASE_DATOS.md`, `docs/SEGURIDAD.md`, `docs/UI_UX.md`, `log_codex.md`.
* Que se hizo: Se ajusto el diseno documental de Fase 11G para que `/papelera` tenga dos acciones claras: `Restaurar` y `Eliminar permanentemente`.
* Eliminacion permanente: Debe borrar fisicamente solo desde tablas operativas o maestras cuando sea seguro, y hacer desaparecer el registro de papelera, mantenedores, selects, candidatos del scheduler y paneles operativos.
* Historial protegido: No debe borrar `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots historicos, futura `auditoria_cambios` ni archivos historicos de log.
* UX: Se documento el modal corporativo fuerte obligatorio, sin `alert()`, `window.confirm()` ni `prompt()`, y el mensaje exacto para dependencias operativas no historicas.
* Reglas: No se modifico codigo funcional, no se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-18 01:05 - Reorganizacion formal del roadmap

* Archivos creados: `docs/ROADMAP.md`.
* Archivos modificados: `README.md`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `docs/UI_UX.md`, `docs/README_PROYECTO.md`, `log_codex.md`.
* Que se hizo: Se reorganizo documentalmente el roadmap del proyecto en Fase 11 robustez operativa interna, Fase 12 Auditoria, Fase 13 operacion/despliegue y Fase 14 mantenimiento avanzado.
* Estado documentado: Se deja como implementado hasta Fase 11F, incluyendo login hibrido, usuarios/roles/permisos, mantenedores, tareas, scripts versionados, `.env` por script, ejecucion manual, consola, detencion, historial, scheduler automatico, configuracion del programador, worker separado, heartbeat, feriados locales, sincronizacion Nager.Date, eventos del programador, resumen inteligente, historial filtrable, UI/UX modernizada, control de ejecuciones huerfanas, borrado operativo seguro y TOP 6 ultimas ejecuciones en panel.
* Pendientes criticos: Fase 11G papelera/restauracion/eliminacion permanente segura, Fase 11H purga controlada, Fase 11I revision integral post-borrado y Fase 12A Auditoria base.
* Decisiones: `scheduler_eventos`, `ejecuciones`, `logs_tareas` y `logs_sistema` no reemplazan Auditoria; `auditoria_cambios` queda para acciones humanas criticas en Fase 12.
* Reglas: No se modifico codigo funcional, no se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-18 00:40 - Diagnostico disponibilidad tareas post Fase 11F

* Archivos creados: `database/diagnostics/001_diagnostico_tareas_scripts_post_11f.sql`.
* Archivos modificados: `app/servicios/servicio_tareas.py`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `log_codex.md`.
* Causa tecnica revisada: `/tareas` se alimenta de `repositorio_tareas.listar_tareas()`, con `LEFT JOIN` sin filtros a `scripts` y `scripts_versiones`; la disponibilidad se calcula en `servicio_tareas._enriquecer_disponibilidad_ejecucion()`.
* Hallazgo: El modelo real de versiones usa `estado_version` y `es_activa`; no existen campos operativos `scripts_versiones.estado` ni `scripts_versiones.activo` en el esquema versionado.
* Correccion: Cuando no existe fila de script asociada, el motivo visible queda como `Sin script asociado`; `Script inactivo` queda reservado para `scripts.activo = 0`.
* Diagnostico: Se agrego SQL manual de solo lectura para revisar Prueba, Prueba2 y Prueba5 contra tarea, script, version activa y ejecuciones en curso.
* Reglas: No se tocaron datos, no se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-18 00:20 - Correccion UX ejecutar ahora en listado de tareas

* Archivos modificados: `app/repositorios/repositorio_tareas.py`, `app/servicios/servicio_tareas.py`, `app/templates/tareas/listado.html`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `log_codex.md`.
* Causa encontrada: `/tareas` deshabilitaba `Ejecutar ahora` con una condicion parcial en el template y el repositorio no entregaba todos los campos necesarios para explicar la causa.
* Que se corrigio: El repositorio entrega estado operativo de tarea, script, version y ejecuciones en curso; el servicio calcula `ejecutable`, `motivo_no_ejecutable` y `disponibilidad_ejecucion`.
* UI: El listado muestra `Ejecutable` o `No ejecutable: motivo`; el boton deshabilitado usa el mismo motivo en el `title`.
* Reglas: No se tocaron datos, no se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-18 00:00 - Correccion validacion ejecucion manual post Fase 11F

* Archivos modificados: `app/repositorios/repositorio_ejecuciones.py`, `app/servicios/servicio_ejecuciones.py`, `docs/CHANGELOG.md`, `log_codex.md`.
* Causa encontrada: La consulta de contexto de ejecucion filtraba `eliminado_operativo` en el repositorio y la validacion mezclaba `activo` con `estado_tarea` bajo un mensaje generico de tarea inactiva.
* Que se corrigio: El repositorio devuelve contexto completo de tarea/script/version, incluyendo campos de borrado operativo; el servicio valida cada condicion por separado.
* Mensajes especificos: tarea inactiva, tarea borrada operativamente, script inactivo, script borrado operativamente, version faltante, version borrada, version no disponible y ejecucion en curso.
* Reglas: No se tocaron datos, no se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-17 18:20 - Fase 11F / Borrado operativo seguro con snapshots

* Archivos creados: `database/migrations/016_agregar_snapshots_historial_borrado_operativo.sql`.
* Archivos modificados: `app/repositorios/repositorio_tareas.py`, `app/servicios/servicio_tareas.py`, `app/repositorios/repositorio_scripts.py`, `app/servicios/servicio_scripts.py`, `app/repositorios/repositorio_usuarios.py`, `app/servicios/servicio_usuarios.py`, `app/rutas_usuarios.py`, `app/repositorios/repositorio_mantenedores.py`, `app/servicios/servicio_mantenedores.py`, `app/repositorios/repositorio_ejecuciones.py`, `app/repositorios/repositorio_scheduler.py`, `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`, `app/repositorios/repositorio_panel.py`, `app/repositorios/repositorio_panel_scheduler.py`, templates de usuarios/mantenedores/tareas/scripts y documentacion.
* Que se hizo: Se implemento borrado operativo seguro para tareas, scripts, versiones, usuarios, clientes, categorias y tipos.
* Historial: `ejecuciones` conserva snapshots de tarea, cliente, categoria, tipo, script, archivo, version y usuario; `scheduler_eventos` conserva snapshots de tarea y contexto.
* Operacion normal: registros con `eliminado_operativo = 1` no aparecen en mantenedores, selects, candidatos del scheduler ni metricas principales.
* Borrado fisico: se mantiene para registros sin historial cuando no rompe integridad.
* Bloqueos: tarea con ejecucion `EN_EJECUCION`, usuario actualmente conectado y ultimo administrador activo.
* Reglas: No se borran ejecuciones, logs historicos ni eventos del programador; no se ejecuto SQL; no se modifico `.env`; no se implemento Auditoria; no se avanzo a Fase 12A.

### 2026-06-17 17:35 - Control de ejecuciones huerfanas

* Archivos creados: `app/servicios/servicio_control_ejecuciones.py`.
* Archivos modificados: `app/repositorios/repositorio_ejecuciones.py`, `app/rutas_ejecuciones.py`, `app/templates/ejecuciones/consola.html`, `app/servicios/servicio_panel.py`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/ARQUITECTURA.md`, `log_codex.md`.
* Causa probable: La ejecucion se lanza con `subprocess.Popen` y se monitorea desde un hilo en memoria del proceso Flask; si Flask se reinicia/cierra o falla el update final, la fila puede quedar `EN_EJECUCION` aunque el PID ya no exista.
* Que se hizo: Se agrego verificacion de PID y control para marcar como `ERROR` una ejecucion huerfana, completando termino, duracion y mensaje.
* UI: La consola muestra boton `Verificar ejecucion` para ejecuciones en curso.
* Panel: `/panel` solicita explicitamente `listar_ultimas_ejecuciones(limite=6)`.
* Reglas: No se matan procesos automaticamente, no se crean ejecuciones, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-17 17:05 - Fase 11D.2 / Historial filtrable de eventos del programador

* Archivos creados: `app/templates/scheduler/eventos.html`.
* Archivos modificados: `app/rutas_scheduler.py`, `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`, `app/templates/base.html`, `app/templates/scheduler/panel.html`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/BASE_DATOS.md`, `log_codex.md`.
* Que se hizo: Se creo `/scheduler/eventos` para consultar eventos activos con filtros y paginacion server-side.
* Filtros: fecha desde, fecha hasta, tarea, tipo evento, decision, motivo, proceso y texto libre en detalle/clave/feriado.
* Paginacion: opciones 10, 25, 50 y 100; orden `fecha_evento DESC, id_evento DESC`.
* Accesos: Sidebar `Eventos programador` y boton `Ver historial de eventos` en `/scheduler/panel`.
* No implementado: No se creo migracion, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria, no se crearon ejecuciones para omisiones y no se avanzo a Fase 12A.

### 2026-06-17 16:40 - Fase 11D.1 / Resumen inteligente y retencion de eventos

* Archivos creados: Ninguno.
* Archivos modificados: `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`, `app/servicios/servicio_panel_scheduler.py`, `app/templates/scheduler/panel.html`, `app/static/css/estilos.css`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/BASE_DATOS.md`, `log_codex.md`.
* Que se hizo: `/scheduler/panel` muestra resumen de eventos del dia, omisiones por motivo y ultimos 10 eventos relevantes.
* Criterio: Se priorizan errores, tareas ejecutadas y omisiones por feriado, ejecucion en curso, duplicado de slot y limite de concurrencia; ciclos y fuera de ventana quedan resumidos para evitar ruido.
* Retencion: Se agrego `limpiar_eventos_antiguos(dias_retencion=90)`, que marca `activo = 0` y no borra fisicamente.
* No implementado: No se creo `/scheduler/eventos`, no se implemento Auditoria, no se ejecuto SQL, no se modifico `.env`, no se crearon migraciones y no se avanzo a Fase 12A.

### 2026-06-17 16:20 - Ajuste Fase 11D / Visualizacion de eventos del programador

* Archivos creados: Ninguno.
* Archivos modificados: `app/servicios/servicio_panel_scheduler.py`, `app/templates/scheduler/panel.html`, `docs/CHANGELOG.md`, `docs/MODULOS.md`, `log_codex.md`.
* Causa: La vista usaba un nombre generico para los eventos y no exponia todos los campos solicitados; se dejo un contrato claro `eventos_programador` para la seccion del panel.
* Que se hizo: `/scheduler/panel` ahora muestra la seccion `Eventos recientes del programador` debajo del estado del proceso programador, con fecha, tarea, tipo evento, decision, motivo, detalle y proceso.
* Datos: Los eventos se obtienen desde `scheduler_eventos`, ultimos 10 registros activos, ordenados por `fecha_evento DESC, id_evento DESC`.
* No implementado: No se crearon migraciones nuevas, no se ejecuto SQL, no se modifico `.env`, no se implemento Auditoria y no se avanzo a Fase 12A.

### 2026-06-17 16:02 - Fase 11D / Eventos y omisiones del programador

* Archivos creados: `database/migrations/015_crear_eventos_programador.sql`, `app/repositorios/repositorio_scheduler_eventos.py`, `app/servicios/servicio_scheduler_eventos.py`.
* Archivos modificados: `app/servicios/servicio_scheduler_worker.py`, `app/servicios/servicio_panel_scheduler.py`, `app/templates/scheduler/panel.html`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se agrego trazabilidad operativa del programador en tabla dedicada `scheduler_eventos`, con eventos de ciclo, ejecucion, omision y error controlado.
* Decisiones: Las omisiones no crean `ejecuciones` ni `logs_tareas`; `logs_sistema` no se usa para cada omision; el heartbeat queda separado.
* Migracion: `015_crear_eventos_programador.sql` fue creada para ejecucion manual en SSMS; Codex no ejecuto SQL.
* No implementado: No se implemento auditoria funcional, no se conectaron APIs nuevas, no se modifico `.env`, no se inicio/detuvo worker desde la app y no se avanzo a Fase 12A.
* Pruebas recomendadas: Ejecutar migracion 015, correr `python scheduler_worker.py --once`, validar eventos `FERIADO`, `EJECUCION_EN_CURSO`, `DUPLICADO_SLOT`, `LIMITE_CONCURRENCIA`, `TAREA_EJECUTADA` y revisar `/scheduler/panel`.

### 2026-06-17 00:00 - Fase 11C / Modernizacion visual UI UX general

* Archivos creados: Ninguno.
* Archivos modificados: `app/static/css/estilos.css`, `app/templates/base.html`, `app/templates/panel.html`, `app/templates/scheduler/panel.html`, `app/templates/scheduler/configuracion.html`, `app/templates/ejecuciones/listado.html`, `app/templates/ejecuciones/consola.html`, `app/templates/feriados/listado.html`, `app/templates/feriados/formulario.html`, `app/templates/feriados/sincronizar.html`, `app/templates/tareas/listado.html`, `app/templates/tareas/formulario.html`, `app/templates/scripts/listado.html`, `app/templates/diagnostico_bd.html`, `app/servicios/servicio_worker_heartbeat.py`, `app/servicios/servicio_panel.py`, `app/servicios/servicio_panel_scheduler.py`, `README.md`, `docs/UI_UX.md`, `docs/MODULOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se modernizo visualmente la interfaz general con mejoras en sidebar, topbar, botones, cards, tablas, formularios, filtros, modales, toasts, consola e historial agrupado.
* Textos visibles: Se reemplazo `Scheduler` por `Programador`, `Worker` por `Proceso programador` y `Heartbeat` por `Senal de vida` donde corresponde en la UI; se retiraron etiquetas de fase visibles en pantallas operativas.
* Decisiones: Mantener HTML/CSS/JS sin dependencias nuevas y no cambiar rutas, permisos, consultas ni reglas de negocio.
* No implementado: No se crearon migraciones, no se ejecuto SQL, no se modifico `.env`, no se agregaron funcionalidades del scheduler y no se implemento iniciar/detener worker desde la app.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; busqueda sin `alert()`, `window.confirm()`, `confirm()` ni `prompt()` en templates/JS; busqueda sin textos visibles obsoletos principales (`Scheduler panel`, `Scheduler config`, `Panel logs`, `Logs en vivo`, etiquetas `Fase` en templates); render Jinja de `panel.html`, `scheduler/panel.html`, `scheduler/configuracion.html`, `ejecuciones/listado.html` y `ejecuciones/consola.html`; verificacion de rutas registradas `/login`, `/panel`, `/scheduler/panel`, `/scheduler/configuracion`, `/usuarios/`, `/clientes/`, `/categorias/`, `/tipos/`, `/tareas/`, `/ejecuciones`, `/feriados/` y `/feriados/sincronizar`; `git diff --check`.
* Pruebas recomendadas: Validar visualmente en navegador login, panel, programador, usuarios, mantenedores, tareas, scripts, ejecuciones, consola, feriados, modales y responsive basico.

### 2026-06-17 00:00 - Fase 11B / Heartbeat del worker scheduler

* Archivos creados: `database/migrations/014_crear_scheduler_worker_heartbeat.sql`, `app/repositorios/repositorio_worker_heartbeat.py`, `app/servicios/servicio_worker_heartbeat.py`.
* Archivos modificados: `scheduler_worker.py`, `app/servicios/servicio_scheduler_worker.py`, `app/servicios/servicio_panel_scheduler.py`, `app/templates/scheduler/panel.html`, `app/servicios/servicio_panel.py`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento heartbeat del worker en tabla dedicada, con registro de inicio, ciclo, error, detencion y contadores del ultimo ciclo.
* Panel: `/scheduler/panel` muestra estado del worker, ultimo heartbeat, tiempo sin senal, ultimo ciclo, resultado, contadores, PID, host y ultimo error.
* Decisiones: No se registra `logs_sistema` por cada heartbeat; los logs quedan para inicio, detencion, error, recuperacion o fallo al actualizar heartbeat.
* Migracion: `014_crear_scheduler_worker_heartbeat.sql` fue creada para ejecucion manual en SSMS; Codex no ejecuto SQL.
* No implementado: No se agrego control para iniciar/detener worker desde la app, no se conectaron nuevas APIs, no se modifico `.env` y no se avanzo a Fase 11C.
* Pruebas recomendadas: Ejecutar migracion 014, correr `python scheduler_worker.py --once`, verificar tabla `scheduler_worker_heartbeat`, levantar `python scheduler_worker.py` en loop y revisar `/scheduler/panel`.

### 2026-06-17 00:00 - Fase 11A.1 / Panel principal general

* Archivos creados: `app/repositorios/repositorio_panel.py`, `app/servicios/servicio_panel.py`.
* Archivos modificados: `app/rutas.py`, `app/templates/panel.html`, `app/static/css/estilos.css`, `README.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se actualizo `/panel` para eliminar textos simulados de fases antiguas y mostrar metricas reales de tareas, scripts, ejecuciones, scheduler y feriados desde SQL Server.
* Metricas: Total de tareas, tareas activas, scripts activos, tareas con script asociado, ejecuciones del dia, exitosas, errores, en curso, feriados activos del anio y ultima ejecucion.
* Interfaz: Se agregaron accesos rapidos segun permisos y tabla de ultimas ejecuciones con enlace a consola.
* Decisiones: El panel carga con advertencia controlada si alguna consulta falla; no expone secretos ni detalles sensibles.
* No implementado: No se agrego heartbeat del worker, no se modifico `.env`, no se ejecuto SQL y no se avanzo a Fase 11B.
* Pruebas recomendadas: Abrir `/panel`, validar ausencia de textos obsoletos, revisar metricas contra SQL Server local, abrir consola desde una ejecucion y confirmar accesos a scheduler/feriados.

### 2026-06-17 00:00 - Fase 11A / Panel operativo del scheduler

* Archivos creados: `app/repositorios/repositorio_panel_scheduler.py`, `app/servicios/servicio_panel_scheduler.py`, `app/templates/scheduler/panel.html`.
* Archivos modificados: `app/rutas_scheduler.py`, `app/templates/base.html`, `README.md`, `docs/ARQUITECTURA.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento `/scheduler/panel` como dashboard operativo de solo lectura para monitorear configuracion, ejecuciones automaticas, errores recientes, tareas candidatas y feriados locales.
* Permisos: Reutiliza `SCHEDULER_CONFIG_VER`.
* Decisiones: No se crea migracion ni seed nuevo; no se inicia/detiene worker desde la app; la edicion de configuracion sigue en `/scheduler/configuracion`.
* No implementado: No se conectaron nuevas APIs externas, no se implementaron notificaciones y no se avanzo a Fase 11B.
* Proximos pasos: Validar visualmente `/scheduler/panel` con datos reales de SQL Server local.

### 2026-06-17 00:00 - Correccion Fase 10B / Preview de sincronizacion

* Archivos creados: Ninguno.
* Archivos modificados: `app/servicios/servicio_sincronizacion_feriados.py`, `app/templates/feriados/sincronizar.html`, `docs/CHANGELOG.md`, `log_codex.md`.
* Causa: El template usaba `preview.items`; al ser `preview` un diccionario, Jinja resolvia `items` como el metodo interno `dict.items` y no como lista iterable.
* Que se hizo: Se reemplazo la clave `items` por `feriados_preview` en la estructura de preview, en el template y en `aplicar_sincronizacion()`.
* Reglas preservadas: Prioridad `MANUAL` sobre `API_NAGER`, actualizacion solo de `API_NAGER`, irrenunciables por reglas locales y scheduler sin consulta a internet.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; render de preview con datos simulados; aplicacion simulada de sincronizacion; busqueda sin referencias Nager/requests en worker; busqueda sin `alert()`, `window.confirm()`, `confirm()` ni `prompt()`.
* Validacion en app reportada: `/feriados/sincronizar` carga correctamente; consultar `2026 / CL` ya no genera `TypeError`; la vista previa renderiza usando `preview.feriados_preview`; se muestran feriados de Nager.Date; irrenunciables se calculan por reglas locales; `MANUAL` mantiene prioridad sobre `API_NAGER`; aplicar sincronizacion funciona; no se duplican fecha + pais.
* No implementado: No se ejecuto SQL, no se modifico `.env`, no se agregaron funcionalidades y no se avanzo a Fase 10C.

### 2026-06-17 00:00 - Fase 10B / Sincronizacion controlada de feriados

* Archivos creados: `database/migrations/013_crear_reglas_feriados_irrenunciables.sql`, `database/seeds/009_reglas_irrenunciables_chile.sql`, `database/seeds/010_permisos_sincronizacion_feriados.sql`, `app/repositorios/repositorio_reglas_feriados.py`, `app/servicios/cliente_nager_date.py`, `app/servicios/servicio_sincronizacion_feriados.py`, `app/templates/feriados/sincronizar.html`.
* Archivos modificados: `requirements.txt`, `app/repositorios/repositorio_feriados.py`, `app/rutas_feriados.py`, `app/templates/base.html`, `app/templates/feriados/listado.html`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento sincronizacion manual desde Nager.Date con vista previa, reglas locales de irrenunciables, prioridad de feriados `MANUAL` y aplicacion confirmada hacia la tabla local `feriados`.
* Base de datos: Se creo migracion 013 para tabla `reglas_feriados_irrenunciables` y ajuste de origen `API_NAGER`; se crearon seeds 009 y 010. Codex no ejecuto SQL.
* Permisos: Se agrego permiso propuesto `FERIADOS_SINCRONIZAR` para SUPER_ADMIN, ADMIN y TI mediante seed 010.
* Reglas: `MANUAL` no se sobrescribe; `API_NAGER` se inserta o actualiza; inactivos no se reactivan automaticamente; irrenunciables se calculan por reglas locales, no por Nager.Date.
* Scheduler: No se modifico `scheduler_worker.py` para consultar internet; sigue usando `servicio_calendario.es_feriado()` contra SQL Server.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; render de `feriados/sincronizar.html`; verificacion de rutas de feriados; consulta real a Nager.Date `2026/CL` con 17 registros; prueba de irrenunciable por regla simulada; prueba de clasificacion `NUEVO`, `MANUAL_NO_SOBRESCRIBE`, `ACTUALIZAR` y `SIN_CAMBIOS`; busqueda sin `alert()`, `window.confirm()`, `confirm()` ni `prompt()`; verificacion de que el worker no referencia Nager.Date.
* No implementado: No se implemento sincronizacion automatica programada, no se implementaron notificaciones y no se avanzo a Fase 10C.
* Riesgos detectados: Requiere instalar `requests` con `pip install -r requirements.txt` y ejecutar migracion/semillas nuevas antes de probar con usuarios de base de datos.
* Proximos pasos: Ejecutar scripts 013, 009 y 010 en SSMS; probar preview CL 2026 y confirmar sincronizacion controlada.

### 2026-06-16 00:00 - Fase 10A / Migracion 012 y seed 008 validados localmente

* Archivos creados: Ninguno.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se registro que `database/migrations/012_crear_calendario_feriados.sql` y `database/seeds/008_permisos_feriados.sql` fueron ejecutados correctamente en SQL Server local.
* Validaciones reportadas: Tabla `feriados` creada; permisos `FERIADOS_*` insertados; `/feriados` carga; crear, editar, activar y desactivar feriados funciona; no se permite duplicar fecha + pais activa.
* Validacion de servicio: `servicio_calendario.es_feriado` retorna `True` cuando existe feriado activo y `False` cuando no existe feriado activo.
* Validacion scheduler: Omite ejecucion automatica si `ejecutar_en_feriados = 0` y la fecha es feriado; permite ejecutar si `ejecutar_en_feriados = 1`.
* Validacion manual: La ejecucion manual no se bloquea por feriados.
* No implementado: No se conecto API externa, no se implemento sincronizacion automatica y no se avanzo a Fase 10B.
* Proximos pasos: Esperar aprobacion explicita antes de iniciar Fase 10B.

### 2026-06-16 00:00 - Fase 10A / Calendario local de feriados

* Archivos creados: `database/migrations/012_crear_calendario_feriados.sql`, `database/seeds/008_permisos_feriados.sql`, `app/repositorios/repositorio_feriados.py`, `app/rutas_feriados.py`, `app/templates/feriados/listado.html`, `app/templates/feriados/formulario.html`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/templates/base.html`, `app/servicios/servicio_calendario.py`, `app/servicios/servicio_scheduler_worker.py`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento calendario local de feriados con tabla propuesta, permisos, mantenedor `/feriados`, servicios de consulta y validacion, y uso desde el worker automatico.
* Regla scheduler: Si `ejecutar_en_feriados = 0` y existe feriado activo local, la tarea automatica se omite y registra `WORKER_TAREA_OMITIDA_FERIADO`; si `ejecutar_en_feriados = 1`, se permite ejecutar.
* Base de datos: Se crearon scripts 012 y seed 008 para ejecucion manual en SSMS; Codex no ejecuto SQL.
* No implementado: No se conecto API externa, no se implemento sincronizacion automatica, no se implementaron notificaciones y no se avanzo a Fase 10B.
* Riesgos detectados: `/feriados` requiere aplicar migracion 012 antes de usar contra BD real; usuarios de base de datos requieren seed 008 para permisos.
* Proximos pasos: Ejecutar scripts 012 y 008 en SSMS, crear feriado local de prueba y validar `python scheduler_worker.py --once`.

### 2026-06-16 00:00 - Ajuste visual Fase 9D / Sin resumen de totales

* Archivos creados: Ninguno.
* Archivos modificados: `app/templates/ejecuciones/listado.html`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se elimino de `/ejecuciones` el bloque visual de resumen `Total`, `Exitosas`, `Errores`, `En ejecucion` y `Detenidas`.
* Decisiones: Se mantiene el total de registros filtrados en header y paginacion; se conservan filtros, paginacion y agrupacion por ano/mes/dia.
* Base de datos: No se creo migracion.
* No implementado: No se avanzo a Fase 10.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; render de `ejecuciones/listado.html` confirmando agrupacion y boton `Ver consola`; busqueda sin `Total`, `Exitosas`, `Errores`, `En ejecucion`, `Detenidas` ni `card-metrica` en el template.

### 2026-06-16 00:00 - Fase 9D / Historial agrupado de ejecuciones

* Archivos creados: Ninguno.
* Archivos modificados: `app/repositorios/repositorio_ejecuciones.py`, `app/servicios/servicio_ejecuciones.py`, `app/rutas_ejecuciones.py`, `app/templates/ejecuciones/listado.html`, `app/static/css/estilos.css`, `README.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se transformo `/ejecuciones` desde tabla plana a vista historica agrupada por ano, mes y dia.
* Filtros: ID ejecucion, tarea, origen, estado, ano, mes, dia, fecha desde, fecha hasta, usuario y worker.
* Paginacion: Server-side con `OFFSET/FETCH`; solo se trae la pagina actual y luego se agrupa en Python.
* Resumen: Totales por estado calculados con los mismos filtros, no solo con la pagina actual.
* Orden: `fecha_hora_inicio DESC, id_ejecucion DESC`.
* Base de datos: No se creo migracion porque se reutilizan columnas existentes.
* No implementado: No se conecto API de feriados, no se implementaron notificaciones, no se creo dashboard avanzado y no se avanzo a Fase 10.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; render de `ejecuciones/listado.html` con datos agrupados simulados; prueba directa de agrupacion por `2026 / 06 - Junio / dia`; validacion de filtros invalidos; verificacion de rutas de ejecuciones; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`.
* Riesgos detectados: Validar visualmente con alto volumen real de ejecuciones para ajustar densidad de tarjetas si corresponde.
* Proximos pasos: Probar filtros y paginacion contra SQL Server local con ejecuciones reales.

### 2026-06-16 00:00 - Fase 9C / Timestamps por linea en logs de ejecucion

* Archivos creados: `app/servicios/servicio_logs_ejecucion.py`.
* Archivos modificados: `app/servicios/servicio_ejecuciones.py`, `README.md`, `docs/ARQUITECTURA.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se centralizo el formato de logs de ejecucion para que cada linea visible tenga `YYYY-MM-DD HH:mm:ss | NIVEL | mensaje`.
* Alcance: Aplica a archivo fisico de log, consola `/ejecuciones/<id_ejecucion>`, endpoint polling, ejecuciones manuales y automaticas, inicio, fin, errores y detencion manual.
* Decision tecnica: `stderr` sigue combinado con `stdout`; la salida normal del script se registra como `INFO`, errores de plataforma y retornos fallidos como `ERROR`, detenciones como `WARN`.
* Seguridad: No se muestra contenido de `.env`; los scripts no deben imprimir secretos porque stdout/stderr se conserva en consola.
* Base de datos: No se creo migracion porque el cambio es solo de formato de archivo/log visible.
* No implementado: No se conecto API de feriados, no se implementaron notificaciones, no se creo dashboard avanzado y no se avanzo a Fase 10.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; prueba directa de `formatear_linea_log()`; escritura de archivo temporal con lineas `INFO`, `WARN` y `ERROR`; verificacion de imports de `servicio_ejecuciones`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`.
* Riesgos detectados: Logs antiguos mantienen formato anterior; el nuevo formato aplica a ejecuciones nuevas.
* Proximos pasos: Probar ejecucion manual y automatica con script simple que imprima varias lineas.

### 2026-06-16 00:00 - Fase 9B / Worker automatico separado

* Archivos creados: `scheduler_worker.py`, `database/migrations/011_agregar_control_scheduler_ejecuciones.sql`, `app/repositorios/repositorio_scheduler.py`, `app/servicios/servicio_programador.py`, `app/servicios/servicio_scheduler_worker.py`, `app/servicios/servicio_calendario.py`, `app/templates/ejecuciones/listado.html`.
* Archivos modificados: `app/repositorios/repositorio_ejecuciones.py`, `app/servicios/servicio_ejecuciones.py`, `app/rutas_ejecuciones.py`, `app/templates/base.html`, `app/templates/ejecuciones/consola.html`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/MODULOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `docs/DESPLIEGUE.md`, `docs/CHANGELOG.md`, `log_codex.md`.
* Que se hizo: Se implemento worker separado ejecutable con `python scheduler_worker.py`, lectura de `configuracion_scheduler`, evaluacion de programaciones y ejecucion automatica reutilizando motor Fase 8.
* Base de datos: Se creo migracion 011 para `fecha_programada`, `clave_programacion`, `nombre_worker` e indice unico filtrado anti-duplicados.
* Reglas: Respeta `scheduler_activo`, `permitir_ejecucion_automatica`, `modo_mantenimiento`, `intervalo_revision_segundos` y `max_ejecuciones_concurrentes`.
* Programaciones: Soporta `DIARIA`, `SEMANAL`, `MENSUAL`, `FECHA_ESPECIFICA`, modos `UNA_VEZ` e `INTERVALO`; `MANUAL` no se ejecuta automaticamente.
* UX: Se agrego listado basico `/ejecuciones` y consola con origen, worker y fecha programada.
* No implementado: No se conecto API de feriados, no se implementaron notificaciones, no se creo dashboard avanzado y no se avanzo a Fase 10.
* Pruebas realizadas: `python -m compileall app scheduler_worker.py`; carga de `crear_app()` y verificacion de rutas; prueba directa de `debe_ejecutarse_ahora()` para diaria una vez.
* Riesgos detectados: No ejecutar worker continuo sin confirmar configuracion, tareas de prueba y migracion 011 aplicada.
* Proximos pasos: Ejecutar migracion 011 en SSMS y validar `python scheduler_worker.py --once` con scheduler inicialmente apagado.

### 2026-06-16 00:00 - Fase 9A / Migracion 010 y seed 007 validados localmente

* Archivos creados: Ninguno.
* Archivos modificados: `docs/CHANGELOG.md`, `docs/BASE_DATOS.md`, `docs/FLUJOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se registro que `database/migrations/010_crear_configuracion_scheduler.sql` y `database/seeds/007_permisos_scheduler.sql` fueron ejecutados correctamente en SQL Server local.
* Validaciones reportadas: Tabla `configuracion_scheduler` creada; registro inicial activo con defaults seguros; `scheduler_activo = 0`; `permitir_ejecucion_automatica = 0`; `intervalo_revision_segundos = 60`; `max_ejecuciones_concurrentes = 3`; `modo_mantenimiento = 0`.
* Permisos validados: `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR` insertados correctamente.
* Validacion funcional: `/scheduler/configuracion` carga, permite editar, muestra modal corporativo con resumen, muestra toast al guardar sin cambios, bloquea valores fuera de rango y registra cambios en `logs_sistema`.
* No implementado: No se implemento worker automatico, no se ejecutan tareas automaticas, no se conecto API de feriados y no se avanzo a Fase 9B.
* Riesgos detectados: Antes de Fase 9B se debe definir el comportamiento del worker ante errores, concurrencia, feriados y recuperacion despues de caidas.
* Proximos pasos: Preparar propuesta tecnica de Fase 9B solo cuando sea aprobada.

### 2026-06-15 00:00 - Fase 9A / Configuracion operativa del scheduler

* Archivos creados: `database/migrations/010_crear_configuracion_scheduler.sql`, `database/seeds/007_permisos_scheduler.sql`, `app/repositorios/repositorio_configuracion_scheduler.py`, `app/servicios/servicio_configuracion_scheduler.py`, `app/rutas_scheduler.py`, `app/templates/scheduler/configuracion.html`.
* Archivos modificados: `app/__init__.py`, `app/seguridad.py`, `app/templates/base.html`, `app/static/js/app.js`, `app/static/css/estilos.css`, `README.md`, `docs/ARQUITECTURA.md`, `docs/BASE_DATOS.md`, `docs/CHANGELOG.md`, `docs/DESPLIEGUE.md`, `docs/FLUJOS.md`, `docs/MODULOS.md`, `docs/SEGURIDAD.md`, `log_codex.md`.
* Que se hizo: Se implemento modulo `/scheduler/configuracion` para administrar configuracion operativa del scheduler desde SQL Server.
* Base de datos: Se creo migracion 010 con tabla `configuracion_scheduler`, defaults seguros y restriccion de una configuracion activa.
* Permisos: Se creo seed 007 con `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR`.
* Decisiones: La configuracion operativa vive en BD; `.env` queda para configuracion tecnica y secretos minimos.
* Validaciones: Intervalo entre 10 y 3600 segundos, maximo concurrentes entre 1 y 20, worker maximo 100 caracteres y descripcion maximo 500.
* UX: Pantalla con resumen, advertencias, formulario, modal con resumen de cambios y toast si no hay cambios.
* Logs: Cambios registrados en `logs_sistema` con valores anteriores/nuevos no sensibles.
* No implementado: No se creo worker automatico, no se ejecutan tareas automaticas, no se conecto API de feriados y no se avanzo a Fase 9B.
* Pruebas realizadas: `python -m compileall app`; carga de `crear_app()` y verificacion de ruta `/scheduler/configuracion`; busqueda sin `alert(`, `window.confirm`, `confirm(` ni `prompt(`; render de `scheduler/configuracion.html` con datos simulados.
* Riesgos detectados: `/scheduler/configuracion` requiere ejecutar migracion 010 antes de probar contra BD real.
* Proximos pasos: Ejecutar migracion 010 y seed 007 en SSMS, validar pantalla y mantener worker para Fase 9B.

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
* Riesgos detectados en ese momento: El modulo requeria ejecutar migracion 008 para usar los nuevos campos; la validacion local de feriados aun no existia; tampoco existia scheduler ni ejecucion real. Nota actual: feriados locales fueron implementados y validados en Fase 10A.
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
