# 🔐 Autenticación QuickBooks API

Este módulo implementa la autenticación OAuth2 con QuickBooks Online API para conectar tu aplicación con QuickBooks.

## 📑 Tabla de Contenidos

- [Configuración Inicial](#-configuración-inicial)
- [Flujo de Autenticación](#-flujo-de-autenticación-oauth2)
- [Endpoints Disponibles](#-endpoints-disponibles)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Seguridad](#-seguridad)
- [Troubleshooting](#-troubleshooting)

## 🔧 Configuración Inicial

### 1. Obtener Credenciales de QuickBooks

1. Inicia sesión en [Intuit Developer Portal](https://developer.intuit.com)
2. Crea una nueva aplicación o usa una existente
3. Obtén tus credenciales:
   - **Client ID**
   - **Client Secret**
   - **Redirect URI** (ejemplo: `http://localhost:8002/v1/auth/callback`)

### 2. Variables de Entorno

Configura las siguientes variables en tu archivo `.env`:

```env
QUICKBOOKS_CLIENT_ID=tu_client_id
QUICKBOOKS_CLIENT_SECRET=tu_client_secret
QUICKBOOKS_REDIRECT_URI=http://localhost:8002/v1/auth/callback
QUICKBOOKS_COMPANY_ID=tu_company_id
QUICKBOOKS_BASE_URL=https://sandbox-quickbooks.api.intuit.com/v3
```

## 🔄 Flujo de Autenticación OAuth2

### Paso 1: Iniciar Login

Abre en tu navegador:

```
GET http://localhost:8002/api/v1/auth/login
```

Esto:
1. Genera un `state` aleatorio seguro (protección CSRF)
2. Redirige automáticamente a QuickBooks para autorización

**Respuesta:** Redirección HTTP 302 a la página de autenticación de QuickBooks

---

### Paso 2: Autorización en QuickBooks

El usuario autoriza la aplicación en QuickBooks (interfaz de Intuit).

---

### Paso 3: Callback y Redirección (Automático)

QuickBooks redirige a: `http://localhost:8002/v1/auth/callback?code=XXX&state=YYY&realmId=ZZZ`

El sistema automáticamente:
1. Valida el `state` para prevenir ataques CSRF
2. Intercambia el código por tokens de acceso
3. Guarda access_token y refresh_token en memoria
4. **Redirige a la raíz del proyecto (`/`)** para continuar usando la aplicación

**Respuesta:** Redirección HTTP 302 a `/` (página principal de la aplicación)

---

### Paso 4: Usar el API

Una vez autenticado, puedes llamar a los endpoints protegidos:

```bash
GET /api/v1/employees
```

## 📊 Endpoints Disponibles

### 🔑 Autenticación

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/auth/login` | GET | Inicia el flujo OAuth2, genera state seguro y redirige a QuickBooks |
| `/api/v1/auth/callback` | GET | Callback OAuth2: valida state, intercambia código por tokens, redirige a `/` |
| `/api/v1/auth/status` | GET | Verifica el estado actual de autenticación y validez del token |

---

### 🔍 Detalles de Endpoints

#### `GET /api/v1/auth/login`

**Resumen:** Iniciar sesión con QuickBooks

**Descripción:** Inicia el flujo de autenticación OAuth2 con QuickBooks. Genera un `state` aleatorio único usando `secrets.token_urlsafe(32)` para protección CSRF y redirige al usuario a la página de autorización de QuickBooks con los scopes correctos.

**Scopes incluidos:**
- `com.intuit.quickbooks.accounting` - Acceso a datos contables
- `openid` - Requerido para OpenID Connect
- `profile`, `email`, `phone`, `address` - Información del usuario (opcional)

**Ejemplo:**
```bash
GET http://localhost:8002/api/v1/auth/login
```

**Respuesta:**
- Redirección HTTP 302 a QuickBooks con state seguro

---

#### `GET /api/v1/auth/callback`

**Resumen:** Callback de OAuth2

**Descripción:** Endpoint de callback que recibe el código de autorización desde QuickBooks, valida el state para prevenir CSRF, intercambia el código por tokens de acceso y redirige a la página principal.

**Parámetros Query:**
- `code` (string, requerido): Código de autorización de QuickBooks
- `state` (string, requerido): Token de seguridad OAuth2 (validado contra el generado en login)
- `realmId` (string, requerido): ID de la compañía (Company ID)
- `error` (string, opcional): Mensaje de error si falla la autorización

**Flujo de seguridad:**
1. Valida que el `state` recibido coincida con el generado
2. Si el state es inválido, retorna error 400 (posible ataque CSRF)
3. Elimina el state usado (un solo uso)
4. Intercambia código por tokens
5. Guarda tokens en memoria
6. Redirige a `/`

**Respuesta exitosa:**
- Redirección HTTP 302 a `/` (aplicación principal)

**Respuesta de error (state inválido):**
```json
{
  "detail": "State inválido. Posible ataque CSRF. Inicie el proceso de login nuevamente."
}
```

---

#### `GET /api/v1/auth/status`

**Resumen:** Verificar estado de autenticación

**Descripción:** Obtiene el estado actual de la autenticación con QuickBooks, incluyendo validez del token y fecha de expiración.

**Ejemplo:**
```bash
GET http://localhost:8002/api/v1/auth/status
```

**Respuesta:**
```json
{
  "authenticated": true,
  "token_valid": true,
  "realm_id": "9341455750901915",
  "expires_at": "2025-11-24T10:30:00"
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: Flujo Completo de Autenticación

```python
import webbrowser
import aiohttp

async def authenticate_with_quickbooks():
    base_url = "http://localhost:8002/api/v1"
    
    # 1. Abrir navegador para login
    print("🚀 Abriendo navegador para autenticación...")
    webbrowser.open(f"{base_url}/auth/login")
    
    # 2. El usuario será redirigido automáticamente a / después de autorizar
    print("✅ Después de autorizar, serás redirigido a la aplicación principal")
    
    # 3. Esperar un momento para que se complete el callback
    await asyncio.sleep(3)
    
    # 3. Verificar estado de autenticación
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/auth/status") as resp:
            status = await resp.json()
            
            if status["authenticated"] and status["token_valid"]:
                print("✅ Autenticación exitosa")
                print(f"Company ID: {status['realm_id']}")
                print(f"Token expira: {status['expires_at']}")
            else:
                print("❌ Autenticación fallida")
```

---

### Ejemplo 2: Verificar Autenticación Antes de Llamar API

```python
import aiohttp

async def call_employees_api():
    base_url = "http://localhost:8002/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # Verificar autenticación
        async with session.get(f"{base_url}/auth/status") as resp:
            status = await resp.json()
            
            if not status["token_valid"]:
                print("❌ Token expirado o inválido")
                print("Por favor, ejecuta /auth/login nuevamente")
                return
        
        # Llamar al API de empleados
        async with session.get(f"{base_url}/employees") as resp:
            data = await resp.json()
            print(f"✅ Empleados encontrados: {data['count']}")
            for emp in data['employees']:
                print(f"  - {emp.get('DisplayName')}")
```

## 🔐 Seguridad

### ✅ Protección CSRF Implementada

La aplicación implementa protección contra ataques CSRF (Cross-Site Request Forgery) en el flujo OAuth:

1. **Generación de state**: Se genera un token aleatorio seguro usando `secrets.token_urlsafe(32)`
2. **Almacenamiento temporal**: El state se guarda en memoria antes de redirigir a QuickBooks
3. **Validación en callback**: Se verifica que el state recibido coincida con el generado
4. **Un solo uso**: El state se elimina después de usarse, evitando reutilización

**Implementación actual:**
```python
import secrets

# En login
state = secrets.token_urlsafe(32)
active_states[state] = True

# En callback
if not state or state not in active_states:
    raise HTTPException(status_code=400, detail="State inválido. Posible ataque CSRF.")
active_states.pop(state, None)  # Eliminar después de usar
```

**⚠️ Nota para producción**: El almacenamiento en memoria (`active_states: dict`) funciona para desarrollo, pero en producción deberías usar Redis con TTL automático para soportar múltiples instancias del servidor.

---

### ⚠️ Almacenamiento de Tokens

**Estado Actual:** Los tokens se almacenan en memoria durante la ejecución del servidor.

**Consideraciones para Producción:**

1. **Base de datos encriptada**
   ```python
   # Ejemplo con SQLAlchemy + cryptography
   from cryptography.fernet import Fernet
   
   # Encriptar token antes de guardar
   cipher = Fernet(encryption_key)
   encrypted_token = cipher.encrypt(access_token.encode())
   ```

2. **Redis con TTL automático**
   ```python
   # Ejemplo con Redis
   import redis
   
   r = redis.Redis(host='localhost', port=6379, db=0)
   r.setex(f"qb_token:{user_id}", 3600, access_token)
   ```

3. **Variables de sesión seguras**
   - Usar cookies HttpOnly y Secure
   - Implementar CSRF protection
   - Usar sesiones encriptadas

---

### 🛡️ Protección de Endpoints

Para proteger endpoints y requerir autenticación:

```python
from fastapi import Depends, HTTPException
from app.utils.quickbooks_auth import quickbooks_auth

async def require_auth():
    """Middleware de autenticación."""
    if not quickbooks_auth.is_token_valid():
        raise HTTPException(
            status_code=401,
            detail="No autenticado o token expirado"
        )
    return quickbooks_auth

@router.get("/protected")
async def protected_endpoint(auth = Depends(require_auth)):
    """Endpoint protegido que requiere autenticación."""
    # Tu lógica aquí
    pass
```

---

### 🔒 Mejores Prácticas

1. **Nunca expongas credenciales**
   - Mantén `.env` fuera del control de versiones
   - Usa variables de entorno en producción

2. **Valida tokens antes de cada llamada**
   ```python
   if not quickbooks_auth.is_token_valid():
       # Refresh token automáticamente
       await quickbooks_auth.refresh_token()
   ```

3. **Implementa rate limiting**
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.get("/auth/login")
   @limiter.limit("5/minute")
   async def login():
       # Tu lógica
       pass
   ```

4. **Logs de auditoría**
   ```python
   logger.info(f"Autenticación exitosa - Realm ID: {realm_id} - IP: {request.client.host}")
   ```

## 🚀 Iniciar el Servidor

```bash
# Activar entorno virtual (si usas venv)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor (construye frontend automáticamente)
python start.py
```

El servidor estará disponible en: **http://localhost:8002**

Documentación interactiva (Swagger): **http://localhost:8002/docs**

**Nota**: El script `start.py` automáticamente construye el frontend de Ionic antes de iniciar el servidor backend.

---

## 🐛 Troubleshooting

### ❌ Error: "OAuth2 no configurado"

**Causa:** Las variables de entorno no están configuradas.

**Solución:**
1. Verifica que exista el archivo `.env`
2. Confirma que contenga `QUICKBOOKS_CLIENT_ID` y `QUICKBOOKS_CLIENT_SECRET`
3. Reinicia el servidor

```bash
# Verificar variables
cat .env | grep QUICKBOOKS  # Linux/Mac
type .env | findstr QUICKBOOKS  # Windows
```

---

### ❌ Error: "Token expirado"

**Causa:** El access token de QuickBooks tiene una validez de 1 hora.

**Solución actual:** Vuelve a ejecutar el flujo de autenticación:
1. Ve a `http://localhost:8002/api/v1/auth/login`
2. Autoriza nuevamente en QuickBooks
3. Serás redirigido automáticamente a `/`

**Mejora futura:** Implementar refresh token automático.

---

### ❌ Error: "No autenticado"

**Causa:** No has completado el flujo de autenticación.

**Solución:**
1. Abre en tu navegador: `http://localhost:8002/api/v1/auth/login`
2. Autoriza la aplicación en QuickBooks
3. Espera la redirección automática a `/`
4. Verifica el estado: `http://localhost:8002/api/v1/auth/status`

---

### ❌ Error: "Redirect URI mismatch" o "redirect_uri no es válido"

**Causa:** La URI de redirección no coincide **exactamente** con la configurada en QuickBooks.

**Solución:**
1. Ve a [Intuit Developer Dashboard](https://developer.intuit.com/app/developer/dashboard)
2. Selecciona tu aplicación
3. Ve a "Keys & credentials" → "Redirect URIs"
4. Agrega EXACTAMENTE estas URIs:
   - **Desarrollo**: `http://localhost:8002/v1/auth/callback`
   - **Producción**: `https://tu-dominio.com/v1/auth/callback`
5. Asegúrate que coincida **exactamente** con `QUICKBOOKS_REDIRECT_URI` en `.env`
6. **Importante**: No incluyas `/api` en el path, solo `/v1/auth/callback`
7. Reinicia el servidor después de cambiar `.env`

---

### ❌ Error al obtener empleados

**Verificar:**

1. **Token válido:**
   ```bash
   curl http://localhost:8002/api/v1/auth/status
   ```

2. **Company ID correcto:**
   ```bash
   # Verifica en .env
   echo $QUICKBOOKS_COMPANY_ID
   ```

3. **Permisos de la app:**
   - Ve a tu app en Intuit Developer Portal
   - Verifica que tenga acceso a "Accounting" scope
   - Re-autoriza si es necesario

---

### ❌ Error: "Connection closed" en callback

**Causa:** (Corregido en v1.1) El cliente HTTP de aiohttp cerraba la conexión antes de leer la respuesta.

**Solución aplicada:**
El `HTTPClient` ahora lee el contenido completo antes de cerrar la sesión:

```python
# En http_request.py
async with session.request(...) as response:
    # Leer antes de cerrar
    response_content = await response.read()
    return ResponseWrapper(response.status, response.headers, response_content)
```

Si aún ves este error:
1. Asegúrate de tener la última versión del código
2. Verifica que `app/core/http_request.py` incluya la corrección
3. Reinicia el servidor

---

### 🔍 Debug Mode

Para ver logs detallados:

```python
# En start.py o main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---
