# -*- coding: utf-8 -*-
import os
import json
import sys

APP_SCHEDULER_EVIDENCIA = True
APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"

def leer_env(nombre, requerido=True):
    valor = os.getenv(nombre)

    if requerido and (valor is None or valor.strip() == ""):
        raise RuntimeError(f"No llegó la variable requerida: {nombre}")

    return valor

def main():
    print("INICIO PRUEBA ENV ADJUNTABLE")
    print("Validando variables recibidas desde APP Scheduler...")

    variables_requeridas = [
        "APP_TEST_CLIENTE",
        "APP_TEST_AMBIENTE",
        "SQL_SERVER",
        "SQL_DATABASE",
        "RUTA_PRUEBA",
        "SFTP_HOST",
        "SFTP_PORT"
    ]

    resumen = []

    for nombre in variables_requeridas:
        valor = leer_env(nombre)

        if "PASSWORD" in nombre.upper() or "SECRET" in nombre.upper() or "TOKEN" in nombre.upper():
            valor_log = "********"
        else:
            valor_log = valor

        print(f"{nombre}: OK -> {valor_log}")
        resumen.append({
            "campo": nombre,
            "valor": "OK"
        })

    password_sql = leer_env("SQL_PASSWORD")
    password_sftp = leer_env("SFTP_PASSWORD")

    print("SQL_PASSWORD: OK -> ********")
    print("SFTP_PASSWORD: OK -> ********")

    resumen.append({"campo": "SQL_PASSWORD", "valor": "OK - protegido"})
    resumen.append({"campo": "SFTP_PASSWORD", "valor": "OK - protegido"})

    print("VARIABLES ENV CARGADAS CORRECTAMENTE")

    evidencia_scheduler = {
        "version_contrato": "1.0",
        "estado": "EXITOSO",
        "tipo_evidencia": "PRUEBA_ENV",
        "titulo": "Prueba de .env adjuntable",
        "resumen": resumen,
        "problemas": []
    }

    print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
    print(json.dumps(evidencia_scheduler, ensure_ascii=False))
    print("###APP_SCHEDULER_EVIDENCIA_FIN###")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR PRUEBA ENV: {e}")

        evidencia_scheduler = {
            "version_contrato": "1.0",
            "estado": "FALLIDO",
            "tipo_evidencia": "PRUEBA_ENV",
            "titulo": "Prueba de .env adjuntable fallida",
            "resumen": [],
            "problemas": [str(e)]
        }

        print("###APP_SCHEDULER_EVIDENCIA_INICIO###")
        print(json.dumps(evidencia_scheduler, ensure_ascii=False))
        print("###APP_SCHEDULER_EVIDENCIA_FIN###")

        sys.exit(1)