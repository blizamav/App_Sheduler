"""Contrato del runtime Docker QA reconstruido."""

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]


def test_compose_arranca_solo_entrypoints_reconstruidos():
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")

    assert "python -m app_scheduler.web" in compose
    assert "python -m app_scheduler.worker.aplicacion" in compose
    assert "python run.py" not in compose
    assert "python scheduler_worker.py" not in compose
    assert compose.count("- .env.docker") == 2
    assert "DOCKER_ENV_FILE" not in compose


def test_compose_declara_supervision_salud_y_persistencia():
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("restart: unless-stopped") == 2
    assert compose.count("healthcheck:") == 2
    assert "http://127.0.0.1:5000/salud" in compose
    assert "app_scheduler.worker.aplicacion\", \"--healthcheck" in compose
    for volumen in ("logs", "logs_tareas", "logs_sistema", "scripts", "env_scripts", "runtime_control"):
        assert compose.count(f"./{volumen}:/app/{volumen}") == 2


def test_worker_no_recibe_credencial_de_mantenimiento_factory_reset():
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")
    worker = compose.split("  worker:", maxsplit=1)[1]

    assert 'FACTORY_RESET_HABILITADO: "false"' in worker
    assert 'FACTORY_RESET_DB_USER: ""' in worker
    assert 'FACTORY_RESET_DB_PASSWORD: ""' in worker
    assert 'APP_SECRET_KEY: ""' in worker
    assert 'USUARIO_ADMIN_DEFECTO: ""' in worker
    assert 'PASSWORD_ADMIN_DEFECTO: ""' in worker


def test_imagen_tiene_entrypoint_reconstruido_y_runtime_control():
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")

    assert 'CMD ["python", "-m", "app_scheduler.web"]' in dockerfile
    assert "runtime_control" in dockerfile
    assert 'CMD ["python", "run.py"]' not in dockerfile
