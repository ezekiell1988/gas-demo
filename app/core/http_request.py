"""
Cliente HTTP asíncrono usando aiohttp para todos los verbos HTTP.
Proporciona una interfaz limpia y reutilizable para realizar peticiones HTTP.
"""

import aiohttp
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Cliente HTTP asíncrono con soporte completo para todos los verbos HTTP.
    
    Características:
    - Soporte para GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
    - Manejo automático de timeouts
    - Logging detallado de peticiones y respuestas
    - Manejo de errores robusto
    - Soporte para headers personalizados
    - Conversión automática de JSON
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """
        Inicializa el cliente HTTP.
        
        Args:
            base_url: URL base para todas las peticiones (opcional)
            timeout: Timeout por defecto en segundos
            default_headers: Headers que se incluirán en todas las peticiones
        """
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.default_headers = default_headers or {}
        
    def _build_url(self, url: str) -> str:
        """
        Construye la URL completa combinando base_url con la URL relativa.
        
        Args:
            url: URL relativa o absoluta
            
        Returns:
            URL completa
        """
        if self.base_url and not url.startswith(('http://', 'https://')):
            return urljoin(self.base_url, url)
        return url
        
    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Combina headers por defecto con headers específicos de la petición.
        
        Args:
            headers: Headers específicos de la petición
            
        Returns:
            Headers combinados
        """
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged
        
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> 'ResponseWrapper':
        """
        Realiza una petición HTTP genérica.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL de destino
            headers: Headers de la petición
            params: Parámetros de query string
            data: Datos del cuerpo (raw)
            json_data: Datos JSON para el cuerpo
            **kwargs: Argumentos adicionales para aiohttp
            
        Returns:
            ResponseWrapper con los datos de la respuesta
            
        Raises:
            aiohttp.ClientError: Si ocurre un error en la petición
        """
        full_url = self._build_url(url)
        merged_headers = self._merge_headers(headers)
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=merged_headers
        ) as session:
            async with session.request(
                method=method,
                url=full_url,
                params=params,
                data=data,
                json=json_data,
                **kwargs
            ) as response:
                # Leer el contenido antes de que se cierre la conexión
                response_status = response.status
                response_headers = response.headers
                response_content = await response.read()
                
                # Wrapper para mantener la interfaz compatible
                class ResponseWrapper:
                    def __init__(self, status, headers, content):
                        self.status = status
                        self.headers = headers
                        self._content = content
                    
                    async def text(self):
                        return self._content.decode('utf-8')
                    
                    async def read(self):
                        return self._content
                    
                    async def json(self):
                        import json
                        return json.loads(self._content.decode('utf-8'))
                
                return ResponseWrapper(response_status, response_headers, response_content)
                
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición GET.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('GET', url, headers, params, **kwargs)
        
    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición POST.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            data: Datos del cuerpo (raw, puede ser FormData para multipart/form-data)
            json_data: Datos JSON para el cuerpo
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('POST', url, headers, params, data, json_data, **kwargs)
    
    async def post_multipart(
        self,
        url: str,
        files: Dict[str, tuple],
        fields: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición POST con multipart/form-data.
        
        Args:
            url: URL de destino
            files: Diccionario de archivos {nombre_campo: (nombre_archivo, bytes, content_type)}
            fields: Campos adicionales del formulario
            headers: Headers adicionales
            params: Parámetros de query string
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
            
        Example:
            files = {'file': ('audio.ogg', audio_bytes, 'audio/ogg')}
            fields = {'model': 'gpt-4o-transcribe', 'response_format': 'text'}
            response = await client.post_multipart(url, files, fields)
        """
        full_url = self._build_url(url)
        merged_headers = self._merge_headers(headers)
        
        
        # Crear FormData
        form = aiohttp.FormData()
        
        # Agregar archivos
        for field_name, file_data in files.items():
            if len(file_data) == 3:
                filename, file_bytes, content_type = file_data
                form.add_field(
                    field_name,
                    file_bytes,
                    filename=filename,
                    content_type=content_type
                )
            else:
                logger.warning(f"Formato incorrecto para archivo {field_name}, esperado (filename, bytes, content_type)")
        
        # Agregar campos adicionales
        if fields:
            for field_name, field_value in fields.items():
                form.add_field(field_name, field_value)
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=merged_headers
        ) as session:
            async with session.post(
                full_url,
                params=params,
                data=form,
                **kwargs
            ) as response:
                
                # Leer el contenido antes de cerrar la conexión
                response_status = response.status
                response_headers = response.headers
                response_content = await response.read()
                
                # Crear un objeto simple para retornar con los datos
                class ResponseWrapper:
                    def __init__(self, status, headers, content):
                        self.status = status
                        self.headers = headers
                        self._content = content
                    
                    async def text(self):
                        return self._content.decode('utf-8')
                    
                    async def read(self):
                        return self._content
                    
                    async def json(self):
                        import json
                        return json.loads(self._content.decode('utf-8'))
                
                return ResponseWrapper(response_status, response_headers, response_content)
        
    async def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición PUT.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            data: Datos del cuerpo (raw)
            json_data: Datos JSON para el cuerpo
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('PUT', url, headers, params, data, json_data, **kwargs)
        
    async def patch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición PATCH.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            data: Datos del cuerpo (raw)
            json_data: Datos JSON para el cuerpo
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('PATCH', url, headers, params, data, json_data, **kwargs)
        
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición DELETE.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('DELETE', url, headers, params, **kwargs)
        
    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición HEAD.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('HEAD', url, headers, params, **kwargs)
        
    async def options(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Realiza una petición OPTIONS.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            **kwargs: Argumentos adicionales
            
        Returns:
            Respuesta HTTP
        """
        return await self._make_request('OPTIONS', url, headers, params, **kwargs)
        
    # Métodos de conveniencia para respuestas comunes
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza una petición GET y devuelve el JSON parseado.
        
        Args:
            url: URL de destino
            **kwargs: Argumentos adicionales para get()
            
        Returns:
            Diccionario con la respuesta JSON
            
        Raises:
            aiohttp.ClientError: Si hay error en la petición
            json.JSONDecodeError: Si la respuesta no es JSON válido
        """
        full_url = self._build_url(url)
        merged_headers = self._merge_headers(kwargs.pop('headers', None))
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=merged_headers
        ) as session:
            async with session.get(full_url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        
    async def get_text(self, url: str, **kwargs) -> str:
        """
        Realiza una petición GET y devuelve el texto de la respuesta.
        
        Args:
            url: URL de destino
            **kwargs: Argumentos adicionales para get()
            
        Returns:
            Texto de la respuesta
            
        Raises:
            aiohttp.ClientError: Si hay error en la petición
        """
        full_url = self._build_url(url)
        merged_headers = self._merge_headers(kwargs.pop('headers', None))
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=merged_headers
        ) as session:
            async with session.get(full_url, **kwargs) as response:
                response.raise_for_status()
                return await response.text()
        
    async def get_bytes(self, url: str, **kwargs) -> bytes:
        """
        Realiza una petición GET y devuelve los bytes de la respuesta.
        
        Args:
            url: URL de destino
            **kwargs: Argumentos adicionales para get()
            
        Returns:
            Bytes de la respuesta
            
        Raises:
            aiohttp.ClientError: Si hay error en la petición
        """
        full_url = self._build_url(url)
        merged_headers = self._merge_headers(kwargs.pop('headers', None))
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=merged_headers
        ) as session:
            async with session.get(full_url, **kwargs) as response:
                response.raise_for_status()
                return await response.read()


