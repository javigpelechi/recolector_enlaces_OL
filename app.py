from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Configurar la base de datos desde la variable de entorno DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de datos
class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(10), nullable=False)

# Ruta principal con formulario
@app.route('/', methods=['GET'])
def index():
    nombres = [
        'Alicia', 'Carmen', 'Ceci', 'Alvaro', 'Kiko',
        'Iván', 'Nico', 'Javier', 'Lucía', 'Iñigo', 'Manolo', 'Raquel'
    ]
    html = """
    <h2>Enviar enlaces</h2>
    <form method="POST" action="/enviar">
        <label>Nombre:</label>
        <select name="nombre">
            {% for n in nombres %}
            <option value="{{n}}">{{n}}</option>
            {% endfor %}
        </select><br><br>
        <label>Fecha (AAAA-MM-DD):</label>
        <input type="date" name="fecha" required><br><br>
        <label>Enlaces (uno por línea):</label><br>
        <textarea name="enlaces" rows="10" cols="60" required></textarea><br><br>
        <input type="submit" value="Enviar">
    </form>
    """
    return render_template_string(html, nombres=nombres)

# Ruta para recibir datos del formulario
@app.route('/enviar', methods=['POST'])
def enviar():
    nombre = request.form['nombre']
    fecha = request.form['fecha']
    enlaces_raw = request.form['enlaces']
    hora = datetime.now().strftime("%H:%M")

    enlaces = [e.strip() for e in enlaces_raw.strip().split('\n') if e.strip()]
    for enlace in enlaces:
        nuevo = Enlace(nombre=nombre, fecha=fecha, hora=hora, enlace=enlace)
        db.session.add(nuevo)
    db.session.commit()

    return f"Se han enviado {len(enlaces)} enlace(s). <a href='/'>Volver</a>"

# Ruta para revisar los datos guardados
@app.route('/revisar')
def revisar():
    datos = Enlace.query.order_by(Enlace.fecha.desc(), Enlace.hora.desc()).all()
    html = "<h2>Enlaces Recogidos</h2><ul>"
    for d in datos:
        html += f"<li>{d.fecha} {d.hora} - {d.nombre}: <a href='{d.enlace}' target='_blank'>{d.enlace}</a></li>"
    html += "</ul><a href='/'>Volver</a>"
    return html

# Comando para crear la base de datos
def init_db():
    with app.app_context():
        db.create_all()
        print("Base de datos creada correctamente.")

# Ejecutar el servidor y crear base de datos al arrancar
if __name__ == "__main__":
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"Error al crear la base de datos (quizás ya existe): {e}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
