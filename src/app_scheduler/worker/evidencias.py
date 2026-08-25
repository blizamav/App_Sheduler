"""Captura y validacion del contrato de evidencia emitido por stdout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


INICIO = "###APP_SCHEDULER_EVIDENCIA_INICIO###"
FIN = "###APP_SCHEDULER_EVIDENCIA_FIN###"
VERSION = "1.0"


class CapturadorEvidencia:
    def __init__(self):
        self.inicio = False
        self.fin = False
        self._capturando = False
        self._lineas: list[str] = []
        self._cantidad_bloques = 0

    def recibir(self, linea: str) -> None:
        texto = str(linea).rstrip("\r\n")
        if not self._capturando and INICIO in texto:
            self._cantidad_bloques += 1
            self.inicio = True
            self._capturando = True
            texto = texto.split(INICIO, 1)[1]
        if self._capturando:
            if FIN in texto:
                anterior = texto.split(FIN, 1)[0]
                if anterior.strip():
                    self._lineas.append(anterior)
                self.fin = True
                self._capturando = False
            elif texto.strip():
                self._lineas.append(texto)

    def procesar(self, codigo_salida: int | None, raiz_adjuntos: Path | None = None) -> dict:
        base = {
            "bloque_detectado": self.inicio,
            "delimitador_inicio_detectado": self.inicio,
            "delimitador_fin_detectado": self.fin,
            "cantidad_campos_resumen": 0,
            "cantidad_adjuntos_declarados": 0,
            "cantidad_problemas": 0,
        }
        if not self.inicio:
            return {**base, "estado_evidencia": "NO_EMITIDA",
                    "error_validacion": "El script no emitio el bloque de evidencia."}
        if self._cantidad_bloques != 1:
            return {**base, "estado_evidencia": "INVALIDA",
                    "error_validacion": "La ejecucion debe emitir un unico bloque de evidencia."}
        texto = "\n".join(self._lineas).strip()
        if not self.fin:
            return {**base, "estado_evidencia": "INVALIDA",
                    "hash_evidencia": _hash(texto),
                    "error_validacion": "El bloque no contiene delimitador de fin."}
        try:
            datos = json.loads(texto)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {**base, "estado_evidencia": "INVALIDA",
                    "hash_evidencia": _hash(texto),
                    "error_validacion": "El bloque no contiene JSON valido."}
        if not isinstance(datos, dict):
            return {**base, "estado_evidencia": "INVALIDA",
                    "hash_evidencia": _hash(texto),
                    "error_validacion": "La evidencia debe ser un objeto JSON."}
        resumen = datos.get("resumen")
        problemas = datos.get("problemas", [])
        adjuntos = datos.get("adjuntos", [])
        errores = []
        if datos.get("version_contrato") != VERSION: errores.append("Version de contrato invalida.")
        if datos.get("estado") not in {"EXITOSO", "ERROR", "ADVERTENCIA"}: errores.append("Estado invalido.")
        if not datos.get("tipo_evidencia"): errores.append("Falta tipo_evidencia.")
        if not datos.get("titulo"): errores.append("Falta titulo.")
        if not isinstance(resumen, list): errores.append("resumen debe ser una lista.")
        if not isinstance(problemas, list): errores.append("problemas debe ser una lista.")
        if not isinstance(adjuntos, list): errores.append("adjuntos debe ser una lista.")
        estado = "INVALIDA" if errores else "VALIDADA"
        adjunto_faltante = False
        if not errores and raiz_adjuntos is not None:
            adjunto_faltante = _existe_adjunto_obligatorio_faltante(
                adjuntos, raiz_adjuntos
            )
            if adjunto_faltante:
                estado = "ADJUNTO_FALTANTE"
        if not errores and (datos.get("estado") != "EXITOSO" or codigo_salida != 0 or problemas):
            if not adjunto_faltante:
                estado = "ERROR_DECLARADO"
        normalizado = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return {
            **base,
            "estado_evidencia": estado,
            "version_contrato": VERSION if datos.get("version_contrato") == VERSION else None,
            "tipo_evidencia": _texto(datos.get("tipo_evidencia"), 100),
            "titulo": _texto(datos.get("titulo"), 255),
            "asunto_sugerido": _texto(datos.get("asunto_sugerido"), 255),
            "hash_evidencia": _hash(normalizado),
            "cantidad_campos_resumen": len(resumen) if isinstance(resumen, list) else 0,
            "cantidad_adjuntos_declarados": len(adjuntos) if isinstance(adjuntos, list) else 0,
            "cantidad_problemas": len(problemas) if isinstance(problemas, list) else 0,
            "error_validacion": "; ".join(errores)[:1000] or None,
            "evidencia": datos,
        }


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8", errors="replace")).hexdigest()


def _texto(valor, limite: int):
    texto = str(valor or "").strip()
    return texto[:limite] or None


def _existe_adjunto_obligatorio_faltante(
    adjuntos: list, raiz_adjuntos: Path
) -> bool:
    raiz = raiz_adjuntos.resolve()
    for adjunto in adjuntos:
        if not isinstance(adjunto, dict) or not _booleano(adjunto.get("obligatorio")):
            continue
        if not adjunto.get("ruta"):
            return True
        candidata = raiz / str(adjunto["ruta"])
        for elemento in (candidata, *candidata.parents):
            if elemento.exists() and elemento.is_symlink():
                return True
            if elemento == raiz:
                break
        ruta = candidata.resolve()
        try:
            ruta.relative_to(raiz)
        except ValueError:
            return True
        if not ruta.is_file():
            return True
    return False


def _booleano(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor or "").strip().lower() in {"1", "true", "si", "yes", "on"}
