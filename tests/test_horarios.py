"""
Pruebas de la lógica central (horarios disponibles y validación de reservas).
Ejecutar:  python -m unittest discover tests
"""

import os
import sys
import unittest
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logica_horarios import horarios_disponibles, se_traslapan, validar_reserva  # noqa: E402

# Lunes 16 de noviembre de 2026, 7:00 a. m. (antes de abrir)
AHORA = datetime(2026, 11, 16, 7, 0)
LUNES = date(2026, 11, 16)
SABADO = date(2026, 11, 21)
DOMINGO = date(2026, 11, 22)


def datos(**extra):
    base = {"nombre": "Juan Pérez", "telefono": "7123-4567", "fecha": "2026-11-17", "hora": "10:00"}
    base.update(extra)
    return base


class PruebasHorarios(unittest.TestCase):
    def test_dia_libre_tiene_todos_los_turnos(self):
        libres = horarios_disponibles(LUNES, 30, [], AHORA)
        self.assertEqual(libres[0], "08:00")
        self.assertEqual(libres[-1], "17:30")
        self.assertEqual(len(libres), 20)

    def test_servicio_largo_no_pasa_del_cierre(self):
        libres = horarios_disponibles(LUNES, 60, [], AHORA)
        self.assertEqual(libres[-1], "17:00")

    def test_cita_ocupada_bloquea_horarios_que_se_cruzan(self):
        libres = horarios_disponibles(LUNES, 60, [("10:00", "11:00")], AHORA)
        self.assertNotIn("09:30", libres)  # 9:30-10:30 se cruza
        self.assertNotIn("10:00", libres)
        self.assertNotIn("10:30", libres)
        self.assertIn("09:00", libres)     # 9:00-10:00 termina justo cuando empieza la otra
        self.assertIn("11:00", libres)

    def test_domingo_cerrado(self):
        self.assertEqual(horarios_disponibles(DOMINGO, 30, [], AHORA), [])

    def test_sabado_cierra_temprano(self):
        self.assertEqual(horarios_disponibles(SABADO, 30, [], AHORA)[-1], "15:30")

    def test_hoy_no_ofrece_horas_pasadas(self):
        libres = horarios_disponibles(LUNES, 30, [], datetime(2026, 11, 16, 12, 10))
        self.assertEqual(libres[0], "12:30")

    def test_traslape(self):
        self.assertTrue(se_traslapan(600, 660, 630, 690))
        self.assertFalse(se_traslapan(600, 660, 660, 690))


class PruebasValidacion(unittest.TestCase):
    def test_reserva_correcta(self):
        self.assertEqual(validar_reserva(datos(), 30, [], AHORA), [])

    def test_choque_de_horario(self):
        errores = validar_reserva(datos(hora="10:00"), 60, [("10:30", "11:00")], AHORA)
        self.assertTrue(any("ya tiene una cita" in e for e in errores))

    def test_telefono_invalido(self):
        self.assertTrue(validar_reserva(datos(telefono="1234"), 30, [], AHORA))
        self.assertTrue(validar_reserva(datos(telefono="5123-4567"), 30, [], AHORA))
        self.assertEqual(validar_reserva(datos(telefono="71234567"), 30, [], AHORA), [])

    def test_nombre_invalido(self):
        self.assertTrue(validar_reserva(datos(nombre="Jo"), 30, [], AHORA))
        self.assertTrue(validar_reserva(datos(nombre="<script>"), 30, [], AHORA))

    def test_fecha_pasada(self):
        self.assertTrue(validar_reserva(datos(fecha="2026-11-10"), 30, [], AHORA))

    def test_fecha_muy_lejana(self):
        self.assertTrue(validar_reserva(datos(fecha="2027-02-01"), 30, [], AHORA))

    def test_domingo(self):
        errores = validar_reserva(datos(fecha="2026-11-22"), 30, [], AHORA)
        self.assertTrue(any("domingo" in e for e in errores))

    def test_fuera_de_horario(self):
        self.assertTrue(validar_reserva(datos(hora="17:30"), 60, [], AHORA))
        self.assertTrue(validar_reserva(datos(hora="07:00"), 30, [], AHORA))

    def test_hora_y_fecha_mal_formadas(self):
        self.assertTrue(validar_reserva(datos(fecha="ayer"), 30, [], AHORA))
        self.assertTrue(validar_reserva(datos(hora="25:99"), 30, [], AHORA))


if __name__ == "__main__":
    unittest.main()
