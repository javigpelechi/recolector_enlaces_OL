import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
import pandas as pd

# Configuración inicial
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Lectura segura de la variable de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida. Asegúrate de configurar esta variable en Render.")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definición de modelos
class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10), nullable=False)
    autor = db.Column(db.String(50), nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    identificador = db.Column(db.String(20), nullable=True)

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    team = db.Column(db.String(1))
    horario_lj = db.Column(db.String(50))
    horario_v = db.Column(db.String(50))

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    miembros = Miembro.query.all()
    if request.method == 'POST':
        fecha = request.form['fecha']
        autor = request.form['autor']
        texto = request.form['enlaces']
        enlaces = [line.strip() for line in texto.splitlines() if line.strip()]
        for enlace in enlaces:
            nuevo = Enlace(fecha=fecha, autor=autor, enlace=enlace)
            db.session.add(nuevo)
        db.session.commit()
        flash(f'Se han enviado {len(enlaces)} enlaces.')
        return redirect(url_for('enviar'))
    fecha_hoy = datetime.today().strftime('%Y-%m-%d')
    return render_template('enviar.html', miembros=miembros, fecha_hoy=fecha_hoy)

@app.route('/basedatos')
def basedatos():
    fechas = db.session.query(Enlace.fecha).distinct().all()
    return render_template('basedatos.html', fechas=[f[0] for f in fechas])

@app.route('/ver_fecha/<fecha>')
def ver_fecha(fecha):
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    return render_template('ver_fecha.html', fecha=fecha, enlaces=enlaces)

@app.route('/ver_todo')
def ver_todo():
    enlaces = Enlace.query.order_by(Enlace.fecha.desc()).all()
    return render_template('ver_todo.html', enlaces=enlaces)

@app.route('/eliminar_duplicados')
def eliminar_duplicados():
    vistos = set()
    duplicados = []
    enlaces = Enlace.query.order_by(Enlace.fecha, Enlace.enlace).all()
    for e in enlaces:
        clave = (e.fecha, e.enlace)
        if clave in vistos:
            duplicados.append(e)
        else:
            vistos.add(clave)
    for dup in duplicados:
        db.session.delete(dup)
    db.session.commit()
    flash(f'Eliminados {len(duplicados)} duplicados.')
    return redirect(url_for('basedatos'))

@app.route('/descargar/<fecha>')
def descargar(fecha):
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    for i, enlace in enumerate(enlaces, start=1):
        enlace.identificador = f"{fecha.replace('-', '_')}_{i:02d}"
    db.session.commit()

    df = pd.DataFrame(
        [(e.fecha, e.autor, e.identificador, e.enlace) for e in enlaces],
        columns=['Fecha', 'Autor', 'Identificador', 'Enlace']
    )
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f'{fecha}_enlaces.xlsx')

@app.route('/limpiar_bd', methods=['POST'])
def limpiar_bd():
    password = request.form.get('password')
    if password == "1234":
        Enlace.query.delete()
        db.session.commit()
        flash("Base de datos limpiada correctamente.", "success")
    else:
        flash("Contraseña incorrecta.", "danger")
    return redirect(url_for('basedatos'))

@app.route('/gestion_equipo', methods=['GET', 'POST'])
def gestion_equipo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        team = request.form['team']
        horario_lj = request.form['horario_lj']
        horario_v = request.form['horario_v']
        nuevo = Miembro(nombre=nombre, team=team, horario_lj=horario_lj, horario_v=horario_v)
        db.session.add(nuevo)
        db.session.commit()
        flash("Miembro añadido.")
        return redirect(url_for('gestion_equipo'))
    miembros = Miembro.query.order_by(Miembro.nombre).all()
    return render_template('gestion_equipo.html', miembros=miembros)

@app.route('/borrar_miembro/<int:id>')
def borrar_miembro(id):
    miembro = Miembro.query.get(id)
    db.session.delete(miembro)
    db.session.commit()
    return redirect(url_for('gestion_equipo'))

@app.route('/clipping')
def clipping():
    from random import shuffle
    fecha = datetime.today().strftime('%Y-%m-%d')
    enlaces = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.id).all()
    miembros = Miembro.query.all()
    nombres = [m.nombre for m in miembros]
    horarios_lj = {m.nombre: m.horario_lj for m in miembros}
    horarios_v = {m.nombre: m.horario_v for m in miembros}

    shuffle(nombres)
    grupos = [nombres[i::3] for i in range(3)]
    total = len(enlaces)
    por_grupo = total // 3
    resto = total % 3
    distribucion = []
    i = 0
    for idx, grupo in enumerate(grupos):
        cantidad = por_grupo + (1 if idx < resto else 0)
        distribucion.append(enlaces[i:i+cantidad])
        i += cantidad

    es_viernes = datetime.today().weekday() == 4
    horarios = horarios_v if_
