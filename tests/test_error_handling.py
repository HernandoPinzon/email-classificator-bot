"""
Pruebas para manejo de errores y casos edge.
"""

import pytest
from src.config import TelegramConfig, AIProviderConfig, OllamaConfig, GroqConfig
from src.notifiers import TelegramNotifier, TelegramConfigError, MockNotifier
from src.providers import (
    OllamaProvider, GroqProvider, AIProviderManager,
    MockAIProvider, create_provider_from_config
)
from src.utils import MockHttpClient
from src.core.models import HttpResponse, HttpError
from src.classifiers import BankEmailClassifier
from src.core import EmailClassification


class TestTelegramConfigValidation:
    """Pruebas de validación de configuración de Telegram"""

    def test_empty_bot_token_raises_error(self):
        """Token vacío lanza TelegramConfigError"""
        config = TelegramConfig(bot_token="", chat_id="123456")

        with pytest.raises(TelegramConfigError) as exc_info:
            TelegramNotifier(config)

        assert "TELEGRAM_BOT_TOKEN" in str(exc_info.value)
        assert "@BotFather" in str(exc_info.value)

    def test_empty_chat_id_raises_error(self):
        """Chat ID vacío lanza TelegramConfigError"""
        config = TelegramConfig(bot_token="valid_token", chat_id="")

        with pytest.raises(TelegramConfigError) as exc_info:
            TelegramNotifier(config)

        assert "TELEGRAM_CHAT_ID" in str(exc_info.value)

    def test_whitespace_only_token_raises_error(self):
        """Token con solo espacios lanza error"""
        config = TelegramConfig(bot_token="   ", chat_id="123456")

        with pytest.raises(TelegramConfigError):
            TelegramNotifier(config)

    def test_valid_config_creates_notifier(self):
        """Configuración válida crea notificador"""
        config = TelegramConfig(bot_token="valid_token", chat_id="123456")
        mock_http = MockHttpClient()

        notifier = TelegramNotifier(config, http_client=mock_http)

        assert notifier.is_configured is True
        assert notifier.bot_token == "valid_token"
        assert notifier.chat_id == "123456"

    def test_validate_false_allows_empty_config(self):
        """validate=False permite configuración vacía"""
        config = TelegramConfig(bot_token="", chat_id="")

        # No debería lanzar error
        notifier = TelegramNotifier(config, validate=False)

        assert notifier.is_configured is False


class TestTelegramSendErrors:
    """Pruebas de errores al enviar mensajes"""

    def test_send_message_http_error(self):
        """Maneja error HTTP al enviar mensaje"""
        config = TelegramConfig(bot_token="token", chat_id="123")
        mock_http = MockHttpClient()
        mock_http.set_response(
            "https://api.telegram.org/bottoken/sendMessage",
            HttpResponse(status_code=401, text='{"ok": false, "error": "Unauthorized"}')
        )

        notifier = TelegramNotifier(config, http_client=mock_http)
        result = notifier.send_message("Test")

        assert result is False

    def test_send_message_network_error(self):
        """Maneja error de red al enviar mensaje"""
        config = TelegramConfig(bot_token="token", chat_id="123")

        class FailingHttpClient:
            def post(self, *args, **kwargs):
                raise HttpError("Connection refused")

        notifier = TelegramNotifier(config, http_client=FailingHttpClient())
        result = notifier.send_message("Test")

        assert result is False


class TestAIProviderErrors:
    """Pruebas de errores en proveedores de IA"""

    def test_ollama_connection_refused(self):
        """Maneja error de conexión a Ollama"""
        class FailingHttpClient:
            def post(self, *args, **kwargs):
                raise HttpError("Connection refused to localhost:11434")

        provider = OllamaProvider(
            host="http://localhost:11434",
            model="llama3",
            http_client=FailingHttpClient()
        )

        with pytest.raises(Exception) as exc_info:
            provider.generate("Test")

        assert "Ollama" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    def test_groq_invalid_api_key(self):
        """Maneja API key inválida de Groq"""
        mock_http = MockHttpClient()
        mock_http.set_response(
            "https://api.groq.com/openai/v1/chat/completions",
            HttpResponse(
                status_code=401,
                text='{"error": {"message": "Invalid API Key"}}'
            )
        )

        provider = GroqProvider(api_key="invalid_key", http_client=mock_http)

        with pytest.raises(Exception) as exc_info:
            provider.generate("Test")

        assert "Groq error" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    def test_groq_rate_limit(self):
        """Maneja rate limit de Groq"""
        mock_http = MockHttpClient()
        mock_http.set_response(
            "https://api.groq.com/openai/v1/chat/completions",
            HttpResponse(
                status_code=429,
                text='{"error": {"message": "Rate limit exceeded"}}'
            )
        )

        provider = GroqProvider(api_key="valid_key", http_client=mock_http)

        with pytest.raises(Exception) as exc_info:
            provider.generate("Test")

        assert "429" in str(exc_info.value)

    def test_provider_manager_all_fail_with_details(self):
        """Manager reporta detalles cuando todos fallan"""
        p1 = MockAIProvider("Provider1")
        p1.set_failure(True, "Provider1 failed: timeout")

        p2 = MockAIProvider("Provider2")
        p2.set_failure(True, "Provider2 failed: rate limit")

        manager = AIProviderManager([p1, p2])

        with pytest.raises(Exception) as exc_info:
            manager.generate("Test")

        error_msg = str(exc_info.value)
        assert "Todos los proveedores fallaron" in error_msg


