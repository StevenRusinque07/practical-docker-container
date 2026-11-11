# Solución de Sistemas Distribuidos Basada en Contenedores (Docker)

Este repositorio contiene la implementación práctica del microservicio de gestión urbana empaquetado mediante la tecnología de **Contenedores (Docker)**.

## Estructura del Repositorio
- `Dockerfile`: Configuración basada en la imagen minimalista `python:3.11-alpine`.
- `docker-compose.yml`: Orquestación local con cuotas estrictas de recursos (CPU: 0.50, RAM: 256MB).
- `src/app.py`: Microservicio distribuido en Python de telemetría urbana.

## Instrucciones de Despliegue

1. **Construir y ejecutar el contenedor:**
   ```bash
   docker-compose up -d --build
