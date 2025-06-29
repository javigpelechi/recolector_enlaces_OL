import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configuración de la base de datos PostgreSQL desde variables de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la base de datos
class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20))
    autor = db.Column(db.String(50))
    enlace = db.Column(db.Text)
    identificador = db.Column(db.String(20))

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)
    equipo = db.Column(db.String(1))
    horario_lj = db.Column(db.String(50))
    horario_v = db.Column(db.String(50))

db.create_all()

# Ruta de inicio
@app.route('/')
def index():
    return render_template('index.html')

# Envío de enlaces
@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    miembros = Miembro.query.all()
    hoy = datetime.now().strftime("%Y-%m-%d")
    if request.method == 'POST':
        fecha = request.form['fecha']
        autor = request.form['autor']
        enlaces = request.form['enlaces'].splitlines()
        existentes = set((n.fecha, n.enlace) for n in Noticia.query.all())
        contador = 1
        for enlace in enlaces:
            if (fecha, enlace) not in existentes:
                identificador = f"{datetime.strptime(fecha, '%Y-%m-%d').strftime('%d_%m_%y')}_{contador:02}"
                nueva = Noticia(fecha=fecha, autor=autor, enlace=enlace, identificador=identificador)
                db.session.add(nueva)
                contador += 1
        db.session.commit()
        flash("Enlaces enviados correctamente.", "success")
        return redirect(url_for('enviar'))
    return render_template('enviar.html', miembros=miembros, hoy=hoy)

# Base de datos
@app.route('/basedatos', methods=['GET', 'POST'])
def basedatos():
    hoy = datetime.now().strftime("%Y-%m-%d")
    fecha = request.form.get('fecha', hoy)
    noticias = Noticia.query.all() if request.form.get('ver_todo') else Noticia.query.filter_by(fecha=fecha).all()
    return render_template('basedatos.html', noticias=noticias, fecha=fecha)

@app.route('/descargar_filtrados', methods=['POST'])
def descargar_filtrados():
    fecha = request.form.get('fecha')
    noticias = Noticia.query.filter_by(fecha=fecha).all()
    return generar_excel(noticias, f"noticias_{fecha}.xlsx")

@app.route('/descargar_todo')
def descargar_todo():
    noticias = Noticia.query.all()
    return generar_excel(noticias, "noticias_todas.xlsx")

def generar_excel(noticias, nombre_archivo):
    data = [{'Fecha': n.fecha, 'Autor': n.autor, 'Enlace': n.enlace, 'ID': n.identificador} for n in noticias]
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name=nombre_archivo, as_attachment=True)

@app.route('/eliminar_duplicados', methods=['POST'])
def eliminar_duplicados():
    existentes = set()
    duplicados = []
    for n in Noticia.query.order_by(Noticia.id).all():
        clave = (n.fecha, n.enlace)
        if clave in existentes:
            duplicados.append(n)
        else:
            existentes.add(clave)
    for d in duplicados:
        db.session.delete(d)
    db.session.commit()
    flash(f"{len(duplicados)} duplicados eliminados.", "info")
    return redirect(url_for('basedatos'))

# Gestión del equipo
@app.route('/equipo', methods=['GET', 'POST'])
def equipo():
    if request.method == 'POST':
        if 'nuevo' in request.form:
            nombre = request.form['nombre']
            equipo = request.form['equipo']
            lj = request.form['horario_lj']
            v = request.form['horario_v']
            db.session.add(Miembro(nombre=nombre, equipo=equipo, horario_lj=lj, horario_v=v))
            db.session.commit()
        elif 'eliminar' in request.form:
            id_miembro = int(request.form['eliminar'])
            miembro = Miembro.query.get(id_miembro)
            db.session.delete(miembro)
            db.session.commit()
    miembros = Miembro.query.all()
    return render_template('equipo.html', miembros=miembros)

# Clipping automático
@app.route('/clipping')
def clipping():
    hoy = datetime.now().strftime("%Y-%m-%d")
    noticias = Noticia.query.filter_by(fecha=hoy).all()
    enlaces = [n.enlace for n in noticias]
    random.shuffle(enlaces)

    miembros = Miembro.query.all()
    random.shuffle(miembros)
    grupos = [miembros[i::3] for i in range(3)]
    distribucion = [enlaces[i::3] for i in range(3)]

    resultado = []
    for i, grupo in enumerate(grupos):
        grupo_datos = []
        for m in grupo:
            horario = m.horario_v if datetime.now().weekday() == 4 else m.horario_lj
            grupo_datos.append((m.nombre, horario))
        resultado.append({'grupo': f'GRUPO {i+1}', 'miembros': grupo_datos, 'enlaces': distribucion[i]})
    return render_template('clipping.html', resultado=resultado, hoy=hoy)

# Botón de borrado con contraseña
@app.route('/limpiar', methods=['POST'])
def limpiar():
    password = request.form.get('password')
    if password == '1234':
        Noticia.query.delete()
        db.session.commit()
        flash("Base de datos limpiada correctamente.", "warning")
    else:
        flash("Contraseña incorrecta.", "danger")
    return redirect(url_for('basedatos'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
