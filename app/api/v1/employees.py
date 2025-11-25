"""
CRUD completo para empleados de QuickBooks.
Maneja la creación, lectura, actualización y eliminación de empleados.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from app.models.employee import EmployeeCreate, EmployeeUpdate
from app.utils.quickbooks_auth import quickbooks_auth
from app.core.http_request import HTTPClient
from app.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Importar user_sessions y serializer desde auth.py
from app.api.v1.auth import user_sessions, serializer


# Helper para procesar errores de QuickBooks
def parse_quickbooks_error(error_text: str, status_code: int) -> Dict[str, Any]:
    """Parsea el error de QuickBooks y retorna un JSON estructurado."""
    try:
        error_json = json.loads(error_text)
        if "Fault" in error_json:
            fault = error_json["Fault"]
            errors = fault.get("Error", [])
            return {
                "error": True,
                "status_code": status_code,
                "type": fault.get("type", "Unknown"),
                "errors": [
                    {
                        "message": err.get("Message", ""),
                        "detail": err.get("Detail", ""),
                        "code": err.get("code", "")
                    }
                    for err in errors
                ],
                "time": error_json.get("time")
            }
        return {"error": True, "status_code": status_code, "message": error_text}
    except json.JSONDecodeError:
        return {"error": True, "status_code": status_code, "message": error_text}


# Helper para verificar autenticación y obtener tokens de la sesión
async def get_session_data(request: Request) -> Dict[str, Any]:
    """Verifica que el usuario esté autenticado y retorna los datos de sesión."""
    # Obtener cookie de sesión
    session_cookie = request.cookies.get("qb_session")
    
    if not session_cookie:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Debe llamar a /auth/login primero"
        )
    
    try:
        # Deserializar session_id de la cookie firmada
        session_id = serializer.loads(session_cookie, max_age=3600)
        
        # Verificar si existe sesión para este usuario
        if session_id not in user_sessions:
            raise HTTPException(
                status_code=401,
                detail="Sesión no encontrada. Debe autenticarse nuevamente"
            )
        
        session_data = user_sessions[session_id]
        token_expiry = session_data.get("token_expiry")
        
        # Verificar si el token sigue siendo válido
        if not token_expiry or datetime.now() >= (token_expiry - timedelta(minutes=5)):
            raise HTTPException(
                status_code=401,
                detail="Token expirado. Debe autenticarse nuevamente"
            )
        
        return session_data
        
    except Exception as e:
        logger.error(f"❌ Error verificando autenticación: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Error de autenticación. Debe llamar a /auth/login"
        )


@router.get(
    "/employees",
    tags=["Employees"],
    summary="Listar empleados",
    description="Obtiene la lista completa de empleados desde QuickBooks con opciones de filtrado por estado activo y límite de resultados."
)
async def get_all_employees(
    request: Request,
    active: Optional[bool] = None,
    limit: int = 100
):
    """
    Obtiene la lista de empleados desde QuickBooks.
    
    **Query de ejemplo:**
    ```
    GET /employees
    GET /employees?active=true
    GET /employees?limit=50
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "count": 3,
      "employees": [...]
    }
    ```
    """
    # Obtener datos de sesión (incluye access_token, realm_id)
    session_data = await get_session_data(request)
    
    try:
        client = HTTPClient()
        
        # Construir query
        query = "SELECT * FROM Employee"
        if active is not None:
            query += f" WHERE Active = {str(active).lower()}"
        query += f" MAXRESULTS {limit}"
        
        # Construir URL con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        url = f"{base_url}/company/{realm_id}/query?query={query}"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info(f"📋 Obteniendo empleados: {query}")
        
        response = await client.get(url, headers=headers)
        
        if response.status == 200:
            data = await response.json()
            employees = data.get("QueryResponse", {}).get("Employee", [])
            
            return {
                "status": "success",
                "count": len(employees),
                "employees": employees
            }
        else:
            error_text = await response.text()
            logger.error(f"❌ Error obteniendo empleados: {response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, response.status)
            return JSONResponse(status_code=response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/employees/{employee_id}",
    tags=["Employees"],
    summary="Obtener empleado por ID",
    description="Obtiene los detalles completos de un empleado específico utilizando su ID de QuickBooks."
)
async def get_employee(request: Request, employee_id: str):
    """
    Obtiene los detalles de un empleado específico.
    
    **Ejemplo:**
    ```
    GET /employees/55
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "employee": {
        "Id": "55",
        "DisplayName": "Juan Pérez",
        "GivenName": "Juan",
        "FamilyName": "Pérez",
        ...
      }
    }
    ```
    """
    # Obtener datos de sesión
    session_data = await get_session_data(request)
    
    try:
        client = HTTPClient()
        
        # Construir URL con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        url = f"{base_url}/company/{realm_id}/employee/{employee_id}"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info(f"👤 Obteniendo empleado ID: {employee_id}")
        
        response = await client.get(url, headers=headers)
        
        if response.status == 200:
            data = await response.json()
            employee = data.get("Employee")
            
            return {
                "status": "success",
                "employee": employee
            }
        else:
            error_text = await response.text()
            logger.error(f"❌ Error: {response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, response.status)
            return JSONResponse(status_code=response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/employees",
    tags=["Employees"],
    status_code=201,
    summary="Crear empleado",
    description="Crea un nuevo empleado en QuickBooks con la información proporcionada. Requiere nombre y apellido."
)
async def create_employee(request: Request, employee: EmployeeCreate):
    """
    Crea un nuevo empleado en QuickBooks.
    
    **Campos requeridos:**
    - GivenName (Nombre)
    - FamilyName (Apellido)
    
    **Ejemplo de request:**
    ```json
    {
      "GivenName": "Juan",
      "FamilyName": "Pérez",
      "PrimaryEmailAddr": {
        "Address": "juan.perez@example.com"
      },
      "PrimaryPhone": {
        "FreeFormNumber": "(555) 123-4567"
      }
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "message": "Empleado creado exitosamente",
      "employee": {...}
    }
    ```
    """
    # Obtener datos de sesión
    session_data = await get_session_data(request)
    
    try:
        client = HTTPClient()
        
        # Construir URL con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        url = f"{base_url}/company/{realm_id}/employee"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Convertir a dict y remover None
        employee_data = employee.model_dump(exclude_none=True)
        
        logger.info(f"➕ Creando empleado: {employee.GivenName} {employee.FamilyName}")
        
        response = await client.post(url, headers=headers, json_data=employee_data)
        
        if response.status == 200:
            data = await response.json()
            created_employee = data.get("Employee")
            
            return {
                "status": "success",
                "message": "Empleado creado exitosamente",
                "employee": created_employee
            }
        else:
            error_text = await response.text()
            logger.error(f"❌ Error creando empleado: {response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, response.status)
            return JSONResponse(status_code=response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/employees/{employee_id}",
    tags=["Employees"],
    summary="Actualizar empleado",
    description="Actualiza completamente la información de un empleado existente. Requiere ID y SyncToken del empleado."
)
async def update_employee(request: Request, employee_id: str, employee: EmployeeUpdate):
    """
    Actualiza un empleado existente (Full Update).
    
    **Importante:** 
    - Debes incluir el Id y SyncToken del empleado
    - El SyncToken se obtiene del GET del empleado
    - Todos los campos escriturables deben incluirse
    
    **Ejemplo de request:**
    ```json
    {
      "Id": "55",
      "SyncToken": "0",
      "GivenName": "Juan",
      "FamilyName": "Pérez García",
      "PrimaryEmailAddr": {
        "Address": "juan.perez@nuevoemail.com"
      },
      "Active": true
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "message": "Empleado actualizado exitosamente",
      "employee": {...}
    }
    ```
    """
    # Obtener datos de sesión
    session_data = await get_session_data(request)
    
    if employee.Id != employee_id:
        raise HTTPException(
            status_code=400,
            detail="El ID del empleado no coincide con el ID en el body"
        )
    
    try:
        client = HTTPClient()
        
        # Construir URL con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        url = f"{base_url}/company/{realm_id}/employee"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Convertir a dict y remover None
        employee_data = employee.model_dump(exclude_none=True)
        
        # Remover solo el campo V4IDPseudonym que es read-only
        employee_data.pop('V4IDPseudonym', None)
        
        # Asegurar que sparse esté en false para full update
        employee_data['sparse'] = False
        
        logger.info(f"✏️ Actualizando empleado ID: {employee_id}")
        logger.info(f"📤 Datos a enviar: {employee_data}")
        logger.info(f"🏢 Realm ID: {realm_id}")
        
        response = await client.post(url, headers=headers, json_data=employee_data)
        
        if response.status == 200:
            data = await response.json()
            updated_employee = data.get("Employee")
            
            return {
                "status": "success",
                "message": "Empleado actualizado exitosamente",
                "employee": updated_employee
            }
        else:
            error_text = await response.text()
            logger.error(f"❌ Error actualizando empleado: {response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, response.status)
            return JSONResponse(status_code=response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/employees/{employee_id}",
    tags=["Employees"],
    summary="Desactivar empleado",
    description="Desactiva un empleado estableciendo Active=false. QuickBooks no permite eliminación permanente de empleados."
)
async def deactivate_employee(request: Request, employee_id: str):
    """
    Desactiva un empleado (soft delete).
    
    **Nota:** QuickBooks no permite eliminar empleados completamente.
    Este endpoint establece Active=false (desactivación).
    
    **Ejemplo:**
    ```
    DELETE /employees/55
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "message": "Empleado desactivado exitosamente",
      "employee": {...}
    }
    ```
    """
    # Obtener datos de sesión
    session_data = await get_session_data(request)
    
    try:
        # Primero obtener el empleado para tener el SyncToken
        client = HTTPClient()
        
        # Construir URLs con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        get_url = f"{base_url}/company/{realm_id}/employee/{employee_id}"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        get_response = await client.get(get_url, headers=headers)
        
        if get_response.status != 200:
            error_text = await get_response.text()
            error_detail = parse_quickbooks_error(error_text, get_response.status)
            return JSONResponse(status_code=get_response.status, content=error_detail)
        
        employee_data = await get_response.json()
        employee = employee_data.get("Employee")
        
        # Actualizar con Active=false
        employee["Active"] = False
        
        logger.info(f"🗑️ Desactivando empleado ID: {employee_id}")
        
        # Update employee
        update_url = f"{base_url}/company/{realm_id}/employee"
        update_response = await client.post(update_url, headers=headers, json_data=employee)
        
        if update_response.status == 200:
            data = await update_response.json()
            deactivated_employee = data.get("Employee")
            
            return {
                "status": "success",
                "message": "Empleado desactivado exitosamente",
                "employee": deactivated_employee
            }
        else:
            error_text = await update_response.text()
            logger.error(f"❌ Error desactivando empleado: {update_response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, update_response.status)
            return JSONResponse(status_code=update_response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/employees/{employee_id}/activate",
    tags=["Employees"],
    summary="Activar empleado",
    description="Reactiva un empleado previamente desactivado estableciendo Active=true."
)
async def activate_employee(request: Request, employee_id: str):
    """
    Reactiva un empleado desactivado.
    
    **Ejemplo:**
    ```
    POST /employees/55/activate
    ```
    
    **Respuesta:**
    ```json
    {
      "status": "success",
      "message": "Empleado activado exitosamente",
      "employee": {...}
    }
    ```
    """
    # Obtener datos de sesión
    session_data = await get_session_data(request)
    
    try:
        client = HTTPClient()
        
        # Construir URLs con realm_id de la sesión
        base_url = settings.quickbooks_base_url
        realm_id = session_data.get("realm_id")
        get_url = f"{base_url}/company/{realm_id}/employee/{employee_id}"
        
        # Headers con access_token de la sesión
        headers = {
            "Authorization": f"Bearer {session_data.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        get_response = await client.get(get_url, headers=headers)
        
        if get_response.status != 200:
            error_text = await get_response.text()
            error_detail = parse_quickbooks_error(error_text, get_response.status)
            return JSONResponse(status_code=get_response.status, content=error_detail)
        
        employee_data = await get_response.json()
        employee = employee_data.get("Employee")
        
        # Actualizar con Active=true
        employee["Active"] = True
        
        logger.info(f"✅ Activando empleado ID: {employee_id}")
        
        # Update employee
        update_url = f"{base_url}/company/{realm_id}/employee"
        update_response = await client.post(update_url, headers=headers, json_data=employee)
        
        if update_response.status == 200:
            data = await update_response.json()
            activated_employee = data.get("Employee")
            
            return {
                "status": "success",
                "message": "Empleado activado exitosamente",
                "employee": activated_employee
            }
        else:
            error_text = await update_response.text()
            logger.error(f"❌ Error activando empleado: {update_response.status} - {error_text}")
            error_detail = parse_quickbooks_error(error_text, update_response.status)
            return JSONResponse(status_code=update_response.status, content=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excepción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
