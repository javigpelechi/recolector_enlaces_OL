from flask import Flask, render_template, request, redirect, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import io
import random
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enlaces.db'
db = SQLAlchemy(app)

from models import Enlace, Miembro

@app.before_first_request
def crear_tablas():
    db.create_all()
    if not Miembro.query.first():
        miembros_iniciales = [
            Miembro(nombre="Alicia", equipo="A", horario_lj="11:30 - 13:30", horario_v="11:30 - 13:30"),
            Miembro(nombre="Carmen", equipo="A", horario_lj="13:30 - 15:30", horario_v="13:30 - 15:30"),
            Miembro(nombre="Ceci", equipo="A", horario_lj="15:30 - 17:30", horario_v="15:30 - 17:30"),
            Miembro(nombre="Alvaro", equipo="A", horario_lj="17:30 - 19:30", horario_v="13:30 - 15:30"),
            Miembro(nombre="Kiko", equipo="A", horario_lj="11:30 - 13:30", horario_v="11:30 - 13:30"),
            Miembro(nombre="Iván", equipo="A", horario_lj="13:30 - 15:30", horario_v="13:30 - 15:30"),
            Miembro(nombre="Nico", equipo="B", horario_lj="15:30 - 17:30", horario_v="15:30 - 17:30"),
            Miembro(nombre="Javier", equipo="B", horario_lj="17:30 - 19:30", horario_v="15:30 - 17:30"),
            Miembro(nombre="Lucía", equipo="B", horario_lj="11:30 - 13:30", horario_v="11:30 - 13:30"),
            Miembro(nombre="Iñigo", equipo="B", horario_lj="13:30 - 15:30", horario_v="13:30 - 15:30"),
            Miembro(nombre="Manolo", equipo="B", horario_lj="15:30 - 17:30", horario_v="15:30 - 17:30"),
            Miembro(nombre="Raquel", equipo="B", horario_lj="17:30 - 19:30", horario_v="11:30 - 13:30"),
        ]
        db.session.add_all(miembros_iniciales)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    miembros = Miembro.query.all()
    hoy = datetime.today().strftime('%Y-%m-%d')
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha = request.form['fecha']
        enlaces = request.form['enlaces'].strip().splitlines()
        for idx, enlace in enumerate(enlaces):
            nuevo = Enlace(nombre=nombre, fecha=fecha, enlace=enlace.strip())
            db.session.add(nuevo)
        db.session.commit()
        return redirect('/basedatos')
    return render_template('enviar.html', miembros=miembros, hoy=hoy)

@app.route('/basedatos', methods=['GET', 'POST'])
def basedatos():
    enlaces = []
    fecha = datetime.today().strftime('%Y-%m-%d')
    if request.method == 'POST':
        if 'filtrar' in request.form:
            fecha = request.form['fecha']
            enlaces = Enlace.query.filter_by(fecha=fecha).all()
        elif 'ver_todos' in request.form:
            enlaces = Enlace.query.order_by(Enlace.fecha.desc()).all()
        elif 'descargar' in request.form:
            fecha = request.form['fecha']
            enlaces = Enlace.query.filter_by(fecha=fecha).all()
            return exportar_excel(enlaces, f"enlaces_filtrados_{fecha}.xlsx")
        elif 'descargar_todo' in request.form:
            enlaces = Enlace.query.all()
            return exportar_excel(enlaces, "enlaces_todos.xlsx")
        elif 'borrar' in request.form:
            if request.form.get("password") == "1234":
                Enlace.query.delete()
                db.session.commit()
                flash("Base de datos borrada correctamente", "success")
            else:
                flash("Contraseña incorrecta", "danger")
        elif 'eliminar_duplicados' in request.form:
            enlaces = Enlace.query.order_by(Enlace.fecha, Enlace.enlace).all()
            vistos = set()
            for e in enlaces:
                clave = (e.fecha, e.enlace)
                if clave in vistos:
                    db.session.delete(e)
                else:
                    vistos.add(clave)
            db.session.commit()
    return render_template('basedatos.html', enlaces=enlaces, fecha=fecha)

def exportar_excel(enlaces, nombre_archivo):
    datos = [{'Nombre': e.nombre, 'Fecha': e.fecha, 'Enlace': e.enlace, 'Identificador': e.identificador} for e in enlaces]
    df = pd.DataFrame(datos)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name=nombre_archivo, as_attachment=True)

@app.route('/equipo', methods=['GET', 'POST'])
def equipo():
    if request.method == 'POST':
        if 'añadir' in request.form:
            nuevo = Miembro(
                nombre=request.form['nombre'],
                equipo=request.form['equipo'],
                horario_lj=request.form['horario_lj'],
                horario_v=request.form['horario_v']
            )
            db.session.add(nuevo)
            db.session.commit()
        elif 'eliminar' in request.form:
            id_borrar = request.form.get('id_borrar')
            Miembro.query.filter_by(id=id_borrar).delete()
            db.session.commit()
    miembros = Miembro.query.all()
    return render_template('equipo.html', miembros=miembros)

@app.route('/clipping', methods=['GET', 'POST'])
def clipping():
    hoy = datetime.today().strftime('%Y-%m-%d')
    fecha = request.form.get("fecha", hoy)
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    enlaces_filtrados = list({e.enlace for e in enlaces})
    random.shuffle(enlaces_filtrados)
    grupos = [[], [], []]
    for idx, enlace in enumerate(enlaces_filtrados):
        grupos[idx % 3].append(enlace)

    miembros = Miembro.query.all()
    random.shuffle(miembros)
    equipos = [[], [], []]
    for idx, m in enumerate(miembros):
        equipos[idx % 3].append(m)

    dia_semana = datetime.strptime(fecha, "%Y-%m-%d").weekday()
    es_viernes = dia_semana == 4
    return render_template('clipping.html', grupos=grupos, equipos=equipos, fecha=fecha, es_viernes=es_viernes)

if __name__ == '__main__':
    app.run(debug=True)
