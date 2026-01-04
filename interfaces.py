"""
Interfaces y protocolos para el sistema de clasificación de correos.
Define contratos que permiten inyección de dependencias y testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Protocol


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


class HttpClient(Protocol):
    """Protocolo para cliente HTTP - permite mockear llamadas externas"""

    def post(self, url: str, **kwargs) -> 'HttpResponse':
        """Realiza una petición POST"""
        ...

    def get(self, url: str, **kwargs) -> 'HttpResponse':
        """Realiza una petición GET"""
        ...


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


class EmailFetcher(ABC):
    """Interfaz para obtener correos electrónicos"""

    @abstractmethod
    def authenticate(self) -> bool:
        """Autentica con el servicio de correo"""
        pass

    @abstractmethod
    def get_unread_emails(self, max_results: int = 50, query: str = "") -> List[Email]:
        """Obtiene correos no leídos"""
        pass

    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """Marca un correo como leído"""
        pass


class EmailRepository(ABC):
    """Interfaz para persistencia de correos clasificados"""

    @abstractmethod
    def init_database(self) -> None:
        """Inicializa el esquema de la base de datos"""
        pass

    @abstractmethod
    def is_processed(self, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado"""
        pass

    @abstractmethod
    def save_classification(self, email: Email, classification: EmailClassification) -> None:
        """Guarda la clasificación de un correo"""
        pass

    @abstractmethod
    def get_daily_stats(self, date: str) -> List[Dict]:
        """Obtiene estadísticas del día"""
        pass


class Notifier(ABC):
    """Interfaz para envío de notificaciones"""

    @abstractmethod
    def send_message(self, message: str, silent: bool = False) -> bool:
        """Envía un mensaje genérico"""
        pass

    @abstractmethod
    def send_email_alert(self, email_data: Dict) -> bool:
        """Envía alerta de correo importante"""
        pass

    @abstractmethod
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """Envía resumen diario"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Prueba la conexión"""
        pass


class EmailClassifier(ABC):
    """Interfaz para clasificación de correos"""

    @abstractmethod
    def classify(self, subject: str, body: str, sender: str = "") -> EmailClassification:
        """Clasifica un correo electrónico"""
        pass


class AIProvider(ABC):
    """Interfaz base para proveedores de IA"""

    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre del proveedor"""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> Dict:
        """Genera una respuesta del modelo"""
        pass
