"""
Pruebas unitarias para AIProviders.
"""

import pytest
import json
from src.providers import (
    OllamaProvider, GroqProvider, CerebrasProvider,
    GeminiProvider, OpenRouterProvider,
    AIProviderManager, MockAIProvider,
    create_provider_from_config
)
from src.config import (
    AIProviderConfig, OllamaConfig, GroqConfig,
    CerebrasConfig, GeminiConfig, OpenRouterConfig
)
from src.utils import MockHttpClient
from src.core.models import HttpResponse


class TestOllamaProvider:
    """Pruebas para OllamaProvider"""

    def test_get_name(self):
        """Retorna nombre correcto"""
        provider = OllamaProvider(host="http://localhost:11434", model="llama3")

        assert provider.get_name() == "Ollama (llama3)"

    def test_generate_success(self, mock_http_client):
        """Genera respuesta exitosamente"""
        response_data = {
            "response": json.dumps({
                "category": "pago",
                "priority": "urgente",
                "summary": "Test"
            })
        }
        mock_http_client.set_json_response(
            "http://localhost:11434/api/generate",
            200,
            response_data
        )

        provider = OllamaProvider(
            host="http://localhost:11434",
            model="llama3",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "pago"
        assert result["priority"] == "urgente"

    def test_generate_with_markdown_response(self, mock_http_client):
        """Maneja respuesta con markdown"""
        response_data = {
            "response": "```json\n{\"category\": \"pago\"}\n```"
        }
        mock_http_client.set_json_response(
            "http://localhost:11434/api/generate",
            200,
            response_data
        )

        provider = OllamaProvider(
            host="http://localhost:11434",
            model="llama3",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "pago"

    def test_generate_error(self, mock_http_client):
        """Maneja error de API"""
        mock_http_client.set_response(
            "http://localhost:11434/api/generate",
            HttpResponse(status_code=500, text="Internal Server Error")
        )

        provider = OllamaProvider(
            host="http://localhost:11434",
            model="llama3",
            http_client=mock_http_client
        )

        with pytest.raises(Exception) as exc_info:
            provider.generate("Test prompt")

        assert "Ollama error" in str(exc_info.value)

    def test_init_with_config(self):
        """Inicializa con objeto de configuración"""
        config = OllamaConfig(host="http://custom:11434", model="custom-model")

        provider = OllamaProvider(config=config)

        assert provider.host == "http://custom:11434"
        assert provider.model == "custom-model"


class TestGroqProvider:
    """Pruebas para GroqProvider"""

    def test_get_name(self):
        """Retorna nombre correcto"""
        provider = GroqProvider(api_key="test", model="mixtral-8x7b-32768")

        assert provider.get_name() == "Groq (mixtral-8x7b-32768)"

    def test_generate_success(self, mock_http_client):
        """Genera respuesta exitosamente"""
        response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "category": "transferencia",
                        "priority": "normal"
                    })
                }
            }]
        }
        mock_http_client.set_json_response(
            "https://api.groq.com/openai/v1/chat/completions",
            200,
            response_data
        )

        provider = GroqProvider(
            api_key="test_key",
            model="mixtral",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "transferencia"

    def test_sends_correct_headers(self, mock_http_client):
        """Envía headers correctos"""
        response_data = {"choices": [{"message": {"content": "{}"}}]}
        mock_http_client.set_json_response(
            "https://api.groq.com/openai/v1/chat/completions",
            200,
            response_data
        )

        provider = GroqProvider(
            api_key="my_api_key",
            http_client=mock_http_client
        )

        provider.generate("Test")

        calls = mock_http_client.get_calls("POST")
        assert len(calls) == 1
        assert calls[0]["headers"]["Authorization"] == "Bearer my_api_key"


class TestCerebrasProvider:
    """Pruebas para CerebrasProvider"""

    def test_get_name(self):
        """Retorna nombre correcto"""
        provider = CerebrasProvider(api_key="test", model="llama3.1-8b")

        assert provider.get_name() == "Cerebras (llama3.1-8b)"

    def test_generate_success(self, mock_http_client):
        """Genera respuesta exitosamente"""
        response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({"category": "pago"})
                }
            }]
        }
        mock_http_client.set_json_response(
            "https://api.cerebras.ai/v1/chat/completions",
            200,
            response_data
        )

        provider = CerebrasProvider(
            api_key="test_key",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "pago"


class TestGeminiProvider:
    """Pruebas para GeminiProvider"""

    def test_get_name(self):
        """Retorna nombre correcto"""
        provider = GeminiProvider(api_key="test", model="gemini-1.5-flash")

        assert provider.get_name() == "Gemini (gemini-1.5-flash)"

    def test_generate_success(self, mock_http_client):
        """Genera respuesta exitosamente"""
        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({"category": "notificacion"})
                    }]
                }
            }]
        }

        # Gemini usa URL diferente con API key como parámetro
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=test_key"
        mock_http_client.set_json_response(url, 200, response_data)

        provider = GeminiProvider(
            api_key="test_key",
            model="gemini-1.5-flash",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "notificacion"


class TestOpenRouterProvider:
    """Pruebas para OpenRouterProvider"""

    def test_get_name(self):
        """Retorna nombre correcto"""
        provider = OpenRouterProvider(
            api_key="test",
            model="meta-llama/llama-3.2-3b-instruct:free"
        )

        assert "OpenRouter" in provider.get_name()

    def test_generate_success(self, mock_http_client):
        """Genera respuesta exitosamente"""
        response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({"category": "promocion"})
                }
            }]
        }
        mock_http_client.set_json_response(
            "https://openrouter.ai/api/v1/chat/completions",
            200,
            response_data
        )

        provider = OpenRouterProvider(
            api_key="test_key",
            http_client=mock_http_client
        )

        result = provider.generate("Test prompt")

        assert result["category"] == "promocion"


