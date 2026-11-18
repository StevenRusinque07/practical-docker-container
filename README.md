# Solución de Sistemas Distribuidos Basada en Contenedores (Docker)

Implementación práctica del sistema distribuido de gestión urbana inteligente (**Cajicá / Sabana Centro**) empaquetado con **Docker** bajo principios de ingeniería sostenible (*Green Computing*).

## Arquitectura Implementada
- **`mqtt-broker` (`eclipse-mosquitto:2.0-alpine`)**: Capa de comunicación ligera mediante protocolo MQTT.
- **`edge-gateway` (`src/edge_simulator.py`)**: Simulación de sensores IoT y filtrado previo en el borde (*Edge Computing*) con firma de seguridad **JWT**.
- **`urban-microservice` (`src/app.py`)**: Microservicio central en `python:3.11-alpine` (menor a 55 MB) con cuotas estrictas de hardware (`0.50` CPU y `256 MB` RAM) que gestiona movilidad adaptativa, alumbrado LED *dimmer* y rutas dinámicas de residuos con IA.

## Instrucciones de Despliegue y Auditoría

1. **Construir y levantar el clúster distribuido:**
   ```bash
   docker compose up -d --build