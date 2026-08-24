"""Subprocess portable y acotado para scripts Python custodiados."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path


VARIABLES_BASE_PERMITIDAS = frozenset({
    "COMSPEC", "HOME", "LANG", "LC_ALL", "LOCALAPPDATA", "PATH", "PATHEXT",
    "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "TZ", "USERPROFILE",
    "WINDIR",
})


def construir_entorno_base(entorno: dict[str, str] | None = None) -> dict[str, str]:
    origen = os.environ if entorno is None else entorno
    resultado = {
        clave: str(valor)
        for clave, valor in origen.items()
        if clave.upper() in VARIABLES_BASE_PERMITIDAS
    }
    resultado.update({"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
    return resultado


def iniciar_python(ruta_script: Path, entorno: dict[str, str], cwd: Path):
    opciones = {
        "args": [sys.executable, "-u", str(ruta_script)],
        "cwd": str(cwd),
        "env": entorno,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
        "shell": False,
    }
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        opciones["start_new_session"] = True
    return subprocess.Popen(**opciones)


def terminar_arbol(proceso, *, espera_segundos: float = 5.0) -> bool:
    """Termina solo el grupo creado para el proceso y retorna si fue forzado."""
    if proceso is None or proceso.poll() is not None:
        return False
    if os.name == "nt":
        proceso.terminate()
    else:
        os.killpg(proceso.pid, signal.SIGTERM)
    try:
        proceso.wait(timeout=espera_segundos)
        return False
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proceso.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, check=False, shell=False,
            )
        else:
            os.killpg(proceso.pid, signal.SIGKILL)
        proceso.wait(timeout=espera_segundos)
        return True
