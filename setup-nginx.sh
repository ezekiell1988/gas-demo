#!/bin/bash

# Script para configurar nginx para el subdominio gas.ezekl.com
# Ejecutar en el servidor Azure: sudo bash setup-nginx.sh

set -e

echo "🔧 Configurando nginx para gas.ezekl.com en el puerto 8002..."

# Crear configuración de nginx para el sitio
cat > /etc/nginx/sites-available/gas.ezekl.com << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name gas.ezekl.com;

    # Logs
    access_log /var/log/nginx/gas.ezekl.com.access.log;
    error_log /var/log/nginx/gas.ezekl.com.error.log;

    # Tamaño máximo de carga
    client_max_body_size 100M;

    # Proxy hacia el contenedor Docker en puerto 8002
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        
        # Headers para proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (si es necesario)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /api/v1/health {
        proxy_pass http://127.0.0.1:8002/api/v1/health;
        access_log off;
    }
}
EOF

# Crear enlace simbólico en sites-enabled
echo "🔗 Habilitando sitio..."
ln -sf /etc/nginx/sites-available/gas.ezekl.com /etc/nginx/sites-enabled/

# Verificar configuración de nginx
echo "✅ Verificando configuración de nginx..."
nginx -t

# Recargar nginx
echo "🔄 Recargando nginx..."
systemctl reload nginx

echo "✅ Configuración de nginx completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Asegúrate de que el contenedor Docker esté corriendo en el puerto 8002"
echo "2. Verifica que Cloudflare esté apuntando a la IP del servidor (20.246.83.239)"
echo "3. En Cloudflare, asegúrate que el proxy esté activado (naranja)"
echo "4. Cloudflare manejará el certificado SSL automáticamente"
echo ""
echo "🧪 Prueba el sitio:"
echo "   curl http://gas.ezekl.com/api/v1/health"
echo "   curl https://gas.ezekl.com/api/v1/health"
