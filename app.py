from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = 'clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///enlaces.db')
db = SQLAlchemy(app)

class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20))
    remitente = db.Column(db.String(50))
    enlace = db.Column(db.String(500))
    identificador = db.Column(db.String(50))

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)
    horario_lj = db.Column(db.String(50))
    horario_v = db.Column(db.String(50))
    equipo = db.Column(db.String(1))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    if request.method == 'POST':
        fecha = request.form['fecha']
        remitente = request.form['remitente']
        texto = request.form['texto']
        enlaces = list(set([line.strip() for line in texto.splitlines() if line.strip()]))
        for i, enlace in enumerate(enlaces, start=1):
            identificador = f"{fecha.replace('-', '_')}_{i:02d}"
            nuevo_enlace = Enlace(fecha=fecha, remitente=remitente, enlace=enlace, identificador=identificador)
            db.session.add(nuevo_enlace)
        db.session.commit()
        return redirect(url_for('basedatos'))
    hoy = datetime.today().strftime('%Y-%m-%d')
    miembros = Miembro.query.order_by(Miembro.nombre).all()
    return render_template('enviar.html', hoy=hoy, miembros=miembros)

@app.route('/basedatos', methods=['GET', 'POST'])
def basedatos():
    hoy = datetime.today().strftime('%Y-%m-%d')
    fecha = request.form.get('fecha', hoy)
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    return render_template('basedatos.html', enlaces=enlaces, fecha=fecha)

@app.route('/descargar_filtrados', methods=['POST'])
def descargar_filtrados():
    fecha = request.form.get('fecha')
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    df = pd.DataFrame([(e.fecha, e.remitente, e.enlace, e.identificador) for e in enlaces],
                      columns=['Fecha', 'Remitente', 'Enlace', 'Identificador'])
    nombre_archivo = f"clipping_{fecha}.xlsx"
    df.to_excel(nombre_archivo, index=False)
    return send_file(nombre_archivo, as_attachment=True)

@app.route('/descargar_todo')
def descargar_todo():
    enlaces = Enlace.query.all()
    df = pd.DataFrame([(e.fecha, e.remitente, e.enlace, e.identificador) for e in enlaces],
                      columns=['Fecha', 'Remitente', 'Enlace', 'Identificador'])
    df.to_excel("todos_los_enlaces.xlsx", index=False)
    return send_file("todos_los_enlaces.xlsx", as_attachment=True)

@app.route('/eliminar_duplicados')
def eliminar_duplicados():
    vistos = set()
    duplicados = []
    for e in Enlace.query.order_by(Enlace.fecha, Enlace.enlace).all():
        clave = (e.fecha, e.enlace)
        if clave in vistos:
            duplicados.append(e)
        else:
            vistos.add(clave)
    for dup in duplicados:
        db.session.delete(dup)
    db.session.commit()
    return redirect(url_for('basedatos'))

@app.route('/clipping')
def clipping():
    hoy = datetime.today().strftime('%Y-%m-%d')
    enlaces = Enlace.query.filter_by(fecha=hoy).all()
    enlaces_unicos = list({e.enlace: e for e in enlaces}.values())
    random.shuffle(enlaces_unicos)
    grupos = [[], [], []]
    for i, enlace in enumerate(enlaces_unicos):
        grupos[i % 3].append(enlace)

    miembros = Miembro.query.order_by(Miembro.nombre).all()
    random.shuffle(miembros)
    grupos_miembros = [miembros[i::3] for i in range(3)]
    dia_semana = datetime.today().weekday()
    es_viernes = dia_semana == 4

    horarios = {}
    for m in miembros:
        horarios[m.nombre] = m.horario_v if es_viernes else m.horario_lj

    return render_template('clipping.html', grupos=grupos, grupos_miembros=grupos_miembros, horarios=horarios)

@app.route('/equipo', methods=['GET', 'POST'])
def equipo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        horario_lj = request.form['horario_lj']
        horario_v = request.form['horario_v']
        equipo = request.form['equipo']
        miembro = Miembro.query.filter_by(nombre=nombre).first()
        if not miembro:
            nuevo = Miembro(nombre=nombre, horario_lj=horario_lj, horario_v=horario_v, equipo=equipo)
            db.session.add(nuevo)
        else:
            miembro.horario_lj = horario_lj
            miembro.horario_v = horario_v
            miembro.equipo = equipo
        db.session.commit()
    miembros = Miembro.query.order_by(Miembro.nombre).all()
    return render_template('equipo.html', miembros=miembros)

@app.route('/limpiar', methods=['POST'])
def limpiar():
    password = request.form['password']
    if password == '1234':
        db.session.query(Enlace).delete()
        db.session.commit()
        flash("Base de datos limpiada", "success")
    else:
        flash("Contraseña incorrecta", "error")
    return redirect(url_for('basedatos'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
