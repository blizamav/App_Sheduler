# log_codex - Bitacora tecnica del proyecto

## 1. Estado general

* Nombre del proyecto: APP Scheduler
* Descripcion: Aplicacion web corporativa para programar, ejecutar, monitorear y auditar tareas Python de equipos TI.
* Stack actual: Python, Flask, HTML, CSS, JavaScript, python-dotenv.
* Base de datos: SQL Server local `APP_SCHEDULER_QA` creada y validada manualmente; conexion Flask-SQL Server inicial agregada con diagnostico controlado.
* Estado actual: Fase 3D implementada como conexion inicial y diagnostico, sin CRUD ni usuarios en base de datos.
* Ambiente actual: LOCAL Windows.
* Fase actual: Fase 3D - Conexion Flask con SQL Server desde .env.
* Ultima actualizacion: 2026-06-12 16:58

## 2. Decisiones tecnicas vigentes

* Backend: Flask con fabrica `crear_app()` y Blueprint principal.
* Frontend: HTML/CSS/JS sin Streamlit.
* Base de datos: SQL Server local creado con scripts versionados; conexion Flask inicial mediante `pyodbc` y `.env`.
* Autenticacion: Login inicial desde variables `USUARIO_ADMIN_DEFECTO` y `PASSWORD_ADMIN_DEFECTO`.
* Scheduler: Pendiente para Fase 8.
* Logs: Rutas configurables por `.env`, implementacion pendiente.
* Auditoria: Pendiente para Fase 10.
* Docker: Pendiente para Fase 11.
* Seguridad: Secretos y credenciales fuera del repositorio mediante `.env`.
* Versiones de scripts: No existe eliminacion fisica desde la app en primera version; se gestionan por estados `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Diseno UI/UX: Corporativo sobrio, responsive, sidebar oscuro, topbar clara, componentes reutilizables, fondo claro, azul corporativo, cyan moderado y estados por color.

## 3. Estructura actual del proyecto

* Carpetas principales: `app/`, `app/templates/`, `app/static/`, `docs/`, `database/migrations/`, `database/seeds/`.
* Archivos principales: `run.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `log_codex.md`.
* Modulos implementados: Login inicial, panel base visual, layout responsive, configuracion centralizada, modelo SQL Server con versionamiento de scripts, scripts SQL versionados ejecutados manualmente en SQL Server local, modulo inicial de conexion SQL Server y diagnostico local/QA.
* Modulos pendientes: Tareas, scripts, clientes, categorias, tipos, usuarios, roles, permisos, scheduler, logs, auditoria, Docker, calendario laboral.

## 4. Reglas del proyecto

* Reglas de codigo: Usar nombres descriptivos en espanol cuando sea razonable, Flask modular y configuracion centralizada.
* Reglas de seguridad: No versionar `.env`, logs reales, scripts cargados por usuarios ni secretos.
* Reglas de documentacion: Toda modificacion debe actualizar `docs/`, `docs/CHANGELOG.md` si aplica y `log_codex.md`.
* Reglas de diseno: UI clara, sobria, responsive, corporativa y futurista moderada.
* Reglas de base de datos: SQL Server con claves primarias, foraneas, indices y auditoria desde Fase 3.
* Reglas de despliegue: Sin rutas absolutas quemadas; usar variables de entorno.

## 5. Pendientes

* Pendiente 1: Resolver/validar conexion OK desde `/diagnostico/bd` en el entorno local del usuario si aparece error de driver/red/cifrado.
* Pendiente 2: Confirmar estrategia de reemplazo fisico de una version existente.
* Pendiente 3: Implementar conexion Flask-SQL Server y repositorios en fase posterior, sin avanzar a Fase 4.

## 6. Historial de cambios

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
