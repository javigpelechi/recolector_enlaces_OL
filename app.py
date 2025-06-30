from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import io
import random

app = Flask(__name__)
app.secret_key = "supersecreto"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///basedatos.db"
db = SQLAlchemy(app)

from models import Enlace, MiembroEquipo

# Precarga inicial
def precargar_miembros():
    if MiembroEquipo.query.first():
        return
    miembros = [
        ("Alicia", "A", "11:30 - 13:30", "11:30 - 13:30"),
        ("Carmen", "A", "13:30 - 15:30", "13:30 - 15:30"),
        ("Ceci", "A", "15:30 - 17:30", "15:30 - 17:30"),
        ("Alvaro", "A", "17:30 - 19:30", "13:30 - 15:30"),
        ("Kiko", "A", "11:30 - 13:30", "11:30 - 13:30"),
        ("Iván", "A", "13:30 - 15:30", "13:30 - 15:30"),
        ("Nico", "B", "15:30 - 17:30", "15:30 - 17:30"),
        ("Javier", "B", "17:30 - 19:30", "15:30 - 17:30"),
        ("Lucía", "B", "11:30 - 13:30", "11:30 - 13:30"),
        ("Iñigo", "B", "13:30 - 15:30", "13:30 - 15:30"),
        ("Manolo", "B", "15:30 - 17:30", "15:30 - 17:30"),
        ("Raquel", "B", "17:30 - 19:30", "11:30 - 13:30"),
    ]
    for nombre, equipo, h_lj, h_v in miembros:
        db.session.add(MiembroEquipo(nombre=nombre, equipo=equipo, horario_lj=h_lj, horario_v=h_v))
    db.session.commit()

@app.before_request
def before_request_func():
    precargar_miembros()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/enviar", methods=["GET", "POST"])
def enviar():
    miembros = MiembroEquipo.query.all()
    hoy = datetime.today().strftime('%Y-%m-%d')
    if request.method == "POST":
        nombre = request.form["nombre"]
        fecha = request.form["fecha"]
        texto = request.form["texto"]
        enlaces = [l.strip() for l in texto.strip().split("\n") if l.strip()]
        for i, enlace in enumerate(enlaces, start=1):
            identificador = f'{fecha.replace("-", "_")}_{i:02d}'
            db.session.add(Enlace(nombre=nombre, fecha=fecha, enlace=enlace, identificador=identificador))
        db.session.commit()
        flash("Enlaces enviados correctamente.")
        return redirect(url_for("enviar"))
    return render_template("enviar.html", miembros=miembros, hoy=hoy)

@app.route("/basedatos")
def basedatos():
    fecha = request.args.get("fecha")
    if fecha:
        datos = Enlace.query.filter_by(fecha=fecha).all()
    else:
        datos = Enlace.query.all()
    return render_template("basedatos.html", datos=datos)

@app.route("/eliminar_duplicados")
def eliminar_duplicados():
    enlaces = Enlace.query.order_by(Enlace.fecha, Enlace.enlace).all()
    vistos = set()
    for enlace in enlaces:
        clave = (enlace.fecha, enlace.enlace)
        if clave in vistos:
            db.session.delete(enlace)
        else:
            vistos.add(clave)
    db.session.commit()
    flash("Duplicados eliminados.")
    return redirect(url_for("basedatos"))

@app.route("/descargar")
def descargar():
    fecha = request.args.get("fecha")
    if fecha:
        datos = Enlace.query.filter_by(fecha=fecha).all()
    else:
        datos = Enlace.query.all()
    if not datos:
        flash("No hay datos para exportar.")
        return redirect(url_for("basedatos"))
    df = pd.DataFrame([(d.fecha, d.nombre, d.enlace, d.identificador) for d in datos],
                      columns=["Fecha", "Nombre", "Enlace", "Identificador"])
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="datos.xlsx", as_attachment=True)

@app.route("/borrar_basedatos", methods=["POST"])
def borrar_basedatos():
    clave = request.form.get("clave")
    if clave != "1234":
        flash("Contraseña incorrecta.")
    else:
        db.session.query(Enlace).delete()
        db.session.commit()
        flash("Base de datos eliminada.")
    return redirect(url_for("basedatos"))

@app.route("/equipo", methods=["GET", "POST"])
def equipo():
    if request.method == "POST":
        nombre = request.form["nombre"]
        equipo = request.form["equipo"]
        horario_lj = request.form["horario_lj"]
        horario_v = request.form["horario_v"]
        db.session.add(MiembroEquipo(nombre=nombre, equipo=equipo,
                                     horario_lj=horario_lj, horario_v=horario_v))
        db.session.commit()
        flash("Miembro añadido.")
        return redirect(url_for("equipo"))
    miembros = MiembroEquipo.query.all()
    return render_template("equipo.html", miembros=miembros)

@app.route("/eliminar_miembro/<int:id>")
def eliminar_miembro(id):
    miembro = MiembroEquipo.query.get(id)
    db.session.delete(miembro)
    db.session.commit()
    flash("Miembro eliminado.")
    return redirect(url_for("equipo"))

@app.route("/clippings")
def clippings():
    fecha = request.args.get("fecha", datetime.today().strftime('%Y-%m-%d'))
    datos = Enlace.query.filter_by(fecha=fecha).all()
    if not datos:
        flash("No hay enlaces para esta fecha.")
        return redirect(url_for("home"))
    equipos = {"Equipo 1": [], "Equipo 2": [], "Equipo 3": []}
    random.shuffle(datos)
    for i, enlace in enumerate(datos):
        equipos[f"Equipo {(i % 3) + 1}"].append(enlace)
    return render_template("clippings.html", equipos=equipos, fecha=fecha)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        precargar_miembros()
    app.run(debug=True)
