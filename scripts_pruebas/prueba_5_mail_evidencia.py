import json

APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"

arreglo = []

for i in range(23):
    print("ESTA ES UNA PRUEBA - Envio de mail desde Scheduler")
    arreglo.append(1)

print(f"LARGO ARREGLO: {len(arreglo)}")

evidencia_scheduler = {
    "version_contrato": "1.0",
    "estado": "EXITOSO",
    "tipo_evidencia": "PRUEBA_MAIL",
    "titulo": "Prueba Api Mail",
    "resumen": [
        {"campo": "Mensajes impresos", "valor": len(arreglo)},
        {"campo": "Resultado", "valor": "Proceso finalizado correctamente"}
    ],
    "adjuntos": [],
    "problemas": []
}

print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
print(json.dumps(evidencia_scheduler, ensure_ascii=False))
print("###APP_SCHEDULER_EVIDENCIA_FIN###")