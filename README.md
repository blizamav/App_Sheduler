# APP Scheduler

Aplicacion web Flask para programar, ejecutar y auditar tareas Python de equipos TI.

La Fase 2 deja una base local funcional con login desde variables de entorno, layout corporativo responsive, componentes visuales iniciales, documentacion y bitacora tecnica.

## Ejecucion local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Luego abrir `http://127.0.0.1:5000`.

## Estado actual

* Fase actual: Fase 2 - Diseno UI/UX base.
* Login: activo desde `.env`.
* Base de datos, tareas, scheduler y logs funcionales: pendientes para fases posteriores.
