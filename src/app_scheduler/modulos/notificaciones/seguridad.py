"""Validaciones para destinatarios y contenido que abandona la aplicacion."""

from __future__ import annotations

import re


PATRON_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
PATRONES_SENSIBLES = (
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+\-/]+=*"),
    re.compile(r"(?i)\b(password|passwd|pwd|contrasena|client_secret|secret|token|authorization)\b\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)\b(DB_PASSWORD|GRAPH_CLIENT_SECRET|APP_SECRET_KEY)\b\s*=\s*([^\r\n]+)"),
)


def normalizar_email(valor: object) -> str:
    email = str(valor or "").strip().lower()
    if len(email) > 255 or not PATRON_EMAIL.fullmatch(email) or "\r" in email or "\n" in email:
        raise ValueError("Direccion de correo invalida.")
    return email


def sanitizar_texto_externo(valor: object, limite: int = 4000) -> str:
    texto = str(valor or "")[:limite]
    for patron in PATRONES_SENSIBLES:
        texto = patron.sub(lambda m: f"{m.group(1)}=[PROTEGIDO]", texto)
    return texto
