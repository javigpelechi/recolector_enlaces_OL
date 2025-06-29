from flask import Flask, request, render_template_string, Response
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import csv
import io

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo
class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(10), nullable=False)

# Formulario con fecha actual predefinida
@app.route('/', methods=['GET'])
def index():
    nombres = [
        'Alicia', 'Carmen', 'Ceci', 'Alvaro', 'Kiko',
        'Iván', 'Nico', 'Javier', 'Lucía', 'Iñigo', 'Manolo', 'Raquel'
    ]
    hoy = datetime.now().strftime("%Y-%m-%d")
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
        <input type="date" name="fecha" value="{{ hoy }}" required><br><br>
        <label>Enlaces (uno por línea):</label><br>
        <textarea name="enlaces" rows="10" cols="60" required></textarea><br><br>
        <input type="submit" value="Enviar">
    </form>
    """
    return render_template_string(html, nombres=nombres, hoy=hoy)

# Procesar envío
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

# Ver todos los registros
@app.route('/revisar')
def revisar():
    datos = Enlace.query.order_by(Enlace.fecha.desc(), Enlace.hora.desc()).all()
    html = "<h2>Enlaces Recogidos</h2><ul>"
    for d in datos:
        html += f"<li>{d.fecha} {d.hora} - {d.nombre}: <a href='{d.enlace}' target='_blank'>{d.enlace}</a></li>"
    html += "</ul><a href='/'>Volver</a>"
    return html

# Descargar CSV por fecha
@app.route('/descargar')
def descargar():
    fecha = request.args.get('fecha')
    if not fecha:
        return "Falta el parámetro ?fecha=AAAA-MM-DD", 400

    registros = Enlace.query.filter_by(fecha=fecha).order_by(Enlace.hora).all()

    if not registros:
        return f"No hay registros para {fecha}", 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nombre', 'Fecha', 'Hora', 'Enlace'])

    for r in registros:
        writer.writerow([r.nombre, r.fecha, r.hora, r.enlace])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=enlaces_{fecha}.csv"}
    )

# Inicializar base de datos al arrancar (una vez)
def init_db():
    with app.app_context():
        db.create_all()
        print("Base de datos creada correctamente.")

if __name__ == "__main__":
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"Error al crear la base de datos (quizás ya existe): {e}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
