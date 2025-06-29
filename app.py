from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import io
import pandas as pd

app = Flask(__name__)

# Configuración de la base de datos desde una variable de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de datos
class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    enlace = db.Column(db.String(500))
    fecha = db.Column(db.String(10))  # yyyy-mm-dd
    hora = db.Column(db.String(5))    # hh:mm

# Inicializar base de datos
def init_db():
    with app.app_context():
        db.create_all()

@app.route("/")
def index():
    hoy = date.today().strftime("%Y-%m-%d")
    nombres = ["Alicia", "Carmen", "Ceci", "Alvaro", "Kiko", "Iván", "Nico",
               "Javier", "Lucía", "Iñigo", "Manolo", "Raquel"]
    return render_template("index.html", hoy=hoy, nombres=nombres)

@app.route("/enviar", methods=["POST"])
def enviar():
    nombre = request.form["nombre"]
    fecha = request.form["fecha"]
    hora = datetime.now().strftime("%H:%M")
    enlaces = [e.strip() for e in request.form.getlist("enlace") if e.strip()]

    for enlace in enlaces:
        nuevo = Enlace(nombre=nombre, enlace=enlace, fecha=fecha, hora=hora)
        db.session.add(nuevo)

    db.session.commit()
    return redirect(url_for("index"))

@app.route("/revisar", methods=["GET", "POST"])
def revisar():
    hoy = date.today().strftime("%Y-%m-%d")
    fecha_filtrada = request.form.get("fecha") if request.method == "POST" else hoy
    enlaces = Enlace.query.filter_by(fecha=fecha_filtrada).order_by(Enlace.hora.asc()).all()
    return render_template("revisar.html", enlaces=enlaces, fecha=fecha_filtrada)

@app.route("/descargar_filtrados", methods=["POST"])
def descargar_filtrados():
    fecha = request.form.get("fecha")
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    return generar_excel(enlaces, f"enlaces_{fecha}.xlsx")

@app.route("/descargar_todo")
def descargar_todo():
    enlaces = Enlace.query.order_by(Enlace.fecha, Enlace.hora).all()
    return generar_excel(enlaces, "enlaces_completos.xlsx")

def generar_excel(enlaces, nombre_archivo):
    datos = [{
        "Nombre": e.nombre,
        "Enlace": e.enlace,
        "Fecha": e.fecha,
        "Hora": e.hora
    } for e in enlaces]

    df = pd.DataFrame(datos)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Enlaces")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=nombre_archivo, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/eliminar_duplicados")
def eliminar_duplicados():
    subquery = db.session.query(
        Enlace.enlace, Enlace.fecha, db.func.min(Enlace.id).label("min_id")
    ).group_by(Enlace.enlace, Enlace.fecha).subquery()

    duplicados = db.session.query(Enlace).join(
        subquery,
        (Enlace.enlace == subquery.c.enlace) &
        (Enlace.fecha == subquery.c.fecha) &
        (Enlace.id != subquery.c.min_id)
    ).all()

    for dup in duplicados:
        db.session.delete(dup)

    db.session.commit()
    return redirect(url_for('revisar'))

if __name__ == "__main__":
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"Error al crear la base de datos (quizás ya existe): {e}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
