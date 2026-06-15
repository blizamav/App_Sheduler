import time
import os

print("Inicio script de prueba", flush=True)
print("AMBIENTE:", os.getenv("AMBIENTE", "SIN_AMBIENTE"), flush=True)

for i in range(1, 11):
    print(f"Iteración {i}", flush=True)
    time.sleep(2)

print("Fin script de prueba", flush=True)