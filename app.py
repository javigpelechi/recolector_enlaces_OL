from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de la base de datos PostgreSQL desde variable de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de datos
class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10))   # YYYY-MM-DD
    hora = db.Column(db.String(8))     # HH:MM:SS
    nombre = db.Column(db.String(50))
    enlace = db.Column(db.String(500))

# Ruta principal: formulario
@app.route('/')
def index():
    return render_template('index.html')

# API para guardar enlaces
@app.route('/enviar', methods=['POST'])
def enviar_enlace():
    data = request.json
    nombre = data.get('nombre')
    enlaces = data.get('enlaces', [])
    fecha = datetime.now().strftime('%Y-%m-%d')
    hora = datetime.now().strftime('%H:%M:%S')

    for url in enlaces:
        nuevo = Enlace(fecha=fecha, hora=hora, nombre=nombre, enlace=url)
        db.session.add(nuevo)
    db.session.commit()

    return jsonify({'status': 'ok'})

# Mostrar enlaces del día actual
@app.route('/revisar')
def revisar():
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    enlaces = Enlace.query.filter_by(fecha=fecha_actual).all()
    return render_template('revisar.html', datos=enlaces)

# Inicializar la base de datos si no existe (solo en local)
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Base de datos creada correctamente.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
