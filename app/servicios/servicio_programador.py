from datetime import datetime, time, timedelta


DIAS_SEMANA = {
    0: "LUNES",
    1: "MARTES",
    2: "MIERCOLES",
    3: "JUEVES",
    4: "VIERNES",
    5: "SABADO",
    6: "DOMINGO",
}


def debe_ejecutarse_ahora(tarea, fecha_hora_actual=None, ventana_segundos=60):
    ahora = fecha_hora_actual or datetime.now()
    ventana_inicio = ahora - timedelta(seconds=max(1, int(ventana_segundos or 60)))
    tipo = tarea.get("tipo_programacion")
    modo = tarea.get("modo_ejecucion_dia") or "UNA_VEZ"

    if tipo == "MANUAL":
        return _resultado(False, "Programacion manual no se ejecuta automaticamente.")
    if tipo not in {"DIARIA", "SEMANAL", "MENSUAL", "FECHA_ESPECIFICA"}:
        return _resultado(False, "Tipo de programacion no soportado por worker.")
    if tipo == "SEMANAL" and not _dia_semana_valido(tarea, ahora):
        return _resultado(False, "Dia de semana no corresponde.")
    if tipo == "MENSUAL" and not _dia_mes_valido(tarea, ahora):
        return _resultado(False, "Dia del mes no corresponde.")
    if tipo == "FECHA_ESPECIFICA" and not _fecha_especifica_valida(tarea, ahora):
        return _resultado(False, "Fecha especifica no corresponde.")

    if modo == "INTERVALO":
        return _evaluar_intervalo(tarea, ahora, ventana_inicio)
    return _evaluar_una_vez(tarea, ahora, ventana_inicio)


def _evaluar_una_vez(tarea, ahora, ventana_inicio):
    hora = _a_time(tarea.get("hora_ejecucion"))
    if not hora:
        return _resultado(False, "Hora de ejecucion no configurada.")

    fecha_base = _fecha_base(tarea, ahora)
    fecha_programada = datetime.combine(fecha_base, hora)
    if ventana_inicio <= fecha_programada <= ahora:
        return _resultado(
            True,
            "Dentro de ventana de ejecucion.",
            fecha_programada,
            _clave(tarea, fecha_programada),
        )
    return _resultado(False, "Fuera de ventana de ejecucion.")


def _evaluar_intervalo(tarea, ahora, ventana_inicio):
    inicio = _a_time(tarea.get("hora_inicio_intervalo"))
    fin = _a_time(tarea.get("hora_fin_intervalo"))
    intervalo = int(tarea.get("intervalo_minutos") or 0)
    if not inicio or not fin or intervalo <= 0:
        return _resultado(False, "Intervalo incompleto.")

    fecha_base = _fecha_base(tarea, ahora)
    cursor = datetime.combine(fecha_base, inicio)
    limite = datetime.combine(fecha_base, fin)
    if cursor > limite:
        return _resultado(False, "Ventana horaria invalida.")

    while cursor <= limite:
        if ventana_inicio <= cursor <= ahora:
            return _resultado(
                True,
                "Slot de intervalo dentro de ventana.",
                cursor,
                _clave(tarea, cursor, intervalo=True),
            )
        cursor += timedelta(minutes=intervalo)
    return _resultado(False, "No hay slot pendiente en ventana.")


def _fecha_base(tarea, ahora):
    if tarea.get("tipo_programacion") == "FECHA_ESPECIFICA":
        fecha = tarea.get("fecha_especifica")
        return fecha if hasattr(fecha, "year") else ahora.date()
    return ahora.date()


def _dia_semana_valido(tarea, ahora):
    dias = {dia.strip().upper() for dia in (tarea.get("dias_semana") or "").split(",") if dia.strip()}
    return DIAS_SEMANA[ahora.weekday()] in dias


def _dia_mes_valido(tarea, ahora):
    try:
        return int(tarea.get("dia_mes") or 0) == ahora.day
    except ValueError:
        return False


def _fecha_especifica_valida(tarea, ahora):
    fecha = tarea.get("fecha_especifica")
    if not fecha:
        return False
    return str(fecha)[:10] == f"{ahora:%Y-%m-%d}"


def _a_time(valor):
    if not valor:
        return None
    if isinstance(valor, time):
        return valor.replace(second=0, microsecond=0)
    partes = str(valor)[:5].split(":")
    if len(partes) != 2:
        return None
    return time(int(partes[0]), int(partes[1]))


def _clave(tarea, fecha_programada, intervalo=False):
    tipo = tarea.get("tipo_programacion")
    sufijo = "_INTERVALO" if intervalo else ""
    return f"TAREA_{tarea['id_tarea']}_{tipo}{sufijo}_{fecha_programada:%Y-%m-%d_%H:%M}"


def _resultado(debe_ejecutar, motivo, fecha_programada=None, clave_programacion=None):
    return {
        "debe_ejecutar": debe_ejecutar,
        "motivo": motivo,
        "fecha_programada": fecha_programada,
        "clave_programacion": clave_programacion,
    }