# Cliente global por defecto
http_client = HTTPClient()


# Funciones de conveniencia para uso rápido
async def get(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para GET usando el cliente global."""
    return await http_client.get(url, **kwargs)


async def post(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para POST usando el cliente global."""
    return await http_client.post(url, **kwargs)


async def post_multipart(url: str, files: Dict[str, tuple], fields: Optional[Dict[str, str]] = None, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para POST multipart usando el cliente global."""
    return await http_client.post_multipart(url, files, fields, **kwargs)


async def put(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para PUT usando el cliente global."""
    return await http_client.put(url, **kwargs)


async def patch(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para PATCH usando el cliente global."""
    return await http_client.patch(url, **kwargs)


async def delete(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para DELETE usando el cliente global."""
    return await http_client.delete(url, **kwargs)


async def head(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para HEAD usando el cliente global."""
    return await http_client.head(url, **kwargs)


async def options(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Función de conveniencia para OPTIONS usando el cliente global."""
    return await http_client.options(url, **kwargs)


# Funciones para respuestas parseadas
async def get_json(url: str, **kwargs) -> Dict[str, Any]:
    """Función de conveniencia para GET + JSON usando el cliente global."""
    return await http_client.get_json(url, **kwargs)


async def get_text(url: str, **kwargs) -> str:
    """Función de conveniencia para GET + texto usando el cliente global."""
    return await http_client.get_text(url, **kwargs)


async def get_bytes(url: str, **kwargs) -> bytes:
    """Función de conveniencia para GET + bytes usando el cliente global."""
    return await http_client.get_bytes(url, **kwargs)