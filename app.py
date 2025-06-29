from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
db = SQLAlchemy(app)

class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enlace = db.Column(db.String, nullable=False)
    fecha = db.Column(db.String, nullable=False)
    autor = db.Column(db.String, nullable=False)

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    equipo = db.Column(db.String, nullable=False)
    horario_lj = db.Column(db.String, nullable=False)
    horario_v = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def inicio():
    return render_template("inicio.html")

@app.route('/enviar', methods=["GET", "POST"])
def enviar():
    miembros = Miembro.query.all()
    if request.method == "POST":
        fecha = request.form["fecha"]
        autor = request.form["autor"]
        texto = request.form["enlaces"]
        enlaces = [line.strip() for line in texto.strip().splitlines() if line.strip()]
        for enlace in enlaces:
            if not Enlace.query.filter_by(enlace=enlace, fecha=fecha).first():
                nuevo = Enlace(enlace=enlace, fecha=fecha, autor=autor)
                db.session.add(nuevo)
        db.session.commit()
        return redirect("/basedatos")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template("enviar.html", fecha=fecha_hoy, miembros=miembros)

@app.route('/basedatos', methods=["GET", "POST"])
def basedatos():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_filtrada = request.form.get("fecha", fecha_hoy)
    datos = Enlace.query.filter_by(fecha=fecha_filtrada).all()
    return render_template("basedatos.html", datos=datos, fecha=fecha_filtrada)

@app.route('/descargar_filtrados', methods=["POST"])
def descargar_filtrados():
    fecha = request.form["fecha"]
    datos = Enlace.query.filter_by(fecha=fecha).all()
    df = pd.DataFrame([{"Fecha": d.fecha, "Autor": d.autor, "Enlace": d.enlace} for d in datos])
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name=f"enlaces_{fecha}.xlsx", as_attachment=True)

@app.route('/descargar_todo')
def descargar_todo():
    datos = Enlace.query.all()
    df = pd.DataFrame([{"Fecha": d.fecha, "Autor": d.autor, "Enlace": d.enlace} for d in datos])
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="enlaces_completos.xlsx", as_attachment=True)

# Rutas adicionales como /clipping y /equipo vendrán luego

if __name__ == '__main__':
    app.run(debug=True)
