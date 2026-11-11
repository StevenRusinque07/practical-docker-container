import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "estado": "operativo",
        "tecnologia": "Contenedores (Docker)",
        "servicio": "Gestion Urbana Distribuida",
        "nodo": os.uname().nodename if hasattr(os, 'uname') else "nodo_local"
    })

@app.route('/telemetria')
def telemetria():
    return jsonify({
        "movilidad": {"sector_norte": "flujo_normal", "vehiculos_minuto": 42},
        "energia": {"alumbrado_publico": "atenuado_30%", "ahorro": "45%"},
        "residuos": {"contenedor_101": "85% (requiere_recoleccion)"}
    })

if __name__ == '__main__':
    print("Iniciando microservicio urbano contenerizado en puerto 5000...")
    app.run(host='0.0.0.0', port=5000)