class TestCreateProviderErrors:
    """Pruebas de errores al crear proveedores"""

    def test_api_mode_no_keys_error(self):
        """Modo API sin keys lanza error descriptivo"""
        config = AIProviderConfig(
            provider_type="api",
            groq=GroqConfig(api_key=""),
        )

        with pytest.raises(Exception) as exc_info:
            create_provider_from_config(config)

        assert "no hay API keys" in str(exc_info.value)

    def test_invalid_provider_type_error(self):
        """Tipo de proveedor inválido lanza error descriptivo"""
        config = AIProviderConfig(provider_type="invalid_type")

        with pytest.raises(Exception) as exc_info:
            create_provider_from_config(config)

        assert "AI_PROVIDER inválido" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)
        assert "ollama" in str(exc_info.value)  # Sugiere opciones válidas


class TestClassifierFallback:
    """Pruebas de fallback del clasificador"""

    def test_classifier_fallback_on_llm_failure(self):
        """Clasificador usa fallback cuando LLM falla"""
        failing_provider = MockAIProvider()
        failing_provider.set_failure(True, "LLM unavailable")

        classifier = BankEmailClassifier(ai_provider=failing_provider)

        # No debería lanzar excepción, debería usar fallback
        result = classifier.classify(
            subject="Pago pendiente urgente",
            body="Tu pago de $1,000 vence mañana",
            sender="banco@test.com"
        )

        assert isinstance(result, EmailClassification)
        assert result.category == "pago"  # Detectado por fallback
        assert result.priority == "urgente"  # Detectado por keywords

    def test_classifier_extracts_amount_on_llm_failure(self):
        """Clasificador extrae monto aunque LLM falle"""
        failing_provider = MockAIProvider()
        failing_provider.set_failure(True, "LLM unavailable")

        classifier = BankEmailClassifier(ai_provider=failing_provider)

        result = classifier.classify(
            subject="Cargo de $2,500.00",
            body="Se realizó un cargo en tu cuenta",
            sender="banco@test.com"
        )

        assert result.amount == "$2,500.00"

    def test_classifier_works_without_ai_provider(self):
        """Clasificador funciona sin proveedor de IA (solo fallback)"""
        classifier = BankEmailClassifier(ai_provider=None)

        result = classifier.classify(
            subject="Transferencia recibida",
            body="Recibiste $5,000 en tu cuenta",
            sender="banco@test.com"
        )

        assert result.category == "transferencia"
        assert result.amount == "$5,000"


class TestMockNotifierForTesting:
    """Pruebas del MockNotifier para testing"""

    def test_mock_notifier_records_all_messages(self):
        """MockNotifier registra todos los mensajes"""
        notifier = MockNotifier()

        notifier.send_message("Mensaje 1")
        notifier.send_message("Mensaje 2", silent=True)

        assert len(notifier.messages) == 2
        assert notifier.messages[0]['text'] == "Mensaje 1"
        assert notifier.messages[1]['silent'] is True

    def test_mock_notifier_simulates_failure(self):
        """MockNotifier puede simular fallo"""
        notifier = MockNotifier()
        notifier.set_connection_failure()

        result = notifier.send_message("Test")

        assert result is False
        assert notifier.test_connection() is False

    def test_mock_notifier_clear_resets(self):
        """MockNotifier.clear() reinicia estado"""
        notifier = MockNotifier()
        notifier.send_message("Test")
        notifier.set_connection_failure()

        notifier.clear()

        assert len(notifier.messages) == 0
        assert notifier.connection_works is True
