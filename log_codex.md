# log_codex - Bitacora tecnica del proyecto

## 1. Estado general

* Nombre del proyecto: APP Scheduler
* Descripcion: Aplicacion web corporativa para programar, ejecutar, monitorear y auditar tareas Python de equipos TI.
* Stack actual: Python, Flask, HTML, CSS, JavaScript, python-dotenv.
* Base de datos: SQL Server objetivo `APP_SCHEDULER_QA`, aun no implementada.
* Estado actual: Fase 1 completada y validada en base inicial funcional.
* Ambiente actual: LOCAL Windows.
* Fase actual: Fase 1 - Base del proyecto.
* Ultima actualizacion: 2026-06-12 14:24

## 2. Decisiones tecnicas vigentes

* Backend: Flask con fabrica `crear_app()` y Blueprint principal.
* Frontend: HTML/CSS/JS sin Streamlit.
* Base de datos: SQL Server sera propuesto e implementado en Fase 3.
* Autenticacion: Login inicial desde variables `USUARIO_ADMIN_DEFECTO` y `PASSWORD_ADMIN_DEFECTO`.
* Scheduler: Pendiente para Fase 8.
* Logs: Rutas configurables por `.env`, implementacion pendiente.
* Auditoria: Pendiente para Fase 10.
* Docker: Pendiente para Fase 11.
* Seguridad: Secretos y credenciales fuera del repositorio mediante `.env`.
* Diseno UI/UX: Corporativo sobrio, fondo claro, azul corporativo, cyan moderado y estados por color.

## 3. Estructura actual del proyecto

* Carpetas principales: `app/`, `app/templates/`, `app/static/`, `docs/`.
* Archivos principales: `run.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `log_codex.md`.
* Modulos implementados: Login inicial, panel base, configuracion centralizada.
* Modulos pendientes: Tareas, scripts, clientes, categorias, tipos, usuarios, roles, permisos, scheduler, logs, auditoria, Docker, calendario laboral.

## 4. Reglas del proyecto

* Reglas de codigo: Usar nombres descriptivos en espanol cuando sea razonable, Flask modular y configuracion centralizada.
* Reglas de seguridad: No versionar `.env`, logs reales, scripts cargados por usuarios ni secretos.
* Reglas de documentacion: Toda modificacion debe actualizar `docs/`, `docs/CHANGELOG.md` si aplica y `log_codex.md`.
* Reglas de diseno: UI clara, sobria, responsive, corporativa y futurista moderada.
* Reglas de base de datos: SQL Server con claves primarias, foraneas, indices y auditoria desde Fase 3.
* Reglas de despliegue: Sin rutas absolutas quemadas; usar variables de entorno.

## 5. Pendientes

* Pendiente 1: Ejecutar Fase 2 para fortalecer layout, componentes y estilos visuales.
* Pendiente 2: Proponer modelo SQL Server en Fase 3 antes de crear scripts.
* Pendiente 3: Implementar roles, permisos, logs, auditoria y scheduler en fases posteriores.

## 6. Historial de cambios

### 2026-06-12 14:24 - Fase 1 / Base inicial del proyecto

* Archivos creados: `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `run.py`, `app/__init__.py`, `app/config.py`, `app/rutas.py`, `app/templates/base.html`, `app/templates/login.html`, `app/templates/panel.html`, `app/static/css/estilos.css`, `app/static/js/app.js`, documentos en `docs/`.
* Archivos modificados: Ninguno previo; repositorio estaba vacio salvo `.git`.
* Que se hizo: Se creo la base Flask, login inicial desde `.env`, panel principal base, layout visual inicial, documentacion obligatoria y bitacora.
* Por que se hizo: Para cerrar la Fase 1 con una base funcional, documentada y preparada para crecimiento incremental.
* Decisiones tomadas: No implementar base de datos, Docker ni scheduler en Fase 1; se dejan documentados como pendientes segun fases definidas.
* Pruebas realizadas: `python -m py_compile run.py app\__init__.py app\config.py app\rutas.py`; carga de aplicacion con `from app import crear_app`.
* Riesgos detectados: `APP_SECRET_KEY` y `PASSWORD_ADMIN_DEFECTO` deben cambiarse en `.env` real antes de uso compartido.
* Proximos pasos: Probar login en navegador con `.env` real e iniciar Fase 2 solo despues de aprobacion.
