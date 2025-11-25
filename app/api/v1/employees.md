# 👥 API de Empleados QuickBooks

Esta documentación cubre el CRUD completo de empleados de QuickBooks Online API.

## 📑 Tabla de Contenidos

- [Requisitos Previos](#-requisitos-previos)
- [Modelos de Datos](#-modelos-de-datos)
- [Endpoints Disponibles](#-endpoints-disponibles)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Validaciones](#-validaciones)
- [Manejo de Errores](#-manejo-de-errores)
- [Mejores Prácticas](#-mejores-prácticas)

---

## ✅ Requisitos Previos

Antes de usar los endpoints de empleados, debes:

1. **Estar autenticado con QuickBooks**
   ```bash
   GET http://localhost:8002/api/v1/auth/login
   ```
   
   **Nota:** El puerto por defecto es 8002, configurable mediante la variable de entorno `PORT`.
   
   Esto creará una cookie de sesión `qb_session` en tu navegador.

2. **Verificar que el token sea válido**
   ```bash
   GET http://localhost:8002/api/v1/auth/status
   ```

⚠️ **Todos los endpoints de empleados requieren autenticación activa.**

### 🔐 Autenticación Basada en Sesiones

Los endpoints de empleados utilizan autenticación basada en sesiones con cookies:

- **Cookie `qb_session`**: Contiene el session_id firmado
- **HttpOnly**: Cookie no accesible desde JavaScript
- **Validación automática**: Cada request verifica la cookie y valida el token
- **Aislamiento de sesiones**: Cada navegador/usuario tiene su propia sesión independiente

**Flujo de autenticación:**
1. Login → Crea cookie `qb_session`
2. Request a `/employees` → Backend lee cookie automáticamente
3. Backend valida session_id y obtiene tokens
4. Backend usa tokens para llamar a QuickBooks API
5. Response devuelta al cliente

**No necesitas enviar headers manualmente** - las cookies se envían automáticamente.

---

## 📦 Modelos de Datos

### PhysicalAddress

Dirección física del empleado.

```json
{
  "Line1": "123 Main Street",
  "Line2": "Apt 4B",
  "City": "San Francisco",
  "CountrySubDivisionCode": "CA",
  "PostalCode": "94107",
  "Country": "USA"
}
```

**Campos:**
- `Line1` - `Line5` (string, opcional): Líneas de dirección
- `City` (string, opcional): Ciudad
- `CountrySubDivisionCode` (string, opcional): Código de estado/provincia
- `PostalCode` (string, opcional): Código postal
- `Country` (string, opcional): País

---

### EmailAddress

Email del empleado.

```json
{
  "Address": "juan.perez@example.com"
}
```

**Campos:**
- `Address` (EmailStr, opcional): Dirección de email válida

⚠️ **Nota:** Se valida que sea un email válido.

---

### TelephoneNumber

Número telefónico.

```json
{
  "FreeFormNumber": "(555) 123-4567"
}
```

**Campos:**
- `FreeFormNumber` (string, opcional, max 20): Número de teléfono

---

### EmployeeCreate

Modelo para crear un empleado nuevo.

```json
{
  "GivenName": "Juan",
  "FamilyName": "Pérez",
  "MiddleName": "Carlos",
  "DisplayName": "Juan C. Pérez",
  "Title": "Mr.",
  "Suffix": "Jr.",
  "PrimaryEmailAddr": {
    "Address": "juan.perez@example.com"
  },
  "PrimaryPhone": {
    "FreeFormNumber": "(555) 123-4567"
  },
  "Mobile": {
    "FreeFormNumber": "(555) 987-6543"
  },
  "PrimaryAddr": {
    "Line1": "123 Main Street",
    "City": "San Francisco",
    "CountrySubDivisionCode": "CA",
    "PostalCode": "94107"
  },
  "EmployeeNumber": "EMP-001",
  "SSN": "XXX-XX-1234",
  "Gender": "Male",
  "HiredDate": "2024-01-15",
  "BirthDate": "1990-05-20",
  "BillableTime": false,
  "BillRate": 75.00,
  "CostRate": 50.00,
  "Active": true
}
```

**Campos Requeridos:**
- `GivenName` (string, max 100): Nombre
- `FamilyName` (string, max 100): Apellido

**Campos Opcionales:**
- `MiddleName` (string, max 100): Segundo nombre
- `DisplayName` (string, max 500): Nombre a mostrar
- `Title` (string, max 16): Título (Mr., Mrs., etc.)
- `Suffix` (string, max 16): Sufijo (Jr., Sr., etc.)
- `PrimaryEmailAddr` (EmailAddress): Email principal
- `PrimaryPhone` (TelephoneNumber): Teléfono principal
- `Mobile` (TelephoneNumber): Teléfono móvil
- `PrimaryAddr` (PhysicalAddress): Dirección principal
- `EmployeeNumber` (string, max 100): Número de empleado
- `SSN` (string, max 100): Número de seguridad social
- `Gender` (string): Género ("Male" o "Female")
- `HiredDate` (date): Fecha de contratación
- `ReleasedDate` (date): Fecha de salida
- `BirthDate` (date): Fecha de nacimiento
- `BillableTime` (bool): ¿Tiempo facturable?
- `BillRate` (float): Tarifa de facturación
- `CostRate` (float): Tarifa de costo
- `Active` (bool): ¿Activo? (default: true)

---

### EmployeeUpdate

Modelo para actualizar un empleado existente.

⚠️ **Importante:** Requiere `Id` y `SyncToken` del empleado.

```json
{
  "Id": "55",
  "SyncToken": "1",
  "GivenName": "Juan",
  "FamilyName": "Pérez García",
  "PrimaryEmailAddr": {
    "Address": "juan.nuevo@example.com"
  },
  "Active": true
}
```

**Campos Requeridos:**
- `Id` (string): ID del empleado
- `SyncToken` (string): Token de sincronización
- `GivenName` (string, max 100): Nombre
- `FamilyName` (string, max 100): Apellido

**Campos Opcionales:**
- Todos los mismos campos opcionales de `EmployeeCreate`

---

## 📊 Endpoints Disponibles

### Resumen

| Endpoint | Método | Resumen |
|----------|--------|---------|
| `/api/v1/employees` | GET | Listar empleados |
| `/api/v1/employees/{id}` | GET | Obtener empleado por ID |
| `/api/v1/employees` | POST | Crear empleado |
| `/api/v1/employees/{id}` | PUT | Actualizar empleado |
| `/api/v1/employees/{id}` | DELETE | Desactivar empleado |
| `/api/v1/employees/{id}/activate` | POST | Activar empleado |

---

## 🔍 Detalles de Endpoints

### `GET /api/v1/employees`

**Resumen:** Listar empleados

**Descripción:** Obtiene la lista completa de empleados desde QuickBooks con opciones de filtrado por estado activo, búsqueda, ordenamiento y paginación.

**Parámetros Query:**
- `active` (bool, opcional): Filtrar por estado activo
  - `true`: Solo empleados activos
  - `false`: Solo empleados inactivos
  - Sin valor: Todos los empleados
- `search` (string, opcional): Buscar en nombre, apellido o display name
- `order_by` (string, default: "GivenName"): Campo para ordenar
  - Valores válidos: `GivenName`, `FamilyName`, `DisplayName`, `EmployeeNumber`
- `order_dir` (string, default: "ASC"): Dirección de orden
  - Valores válidos: `ASC`, `DESC`
- `limit` (int, default: 5): Cantidad de resultados por página
- `offset` (int, default: 0): Posición inicial para paginación

**Ejemplos:**

```bash
# Obtener todos los empleados (primera página)
GET http://localhost:8001/api/v1/employees

# Solo empleados activos, 10 por página
GET http://localhost:8001/api/v1/employees?active=true&limit=10

# Buscar empleados con "Juan"
GET http://localhost:8001/api/v1/employees?search=juan

# Ordenar por apellido descendente
GET http://localhost:8001/api/v1/employees?order_by=FamilyName&order_dir=DESC

# Segunda página (5 resultados por página)
GET http://localhost:8001/api/v1/employees?limit=5&offset=5

# Combinar filtros: activos, buscar "García", ordenar por nombre, segunda página
GET http://localhost:8001/api/v1/employees?active=true&search=García&order_by=GivenName&order_dir=ASC&limit=10&offset=10
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "count": 5,
  "pagination": {
    "limit": 5,
    "offset": 0,
    "has_more": true,
    "next_offset": 5,
    "prev_offset": null
  },
  "filters": {
    "active": true,
    "search": null,
    "order_by": "GivenName",
    "order_dir": "ASC"
  },
  "employees": [
    {
      "Id": "55",
      "DisplayName": "Juan Pérez",
      "GivenName": "Juan",
      "FamilyName": "Pérez",
      "PrimaryEmailAddr": {
        "Address": "juan.perez@example.com"
      },
      "Active": true,
      "SyncToken": "1"
    }
  ]
}
```

**Errores Posibles:**
- `401 Unauthorized`: No autenticado o token expirado
- `500 Internal Server Error`: Error en QuickBooks API

---

### `GET /api/v1/employees/{employee_id}`

**Resumen:** Obtener empleado por ID

**Descripción:** Obtiene los detalles completos de un empleado específico utilizando su ID de QuickBooks.

**Parámetros de Ruta:**
- `employee_id` (string, requerido): ID del empleado en QuickBooks

**Ejemplo:**

```bash
GET http://localhost:8001/api/v1/employees/55
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "employee": {
    "Id": "55",
    "SyncToken": "1",
    "DisplayName": "Juan Pérez",
    "GivenName": "Juan",
    "FamilyName": "Pérez",
    "PrimaryEmailAddr": {
      "Address": "juan.perez@example.com"
    },
    "PrimaryPhone": {
      "FreeFormNumber": "(555) 123-4567"
    },
    "Active": true,
    "HiredDate": "2024-01-15",
    "EmployeeNumber": "EMP-001"
  }
}
```

**Errores Posibles:**
- `401 Unauthorized`: No autenticado
- `404 Not Found`: Empleado no encontrado
- `500 Internal Server Error`: Error en QuickBooks API

---

### `POST /api/v1/employees`

**Resumen:** Crear empleado

**Descripción:** Crea un nuevo empleado en QuickBooks con la información proporcionada. Requiere nombre y apellido.

**Body (JSON):**

```json
{
  "GivenName": "María",
  "FamilyName": "González",
  "PrimaryEmailAddr": {
    "Address": "maria.gonzalez@example.com"
  },
  "PrimaryPhone": {
    "FreeFormNumber": "(555) 234-5678"
  },
  "PrimaryAddr": {
    "Line1": "456 Oak Avenue",
    "City": "Los Angeles",
    "CountrySubDivisionCode": "CA",
    "PostalCode": "90001"
  },
  "HiredDate": "2025-01-01",
  "EmployeeNumber": "EMP-002",
  "Active": true
}
```

**Respuesta Exitosa (201 Created):**

```json
{
  "status": "success",
  "message": "Empleado creado exitosamente",
  "employee": {
    "Id": "56",
    "SyncToken": "0",
    "DisplayName": "María González",
    "GivenName": "María",
    "FamilyName": "González",
    "PrimaryEmailAddr": {
      "Address": "maria.gonzalez@example.com"
    },
    "Active": true
  }
}
```

**Errores Posibles:**
- `400 Bad Request`: Datos inválidos (ej: email inválido)
- `401 Unauthorized`: No autenticado
- `500 Internal Server Error`: Error en QuickBooks API

---

### `PUT /api/v1/employees/{employee_id}`

**Resumen:** Actualizar empleado

**Descripción:** Actualiza completamente la información de un empleado existente. Requiere ID y SyncToken del empleado.

⚠️ **Importante:** 
- Debes obtener primero el empleado con GET para obtener el `SyncToken`
- El `SyncToken` cambia con cada actualización
- Debes incluir TODOS los campos que quieres mantener

**Parámetros de Ruta:**
- `employee_id` (string, requerido): ID del empleado

**Body (JSON):**

```json
{
  "Id": "55",
  "SyncToken": "1",
  "GivenName": "Juan",
  "FamilyName": "Pérez García",
  "DisplayName": "Juan Pérez García",
  "PrimaryEmailAddr": {
    "Address": "juan.nuevo@example.com"
  },
  "PrimaryPhone": {
    "FreeFormNumber": "(555) 999-8888"
  },
  "Active": true
}
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "message": "Empleado actualizado exitosamente",
  "employee": {
    "Id": "55",
    "SyncToken": "2",
    "GivenName": "Juan",
    "FamilyName": "Pérez García",
    "DisplayName": "Juan Pérez García",
    "PrimaryEmailAddr": {
      "Address": "juan.nuevo@example.com"
    },
    "Active": true
  }
}
```

**Errores Posibles:**
- `400 Bad Request`: ID no coincide o SyncToken inválido
- `401 Unauthorized`: No autenticado
- `404 Not Found`: Empleado no encontrado
- `409 Conflict`: SyncToken desactualizado
- `500 Internal Server Error`: Error en QuickBooks API

---

### `DELETE /api/v1/employees/{employee_id}`

**Resumen:** Desactivar empleado

**Descripción:** Desactiva un empleado estableciendo Active=false. QuickBooks no permite eliminación permanente de empleados.

⚠️ **Nota:** Esto es un "soft delete" - el empleado permanece en la base de datos pero marcado como inactivo.

**Parámetros de Ruta:**
- `employee_id` (string, requerido): ID del empleado

**Ejemplo:**

```bash
DELETE http://localhost:8001/api/v1/employees/55
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "message": "Empleado desactivado exitosamente",
  "employee": {
    "Id": "55",
    "SyncToken": "3",
    "GivenName": "Juan",
    "FamilyName": "Pérez",
    "Active": false
  }
}
```

**Errores Posibles:**
- `401 Unauthorized`: No autenticado
- `404 Not Found`: Empleado no encontrado
- `500 Internal Server Error`: Error en QuickBooks API

---

### `POST /api/v1/employees/{employee_id}/activate`

**Resumen:** Activar empleado

**Descripción:** Reactiva un empleado previamente desactivado estableciendo Active=true.

**Parámetros de Ruta:**
- `employee_id` (string, requerido): ID del empleado

**Ejemplo:**

```bash
POST http://localhost:8001/api/v1/employees/55/activate
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "message": "Empleado activado exitosamente",
  "employee": {
    "Id": "55",
    "SyncToken": "4",
    "GivenName": "Juan",
    "FamilyName": "Pérez",
    "Active": true
  }
}
```

**Errores Posibles:**
- `401 Unauthorized`: No autenticado
- `404 Not Found`: Empleado no encontrado
- `500 Internal Server Error`: Error en QuickBooks API

---



## ✅ Validaciones

### Validación de Email

El campo `PrimaryEmailAddr.Address` usa `EmailStr` de Pydantic:

✅ **Válidos:**
- `usuario@example.com`
- `nombre.apellido@empresa.co.uk`
- `test+tag@domain.com`

❌ **Inválidos:**
- `no-es-email`
- `@example.com`
- `usuario@`
- `usuario @example.com` (con espacio)

### Validación de Longitud de Campos

| Campo | Longitud Máxima |
|-------|-----------------|
| `GivenName` | 100 |
| `FamilyName` | 100 |
| `MiddleName` | 100 |
| `DisplayName` | 500 |
| `Title` | 16 |
| `Suffix` | 16 |
| `EmployeeNumber` | 100 |
| `SSN` | 100 |
| `FreeFormNumber` (Phone) | 20 |
| Address Lines | 500 |
| `City` | 255 |
| `CountrySubDivisionCode` | 255 |

### Validación de Género

Valores aceptados:
- `"Male"`
- `"Female"`
- `null` (sin especificar)

---

## ⚠️ Manejo de Errores

### Error 401: No Autenticado

```json
{
  "detail": "No autenticado. Debe llamar a /auth/login primero"
}
```

**Causa:** No hay cookie de sesión o la cookie es inválida.

**Solución:** 
1. Completa el flujo de autenticación OAuth2 abriendo `/auth/login` en tu navegador
2. Asegúrate de que las cookies estén habilitadas
3. Si usas Postman/Insomnia, habilita el manejo automático de cookies

---

### Error 401: Sesión No Encontrada

```json
{
  "detail": "Sesión no encontrada. Debe autenticarse nuevamente"
}
```

**Causa:** El servidor se reinició y las sesiones en memoria se perdieron.

**Solución:** Vuelve a autenticarte con `/auth/login`

---

### Error 401: Token Expirado

```json
{
  "detail": "Token expirado. Debe autenticarse nuevamente"
}
```

**Causa:** El access token de QuickBooks tiene 1 hora de validez y expiró.

**Solución:** Vuelve a autenticarte con `/auth/login` (mejora futura: refresh automático)

---

### Error 400: Datos Inválidos

```json
{
  "detail": [
    {
      "loc": ["body", "PrimaryEmailAddr", "Address"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Solución:** Verifica que todos los datos cumplan con las validaciones.

---

### Error 409: SyncToken Desactualizado

```json
{
  "Fault": {
    "Error": [{
      "Message": "Stale object error",
      "code": "1234"
    }]
  }
}
```

**Solución:** Vuelve a obtener el empleado con GET para obtener el SyncToken actualizado.

---

### Error 404: Empleado No Encontrado

```json
{
  "detail": "Employee not found"
}
```

**Solución:** Verifica que el ID del empleado sea correcto.

---

## 🎯 Mejores Prácticas

### 1. Siempre Verifica Autenticación Primero

```python
# Verificar autenticación antes de operaciones
async with aiohttp.ClientSession() as session:
    async with session.get("http://localhost:8001/api/v1/auth/status") as resp:
        status = await resp.json()
        if not status["token_valid"]:
            print("❌ Token inválido, re-autenticar")
            return
```

---

### 2. Manejo Correcto de SyncToken

```python
# ❌ INCORRECTO - Usar SyncToken viejo
employee_data["SyncToken"] = "0"

# ✅ CORRECTO - Obtener SyncToken actual
current_employee = await get_employee(employee_id)
employee_data["SyncToken"] = current_employee["SyncToken"]
```

---

### 3. Validar Emails Antes de Enviar

```python
from email_validator import validate_email, EmailNotValidError

def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

# Uso
if is_valid_email("test@example.com"):
    # Crear empleado
    pass
```

---

### 4. Usar Paginación para Listas Grandes

```python
# Obtener empleados en lotes
async def get_all_employees_paginated():
    limit = 100
    all_employees = []
    
    url = f"http://localhost:8001/api/v1/employees?limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            all_employees.extend(data['employees'])
    
    return all_employees
```

---

### 5. Soft Delete en Lugar de Eliminación

```python
# ❌ INCORRECTO - No se puede hacer hard delete
# QuickBooks no permite eliminación permanente

# ✅ CORRECTO - Usar desactivación (soft delete)
async with session.delete(f"{base_url}/employees/{employee_id}") as resp:
    # Esto establece Active=false
    pass
```

---

### 6. Manejo de Errores Robusto

```python
async def safe_create_employee(employee_data: dict):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=employee_data) as resp:
                if resp.status == 201:
                    return await resp.json()
                elif resp.status == 400:
                    error = await resp.json()
                    print(f"❌ Datos inválidos: {error}")
                elif resp.status == 401:
                    print("❌ No autenticado")
                else:
                    print(f"❌ Error {resp.status}")
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    return None
```

---

## 📚 Recursos Adicionales

- 📖 [QuickBooks Employee API Documentation](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/employee)
- 🔍 [QuickBooks API Explorer](https://developer.intuit.com/app/developer/playground)
- 💻 [Pydantic Documentation](https://docs.pydantic.dev/)
- 📧 [email-validator Documentation](https://github.com/JoshData/python-email-validator)

---

## 📝 Notas Importantes

1. **QuickBooks no permite eliminación permanente** de empleados - solo desactivación.

2. **SyncToken es obligatorio** para actualizaciones - cambia con cada modificación.

3. **DisplayName se auto-genera** si no se proporciona: `GivenName + " " + FamilyName`

4. **Empleados desactivados** no aparecen en listas a menos que uses `active=false`.

5. **Rate Limits de QuickBooks:**
   - Sandbox: 100 requests/minuto
   - Production: 500 requests/minuto

6. **Campos de fecha** deben estar en formato ISO: `YYYY-MM-DD`

---

**Documentación actualizada:** 24 de noviembre de 2025
