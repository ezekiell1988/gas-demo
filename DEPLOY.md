# Guía de Despliegue - GAS Demo

## 📋 Requisitos Previos

- Servidor Azure VM con Docker instalado
- Acceso SSH al servidor (20.246.83.239)
- Repositorio GitHub: ezekiell1988/gas-demo
- Dominio configurado en Cloudflare: gas.ezekl.com → 20.246.83.239

## 🔐 Secrets de GitHub

Debes configurar los siguientes secrets en GitHub (Settings → Secrets and variables → Actions → New repository secret):

### SSH_PRIVATE_KEY
Contenido completo del archivo `.pem`:
```bash
# En Windows PowerShell, ejecuta:
Get-Content "C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\PublishSettings\demo-linux_key.pem" | Out-String
```

### Secrets de QuickBooks (Ya configurados)
- ✅ QUICKBOOKS_BASE_URL
- ✅ QUICKBOOKS_CLIENT_ID
- ✅ QUICKBOOKS_CLIENT_SECRET
- ✅ QUICKBOOKS_COMPANY_ID
- ✅ QUICKBOOKS_ENVIRONMENT

## 🚀 Pasos de Configuración

### 1. Configurar Nginx en el Servidor

Conéctate al servidor:
```bash
ssh -i "C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\PublishSettings\demo-linux_key.pem" azureuser@20.246.83.239
```

Copia el script de configuración y ejecútalo:
```bash
# En el servidor
sudo bash /home/azureuser/gas-demo/setup-nginx.sh
```

### 2. Verificar Cloudflare

En el panel de Cloudflare:
- ✅ Subdominio: `gas.ezekl.com`
- ✅ Tipo: `A`
- ✅ Apunta a: `20.246.83.239`
- ✅ Proxy status: **Proxied (naranja)** 🟠
- ✅ SSL/TLS: **Full** (recomendado)

### 3. Configurar SSH_PRIVATE_KEY en GitHub

1. Ve a: https://github.com/ezekiell1988/gas-demo/settings/secrets/actions
2. Click en "New repository secret"
3. Name: `SSH_PRIVATE_KEY`
4. Value: Pega el contenido completo del archivo `.pem` (incluye BEGIN y END)
5. Click "Add secret"

### 4. Primer Despliegue

Puedes hacer el primer despliegue de dos formas:

#### Opción A: Push a main (automático)
```bash
git add .
git commit -m "feat: configuración inicial de Docker y CI/CD"
git push origin main
```

#### Opción B: Manual desde GitHub
1. Ve a: https://github.com/ezekiell1988/gas-demo/actions
2. Click en "Deploy GAS Demo to Azure VM"
3. Click en "Run workflow"
4. Selecciona la rama `main`
5. Click "Run workflow"

## 🔍 Verificación

### En el Servidor
```bash
# Ver contenedores corriendo
docker ps

# Ver logs del contenedor
docker logs gas-demo -f

# Ver estado de nginx
sudo systemctl status nginx

# Ver logs de nginx
sudo tail -f /var/log/nginx/gas.ezekl.com.access.log
```

### Desde tu Máquina
```bash
# Health check
curl https://gas.ezekl.com/api/v1/health

# Ver la aplicación
# Abrir en el navegador: https://gas.ezekl.com
```

## 🏗️ Estructura del Proyecto

```
gas-demo/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD GitHub Actions
├── app/                        # Backend FastAPI
│   ├── main.py
│   ├── api/
│   └── core/
├── gas-app/                    # Frontend Ionic Angular
│   ├── src/
│   └── www/                    # Build del frontend
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Configuración de Docker
├── setup-nginx.sh              # Script de configuración nginx
└── .env                        # Variables de entorno (no subir a git)
```

## 🔄 Flujo de CI/CD

1. **Push a main** → Trigger del workflow
2. **GitHub Actions** → Clona el código
3. **SSH al servidor** → Conecta con el servidor Azure
4. **Git pull** → Actualiza el código en el servidor
5. **Docker build** → Construye la nueva imagen
6. **Docker run** → Despliega el contenedor en puerto 8001
7. **Health check** → Verifica que el servicio esté funcionando

## 🐛 Troubleshooting

### El contenedor no inicia
```bash
docker logs gas-demo
docker ps -a
```

### Nginx no está funcionando
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

### Puerto 8001 ya en uso
```bash
sudo lsof -i :8001
sudo docker stop gas-demo
```

### Error de permisos SSH
```bash
# Verificar permisos del archivo .pem
icacls "C:\...\demo-linux_key.pem"
```

## 📝 Notas

- El proyecto usa **Python 3.13** y **Node 22**
- El frontend se construye automáticamente durante el build de Docker
- Cloudflare maneja el SSL automáticamente (HTTPS)
- El servidor ya tiene otro proyecto en puerto 8000
- Este proyecto usa el puerto **8001**

## 🔗 URLs

- **Producción**: https://gas.ezekl.com
- **API Docs**: https://gas.ezekl.com/docs
- **Health Check**: https://gas.ezekl.com/api/v1/health
- **GitHub Actions**: https://github.com/ezekiell1988/gas-demo/actions
