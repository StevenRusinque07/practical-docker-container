import base64
import hashlib
import hmac
import json
import os
import random
import time
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
JWT_SECRET = os.getenv("JWT_SECRET", "clave_secreta_umb_2026")

# Memoria local del nodo Edge para filtrar datos repetidos
ultimo_llenado = {}
paquetes_generados = 0
paquetes_filtrados = 0


def generar_jwt(payload: dict) -> str:
    """Genera un token JWT (HS256) ligero sin dependencias externas."""
    header = {"alg": "HS256", "typ": "JWT"}
    b64_header = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    mensaje = f"{b64_header}.{b64_payload}".encode()
    firma = hmac.new(JWT_SECRET.encode(), mensaje, hashlib.sha256).digest()
    b64_firma = base64.urlsafe_b64encode(firma).rstrip(b"=").decode()
    return f"{b64_header}.{b64_payload}.{b64_firma}"


def conectar_mqtt() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-gateway-cajica")
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            print("[EDGE] Conectado exitosamente al Broker MQTT.")
            return client
        except Exception as e:
            print(f"[EDGE] Esperando al Broker MQTT ({e})... reintentando en 2s")
            time.sleep(2)


def main():
    global paquetes_generados, paquetes_filtrados
    client = conectar_mqtt()
    contenedores = ["CONT-CENTRO-01", "CONT-ESTACION-02", "CONT-PARQUE-03", "CONT-VARIANTE-04"]

    while True:
        # 1. RESIDUOS SOLIDOS (Sensores Ultrasonido + Filtrado Edge)
        cont_id = random.choice(contenedores)
        nivel_actual = random.randint(25, 98)
        nivel_previo = ultimo_llenado.get(cont_id, -100)
        paquetes_generados += 1

        # Regla Edge: solo transmite si vario >= 5% o si esta en estado critico (>= 80%)
        if abs(nivel_actual - nivel_previo) >= 5 or nivel_actual >= 80:
            ultimo_llenado[cont_id] = nivel_actual
            datos = {
                "tipo": "residuos",
                "id": cont_id,
                "llenado": nivel_actual,
                "filtrados_edge": paquetes_filtrados,
                "generados_edge": paquetes_generados,
                "exp": int(time.time()) + 60,
            }
            token = generar_jwt(datos)
            client.publish("ciudad/cajica/residuos", json.dumps({"token": token}), qos=1)
            print(f"[EDGE -> NUBE] Enviado {cont_id}: {nivel_actual}% (Ahorro Edge: {paquetes_filtrados}/{paquetes_generados})")
        else:
            paquetes_filtrados += 1
            print(f"[EDGE FILTRADO] Dato redundante descartado localmente para {cont_id} ({nivel_actual}%)")

        # 2. ENERGIA (Fotoceldas LED Dimmerizables - control local inmediato)
        presencia = random.choice([True, False, False])
        dimmer = 100 if presencia else 20
        datos_energia = {
            "tipo": "energia",
            "sector": "Av. Principal Cajica",
            "presencia": presencia,
            "dimmer": dimmer,
            "exp": int(time.time()) + 60,
        }
        client.publish("ciudad/cajica/energia", json.dumps({"token": generar_jwt(datos_energia)}), qos=0)

        # 3. MOVILIDAD (Lazos Inductivos - conteo vehicular)
        vehiculos = random.randint(6, 55)
        datos_movilidad = {
            "tipo": "movilidad",
            "interseccion": "Glorieta Sabana Centro",
            "vehiculos_min": vehiculos,
            "exp": int(time.time()) + 60,
        }
        client.publish("ciudad/cajica/movilidad", json.dumps({"token": generar_jwt(datos_movilidad)}), qos=0)

        time.sleep(3)


if __name__ == "__main__":
    main()