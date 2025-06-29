from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os, io
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Enlace(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    nombre  = db.Column(db.String(50), nullable=False)
    enlace  = db.Column(db.String(500), nullable=False)
    fecha   = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    hora    = db.Column(db.String(5), nullable=False)   # HH:MM

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    hoy = date.today().strftime("%Y-%m-%d")
    nombres = ["Alicia","Carmen","Ceci","Alvaro","Kiko",
               "Iván","Nico","Javier","Lucía","Iñigo","Manolo","Raquel"]
    return render_template("index.html", hoy=hoy, nombres=nombres)

@app.route('/enviar', methods=['POST'])
def enviar():
    fecha = request.form["fecha"]
    nombre = request.form["nombre"]
    hora = datetime.now().strftime("%H:%M")
    texto = request.form.get("enlaces","")
    enlaces = [e.strip() for e in texto.split('\n') if e.strip()]

    for url in enlaces:
        db.session.add(Enlace(nombre=nombre, enlace=url, fecha=fecha, hora=hora))
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/basedatos', methods=['GET'])
def basedatos():
    # Si ?all=true, mostramos todos
    if request.args.get("all") == "true":
        datos = Enlace.query.order_by(Enlace.fecha.desc(), Enlace.hora.desc()).all()
        fecha = None
    else:
        # Filtrar por fecha o, si no viene, por hoy
        fecha = request.args.get("fecha") or date.today().strftime("%Y-%m-%d")
        datos = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora.asc()).all()

    return render_template("basedatos.html", datos=datos, fecha=fecha)

@app.route('/descargar_filtrados', methods=['GET'])
def descargar_filtrados():
    fecha = request.args.get("fecha")
    registros = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora).all()
    return _generar_excel(registros, f"enlaces_{fecha}.xlsx")

@app.route('/descargar_todos', methods=['GET'])
def descargar_todos():
    registros = Enlace.query.order_by(Enlace.fecha.desc(), Enlace.hora.desc()).all()
    return _generar_excel(registros, "enlaces_completos.xlsx")

def _generar_excel(registros, filename):
    data = [{
        "Nombre": r.nombre,
        "Enlace": r.enlace,
        "Fecha": r.fecha,
        "Hora": r.hora
    } for r in registros]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Enlaces")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/eliminar_duplicados', methods=['POST'])
def eliminar_duplicados():
    subq = db.session.query(
        Enlace.enlace, Enlace.fecha,
        db.func.min(Enlace.id).label("min_id")
    ).group_by(Enlace.enlace, Enlace.fecha).subquery()

    duplicados = db.session.query(Enlace).join(
        subq,
        (Enlace.enlace == subq.c.enlace) &
        (Enlace.fecha == subq.c.fecha) &
        (Enlace.id != subq.c.min_id)
    ).all()

    for dup in duplicados:
        db.session.delete(dup)
    db.session.commit()

    return redirect(url_for("basedatos"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
