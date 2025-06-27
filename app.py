from flask import Flask, request, jsonify, render_template
import csv
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enviar', methods=['POST'])
def enviar_enlace():
    data = request.json
    nombre = data.get('nombre')
    enlaces = data.get('enlaces', [])
    fecha = datetime.now().strftime('%Y-%m-%d')
    hora = datetime.now().strftime('%H:%M:%S')

    os.makedirs('data', exist_ok=True)
    filename = f"data/{fecha}.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['fecha', 'hora', 'nombre', 'enlace'])
        for enlace in enlaces:
            writer.writerow([fecha, hora, nombre, enlace])

    return jsonify({'status': 'ok'})

# 🔧 Adaptación para Render: usa 0.0.0.0 y puerto del entorno
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
