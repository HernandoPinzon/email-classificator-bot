"""
Cliente HTTP abstracto para permitir testing con mocks.
"""

from typing import Dict, Optional
import requests

from ..core.models import HttpResponse, HttpError


class RequestsHttpClient:
    """
    Implementación del cliente HTTP usando la librería requests.
    Esta es la implementación real para producción.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def post(self, url: str, headers: Optional[Dict] = None,
             json: Optional[Dict] = None, data: Optional[Dict] = None,
             timeout: Optional[int] = None) -> HttpResponse:
        """Realiza una petición POST"""
        try:
            response = requests.post(
                url,
                headers=headers,
                json=json,
                data=data,
                timeout=timeout or self.timeout
            )
            return HttpResponse(
                status_code=response.status_code,
                text=response.text
            )
        except requests.exceptions.RequestException as e:
            raise HttpError(f"Error en petición POST a {url}: {e}")

    def get(self, url: str, headers: Optional[Dict] = None,
            params: Optional[Dict] = None,
            timeout: Optional[int] = None) -> HttpResponse:
        """Realiza una petición GET"""
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout or self.timeout
            )
            return HttpResponse(
                status_code=response.status_code,
                text=response.text
            )
        except requests.exceptions.RequestException as e:
            raise HttpError(f"Error en petición GET a {url}: {e}")


class MockHttpClient:
    """
    Cliente HTTP mock para testing.
    Permite configurar respuestas predefinidas.
    """

    def __init__(self):
        self.responses: Dict[str, HttpResponse] = {}
        self.calls: list = []

    def set_response(self, url: str, response: HttpResponse):
        """Configura una respuesta para una URL específica"""
        self.responses[url] = response

    def set_json_response(self, url: str, status_code: int, data: Dict):
        """Configura una respuesta JSON para una URL"""
        import json
        self.responses[url] = HttpResponse(
            status_code=status_code,
            text=json.dumps(data)
        )

    def post(self, url: str, headers: Optional[Dict] = None,
             json: Optional[Dict] = None, data: Optional[Dict] = None,
             timeout: Optional[int] = None) -> HttpResponse:
        """Simula una petición POST"""
        self.calls.append({
            'method': 'POST',
            'url': url,
            'headers': headers,
            'json': json,
            'data': data
        })

        if url in self.responses:
            return self.responses[url]

        # Respuesta por defecto
        return HttpResponse(status_code=200, text='{"ok": true}')

    def get(self, url: str, headers: Optional[Dict] = None,
            params: Optional[Dict] = None,
            timeout: Optional[int] = None) -> HttpResponse:
        """Simula una petición GET"""
        self.calls.append({
            'method': 'GET',
            'url': url,
            'headers': headers,
            'params': params
        })

        if url in self.responses:
            return self.responses[url]

        return HttpResponse(status_code=200, text='{}')

    def get_calls(self, method: Optional[str] = None) -> list:
        """Retorna las llamadas realizadas, opcionalmente filtradas por método"""
        if method:
            return [c for c in self.calls if c['method'] == method]
        return self.calls

    def reset(self):
        """Limpia las respuestas y llamadas registradas"""
        self.responses.clear()
        self.calls.clear()
