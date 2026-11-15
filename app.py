"""
app.py
BarberTime - Prototipo inicial (Primer avance)
Funcionalidad central: reservar una cita en la barbería sin choques de horario.

Ejecutar:  python app.py   y abrir http://127.0.0.1:5000
"""

import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

import database as db
from logica_horarios import (
    DIAS_MAX_ANTICIPACION, DIAS_SEMANA, hora_fin, horarios_disponibles, validar_reserva,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "barbertime-prototipo-pc3"  # solo para mensajes flash en desarrollo

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


@app.template_filter("fecha_larga")
def fecha_larga(texto):
    d = date.fromisoformat(texto)
    return f"{DIAS_SEMANA[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"


def obtener_servicio(con, servicio_id):
    return con.execute("SELECT * FROM servicios WHERE id = ?", (servicio_id,)).fetchone()


def obtener_barbero(con, barbero_id):
    return con.execute("SELECT * FROM barberos WHERE id = ? AND activo = 1", (barbero_id,)).fetchone()


# ---------------------------------------------------------------- páginas
def formulario_reserva(previo=None, codigo=200):
    """Muestra el formulario; si hubo errores se vuelve a llenar con lo que el cliente escribió."""
    with db.conectar() as con:
        servicios = con.execute("SELECT * FROM servicios ORDER BY id").fetchall()
        barberos = con.execute("SELECT * FROM barberos WHERE activo = 1 ORDER BY id").fetchall()
    hoy = date.today()
    return render_template(
        "index.html",
        servicios=servicios,
        barberos=barberos,
        fecha_min=hoy.isoformat(),
        fecha_max=(hoy + timedelta(days=DIAS_MAX_ANTICIPACION)).isoformat(),
        previo=previo or {},
    ), codigo


@app.route("/")
def inicio():
    return formulario_reserva()


@app.route("/reservar", methods=["POST"])
def reservar():
    datos = {k: (request.form.get(k) or "").strip()
             for k in ("servicio_id", "barbero_id", "fecha", "hora", "nombre", "telefono")}

    con = db.conectar()
    try:
        servicio = obtener_servicio(con, datos["servicio_id"]) if datos["servicio_id"].isdigit() else None
        barbero = obtener_barbero(con, datos["barbero_id"]) if datos["barbero_id"].isdigit() else None
        if servicio is None or barbero is None:
            flash("Selecciona un servicio y un barbero válidos.", "danger")
            return formulario_reserva(datos, 400)

        # BEGIN IMMEDIATE bloquea la base mientras se revisa y se guarda,
        # así dos clientes no pueden tomar el mismo horario al mismo tiempo.
        con.execute("BEGIN IMMEDIATE")
        ocupadas = db.citas_ocupadas(con, barbero["id"], datos["fecha"])
        errores = validar_reserva(datos, servicio["duracion_min"], ocupadas)
        if errores:
            con.rollback()
            for e in errores:
                flash(e, "danger")
            return formulario_reserva(datos, 400)

        telefono = datos["telefono"].replace("-", "")
        cur = con.execute(
            "INSERT INTO citas (cliente_nombre, cliente_telefono, barbero_id, servicio_id, "
            "fecha, hora_inicio, hora_fin) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (" ".join(datos["nombre"].split()), f"{telefono[:4]}-{telefono[4:]}", barbero["id"],
             servicio["id"], datos["fecha"], datos["hora"],
             hora_fin(datos["hora"], servicio["duracion_min"])),
        )
        con.commit()
        return redirect(url_for("ver_cita", cita_id=cur.lastrowid, nueva=1))
    except sqlite3.Error:
        con.rollback()
        flash("Ocurrió un problema al guardar la cita. Intenta de nuevo.", "danger")
        return formulario_reserva(datos, 400)
    finally:
        con.close()


@app.route("/cita/<int:cita_id>")
def ver_cita(cita_id):
    with db.conectar() as con:
        cita = con.execute(
            "SELECT c.*, b.nombre AS barbero, s.nombre AS servicio, s.precio, s.duracion_min "
            "FROM citas c JOIN barberos b ON b.id = c.barbero_id JOIN servicios s ON s.id = c.servicio_id "
            "WHERE c.id = ?", (cita_id,)).fetchone()
    if cita is None:
        abort(404)
    return render_template("confirmacion.html", cita=cita, nueva=request.args.get("nueva"))


