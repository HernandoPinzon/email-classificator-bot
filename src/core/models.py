"""
Modelos de datos para el sistema de clasificación de correos.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EmailClassification:
    """Resultado de clasificación de un correo"""
    category: str
    priority: str  # 'urgente', 'normal', 'sin_prioridad'
    summary: str
    amount: Optional[str] = None
    action_required: bool = False


@dataclass
class Email:
    """Representa un correo electrónico"""
    id: str
    subject: str
    sender: str
    body: str
    date: str = ""


@dataclass
class HttpResponse:
    """Respuesta HTTP estandarizada"""
    status_code: int
    text: str

    def json(self) -> Dict:
        """Parsea el contenido como JSON"""
        import json
        return json.loads(self.text)

    def raise_for_status(self):
        """Lanza excepción si el status code indica error"""
        if self.status_code >= 400:
            raise HttpError(f"HTTP {self.status_code}: {self.text}")


class HttpError(Exception):
    """Error en petición HTTP"""
    pass
