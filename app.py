from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os, io
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Necesario para flash/message, si decides usarlo
app.secret_key = os.environ.get("SECRET_KEY", "un-secretillo")

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
    # Filtrado por fecha o todos
    all_flag = request.args.get("all") == "true"
    if all_flag:
        registros = Enlace.query.order_by(Enlace.fecha.desc(), Enlace.hora.desc()).all()
        fecha = None
    else:
        fecha = request.args.get("fecha") or date.today().strftime("%Y-%m-%d")
        registros = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora.asc()).all()

    # Generar lista con identificadores
    datos = []
    # Si filtramos por fecha, solo esas; si no, agrupamos por fecha
    if all_flag:
        # agrupar por fecha y resetear contador por grupo
        from itertools import groupby
        for f, group in groupby(registros, key=lambda e: e.fecha):
            for i, r in enumerate(group, start=1):
                yyyy,mm,dd = f.split('-')
                ident = f"{dd}_{mm}_{yyyy[2:]}_{i:02d}"
                datos.append((r, ident))
    else:
        # solo una fecha
        for i, r in enumerate(registros, start=1):
            yyyy,mm,dd = r.fecha.split('-')
            ident = f"{dd}_{mm}_{yyyy[2:]}_{i:02d}"
            datos.append((r, ident))

    return render_template("basedatos.html",
                           datos=datos,
                           fecha=fecha,
                           all_flag=all_flag)

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
        "ID":        ident,
        "Fecha":     r.fecha,
        "Hora":      r.hora,
        "Nombre":    r.nombre,
        "Enlace":    r.enlace
    } for r, ident in [
        *((r, f"{r.fecha.split('-')[2]}_{r.fecha.split('-')[1]}_{r.fecha.split('-')[0][2:]}_{i:02d}")
          for i, r in enumerate(registros, start=1))
    ]]

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

@app.route('/limpiar_base', methods=['POST'])
def limpiar_base():
    passwd = request.form.get("password", "")
    if passwd != "1234":
        return "Contraseña incorrecta. <a href='/basedatos'>Volver</a>", 403
    Enlace.query.delete()
    db.session.commit()
    return redirect(url_for("basedatos"))

if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