@app.route("/agenda")
def agenda():
    texto = request.args.get("fecha") or date.today().isoformat()
    try:
        fecha = date.fromisoformat(texto)
    except ValueError:
        flash("Fecha no válida, se muestra la agenda de hoy.", "warning")
        fecha = date.today()

    with db.conectar() as con:
        barberos = con.execute("SELECT * FROM barberos WHERE activo = 1 ORDER BY id").fetchall()
        citas = con.execute(
            "SELECT c.*, s.nombre AS servicio, s.precio FROM citas c "
            "JOIN servicios s ON s.id = c.servicio_id WHERE c.fecha = ? ORDER BY c.hora_inicio",
            (fecha.isoformat(),)).fetchall()

    por_barbero = {b["id"]: [] for b in barberos}
    for c in citas:
        por_barbero.setdefault(c["barbero_id"], []).append(c)
    activas = [c for c in citas if c["estado"] != "Cancelada"]
    resumen = {
        "total": len(activas),
        "atendidas": sum(c["estado"] == "Atendida" for c in activas),
        "ingreso_estimado": sum(c["precio"] for c in activas),
    }
    return render_template(
        "agenda.html", fecha=fecha.isoformat(), barberos=barberos, por_barbero=por_barbero,
        resumen=resumen, anterior=(fecha - timedelta(days=1)).isoformat(),
        siguiente=(fecha + timedelta(days=1)).isoformat(),
    )


@app.route("/cita/<int:cita_id>/estado", methods=["POST"])
def cambiar_estado(cita_id):
    nuevo = request.form.get("estado")
    if nuevo not in ("Atendida", "Cancelada", "Pendiente"):
        abort(400)
    with db.conectar() as con:
        cita = con.execute("SELECT fecha FROM citas WHERE id = ?", (cita_id,)).fetchone()
        if cita is None:
            abort(404)
        con.execute("UPDATE citas SET estado = ? WHERE id = ?", (nuevo, cita_id))
    flash(f"Cita #{cita_id} marcada como {nuevo.lower()}.", "success")
    return redirect(request.form.get("volver") or url_for("agenda", fecha=cita["fecha"]))


# ---------------------------------------------------------------- API
@app.route("/api/horarios")
def api_horarios():
    """Devuelve en JSON los horarios libres de un barbero para un servicio y una fecha."""
    try:
        fecha = date.fromisoformat(request.args.get("fecha", ""))
        servicio_id = int(request.args.get("servicio_id", ""))
        barbero_id = int(request.args.get("barbero_id", ""))
    except ValueError:
        return jsonify(error="Parámetros incompletos o no válidos."), 400

    with db.conectar() as con:
        servicio = obtener_servicio(con, servicio_id)
        barbero = obtener_barbero(con, barbero_id)
        if servicio is None or barbero is None:
            return jsonify(error="Servicio o barbero no encontrado."), 404
        ocupadas = db.citas_ocupadas(con, barbero_id, fecha.isoformat())

    hoy = date.today()
    if fecha < hoy:
        mensaje = "No se puede reservar en fechas pasadas."
        libres = []
    elif fecha > hoy + timedelta(days=DIAS_MAX_ANTICIPACION):
        mensaje = f"Solo se reserva hasta {DIAS_MAX_ANTICIPACION} días adelante."
        libres = []
    else:
        libres = horarios_disponibles(fecha, servicio["duracion_min"], ocupadas, datetime.now())
        if fecha.weekday() == 6:
            mensaje = "La barbería no atiende los domingos."
        elif not libres:
            mensaje = f"{barbero['nombre']} no tiene horarios libres ese día. Prueba otra fecha u otro barbero."
        else:
            mensaje = ""
    return jsonify(horarios=libres, mensaje=mensaje, duracion=servicio["duracion_min"])


@app.errorhandler(404)
def no_encontrado(_e):
    return render_template("error.html", codigo=404, mensaje="La página o la cita que buscas no existe."), 404


@app.errorhandler(400)
def solicitud_invalida(_e):
    return render_template("error.html", codigo=400, mensaje="La solicitud no es válida."), 400


db.inicializar()

if __name__ == "__main__":
    app.run(debug=True)
