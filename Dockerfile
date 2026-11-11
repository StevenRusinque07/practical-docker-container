# Imagen base ligera para minimizar consumo de espacio y RAM
FROM python:3.11-alpine

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiar e instalar dependencias estrictas
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/ .

# Exponer el puerto de escucha del microservicio
EXPOSE 5000

# Comando de ejecución
CMD ["python", "app.py"]
