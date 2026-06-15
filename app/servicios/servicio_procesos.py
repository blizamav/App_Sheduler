import os
import signal
import subprocess
import sys
import time


PROCESOS_EJECUCION = {}


def iniciar_proceso_python(ruta_script, entorno):
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "env": entorno,
        "text": True,
        "bufsize": 1,
        "shell": False,
    }
    if os.name != "nt":
        kwargs["start_new_session"] = True
    return subprocess.Popen([sys.executable, str(ruta_script)], **kwargs)


def registrar_proceso(id_ejecucion, proceso):
    PROCESOS_EJECUCION[int(id_ejecucion)] = proceso


def olvidar_proceso(id_ejecucion):
    PROCESOS_EJECUCION.pop(int(id_ejecucion), None)


def detener_proceso(id_ejecucion, pid, espera_segundos=5):
    proceso = PROCESOS_EJECUCION.get(int(id_ejecucion))
    fue_forzada = False

    if proceso and proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=espera_segundos)
            return fue_forzada
        except subprocess.TimeoutExpired:
            fue_forzada = True
            proceso.kill()
            proceso.wait(timeout=espera_segundos)
            return fue_forzada

    if not pid:
        return fue_forzada

    fue_forzada = True
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, check=False)
    else:
        try:
            os.killpg(int(pid), signal.SIGTERM)
            time.sleep(espera_segundos)
        except Exception:
            pass
        try:
            os.killpg(int(pid), signal.SIGKILL)
        except Exception:
            try:
                os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass
    return fue_forzada
