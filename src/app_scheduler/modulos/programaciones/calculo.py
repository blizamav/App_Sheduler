"""Calculo temporal deterministico de programaciones."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app_scheduler.compartido.errores import ErrorValidacion


DIAS = {"LUNES": 0, "MARTES": 1, "MIERCOLES": 2, "JUEVES": 3,
        "VIERNES": 4, "SABADO": 5, "DOMINGO": 6}


def zona_valida(nombre: str) -> ZoneInfo:
    try:
        return ZoneInfo(nombre)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ErrorValidacion("La zona horaria no es valida.") from error


def normalizar_referencia(referencia: datetime, zona_horaria: str) -> datetime:
    zona = zona_valida(zona_horaria)
    if referencia.tzinfo is None:
        return referencia.replace(tzinfo=zona)
    return referencia.astimezone(zona)


def calcular_proxima_ejecucion(programacion, referencia: datetime) -> datetime | None:
    referencia = normalizar_referencia(referencia, programacion.zona_horaria)
    zona = zona_valida(programacion.zona_horaria)
    for desplazamiento in range(0, 367 * 6):
        dia = referencia.date() + timedelta(days=desplazamiento)
        if not _dia_aplica(programacion, dia):
            continue
        for hora in _horas(programacion):
            candidata_local = datetime.combine(dia, hora)
            candidata = _localizar_hora_civil(candidata_local, zona)
            if candidata is not None and _instante_utc(candidata) > _instante_utc(referencia):
                return candidata_local
    return None


def calcular_ocurrencia_vencida(programacion, referencia: datetime, ventana_segundos: int) -> datetime | None:
    referencia = normalizar_referencia(referencia, programacion.zona_horaria)
    zona = zona_valida(programacion.zona_horaria)
    limite = referencia - timedelta(seconds=max(1, int(ventana_segundos)))
    candidatas = []
    for dia in {limite.date(), referencia.date()}:
        if _dia_aplica(programacion, dia):
            for hora in _horas(programacion):
                candidata = _localizar_hora_civil(datetime.combine(dia, hora), zona)
                if candidata is not None:
                    candidatas.append(candidata)
    limite_utc = _instante_utc(limite)
    referencia_utc = _instante_utc(referencia)
    validas = [item for item in candidatas
               if limite_utc <= _instante_utc(item) <= referencia_utc]
    return max(validas).replace(tzinfo=None) if validas else None


def _localizar_hora_civil(valor: datetime, zona: ZoneInfo) -> datetime | None:
    """Omite horas inexistentes y elige fold=0 para horas repetidas."""
    candidatas = []
    for fold in (0, 1):
        candidata = valor.replace(tzinfo=zona, fold=fold)
        vuelta = candidata.astimezone(timezone.utc).astimezone(zona)
        if vuelta.replace(tzinfo=None) == valor and vuelta.fold == fold:
            candidatas.append(candidata)
    return candidatas[0] if candidatas else None


def _instante_utc(valor: datetime) -> datetime:
    return valor.astimezone(timezone.utc)


def _dia_aplica(programacion, dia: date) -> bool:
    if programacion.fecha_inicio_vigencia and dia < programacion.fecha_inicio_vigencia:
        return False
    if programacion.fecha_fin_vigencia and dia > programacion.fecha_fin_vigencia:
        return False
    tipo = programacion.tipo_programacion
    if tipo == "DIARIA": return True
    if tipo == "SEMANAL":
        seleccion = {DIAS[item] for item in _separar(programacion.dias_semana) if item in DIAS}
        return dia.weekday() in seleccion
    if tipo == "MENSUAL": return dia.day == programacion.dia_mes
    if tipo == "FECHA_ESPECIFICA": return dia == programacion.fecha_especifica
    if tipo == "FECHAS_ESPECIFICAS": return dia.isoformat() in _fechas(programacion.fechas_especificas)
    return False


def _horas(programacion) -> tuple[time, ...]:
    if programacion.modo_ejecucion_dia == "UNA_VEZ":
        return (programacion.hora_ejecucion,) if programacion.hora_ejecucion else ()
    if not programacion.hora_inicio or not programacion.hora_termino or not programacion.intervalo_minutos:
        return ()
    cursor = datetime.combine(date.min, programacion.hora_inicio)
    fin = datetime.combine(date.min, programacion.hora_termino)
    resultado = []
    while cursor <= fin and len(resultado) < 1440:
        resultado.append(cursor.time().replace(microsecond=0))
        cursor += timedelta(minutes=programacion.intervalo_minutos)
    return tuple(resultado)


def _separar(valor: str | None) -> tuple[str, ...]:
    return tuple(item.strip().upper() for item in str(valor or "").split(",") if item.strip())


def _fechas(valor: str | None) -> set[str]:
    try: datos = json.loads(valor or "[]")
    except (TypeError, ValueError, json.JSONDecodeError): return set()
    return {str(item) for item in datos if isinstance(item, str)}
