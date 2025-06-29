from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    enlace = db.Column(db.Text, nullable=False)
    identificador = db.Column(db.String(20), nullable=True)

class Miembro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    equipo = db.Column(db.String(10), nullable=False)
    horario_lj = db.Column(db.String(50), nullable=False)
    horario_v = db.Column(db.String(50), nullable=False)
