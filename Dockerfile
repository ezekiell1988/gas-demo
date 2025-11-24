# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copiar archivos de configuración del frontend
COPY gas-app/package*.json ./

# Instalar dependencias del frontend
RUN npm ci

# Copiar código fuente del frontend
COPY gas-app/ ./

# Construir el frontend de Ionic
RUN npm run build

# Stage 2: Build backend
FROM python:3.13-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del backend
COPY app/ ./app/
COPY start.py .

# Copiar el frontend construido desde el stage anterior
COPY --from=frontend-builder /app/frontend/www ./gas-app/www

# Exponer el puerto 8002
EXPOSE 8002

# Variables de entorno (serán sobrescritas por docker-compose o GitHub Actions)
ENV PORT=8002
ENV ENVIRONMENT=production
ENV FRONTEND_PATH=gas-app

# Comando para ejecutar la aplicación
CMD ["python", "-m", "app.main"]
