"""
Módulo core - Interfaces, modelos y procesador principal
"""

from .models import Email, EmailClassification, HttpResponse, HttpError
from .interfaces import (
    HttpClient,
    EmailFetcher,
    EmailRepository,
    Notifier,
    EmailClassifier,
    AIProvider,
)
from .processor import EmailProcessor

__all__ = [
    # Models
    "Email",
    "EmailClassification",
    "HttpResponse",
    "HttpError",
    # Interfaces
    "HttpClient",
    "EmailFetcher",
    "EmailRepository",
    "Notifier",
    "EmailClassifier",
    "AIProvider",
    # Processor
    "EmailProcessor",
]
