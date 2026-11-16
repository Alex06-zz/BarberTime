# 💈 BarberTime: sistema de reservas para barberías

**Universidad Gerardo Barrios**, Programación Computacional III, Laboratorio 1, Tercer Cómputo (primer avance del proyecto)

**Docente:** Ing. Willian Alexis Montes Girón

Facultad de Ciencia y Tecnología, Ingeniería en Sistemas y Redes Informáticas

## Integrantes

| Nombre | Carnet |
|--------|--------|
| William Alexander Valencia Rosa | SMSS2535235 |
| Abner Lemuel Pérez Medrano | SMSS136525 |
| Velinda Lisseth Guevara Guevara | SMSS039325 |
| Mariela Elizabeth Perez Hernández | SMSS233823 |
| Fernando José Castro Méndez | SMSS024725 |

## Descripción

En muchas barberías de San Miguel las citas se manejan por mensajes de WhatsApp, llamadas o
"por orden de llegada". Eso provoca esperas largas, dos clientes citados a la misma hora,
clientes que no llegan y ningún registro ordenado de la agenda ni de los ingresos.

**BarberTime** es una aplicación web en Python (Flask) que permite al cliente **reservar su cita
en línea eligiendo el servicio, el barbero y un horario libre**, y al barbero o dueño **ver la
agenda del día** de cada barbero. El sistema calcula los horarios disponibles según la duración de
cada servicio y el horario de atención, y **no permite choques de horario**.

## Funcionalidad central del prototipo (primer avance)

- Reserva de cita en 4 pasos: servicio → barbero → fecha y hora → datos del cliente.
- Cálculo automático de **horarios libres** según la duración del servicio, las citas ya
  registradas del barbero y el horario de atención (lun–vie 8:00–18:00, sáb 8:00–16:00, domingo cerrado).
- **Validaciones** en el navegador y en el servidor: nombre, teléfono salvadoreño (8 dígitos que
  empiezan con 2, 6 o 7), fechas pasadas, máximo 30 días de anticipación, fuera de horario y
  choque con otra cita. La base de datos se bloquea al guardar para evitar reservas dobles.
- Pantalla de confirmación con el detalle de la cita.
- **Agenda del día** por barbero: total de citas, atendidas e ingreso estimado. Permite marcar
  una cita como atendida o cancelarla (al cancelar, el horario vuelve a quedar libre).

## Estructura del repositorio

| Archivo / carpeta | Descripción |
|-------------------|-------------|
| `app.py` | Aplicación Flask: rutas de reserva, confirmación, agenda y API de horarios |
| `logica_horarios.py` | Lógica central: horarios disponibles y validación de reservas |
| `database.py` | Base de datos SQLite: tablas, datos iniciales y consultas |
| `templates/` | Vistas HTML (Jinja2 + Bootstrap 5) |
| `static/` | Estilos (`css/estilos.css`) y script de reserva (`js/reserva.js`) |
| `tests/test_horarios.py` | Pruebas unitarias de la lógica central (16 pruebas) |
| `Documento_Avance1_BarberTime.pdf` | **Documento del primer avance** (portada, índice, introducción, objetivos, delimitación, tecnologías y requerimientos) |
| `requirements.txt` | Dependencias del proyecto |

## Instalación y ejecución

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt

python app.py                  # abrir http://127.0.0.1:5000
python -m unittest discover tests   # ejecutar las pruebas
```

La base de datos `barbertime.db` se crea sola la primera vez, con 3 barberos y 5 servicios de ejemplo.

## Tecnologías

Python 3 · Flask · SQLite · Jinja2 · Bootstrap 5 · JavaScript

## Próximos avances

Inicio de sesión para barberos y administrador, gestión de barberos y servicios, recordatorio de
cita por WhatsApp, cancelación por parte del cliente y reportes de ingresos con gráficas.

## Cómo reservar una cita

1. Entrar a la página principal de BarberTime.
2. Elegir el servicio (corte, corte + barba, arreglo de barba, etc.); se muestra su precio y duración.
3. Elegir el barbero que lo atenderá.
4. Seleccionar la fecha: el sistema muestra solo las horas libres de ese barbero.
5. Tocar la hora deseada y escribir nombre completo y teléfono (WhatsApp).
6. Presionar "Confirmar cita". Aparece la confirmación con el número de cita.
