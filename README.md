# APP Scheduler

Aplicacion web Flask para programar, ejecutar y auditar tareas Python de equipos TI.

La Fase 1 deja una base local funcional con login desde variables de entorno, layout corporativo inicial, documentacion y bitacora tecnica.

## Ejecucion local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Luego abrir `http://127.0.0.1:5000`.
