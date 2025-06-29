from flask import Flask, render_template, request, redirect, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Enlace, Miembro
import pandas as pd
import io
import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enlaces.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def inicializar_app():
    with app.app_context():
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
def index():
    return render_template('home.html')

@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    miembros = Miembro.query.all()
    if request.method == 'POST':
        autor = request.form['autor']
        fecha = request.form['fecha']
        texto = request.form['texto']
        enlaces = [e.strip() for e in texto.splitlines() if e.strip()]
        for idx, enlace in enumerate(enlaces, start=1):
            identificador = f"{fecha.replace('-', '_')}_{idx:02}"
            nuevo = Enlace(autor=autor, fecha=fecha, enlace=enlace, identificador=identificador)
            db.session.add(nuevo)
        db.session.commit()
        return redirect('/basedatos')
    hoy = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('enviar.html', miembros=miembros, fecha_actual=hoy)

@app.route('/basedatos', methods=['GET', 'POST'])
def basedatos():
    fecha = request.form.get('fecha')
    if fecha:
        enlaces = Enlace.query.filter_by(fecha=fecha).all()
    else:
        enlaces = Enlace.query.all()
    return render_template('basedatos.html', enlaces=enlaces)

@app.route('/descargar_filtrados', methods=['POST'])
def descargar_filtrados():
    fecha = request.form.get('fecha')
    if not fecha:
        return "No hay fecha seleccionada", 400
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    return generar_excel(enlaces, f"enlaces_filtrados_{fecha}.xlsx")

@app.route('/descargar_todos')
def descargar_todos():
    enlaces = Enlace.query.all()
    return generar_excel(enlaces, "enlaces_todos.xlsx")

@app.route('/eliminar_todos', methods=['POST'])
def eliminar_todos():
    contraseña = request.form.get('password')
    if contraseña == '1234':
        Enlace.query.delete()
        db.session.commit()
        return redirect('/basedatos')
    return "Contraseña incorrecta", 403

@app.route('/equipo', methods=['GET', 'POST'])
def equipo():
    if request.method == 'POST':
        if 'modificar' in request.form:
            id = request.form['id']
            miembro = Miembro.query.get(id)
            miembro.nombre = request.form['nombre']
            miembro.equipo = request.form['equipo']
            miembro.horario_lj = request.form['horario_lj']
            miembro.horario_v = request.form['horario_v']
            db.session.commit()
        elif 'eliminar' in request.form:
            id = request.form['id']
            miembro = Miembro.query.get(id)
            db.session.delete(miembro)
            db.session.commit()
        elif 'nuevo' in request.form:
            nombre = request.form['nombre']
            equipo = request.form['equipo']
            horario_lj = request.form['horario_lj']
            horario_v = request.form['horario_v']
            nuevo = Miembro(nombre=nombre, equipo=equipo, horario_lj=horario_lj, horario_v=horario_v)
            db.session.add(nuevo)
            db.session.commit()
    miembros = Miembro.query.all()
    return render_template('equipo.html', miembros=miembros)

@app.route('/clippings', methods=['GET'])
def clippings():
    fecha = request.args.get('fecha') or datetime.date.today().strftime('%Y-%m-%d')
    enlaces = Enlace.query.filter_by(fecha=fecha).all()
    random.shuffle(enlaces)
    equipos = {'Equipo 1': [], 'Equipo 2': [], 'Equipo 3': []}
    for i, enlace in enumerate(enlaces):
        equipo = f'Equipo {(i % 3) + 1}'
        equipos[equipo].append(enlace)
    return render_template('clippings.html', equipos=equipos, fecha=fecha)

def generar_excel(enlaces, filename):
    data = [{
        "ID": e.identificador,
        "Autor": e.autor,
        "Fecha": e.fecha,
        "Enlace": e.enlace
    } for e in enlaces]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Enlaces")
    output.seek(0)
    return send_file(output, download_name=filename, as_attachment=True)

if __name__ == '__main__':
    inicializar_app()
    app.run(debug=True)