class TestAIProviderManager:
    """Pruebas para AIProviderManager"""

    def test_init_empty(self):
        """Inicializa vacío"""
        manager = AIProviderManager()

        assert len(manager.providers) == 0

    def test_init_with_providers(self):
        """Inicializa con proveedores"""
        providers = [MockAIProvider("P1"), MockAIProvider("P2")]
        manager = AIProviderManager(providers=providers)

        assert len(manager.providers) == 2

    def test_add_provider(self):
        """Agrega proveedor"""
        manager = AIProviderManager()
        provider = MockAIProvider("Test")

        manager.add_provider(provider)

        assert len(manager.providers) == 1

    def test_get_name(self):
        """Retorna nombre con proveedores"""
        manager = AIProviderManager([
            MockAIProvider("P1"),
            MockAIProvider("P2")
        ])

        name = manager.get_name()

        assert "AIProviderManager" in name
        assert "P1" in name
        assert "P2" in name

    def test_generate_uses_first_provider(self):
        """Usa el primer proveedor"""
        p1 = MockAIProvider("P1")
        p1.set_default_response({"source": "p1"})

        p2 = MockAIProvider("P2")
        p2.set_default_response({"source": "p2"})

        manager = AIProviderManager([p1, p2])

        result = manager.generate("Test")

        assert result["source"] == "p1"

    def test_rotation_round_robin(self):
        """Rotación round-robin"""
        p1 = MockAIProvider("P1")
        p1.set_default_response({"source": "p1"})

        p2 = MockAIProvider("P2")
        p2.set_default_response({"source": "p2"})

        manager = AIProviderManager([p1, p2])

        result1 = manager.generate("Test 1")
        result2 = manager.generate("Test 2")
        result3 = manager.generate("Test 3")

        assert result1["source"] == "p1"
        assert result2["source"] == "p2"
        assert result3["source"] == "p1"  # Vuelve al primero

    def test_failover_on_error(self):
        """Failover cuando un proveedor falla"""
        p1 = MockAIProvider("P1")
        p1.set_failure(True, "P1 failed")

        p2 = MockAIProvider("P2")
        p2.set_default_response({"source": "p2"})

        manager = AIProviderManager([p1, p2])

        result = manager.generate("Test")

        # Debería usar P2 después de que P1 falle
        assert result["source"] == "p2"

    def test_all_providers_fail(self):
        """Error cuando todos los proveedores fallan"""
        p1 = MockAIProvider("P1")
        p1.set_failure(True, "P1 failed")

        p2 = MockAIProvider("P2")
        p2.set_failure(True, "P2 failed")

        manager = AIProviderManager([p1, p2])

        with pytest.raises(Exception) as exc_info:
            manager.generate("Test")

        assert "Todos los proveedores fallaron" in str(exc_info.value)

    def test_generate_without_providers(self):
        """Error sin proveedores configurados"""
        manager = AIProviderManager()

        with pytest.raises(Exception) as exc_info:
            manager.generate("Test")

        assert "No hay proveedores configurados" in str(exc_info.value)

    def test_reset_rotation(self):
        """Reinicia rotación"""
        p1 = MockAIProvider("P1")
        p1.set_default_response({"source": "p1"})

        p2 = MockAIProvider("P2")
        p2.set_default_response({"source": "p2"})

        manager = AIProviderManager([p1, p2])

        manager.generate("Test 1")  # Usa P1, apunta a P2
        manager.reset_rotation()
        result = manager.generate("Test 2")  # Debería usar P1 de nuevo

        assert result["source"] == "p1"


