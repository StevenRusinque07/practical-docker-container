import base64
import hashlib
import hmac
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
JWT_SECRET = os.getenv("JWT_SECRET", "clave_secreta_umb_2026")

# Estado distribuido en memoria del microservicio
estado_ciudad = {
    "movilidad": {"interseccion": "Sin datos", "vehiculos_min": 0, "tiempo_verde_seg": 30, "estado": "Normal"},
    "energia": {"sector": "Sin datos", "presencia": False, "dimmer": 20, "ahorro_energetico": "80%"},
    "residuos": {
        "contenedores": {},
        "ruta_ia_prioritaria": [],
        "ahorro_combustible_est": "0%",
    },
    "sostenibilidad": {
        "paquetes_generados_edge": 0,
        "paquetes_filtrados_edge": 0,
        "reduccion_trafico_red": "0%",
        "mensajes_jwt_validados": 0,
        "mensajes_rechazados": 0,
    },
}


def verificar_jwt(token: str) -> dict | None:
    """Valida firma HMAC-SHA256 y expiracion del token JWT."""
    try:
        partes = token.split(".")
        if len(partes) != 3:
            return None
        b64_header, b64_payload, b64_firma = partes
        mensaje = f"{b64_header}.{b64_payload}".encode()
        firma_esperada = hmac.new(JWT_SECRET.encode(), mensaje, hashlib.sha256).digest()
        b64_esperada = base64.urlsafe_b64encode(firma_esperada).rstrip(b"=").decode()

        if not hmac.compare_digest(b64_firma, b64_esperada):
            return None

        padding = "=" * (-len(b64_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(b64_payload + padding).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def recalcular_ruta_ia():
    """Algoritmo IA heuristico: prioriza contenedores >= 80% ordenados por urgencia."""
    conts = estado_ciudad["residuos"]["contenedores"]
    criticos = {k: v for k, v in conts.items() if v >= 80}
    ruta_ordenada = sorted(criticos.keys(), key=lambda k: criticos[k], reverse=True)
    estado_ciudad["residuos"]["ruta_ia_prioritaria"] = [
        f"{cid} ({criticos[cid]}%)" for cid in ruta_ordenada
    ]
    total = max(len(conts), 1)
    evitados = total - len(ruta_ordenada)
    ahorro = round((evitados / total) * 100, 1)
    estado_ciudad["residuos"]["ahorro_combustible_est"] = f"{ahorro}% (rutas innecesarias evitadas)"


def on_message(client, userdata, msg):
    try:
        crudo = json.loads(msg.payload.decode())
        datos = verificar_jwt(crudo.get("token", ""))
        if not datos:
            estado_ciudad["sostenibilidad"]["mensajes_rechazados"] += 1
            print("[SEGURIDAD] Token JWT invalido rechazado.")
            return

        estado_ciudad["sostenibilidad"]["mensajes_jwt_validados"] += 1
        tipo = datos.get("tipo")

        if tipo == "movilidad":
            veh = datos["vehiculos_min"]
            verde = min(60, max(20, int(veh * 1.1)))
            estado_ciudad["movilidad"] = {
                "interseccion": datos["interseccion"],
                "vehiculos_min": veh,
                "tiempo_verde_seg": verde,
                "estado": "Alta congestion - Prioridad Verde" if veh > 35 else "Flujo fluido",
            }

        elif tipo == "energia":
            dimmer = datos["dimmer"]
            estado_ciudad["energia"] = {
                "sector": datos["sector"],
                "presencia": datos["presencia"],
                "dimmer": dimmer,
                "ahorro_energetico": f"{100 - dimmer}%",
            }

        elif tipo == "residuos":
            estado_ciudad["residuos"]["contenedores"][datos["id"]] = datos["llenado"]
            gen = max(datos.get("generados_edge", 1), 1)
            filt = datos.get("filtrados_edge", 0)
            estado_ciudad["sostenibilidad"]["paquetes_generados_edge"] = gen
            estado_ciudad["sostenibilidad"]["paquetes_filtrados_edge"] = filt
            estado_ciudad["sostenibilidad"]["reduccion_trafico_red"] = f"{round((filt / gen) * 100, 1)}%"
            recalcular_ruta_ia()

    except Exception as e:
        print(f"[ERROR PROCESAMIENTO] {e}")


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/estado":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(estado_ciudad, indent=2, ensure_ascii=False).encode("utf-8"))
            return

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="3">
  <title>Sistema Distribuido Urbano - Cajicá (Docker)</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
    h1 {{ color: #38bdf8; margin-bottom: 4px; }}
    .sub {{ color: #94a3b8; margin-bottom: 24px; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; }}
    .card h2 {{ margin-top: 0; font-size: 17px; color: #22d3ee; }}
    .badge {{ display: inline-block; background: #065f46; color: #6ee7b7; padding: 3px 8px; border-radius: 6px; font-size: 12px; }}
    pre {{ background: #0f172a; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 13px; color: #e2e8f0; }}
  </style>
</head>
<body>
  <h1>Gestión Urbana Inteligente — Nodo Cajicá / Sabana Centro</h1>
  <div class="sub">Arquitectura Distribuida en Contenedores Docker (python:3.11-alpine | Límite: 0.50 CPU / 256MB RAM) • Actualización automática cada 3s</div>
  <div class="grid">
    <div class="card">
      <h2>1. Movilidad (Semáforos Adaptativos)</h2>
      <p><b>Intersección:</b> {estado_ciudad['movilidad']['interseccion']}</p>
      <p><b>Flujo:</b> {estado_ciudad['movilidad']['vehiculos_min']} veh/min</p>
      <p><b>Luz Verde Asignada:</b> <span class="badge">{estado_ciudad['movilidad']['tiempo_verde_seg']} segundos</span></p>
      <p><b>Diagnóstico:</b> {estado_ciudad['movilidad']['estado']}</p>
    </div>
    <div class="card">
      <h2>2. Energía (Alumbrado LED Dimmer)</h2>
      <p><b>Sector:</b> {estado_ciudad['energia']['sector']}</p>
      <p><b>Presencia Detectada:</b> {'Sí' if estado_ciudad['energia']['presencia'] else 'No (Vía despejada)'}</p>
      <p><b>Intensidad Luminaria:</b> {estado_ciudad['energia']['dimmer']}%</p>
      <p><b>Ahorro Energético Actual:</b> <span class="badge">{estado_ciudad['energia']['ahorro_energetico']}</span></p>
    </div>
    <div class="card">
      <h2>3. Residuos Sólidos + Ruta IA</h2>
      <p><b>Ruta Óptima Prioritaria (>=80%):</b></p>
      <pre>{json.dumps(estado_ciudad['residuos']['ruta_ia_prioritaria'], indent=2, ensure_ascii=False)}</pre>
      <p><b>Optimización:</b> <span class="badge">{estado_ciudad['residuos']['ahorro_combustible_est']}</span></p>
    </div>
    <div class="card">
      <h2>4. Sostenibilidad Edge & Seguridad JWT</h2>
      <p><b>Reducción de tráfico en Edge:</b> <span class="badge">{estado_ciudad['sostenibilidad']['reduccion_trafico_red']}</span></p>
      <p><b>Paquetes filtrados localmente:</b> {estado_ciudad['sostenibilidad']['paquetes_filtrados_edge']} de {estado_ciudad['sostenibilidad']['paquetes_generados_edge']}</p>
      <p><b>Mensajes JWT autenticados:</b> {estado_ciudad['sostenibilidad']['mensajes_jwt_validados']}</p>
      <p><b>Endpoint JSON:</b> <a href="/api/estado" style="color:#38bdf8">/api/estado</a></p>
    </div>
  </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def iniciar_servidor_web():
    server = ThreadingHTTPServer(("0.0.0.0", 8000), DashboardHandler)
    print("[WEB] Dashboard municipal activo en http://localhost:8000")
    server.serve_forever()


def main():
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="urban-microservice-central")
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.subscribe("ciudad/cajica/#")
            print("[CENTRAL] Suscrito a telemetria urbana en MQTT. Esperando eventos...")
            client.loop_forever()
        except Exception as e:
            print(f"[CENTRAL] Reintentando conexion MQTT ({e})...")
            time.sleep(2)


if __name__ == "__main__":
    main()