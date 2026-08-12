from datetime import date, timedelta

from app import app
import base_datos as bd

HOY = date.today()


def dias(n):
    """Fecha de hoy desplazada n días."""
    return (HOY + timedelta(days=n)).isoformat()


PACIENTES = [
    {
        "paciente": {
            "nombre": "Ashly Ejemplo Ficticia",
            "fecha_nacimiento": "2003-10-20", "sexo": "Mujer",
            "ocupacion": "Diseñadora (ficticio)", "telefono": "5550000001",
            "correo": "ashly@ejemplo.invalid", "fecha_apertura": dias(-35),
            "motivo_consulta": "Dato ficticio: Refiere malestar ante situaciones "
                               "de evaluación en el trabajo.",
            "antecedentes": "Dato ficticio: Proceso psicológico previo de seis meses.",
            "estado": "Activo",
        },
        "sesiones": [
            {"fecha": dias(-35), "tema": "Encuadre y motivo de consulta",
             "resumen": "Sesión de ejemplo. Se establece el encuadre y se explora "
                        "el motivo de consulta.",
             "tareas": "Registro diario de situaciones (ficticio).",
             "nivel_avance": "Moderado", "proxima_sesion": dias(-28)},
            {"fecha": dias(-28), "tema": "Psicoeducación",
             "resumen": "Sesión de ejemplo sobre el funcionamiento de la ansiedad.",
             "tareas": "Lectura del material entregado.",
             "nivel_avance": "Moderado", "proxima_sesion": dias(-21)},
            {"fecha": dias(-21), "tema": "Identificación de pensamientos",
             "resumen": "Sesión de ejemplo.", "tareas": "Continuar el registro.",
             "nivel_avance": "Moderado", "proxima_sesion": dias(-14)},
            {"fecha": dias(-14), "tema": "Reestructuración cognitiva",
             "resumen": "Sesión de ejemplo.", "tareas": "Practicar lo trabajado.",
             "nivel_avance": "Alto", "proxima_sesion": dias(-7)},
            {"fecha": dias(-7), "tema": "Revisión de avances",
             "resumen": "Sesión de ejemplo.", "tareas": "",
             "nivel_avance": "Alto", "proxima_sesion": dias(3)},
        ],
    },
    {
        "paciente": {
            "nombre": "Diego Ejemplo Ficticio",
            "fecha_nacimiento": "2005-12-02", "sexo": "Hombre",
            "ocupacion": "Ingeniero (ficticio)", "telefono": "5550000002",
            "correo": "diego@ejemplo.invalid", "fecha_apertura": dias(-56),
            "motivo_consulta": "Dato ficticio: dificultades para conciliar el sueño.",
            "antecedentes": "Dato ficticio: seguimiento con medicina general.",
            "estado": "Activo",
        },
        "sesiones": [
            {"fecha": dias(-56), "tema": "Encuadre",
             "resumen": "Sesión de ejemplo.", "tareas": "Registro de sueño.",
             "nivel_avance": "Bajo", "proxima_sesion": dias(-42)},
            {"fecha": dias(-42), "tema": "Higiene del sueño",
             "resumen": "Sesión de ejemplo.", "tareas": "Aplicar las pautas.",
             "nivel_avance": "Moderado", "proxima_sesion": dias(-28)},
            {"fecha": dias(-28), "tema": "Técnicas de relajación",
             "resumen": "Sesión de ejemplo.", "tareas": "Practicar a diario.",
             "nivel_avance": "Moderado", "proxima_sesion": dias(1)},
        ],
    },
    {
        "paciente": {
            "nombre": "Astrid Ejemplo Ficticia",
            "fecha_nacimiento": "2003-07-19", "sexo": "Mujer",
            "ocupacion": "Estudiante (ficticio)", "telefono": "5550000003",
            "correo": "astrid@ejemplo.invalid", "fecha_apertura": dias(-120),
            "motivo_consulta": "Dato ficticio: orientación vocacional.",
            "antecedentes": "Sin antecedentes relevantes (ficticio).",
            "estado": "Inactivo",
        },
        "sesiones": [
            {"fecha": dias(-120), "tema": "Encuadre",
             "resumen": "Sesión de ejemplo.", "tareas": "",
             "nivel_avance": "Moderado", "proxima_sesion": dias(-106)},
            {"fecha": dias(-106), "tema": "Clarificación de intereses",
             "resumen": "Sesión de ejemplo. Cierre del proceso.", "tareas": "",
             "nivel_avance": "Alto", "proxima_sesion": None},
        ],
    },
    {
        "paciente": {
            "nombre": "Daniel Ejemplo Ficticio",
            "fecha_nacimiento": "1975-01-30", "sexo": "Hombre",
            "ocupacion": "Docente (ficticio)", "telefono": "5550000004",
            "correo": "daniel@ejemplo.invalid", "fecha_apertura": dias(-5),
            "motivo_consulta": "Dato ficticio: proceso de duelo.",
            "antecedentes": "", "estado": "Activo",
        },
        "sesiones": [],
    },
]


def cargar():
    bd.crear_tablas()
    with app.app_context():
        if bd.consultar("SELECT COUNT(*) AS t FROM pacientes", uno=True)["t"]:
            print("La base de datos ya tiene pacientes. No se ha añadido nada.")
            print("Si quieres empezar de cero, borra el archivo datos/sistema.db")
            return

        for registro in PACIENTES:
            paciente_id = bd.guardar_paciente(registro["paciente"])
            for sesion in registro["sesiones"]:
                bd.guardar_sesion(paciente_id, sesion)
            paciente = bd.obtener_paciente(paciente_id)
            print(f"  {paciente['expediente']}  {paciente['nombre']}  "
                  f"({len(registro['sesiones'])} sesiones)")

        print("\nDatos de ejemplo cargados. Todos son ficticios.")
        print("Arranca el sistema con:  python app.py")


if __name__ == "__main__":
    cargar()