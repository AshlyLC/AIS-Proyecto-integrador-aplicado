import os
import re
import sqlite3
from datetime import date, datetime

from flask import g
from werkzeug.security import check_password_hash, generate_password_hash

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(CARPETA, "datos", "sistema.db")

ESQUEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario       TEXT NOT NULL UNIQUE,
    nombre        TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL          -- nunca la contraseña en texto plano
);

CREATE TABLE IF NOT EXISTS pacientes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente       TEXT    NOT NULL UNIQUE,   -- EXP-001, EXP-002, ...
    nombre           TEXT    NOT NULL,
    fecha_nacimiento TEXT,                      -- formato YYYY-MM-DD
    edad             INTEGER,
    sexo             TEXT,
    ocupacion        TEXT,
    telefono         TEXT,
    correo           TEXT,
    fecha_apertura   TEXT    NOT NULL,
    motivo_consulta  TEXT    DEFAULT '',
    antecedentes     TEXT    DEFAULT '',
    estado           TEXT    NOT NULL DEFAULT 'Activo'   -- Activo | Inactivo
);

CREATE TABLE IF NOT EXISTS sesiones (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id    INTEGER NOT NULL
                   REFERENCES pacientes(id) ON DELETE CASCADE,
    numero_sesion  INTEGER NOT NULL,
    fecha          TEXT    NOT NULL,
    tema           TEXT    DEFAULT '',
    resumen        TEXT    DEFAULT '',
    tareas         TEXT    DEFAULT '',
    nivel_avance   TEXT    DEFAULT 'Moderado',   -- Bajo | Moderado | Alto
    proxima_sesion TEXT
);
"""

OPCIONES_SEXO = ["Mujer", "Hombre", "Otro"]
OPCIONES_ESTADO = ["Activo", "Inactivo"]
OPCIONES_AVANCE = ["Bajo", "Moderado", "Alto"]


def conectar():
    """Devuelve la conexión a la base de datos de la petición actual."""
    if "bd" not in g:
        os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)
        g.bd = sqlite3.connect(RUTA_BD)
        g.bd.row_factory = sqlite3.Row      # permite acceder por nombre: fila["nombre"]
        g.bd.execute("PRAGMA foreign_keys = ON")
    return g.bd


def cerrar(excepcion=None):
    """Cierra la conexión al terminar la petición."""
    bd = g.pop("bd", None)
    if bd is not None:
        bd.close()


def consultar(sql, parametros=(), uno=False):
    """Ejecuta un SELECT. Devuelve una lista de filas (o una sola si uno=True)."""
    filas = conectar().execute(sql, parametros).fetchall()
    if uno:
        return filas[0] if filas else None
    return filas


def ejecutar(sql, parametros=()):
    """Ejecuta INSERT / UPDATE / DELETE. Devuelve el id del registro insertado."""
    bd = conectar()
    cursor = bd.execute(sql, parametros)
    bd.commit()
    return cursor.lastrowid


def crear_tablas():
    """Crea las tablas si no existen y la cuenta de acceso inicial."""
    os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)
    bd = sqlite3.connect(RUTA_BD)
    bd.executescript(ESQUEMA)
    # Cuenta por defecto la primera vez (se puede cambiar desde el código)
    existe = bd.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if not existe:
        bd.execute(
            "INSERT INTO usuarios (usuario, nombre, password_hash) VALUES (?, ?, ?)",
            ("psicologa", "Psicóloga", generate_password_hash("psicologa123")),
        )
    bd.commit()
    bd.close()


def hoy():
    """Fecha de hoy en el formato que usa la base de datos (2026-08-11)."""
    return date.today().isoformat()


def formato_fecha(texto):
    """Convierte 2026-08-11 en 11/08/2026 para mostrarlo en pantalla."""
    if not texto:
        return "—"
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return texto


def calcular_edad(fecha_nacimiento):
    """Calcula los años cumplidos a partir de la fecha de nacimiento."""
    if not fecha_nacimiento:
        return None
    try:
        nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    except ValueError:
        return None
    referencia = date.today()
    edad = referencia.year - nacimiento.year
    if (referencia.month, referencia.day) < (nacimiento.month, nacimiento.day):
        edad -= 1
    return max(edad, 0)


def limpiar(valor, maximo=500):
    """Quita espacios sobrantes y recorta el texto que llega del formulario."""
    if valor is None:
        return ""
    return str(valor).strip()[:maximo]


def buscar_usuario(nombre_usuario):
    return consultar("SELECT * FROM usuarios WHERE usuario = ?",
                     (limpiar(nombre_usuario, 50),), uno=True)


def password_correcta(usuario, password):
    """Compara la contraseña escrita con el hash guardado."""
    if usuario is None:
        return False
    return check_password_hash(usuario["password_hash"], password or "")

SELECT_PACIENTE = """
SELECT p.*,
       (SELECT COUNT(*)              FROM sesiones s WHERE s.paciente_id = p.id)
           AS total_sesiones,
       (SELECT MAX(s.fecha)          FROM sesiones s WHERE s.paciente_id = p.id)
           AS ultima_sesion,
       (SELECT s.proxima_sesion      FROM sesiones s WHERE s.paciente_id = p.id
            ORDER BY s.fecha DESC, s.numero_sesion DESC LIMIT 1)
           AS proxima_sesion
