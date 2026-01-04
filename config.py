"""
Configuración centralizada para el sistema de clasificación de correos.
Permite inyectar configuración en tests sin depender de variables de entorno.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class OllamaConfig:
    """Configuración para Ollama local"""
    host: str = "http://localhost:11434"
    model: str = "llama3.2"


@dataclass
class GroqConfig:
    """Configuración para Groq API"""
    api_key: str = ""
    model: str = "mixtral-8x7b-32768"
    base_url: str = "https://api.groq.com/openai/v1"


@dataclass
class CerebrasConfig:
    """Configuración para Cerebras API"""
    api_key: str = ""
    model: str = "llama3.1-8b"
    base_url: str = "https://api.cerebras.ai/v1"


@dataclass
class GeminiConfig:
    """Configuración para Google Gemini API"""
    api_key: str = ""
    model: str = "gemini-1.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"


@dataclass
class OpenRouterConfig:
    """Configuración para OpenRouter API"""
    api_key: str = ""
    model: str = "meta-llama/llama-3.2-3b-instruct:free"
    base_url: str = "https://openrouter.ai/api/v1"


@dataclass
class TelegramConfig:
    """Configuración para Telegram"""
    bot_token: str = ""
    chat_id: str = ""
    api_url: str = "https://api.telegram.org"


@dataclass
class GmailConfig:
    """Configuración para Gmail API"""
    credentials_path: str = "./config/credentials.json"
    token_path: str = "./config/token.json"
    scopes: List[str] = field(default_factory=lambda: ['https://www.googleapis.com/auth/gmail.modify'])


@dataclass
class DatabaseConfig:
    """Configuración para base de datos"""
    path: str = "./emails.db"


@dataclass
class ClassifierConfig:
    """Configuración para el clasificador de correos"""
    urgent_keywords: List[str] = field(default_factory=lambda: [
        'pago pendiente',
        'pago vencido',
        'acción requerida',
        'urgente',
        'importante',
        'verificación requerida',
        'confirma tu',
        'por vencer',
        'último día',
        'fecha límite',
        'cobro próximo',
        'cargo próximo',
        'saldo insuficiente',
        'cuenta bloqueada',
        'suspensión',
    ])
    payment_keywords: List[str] = field(default_factory=lambda: [
        'pago',
        'cargo',
        'compra',
        'transferencia',
        'retiro',
        'depósito',
        'comisión',
        'intereses',
        'domiciliación',
    ])
    low_priority_keywords: List[str] = field(default_factory=lambda: [
        'promoción',
        'oferta',
        'descuento',
        'newsletter',
        'boletín',
        'tips',
        'consejos',
        'beneficios',
        'programa de puntos',
        'invitación',
        'evento',
        'encuesta',
        'noticia',
    ])
    amount_patterns: List[str] = field(default_factory=lambda: [
        r'\$\s*[\d,]+\.?\d{0,2}',
        r'[\d,]+\.?\d{0,2}\s*(?:pesos|MXN|USD|EUR)',
        r'(?:total|monto|importe|cantidad|cargo):\s*\$?\s*[\d,]+\.?\d{0,2}',
    ])


@dataclass
class AIProviderConfig:
    """Configuración general de proveedores de IA"""
    provider_type: str = "ollama"  # 'ollama', 'api', 'auto'
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    groq: GroqConfig = field(default_factory=GroqConfig)
    cerebras: CerebrasConfig = field(default_factory=CerebrasConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    openrouter: OpenRouterConfig = field(default_factory=OpenRouterConfig)


@dataclass
class AppConfig:
    """Configuración completa de la aplicación"""
    ai_provider: AIProviderConfig = field(default_factory=AIProviderConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    gmail: GmailConfig = field(default_factory=GmailConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)


def load_config_from_env() -> AppConfig:
    """
    Carga la configuración desde variables de entorno.
    Útil para producción, pero en tests se puede crear AppConfig directamente.
    """
    from dotenv import load_dotenv
    load_dotenv()

    return AppConfig(
        ai_provider=AIProviderConfig(
            provider_type=os.getenv('AI_PROVIDER', 'ollama'),
            ollama=OllamaConfig(
                host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
                model=os.getenv('OLLAMA_MODEL', 'llama3.2'),
            ),
            groq=GroqConfig(
                api_key=os.getenv('GROQ_API_KEY', ''),
                model=os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
            ),
            cerebras=CerebrasConfig(
                api_key=os.getenv('CEREBRAS_API_KEY', ''),
                model=os.getenv('CEREBRAS_MODEL', 'llama3.1-8b'),
            ),
            gemini=GeminiConfig(
                api_key=os.getenv('GEMINI_API_KEY', ''),
                model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            ),
            openrouter=OpenRouterConfig(
                api_key=os.getenv('OPENROUTER_API_KEY', ''),
                model=os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free'),
            ),
        ),
        telegram=TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
        ),
        gmail=GmailConfig(
            credentials_path=os.getenv('GMAIL_CREDENTIALS_PATH', './config/credentials.json'),
            token_path=os.getenv('GMAIL_TOKEN_PATH', './config/token.json'),
        ),
        database=DatabaseConfig(
            path=os.getenv('DATABASE_PATH', './emails.db'),
        ),
    )