class TestMockAIProvider:
    """Pruebas para MockAIProvider"""

    def test_default_response(self):
        """Retorna respuesta por defecto"""
        provider = MockAIProvider()

        result = provider.generate("Test")

        assert "category" in result
        assert "priority" in result

    def test_custom_response(self):
        """Retorna respuesta personalizada"""
        provider = MockAIProvider()
        provider.set_default_response({"custom": "value"})

        result = provider.generate("Test")

        assert result["custom"] == "value"

    def test_response_by_prompt_content(self):
        """Respuesta basada en contenido del prompt"""
        provider = MockAIProvider()
        provider.set_response("urgente", {"priority": "urgente"})
        provider.set_response("normal", {"priority": "normal"})

        result1 = provider.generate("Este es un mensaje urgente")
        result2 = provider.generate("Este es un mensaje normal")

        assert result1["priority"] == "urgente"
        assert result2["priority"] == "normal"

    def test_records_calls(self):
        """Registra llamadas"""
        provider = MockAIProvider()

        provider.generate("Prompt 1")
        provider.generate("Prompt 2")

        calls = provider.get_calls()
        assert len(calls) == 2
        assert "Prompt 1" in calls[0]
        assert "Prompt 2" in calls[1]

    def test_simulates_failure(self):
        """Simula fallo"""
        provider = MockAIProvider()
        provider.set_failure(True, "Simulated error")

        with pytest.raises(Exception) as exc_info:
            provider.generate("Test")

        assert "Simulated error" in str(exc_info.value)

    def test_clear_resets_state(self):
        """Clear reinicia estado"""
        provider = MockAIProvider()
        provider.set_failure(True)

        # Verificar que falla antes de clear
        with pytest.raises(Exception):
            provider.generate("Test")

        provider.clear()

        # Después de clear, no debería fallar
        result = provider.generate("Test")
        assert result is not None


class TestCreateProviderFromConfig:
    """Pruebas para create_provider_from_config"""

    def test_create_ollama_provider(self):
        """Crea proveedor Ollama"""
        config = AIProviderConfig(
            provider_type="ollama",
            ollama=OllamaConfig(host="http://localhost:11434", model="llama3")
        )

        manager = create_provider_from_config(config)

        assert len(manager.providers) == 1
        assert "Ollama" in manager.providers[0].get_name()

    def test_create_api_providers(self):
        """Crea proveedores API"""
        config = AIProviderConfig(
            provider_type="api",
            groq=GroqConfig(api_key="groq_key", model="mixtral"),
            cerebras=CerebrasConfig(api_key="cerebras_key", model="llama3")
        )

        manager = create_provider_from_config(config)

        assert len(manager.providers) == 2

    def test_create_auto_with_apis(self):
        """Modo auto usa APIs disponibles"""
        config = AIProviderConfig(
            provider_type="auto",
            groq=GroqConfig(api_key="groq_key"),
            ollama=OllamaConfig()
        )

        manager = create_provider_from_config(config)

        # Debería tener Groq (tiene API key)
        assert len(manager.providers) >= 1
        assert any("Groq" in p.get_name() for p in manager.providers)

    def test_create_auto_fallback_to_ollama(self):
        """Modo auto usa Ollama como fallback"""
        config = AIProviderConfig(
            provider_type="auto",
            groq=GroqConfig(api_key=""),  # Sin API key
            cerebras=CerebrasConfig(api_key=""),  # Sin API key
            ollama=OllamaConfig(host="http://localhost:11434", model="llama3")
        )

        manager = create_provider_from_config(config)

        assert len(manager.providers) == 1
        assert "Ollama" in manager.providers[0].get_name()

    def test_api_mode_without_keys_raises_error(self):
        """Modo API sin keys lanza error"""
        config = AIProviderConfig(
            provider_type="api",
            groq=GroqConfig(api_key=""),
            cerebras=CerebrasConfig(api_key="")
        )

        with pytest.raises(Exception) as exc_info:
            create_provider_from_config(config)

        assert "no hay API keys" in str(exc_info.value)

    def test_invalid_provider_type_raises_error(self):
        """Tipo de proveedor inválido lanza error"""
        config = AIProviderConfig(provider_type="invalid")

        with pytest.raises(Exception) as exc_info:
            create_provider_from_config(config)

        assert "AI_PROVIDER inválido" in str(exc_info.value)
