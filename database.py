"""
database.py
Conexión a SQLite, creación de tablas y datos iniciales (barberos y servicios).
"""

import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(BASE, "barbertime.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS barberos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT    NOT NULL,
    especialidad TEXT,
    activo  INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS servicios (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT    NOT NULL,
    descripcion  TEXT,
    duracion_min INTEGER NOT NULL CHECK (duracion_min > 0),
    precio       REAL    NOT NULL CHECK (precio >= 0)
);

CREATE TABLE IF NOT EXISTS citas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nombre   TEXT    NOT NULL,
    cliente_telefono TEXT    NOT NULL,
    barbero_id       INTEGER NOT NULL REFERENCES barberos(id),
    servicio_id      INTEGER NOT NULL REFERENCES servicios(id),
    fecha            TEXT    NOT NULL,   -- AAAA-MM-DD
    hora_inicio      TEXT    NOT NULL,   -- HH:MM
    hora_fin         TEXT    NOT NULL,   -- HH:MM
    estado           TEXT    NOT NULL DEFAULT 'Pendiente'
                     CHECK (estado IN ('Pendiente', 'Atendida', 'Cancelada')),
    creada_en        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_citas_barbero_fecha ON citas (barbero_id, fecha);
"""

BARBEROS_INICIALES = [
    ("Carlos Méndez", "Fades y cortes modernos"),
    ("José Ramírez", "Barba y afeitado clásico"),
    ("Luis Hernández", "Cortes infantiles y clásicos"),
]

SERVICIOS_INICIALES = [
    ("Corte de cabello", "Corte clásico o moderno con máquina y tijera", 30, 5.00),
    ("Corte + barba", "Corte completo y arreglo de barba", 60, 8.00),
    ("Arreglo de barba", "Perfilado y arreglo de barba con navaja", 30, 4.00),
    ("Corte infantil", "Corte para niños menores de 12 años", 30, 4.00),
    ("Diseño / líneas", "Corte con diseño o líneas personalizadas", 60, 7.00),
    ("Tinte o mechas", "Aplicación de tinte o mechas en el cabello", 60, 12.00),
]


def conectar():
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar():
    """Crea las tablas y carga barberos y servicios si la base está vacía."""
    with conectar() as con:
        con.executescript(ESQUEMA)
        if con.execute("SELECT COUNT(*) FROM barberos").fetchone()[0] == 0:
            con.executemany("INSERT INTO barberos (nombre, especialidad) VALUES (?, ?)", BARBEROS_INICIALES)
        if con.execute("SELECT COUNT(*) FROM servicios").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO servicios (nombre, descripcion, duracion_min, precio) VALUES (?, ?, ?, ?)",
                SERVICIOS_INICIALES,
            )
    con.close()


def citas_ocupadas(con, barbero_id, fecha):
    """Lista de (hora_inicio, hora_fin) de las citas activas del barbero en esa fecha."""
    filas = con.execute(
        "SELECT hora_inicio, hora_fin FROM citas "
        "WHERE barbero_id = ? AND fecha = ? AND estado != 'Cancelada' ORDER BY hora_inicio",
        (barbero_id, fecha),
    ).fetchall()
    return [(f["hora_inicio"], f["hora_fin"]) for f in filas]
