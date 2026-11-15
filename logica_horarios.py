"""
logica_horarios.py
Lógica central de BarberTime: calcula los horarios libres de un barbero
y valida que una reserva sea correcta antes de guardarla.

No depende de Flask ni de la base de datos, por eso se puede probar sola
(ver tests/test_horarios.py).
"""

import re
from datetime import date, datetime, time, timedelta

# Horario de atención de la barbería (0 = lunes ... 6 = domingo).
# Domingo cerrado.
HORARIO_ATENCION = {
    0: (time(8, 0), time(18, 0)),
    1: (time(8, 0), time(18, 0)),
    2: (time(8, 0), time(18, 0)),
    3: (time(8, 0), time(18, 0)),
    4: (time(8, 0), time(18, 0)),
    5: (time(8, 0), time(16, 0)),
}

INTERVALO_MIN = 30          # cada cuántos minutos inicia un turno posible
DIAS_MAX_ANTICIPACION = 30  # no se reserva con más de 30 días de anticipación

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Teléfono de El Salvador: 8 dígitos que empiezan con 2, 6 o 7 (se permite guion).
_PATRON_TELEFONO = re.compile(r"^[267]\d{3}-?\d{4}$")


def a_minutos(t):
    """Convierte un objeto time o un texto 'HH:MM' a minutos desde las 00:00."""
    if isinstance(t, str):
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    return t.hour * 60 + t.minute


def a_texto(minutos):
    """Convierte minutos desde las 00:00 a texto 'HH:MM'."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def se_traslapan(inicio_a, fin_a, inicio_b, fin_b):
    """True si los intervalos [inicio_a, fin_a) y [inicio_b, fin_b) se cruzan (en minutos)."""
    return inicio_a < fin_b and fin_a > inicio_b


def horario_del_dia(fecha):
    """Devuelve (apertura, cierre) del día o None si la barbería está cerrada."""
    return HORARIO_ATENCION.get(fecha.weekday())


def horarios_disponibles(fecha, duracion_min, citas_ocupadas, ahora=None):
    """
    Calcula las horas de inicio libres para un servicio.

    fecha          : datetime.date del día consultado
    duracion_min   : duración del servicio en minutos
    citas_ocupadas : lista de tuplas (hora_inicio 'HH:MM', hora_fin 'HH:MM')
                     con las citas activas del barbero ese día
    ahora          : datetime actual (se puede pasar uno fijo para las pruebas)

    Devuelve una lista de textos 'HH:MM'.
    """
    ahora = ahora or datetime.now()
    horario = horario_del_dia(fecha)
    if horario is None or fecha < ahora.date():
        return []

    apertura, cierre = a_minutos(horario[0]), a_minutos(horario[1])
    ocupadas = [(a_minutos(i), a_minutos(f)) for i, f in citas_ocupadas]

    # Si es hoy, solo se ofrecen horas que aún no han pasado.
    minimo = apertura
    if fecha == ahora.date():
        minimo = max(apertura, ahora.hour * 60 + ahora.minute + 1)

    libres = []
    inicio = apertura
    while inicio + duracion_min <= cierre:
        fin = inicio + duracion_min
        if inicio >= minimo and not any(se_traslapan(inicio, fin, oi, of) for oi, of in ocupadas):
            libres.append(a_texto(inicio))
        inicio += INTERVALO_MIN
    return libres


def validar_reserva(datos, duracion_min, citas_ocupadas, ahora=None):
    """
    Revisa los datos del formulario de reserva.

    datos : diccionario con 'nombre', 'telefono', 'fecha' (AAAA-MM-DD) y 'hora' (HH:MM)
    Devuelve una lista de mensajes de error (vacía si todo está bien).
    """
    ahora = ahora or datetime.now()
    errores = []

    nombre = (datos.get("nombre") or "").strip()
    if len(nombre) < 3:
        errores.append("Escribe tu nombre completo (mínimo 3 letras).")
    elif len(nombre) > 80:
        errores.append("El nombre es demasiado largo (máximo 80 caracteres).")
    elif not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü .'-]+", nombre):
        errores.append("El nombre solo puede llevar letras y espacios.")

    telefono = (datos.get("telefono") or "").strip()
    if not _PATRON_TELEFONO.match(telefono):
        errores.append("El teléfono debe tener 8 dígitos y empezar con 2, 6 o 7 (ej. 7123-4567).")

    try:
        fecha = date.fromisoformat(datos.get("fecha") or "")
    except ValueError:
        errores.append("Selecciona una fecha válida.")
        return errores

    try:
        hora = datetime.strptime(datos.get("hora") or "", "%H:%M").time()
    except ValueError:
        errores.append("Selecciona una hora de la lista.")
        return errores

    if fecha < ahora.date():
        errores.append("No se pueden reservar citas en fechas pasadas.")
        return errores
    if fecha > ahora.date() + timedelta(days=DIAS_MAX_ANTICIPACION):
        errores.append(f"Solo se puede reservar con un máximo de {DIAS_MAX_ANTICIPACION} días de anticipación.")
        return errores

    horario = horario_del_dia(fecha)
    if horario is None:
        errores.append(f"La barbería no atiende los {DIAS_SEMANA[fecha.weekday()]}.")
        return errores

    inicio = a_minutos(hora)
    fin = inicio + duracion_min
    if inicio < a_minutos(horario[0]) or fin > a_minutos(horario[1]):
        errores.append(
            f"El servicio debe terminar dentro del horario de atención "
            f"({horario[0]:%H:%M} a {horario[1]:%H:%M})."
        )
        return errores

    if datetime.combine(fecha, hora) <= ahora:
        errores.append("Esa hora ya pasó. Elige una hora posterior.")
        return errores

    for oi, of in citas_ocupadas:
        if se_traslapan(inicio, fin, a_minutos(oi), a_minutos(of)):
            errores.append(f"El barbero ya tiene una cita de {oi} a {of}. Elige otro horario.")
            break

    return errores


def hora_fin(hora_inicio, duracion_min):
    """Calcula la hora de fin 'HH:MM' de una cita."""
    return a_texto(a_minutos(hora_inicio) + duracion_min)
