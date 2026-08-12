from functools import wraps

from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for,
)

import base_datos as bd

app = Flask(__name__)

app.secret_key = "clave-del-sistema-de-pacientes-cambiar-en-produccion"

app.teardown_appcontext(bd.cerrar)

app.jinja_env.filters["fecha"] = bd.formato_fecha
app.jinja_env.globals["hoy"] = bd.hoy


def login_requerido(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Inicia sesión para entrar al sistema.", "aviso")
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltorio


def obtener_paciente_o_404(paciente_id):
    """Busca un paciente y muestra la página de error 404 si no existe."""
    paciente = bd.obtener_paciente(paciente_id)
    if paciente is None:
        abort(404)
    return paciente


@app.route("/login", methods=["GET", "POST"])
def login():
    """Pantalla de inicio de sesión."""
    if request.method == "POST":
        usuario = bd.buscar_usuario(request.form.get("usuario", ""))
        if bd.password_correcta(usuario, request.form.get("password", "")):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            return redirect(url_for("inicio"))
        # Mensaje genérico a propósito: no revela si el usuario existe
        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "exito")
    return redirect(url_for("login"))


@app.route("/")
@login_requerido
def inicio():
    """Panel con los totales y los accesos a las funciones principales."""
    conteo = bd.contar_pacientes()
    return render_template(
        "inicio.html",
        activos=conteo["Activo"],
        inactivos=conteo["Inactivo"],
        total_sesiones=bd.total_sesiones(),
        recientes=bd.listar_pacientes("Activo")[:5],
    )

@app.route("/pacientes")
@login_requerido
def pacientes():
    """Listado de pacientes con buscador."""
    termino = request.args.get("q", "").strip()
    if termino:
        lista = bd.buscar_pacientes(termino)
    else:
        lista = bd.listar_pacientes()
    return render_template("pacientes.html", pacientes=lista, termino=termino)


@app.route("/pacientes/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_paciente():
    """Formulario de alta. El número de expediente se genera solo."""
    if request.method == "POST":
        try:
            paciente_id = bd.guardar_paciente(request.form)
            flash("Paciente registrado correctamente.", "exito")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
        except ValueError as error:
            flash(str(error), "error")

    return render_template(
        "formulario_paciente.html",
        titulo="Nuevo paciente",
        paciente=None,
        expediente=bd.siguiente_expediente(),
        opciones_sexo=bd.OPCIONES_SEXO,
        opciones_estado=bd.OPCIONES_ESTADO,
    )

@app.route("/pacientes/<int:paciente_id>")
@login_requerido
def ver_paciente(paciente_id):
    """Ficha del paciente con su resumen y sus últimas sesiones."""
    paciente = obtener_paciente_o_404(paciente_id)
    sesiones = bd.listar_sesiones(paciente_id)
    return render_template(
        "paciente.html",
        paciente=paciente,
        sesiones=list(reversed(sesiones))[:5],
        total=len(sesiones),
    )

@app.route("/pacientes/<int:paciente_id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_paciente(paciente_id):
    """Formulario de edición. El expediente no se modifica nunca."""
    paciente = obtener_paciente_o_404(paciente_id)

    if request.method == "POST":
        try:
            bd.guardar_paciente(request.form, paciente_id)
            flash("Datos actualizados.", "exito")
            return redirect(url_for("ver_paciente", paciente_id=paciente_id))
        except ValueError as error:
            flash(str(error), "error")

    return render_template(
        "formulario_paciente.html",
        titulo="Editar paciente",
        paciente=paciente,
        expediente=paciente["expediente"],
        opciones_sexo=bd.OPCIONES_SEXO,
        opciones_estado=bd.OPCIONES_ESTADO,
    )


@app.route("/pacientes/<int:paciente_id>/estado", methods=["POST"])
@login_requerido
def cambiar_estado(paciente_id):
    """
    Da de alta o de baja a un paciente.
    Un paciente inactivo conserva toda su información y puede reactivarse.
    """
    obtener_paciente_o_404(paciente_id)
    try:
        estado = request.form.get("estado", "")
        bd.cambiar_estado_paciente(paciente_id, estado)
        flash(f"Paciente marcado como {estado.lower()}. "
              f"Su información se conserva.", "exito")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("ver_paciente", paciente_id=paciente_id))


@app.route("/pacientes/<int:paciente_id>/sesiones")
@login_requerido
def historial(paciente_id):
    """Historial completo de sesiones, en orden cronológico."""
    paciente = obtener_paciente_o_404(paciente_id)
    return render_template("historial.html", paciente=paciente,
                           sesiones=bd.listar_sesiones(paciente_id))


@app.route("/pacientes/<int:paciente_id>/sesiones/nueva", methods=["GET", "POST"])
@login_requerido
def nueva_sesion(paciente_id):
    """Formulario de nota de sesión. El número se calcula automáticamente."""
    paciente = obtener_paciente_o_404(paciente_id)

    if request.method == "POST":
        try:
            bd.guardar_sesion(paciente_id, request.form)
            flash("Sesión registrada correctamente.", "exito")
            return redirect(url_for("historial", paciente_id=paciente_id))
        except ValueError as error:
            flash(str(error), "error")

    return render_template(
        "formulario_sesion.html",
        titulo="Nueva sesión",
        paciente=paciente,
        sesion=None,
        numero=bd.numero_siguiente_sesion(paciente_id),
        opciones_avance=bd.OPCIONES_AVANCE,
    )

@app.route("/sesiones/<int:sesion_id>")
@login_requerido
def ver_sesion(sesion_id):
    """Nota de sesión completa."""
    sesion = bd.obtener_sesion(sesion_id)
    if sesion is None:
        abort(404)
    return render_template("sesion.html", sesion=sesion)

@app.route("/sesiones/<int:sesion_id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_sesion(sesion_id):
    """Corrige una nota registrada por error."""
    sesion = bd.obtener_sesion(sesion_id)
    if sesion is None:
        abort(404)
    paciente = bd.obtener_paciente(sesion["paciente_id"])

    if request.method == "POST":
        bd.guardar_sesion(sesion["paciente_id"], request.form, sesion_id)
        flash("Sesión actualizada.", "exito")
        return redirect(url_for("ver_sesion", sesion_id=sesion_id))

    return render_template(
        "formulario_sesion.html",
        titulo="Editar sesión",
        paciente=paciente,
        sesion=sesion,
        numero=sesion["numero_sesion"],
        opciones_avance=bd.OPCIONES_AVANCE,
    )

@app.errorhandler(404)
def no_encontrado(error):
    return render_template("error.html"), 404


if __name__ == "__main__":
    bd.crear_tablas()          
    print("\n  Sistema de Registro de Pacientes y Sesiones")
    print("  Abre en el navegador:  http://127.0.0.1:5000")
    print("  Usuario: psicologa   Contraseña: psicologa123\n")
    app.run(host="127.0.0.1", port=5000, debug=True)