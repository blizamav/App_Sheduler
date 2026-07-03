import json
import time

APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"

print("Inicio proceso de prueba con error controlado")
print("Conectando a origen de datos...")
time.sleep(1)

print("Leyendo registros de ejemplo...")
time.sleep(1)

registros = [
    {"rut": "11111111-1", "monto": "15000", "fecha": "2026-07-03"},
    {"rut": "22222222-2", "monto": "23000", "fecha": "2026-07-03"},
    {"rut": "33333333-3", "monto": "NO_NUMERICO", "fecha": "2026-07-03"},
    {"rut": "44444444-4", "monto": "18000", "fecha": "2026-07-03"}
]

print(f"Registros encontrados: {len(registros)}")
print("Iniciando validación de montos...")

total = 0

for indice, registro in enumerate(registros, start=1):
    print(f"Procesando registro {indice}: RUT {registro['rut']}")

    monto = int(registro["monto"])

    total += monto
    print(f"Registro {indice} OK - monto: {monto}")

print(f"Total procesado: {total}")

evidencia_scheduler = {
    "version_contrato": "1.0",
    "estado": "EXITOSO",
    "tipo_evidencia": "PRUEBA_ERROR",
    "titulo": "Prueba proceso con error",
    "resumen": [
        {"campo": "Registros procesados", "valor": len(registros)},
        {"campo": "Total procesado", "valor": total}
    ],
    "adjuntos": [],
    "problemas": []
}

print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
print(json.dumps(evidencia_scheduler, ensure_ascii=False))
print("###APP_SCHEDULER_EVIDENCIA_FIN###")