FROM pacientes p
"""

def siguiente_expediente():
    """
    Genera el siguiente número de expediente: EXP-001, EXP-002, EXP-003...

    Busca el número más alto que ya existe y le suma uno, así nunca se repite.
    Además la columna es UNIQUE, que es la garantía definitiva.
    """
    maximo = 0
    for fila in consultar("SELECT expediente FROM pacientes"):
        numero = re.search(r"(\d+)$", fila["expediente"])
        if numero:
            maximo = max(maximo, int(numero.group(1)))
    return f"EXP-{maximo + 1:03d}"


def obtener_paciente(paciente_id):
    return consultar(SELECT_PACIENTE + " WHERE p.id = ?", (paciente_id,), uno=True)


def listar_pacientes(estado=None):
    """Lista los pacientes. `estado` puede ser 'Activo', 'Inactivo' o None."""
    if estado in ("Activo", "Inactivo"):
        return consultar(SELECT_PACIENTE + " WHERE p.estado = ? ORDER BY p.nombre",
                         (estado,))
    return consultar(SELECT_PACIENTE + " ORDER BY p.nombre")


def buscar_pacientes(termino):
    """
    Busca por nombre, número de expediente o teléfono.

    El texto se pasa como parámetro (?) y nunca se pega dentro del SQL:
    así no es posible una inyección SQL desde la barra de búsqueda.
    """
    patron = f"%{limpiar(termino, 60)}%"
    return consultar(
        SELECT_PACIENTE + """
        WHERE p.nombre     LIKE ? COLLATE NOCASE
           OR p.expediente LIKE ? COLLATE NOCASE
           OR p.telefono   LIKE ?
        ORDER BY p.nombre
        """,
        (patron, patron, patron),
    )


def contar_pacientes():
    """Devuelve cuántos pacientes hay activos e inactivos."""
    conteo = {"Activo": 0, "Inactivo": 0}
    for fila in consultar("SELECT estado, COUNT(*) AS total "
                          "FROM pacientes GROUP BY estado"):
        conteo[fila["estado"]] = fila["total"]
    return conteo


def guardar_paciente(datos, paciente_id=None):
    """
    Crea un paciente nuevo o actualiza uno existente.

    Si `paciente_id` es None, se crea (y se genera su número de expediente).
    Devuelve el id del paciente. Lanza ValueError si falta el nombre.
    """
    nombre = limpiar(datos.get("nombre"), 150)
    if not nombre:
        raise ValueError("El nombre del paciente es obligatorio.")

    fecha_nacimiento = limpiar(datos.get("fecha_nacimiento"), 10)
    edad = calcular_edad(fecha_nacimiento)
    if edad is None:
        try:
            edad = int(datos.get("edad")) if datos.get("edad") else None
        except (TypeError, ValueError):
            edad = None

    valores = (
        nombre,
        fecha_nacimiento or None,
        edad,
        limpiar(datos.get("sexo"), 20),
        limpiar(datos.get("ocupacion"), 100),
        limpiar(datos.get("telefono"), 20),
        limpiar(datos.get("correo"), 120),
        limpiar(datos.get("fecha_apertura"), 10) or hoy(),
        limpiar(datos.get("motivo_consulta"), 4000),
        limpiar(datos.get("antecedentes"), 4000),
        limpiar(datos.get("estado"), 20) or "Activo",
    )

    if paciente_id is None:
        return ejecutar(
            """INSERT INTO pacientes
               (nombre, fecha_nacimiento, edad, sexo, ocupacion, telefono,
                correo, fecha_apertura, motivo_consulta, antecedentes, estado,
                expediente)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            valores + (siguiente_expediente(),),
        )

    ejecutar(
        """UPDATE pacientes SET
             nombre = ?, fecha_nacimiento = ?, edad = ?, sexo = ?, ocupacion = ?,
             telefono = ?, correo = ?, fecha_apertura = ?, motivo_consulta = ?,
             antecedentes = ?, estado = ?
           WHERE id = ?""",
        valores + (paciente_id,),
    )
    return paciente_id


