from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Enlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    autor = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)  # formato: dd/mm/aa
    enlace = db.Column(db.Text, nullable=False)
    identificador = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Enlace {self.identificador} - {self.autor}>"

class MiembroEquipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    equipo = db.Column(db.String(10), nullable=True)
    horario_lj = db.Column(db.String(50), nullable=True)
    horario_v = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Miembro {self.nombre}>"
