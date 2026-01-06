"""
Configuración centralizada para el sistema de clasificación de correos.
Permite inyectar configuración en tests sin depender de variables de entorno.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import os
from pathlib import Path

import yaml


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
    # Modo headless: 'auto', 'browser', 'manual', 'token_env'
    # - auto: intenta browser, si falla usa manual
    # - browser: usa navegador local (requiere GUI)
    # - manual: muestra URL y pide código manualmente (para servidores)
    # - token_env: usa token desde variable de entorno GMAIL_TOKEN_JSON
    auth_mode: str = "auto"


@dataclass
class DatabaseConfig:
    """Configuración para base de datos"""
    path: str = "./emails.db"


@dataclass
class ScheduleConfig:
    """Configuración de modo de ejecución"""
    # Modo: 'hourly' o 'daily'
    # - hourly: Revisa correos de las últimas N horas, solo notifica si hay importantes
    # - daily: Revisa correos desde ayer, envía resumen diario completo
    check_mode: str = "daily"
    # Intervalo en horas (solo aplica en modo hourly)
    check_interval_hours: int = 2
    # Minutos extra para cubrir delays
    check_buffer_minutes: int = 1


def _get_default_rules_path() -> str:
    """Obtiene la ruta por defecto del archivo de reglas"""
    return str(Path(__file__).parent / "config" / "classification_rules.yaml")


def load_classification_rules(rules_path: str = None) -> dict:
    """
    Carga las reglas de clasificación desde un archivo YAML.

    Args:
        rules_path: Ruta al archivo YAML. Si es None, usa la ruta por defecto.

    Returns:
        Diccionario con las reglas de clasificación
    """
    if rules_path is None:
        rules_path = _get_default_rules_path()

    path = Path(rules_path)

    if not path.exists():
        print(f"Archivo de reglas no encontrado: {rules_path}")
        print("Usando reglas por defecto.")
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
            return rules if rules else {}
    except Exception as e:
        print(f"Error cargando reglas desde {rules_path}: {e}")
        print("Usando reglas por defecto.")
        return {}


# Valores por defecto (usados si el archivo YAML no existe o hay errores)
_DEFAULT_URGENT_KEYWORDS = [
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
]

_DEFAULT_PAYMENT_KEYWORDS = [
    'pago',
    'cargo',
    'compra',
    'transferencia',
    'retiro',
    'depósito',
    'comisión',
    'intereses',
    'domiciliación',
]

_DEFAULT_LOW_PRIORITY_KEYWORDS = [
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
]

_DEFAULT_AMOUNT_PATTERNS = [
    r'\$\s*[\d,]+\.?\d{0,2}',
    r'[\d,]+\.?\d{0,2}\s*(?:pesos|MXN|USD|EUR|COP)',
    r'(?:total|monto|importe|cantidad|cargo):\s*\$?\s*[\d,]+\.?\d{0,2}',
]


@dataclass
class ClassifierConfig:
    """Configuración para el clasificador de correos"""
    # Ruta al archivo YAML de reglas (None = usar ruta por defecto)
    rules_path: Optional[str] = None

    # Keywords y patrones (se cargan desde YAML o usan defaults)
    urgent_keywords: List[str] = field(default_factory=list)
    payment_keywords: List[str] = field(default_factory=list)
    low_priority_keywords: List[str] = field(default_factory=list)
    amount_patterns: List[str] = field(default_factory=list)

    # Remitentes por prioridad (nuevo desde YAML)
    low_priority_senders: List[str] = field(default_factory=list)
    high_priority_senders: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Carga las reglas desde YAML después de inicializar"""
        rules = load_classification_rules(self.rules_path)

        # Cargar desde YAML o usar defaults
        if not self.urgent_keywords:
            self.urgent_keywords = rules.get('urgent_keywords', _DEFAULT_URGENT_KEYWORDS)
        if not self.payment_keywords:
            self.payment_keywords = rules.get('payment_keywords', _DEFAULT_PAYMENT_KEYWORDS)
        if not self.low_priority_keywords:
            self.low_priority_keywords = rules.get('low_priority_keywords', _DEFAULT_LOW_PRIORITY_KEYWORDS)
        if not self.amount_patterns:
            self.amount_patterns = rules.get('amount_patterns', _DEFAULT_AMOUNT_PATTERNS)

        # Remitentes (solo desde YAML, vacío por defecto)
        if not self.low_priority_senders:
            self.low_priority_senders = rules.get('low_priority_senders', [])
        if not self.high_priority_senders:
            self.high_priority_senders = rules.get('high_priority_senders', [])


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
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)


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
            auth_mode=os.getenv('GMAIL_AUTH_MODE', 'auto'),
        ),
        database=DatabaseConfig(
            path=os.getenv('DATABASE_PATH', './emails.db'),
        ),
        schedule=ScheduleConfig(
            check_mode=os.getenv('CHECK_MODE', 'daily'),
            check_interval_hours=int(os.getenv('CHECK_INTERVAL_HOURS', '2')),
            check_buffer_minutes=int(os.getenv('CHECK_BUFFER_MINUTES', '1')),
        ),
    )