def cambiar_estado_paciente(paciente_id, estado):
    """Marca al paciente como Activo o Inactivo. No borra ninguna información."""
    if estado not in OPCIONES_ESTADO:
        raise ValueError("Estado no válido.")
    ejecutar("UPDATE pacientes SET estado = ? WHERE id = ?", (estado, paciente_id))


# ===========================================================================
# SESIONES
# ===========================================================================

def numero_siguiente_sesion(paciente_id):
    """Calcula qué número de sesión corresponde a este paciente."""
    fila = consultar(
        "SELECT COALESCE(MAX(numero_sesion), 0) + 1 AS siguiente "
        "FROM sesiones WHERE paciente_id = ?",
        (paciente_id,), uno=True,
    )
    return fila["siguiente"]


def obtener_sesion(sesion_id):
    """Devuelve una sesión junto con el nombre y expediente de su paciente."""
    return consultar(
        """SELECT s.*, p.nombre AS paciente_nombre, p.expediente
           FROM sesiones s
           JOIN pacientes p ON p.id = s.paciente_id
           WHERE s.id = ?""",
        (sesion_id,), uno=True,
    )


def listar_sesiones(paciente_id):
    """Historial de un paciente, de la sesión más antigua a la más reciente."""
    return consultar(
        "SELECT * FROM sesiones WHERE paciente_id = ? "
        "ORDER BY fecha, numero_sesion",
        (paciente_id,),
    )


def total_sesiones():
    return consultar("SELECT COUNT(*) AS total FROM sesiones", uno=True)["total"]


def guardar_sesion(paciente_id, datos, sesion_id=None):
    """
    Crea una nota de sesión nueva o corrige una existente.

    El número de sesión se calcula automáticamente al crearla y no cambia
    al editarla.
    """
    if obtener_paciente(paciente_id) is None:
        raise ValueError("El paciente indicado no existe.")

    avance = limpiar(datos.get("nivel_avance"), 20)
    if avance not in OPCIONES_AVANCE:
        avance = "Moderado"

    valores = (
        limpiar(datos.get("fecha"), 10) or hoy(),
        limpiar(datos.get("tema"), 200),
        limpiar(datos.get("resumen"), 5000),
        limpiar(datos.get("tareas"), 2000),
        avance,
        limpiar(datos.get("proxima_sesion"), 10) or None,
    )

    if sesion_id is None:
        return ejecutar(
            """INSERT INTO sesiones
               (fecha, tema, resumen, tareas, nivel_avance, proxima_sesion,
                paciente_id, numero_sesion)
               VALUES (?,?,?,?,?,?,?,?)""",
            valores + (paciente_id, numero_siguiente_sesion(paciente_id)),
        )

    ejecutar(
        """UPDATE sesiones SET
             fecha = ?, tema = ?, resumen = ?, tareas = ?,
             nivel_avance = ?, proxima_sesion = ?
           WHERE id = ?""",
        valores + (sesion_id,),
    )
    return sesion_id