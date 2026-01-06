"""
Fixtures compartidos para todas las pruebas.
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core import Email, EmailClassification
from src.config import (
    AppConfig, ClassifierConfig, TelegramConfig,
    DatabaseConfig, AIProviderConfig, OllamaConfig
)
from src.utils import MockHttpClient
from src.core.models import HttpResponse
from src.repositories import InMemoryEmailRepository
from src.fetchers import MockEmailFetcher
from src.notifiers import MockNotifier
from src.classifiers import MockEmailClassifier
from src.providers import MockAIProvider, AIProviderManager


# ============== Fixtures de Configuración ==============

@pytest.fixture
def classifier_config():
    """Configuración del clasificador con keywords de prueba"""
    return ClassifierConfig(
        urgent_keywords=['urgente', 'pago pendiente', 'vence mañana'],
        payment_keywords=['pago', 'cargo', 'transferencia'],
        low_priority_keywords=['promoción', 'oferta', 'newsletter'],
        amount_patterns=[
            r'\$\s*[\d,]+\.?\d{0,2}',
            r'[\d,]+\.?\d{0,2}\s*(?:pesos|MXN|USD)',
        ]
    )


@pytest.fixture
def app_config():
    """Configuración completa de la aplicación para tests"""
    return AppConfig(
        database=DatabaseConfig(path=":memory:"),
        telegram=TelegramConfig(
            bot_token="test_token",
            chat_id="test_chat_id"
        ),
        ai_provider=AIProviderConfig(
            provider_type="ollama",
            ollama=OllamaConfig(
                host="http://localhost:11434",
                model="test-model"
            )
        )
    )


# ============== Fixtures de Mocks ==============

@pytest.fixture
def mock_http_client():
    """Cliente HTTP mock para simular respuestas"""
    return MockHttpClient()


@pytest.fixture
def mock_ai_provider():
    """Proveedor de IA mock"""
    provider = MockAIProvider(name="TestProvider")
    provider.set_default_response({
        "category": "notificacion",
        "priority": "normal",
        "summary": "Test summary",
        "action_required": False
    })
    return provider


@pytest.fixture
def mock_email_fetcher():
    """Fetcher de emails mock"""
    fetcher = MockEmailFetcher()
    fetcher.authenticate()
    return fetcher


@pytest.fixture
def mock_notifier():
    """Notificador mock"""
    return MockNotifier()


@pytest.fixture
def mock_classifier():
    """Clasificador mock"""
    return MockEmailClassifier()


@pytest.fixture
def in_memory_repository():
    """Repositorio en memoria"""
    repo = InMemoryEmailRepository()
    repo.init_database()
    return repo


# ============== Fixtures de Datos de Prueba ==============

@pytest.fixture
def sample_urgent_email():
    """Email urgente de prueba"""
    return Email(
        id="urgent_001",
        subject="URGENTE: Pago pendiente de tarjeta",
        sender="alertas@banco.com",
        body="Tu pago de $5,000.00 vence mañana. Realiza tu pago para evitar cargos.",
        date="2024-01-15"
    )


@pytest.fixture
def sample_normal_email():
    """Email normal de prueba"""
    return Email(
        id="normal_001",
        subject="Transferencia recibida",
        sender="notificaciones@banco.com",
        body="Has recibido una transferencia de $15,000.00 en tu cuenta.",
        date="2024-01-15"
    )


@pytest.fixture
def sample_promo_email():
    """Email promocional de prueba"""
    return Email(
        id="promo_001",
        subject="Oferta especial para ti",
        sender="promociones@banco.com",
        body="Aprovecha nuestra promoción de puntos dobles este mes.",
        date="2024-01-15"
    )


@pytest.fixture
def sample_emails(sample_urgent_email, sample_normal_email, sample_promo_email):
    """Lista de emails de prueba"""
    return [sample_urgent_email, sample_normal_email, sample_promo_email]


@pytest.fixture
def urgent_classification():
    """Clasificación urgente de prueba"""
    return EmailClassification(
        category="pago",
        priority="urgente",
        summary="Pago de $5,000 vence mañana",
        amount="$5,000.00",
        action_required=True
    )


@pytest.fixture
def normal_classification():
    """Clasificación normal de prueba"""
    return EmailClassification(
        category="transferencia",
        priority="normal",
        summary="Transferencia recibida de $15,000",
        amount="$15,000.00",
        action_required=False
    )


@pytest.fixture
def promo_classification():
    """Clasificación promocional de prueba"""
    return EmailClassification(
        category="promocion",
        priority="sin_prioridad",
        summary="Promoción de puntos",
        amount=None,
        action_required=False
    )
