import os, io, random
from datetime import datetime, date
from flask import (
    Flask, request, render_template, redirect, url_for, send_file
)
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelos ---
class Member(db.Model):
    id        = db.Column(db.Integer,   primary_key=True)
    nombre    = db.Column(db.String(50), nullable=False, unique=True)
    team      = db.Column(db.String(1),  nullable=False)  # A o B
    horario_LJ= db.Column(db.String(20), nullable=False)  # Lunes-Jueves
    horario_V = db.Column(db.String(20), nullable=False)  # Viernes

class Enlace(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    nombre  = db.Column(db.String(50), nullable=False)
    enlace  = db.Column(db.String(500), nullable=False)
    fecha   = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    hora    = db.Column(db.String(5),  nullable=False)  # HH:MM

def init_db():
    with app.app_context():
        db.create_all()

# --- Rutas de gestión de miembros ---
@app.route('/miembros', methods=['GET'])
def miembros():
    todos = Member.query.order_by(Member.nombre).all()
    return render_template('miembros.html', miembros=todos)

@app.route('/miembros/add', methods=['POST'])
def miembros_add():
    nombre = request.form['nombre']
    team = request.form['team']
    lj = request.form['horario_LJ']
    v = request.form['horario_V']
    db.session.add(Member(nombre=nombre, team=team,
                          horario_LJ=lj, horario_V=v))
    db.session.commit()
    return redirect(url_for('miembros'))

@app.route('/miembros/edit/<int:id>', methods=['POST'])
def miembros_edit(id):
    m = Member.query.get_or_404(id)
    m.team = request.form['team']
    m.horario_LJ = request.form['horario_LJ']
    m.horario_V = request.form['horario_V']
    db.session.commit()
    return redirect(url_for('miembros'))

@app.route('/miembros/delete/<int:id>', methods=['POST'])
def miembros_delete(id):
    Member.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('miembros'))

# --- Rutas de envío y consulta ---
@app.route('/')
def index():
    hoy = date.today().strftime("%Y-%m-%d")
    nombres = [m.nombre for m in Member.query.order_by(Member.nombre)]
    return render_template('index.html', hoy=hoy, nombres=nombres)

@app.route('/enviar', methods=['POST'])
def enviar():
    fecha  = request.form["fecha"]
    nombre = request.form["nombre"]
    hora   = datetime.now().strftime("%H:%M")
    texto  = request.form.get("enlaces","")
    enlaces = [e.strip() for e in texto.split('\n') if e.strip()]
    for url in enlaces:
        db.session.add(Enlace(nombre=nombre, enlace=url,
                              fecha=fecha, hora=hora))
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/basedatos')
def basedatos():
    fecha = request.args.get("fecha") or date.today().strftime("%Y-%m-%d")
    datos = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora).all()
    return render_template('basedatos.html', datos=datos, fecha=fecha)

# --- Clipping ---
@app.route('/clipping')
def clipping():
    fecha = request.args.get("fecha") or date.today().strftime("%Y-%m-%d")
    enlaces = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora).all()
    random.shuffle(enlaces)
    # repartir en 3 grupos de 4
    grupos = [enlaces[i*4:(i+1)*4] for i in range(3)]
    # calcular identificadores y horarios
    is_viernes = datetime.strptime(fecha, "%Y-%m-%d").weekday() == 4
    miembros = {m.nombre: m for m in Member.query.all()}
    salida = []
    for gi, grupo in enumerate(grupos, start=1):
        grp = []
        for idx, enlace in enumerate(grupo, start=1):
            # ID: DD_MM_YY_NN
            dd, mm, yyyy = fecha.split('-')
            ident = f"{dd}_{mm}_{yyyy[2:]}_{idx:02d}"
            h = miembros[enlace.nombre].horario_V if is_viernes else miembros[enlace.nombre].horario_LJ
            grp.append({
                'nombre': enlace.nombre,
                'horario': h,
                'id': ident,
                'url': enlace.enlace
            })
        salida.append(grp)
    return render_template('clipping.html',
                           grupos=salida, fecha=fecha,
                           is_viernes=is_viernes)

# --- Helpers de descarga y duplicados (si quieres mantenerlos) ---
# ...

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            debug=True)
