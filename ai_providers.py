"""
Proveedores de IA - Soporte para Ollama local y APIs gratuitas
Implementa rotación entre servicios para aprovechar capas gratuitas
"""

import json
import re
from typing import Dict, List, Optional

from interfaces import AIProvider
from config import (
    AIProviderConfig, OllamaConfig, GroqConfig,
    CerebrasConfig, GeminiConfig, OpenRouterConfig
)
from http_client import RequestsHttpClient


class OllamaProvider(AIProvider):
    """Proveedor para Ollama local"""

    def __init__(self, config: OllamaConfig = None, http_client=None,
                 host: str = None, model: str = None):
        """
        Args:
            config: Configuración de Ollama
            http_client: Cliente HTTP inyectable
            host: Host de Ollama (legacy, para compatibilidad)
            model: Modelo a usar (legacy, para compatibilidad)
        """
        if config:
            self.host = config.host
            self.model = config.model
        else:
            self.host = host or "http://localhost:11434"
            self.model = model or "llama3.2"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Ollama ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Ollama local"""
        try:
            response = self.http_client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                return self._parse_response(response_text)
            else:
                raise Exception(f"Ollama error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Ollama: {e}")

    def _parse_response(self, response_text: str) -> Dict:
        """Parsea y limpia la respuesta JSON"""
        response_text = response_text.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return json.loads(response_text)


class GroqProvider(AIProvider):
    """Proveedor para Groq API - Hasta 60 llamadas/minuto gratis"""

    def __init__(self, config: GroqConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "mixtral-8x7b-32768"
            self.base_url = "https://api.groq.com/openai/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Groq ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Groq API"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                raise Exception(f"Groq error: {response.status_code} - {response.text}")

        except Exception as e:
            raise Exception(f"Error en Groq: {e}")


class CerebrasProvider(AIProvider):
    """Proveedor para Cerebras API - Hasta 30 llamadas/minuto gratis"""

    def __init__(self, config: CerebrasConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "llama3.1-8b"
            self.base_url = "https://api.cerebras.ai/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Cerebras ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Cerebras API"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                raise Exception(f"Cerebras error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Cerebras: {e}")


class GeminiProvider(AIProvider):
    """Proveedor para Google Gemini API - Hasta 60 llamadas/minuto gratis"""

    def __init__(self, config: GeminiConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "gemini-1.5-flash"
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Gemini ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Gemini API"""
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            response = self.http_client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(content)
            else:
                raise Exception(f"Gemini error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Gemini: {e}")


class OpenRouterProvider(AIProvider):
    """Proveedor para OpenRouter - Múltiples modelos con capa gratuita"""

    def __init__(self, config: OpenRouterConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "meta-llama/llama-3.2-3b-instruct:free"
            self.base_url = "https://openrouter.ai/api/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"OpenRouter ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando OpenRouter API"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/email-classifier",
                    "X-Title": "Email Classifier"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                raise Exception(f"OpenRouter error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en OpenRouter: {e}")


class AIProviderManager(AIProvider):
    """
    Gestor de proveedores de IA con rotación automática (Round Robin)
    Permite usar múltiples servicios gratuitos alternándolos
    """

    def __init__(self, providers: List[AIProvider] = None):
        self._providers: List[AIProvider] = providers or []
        self._current_index = 0

    @property
    def providers(self) -> List[AIProvider]:
        return self._providers

    def add_provider(self, provider: AIProvider):
        """Agrega un proveedor a la lista"""
        self._providers.append(provider)
        print(f"Proveedor agregado: {provider.get_name()}")

    def get_name(self) -> str:
        """Retorna el nombre del gestor"""
        provider_names = [p.get_name() for p in self._providers]
        return f"AIProviderManager ({', '.join(provider_names)})"

    def get_next_provider(self) -> AIProvider:
        """
        Obtiene el siguiente proveedor en rotación (Round Robin)

        Returns:
            El siguiente proveedor disponible
        """
        if not self._providers:
            raise Exception("No hay proveedores configurados")

        provider = self._providers[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._providers)

        return provider

    def reset_rotation(self):
        """Reinicia la rotación al primer proveedor"""
        self._current_index = 0

    def generate(self, prompt: str) -> Dict:
        """
        Genera una respuesta usando el siguiente proveedor en rotación
        Si falla, intenta con el siguiente proveedor

        Args:
            prompt: El prompt a enviar

        Returns:
            Dict con la respuesta del modelo
        """
        if not self._providers:
            raise Exception("No hay proveedores configurados")

        attempts = len(self._providers)
        last_error = None

        for _ in range(attempts):
            provider = self.get_next_provider()

            try:
                print(f"Usando: {provider.get_name()}")
                return provider.generate(prompt)
            except Exception as e:
                print(f"Error con {provider.get_name()}: {e}")
                last_error = e
                continue

        raise Exception(f"Todos los proveedores fallaron. Último error: {last_error}")


class MockAIProvider(AIProvider):
    """
    Proveedor de IA mock para testing.
    Permite configurar respuestas predefinidas.
    """

    def __init__(self, name: str = "MockProvider"):
        self._name = name
        self.responses: Dict[str, Dict] = {}
        self.default_response: Dict = {
            "category": "notificacion",
            "priority": "normal",
            "summary": "Mock response",
            "action_required": False
        }
        self.calls: List[str] = []
        self.should_fail = False
        self.failure_message = "Mock failure"

    def get_name(self) -> str:
        return self._name

    def set_response(self, prompt_contains: str, response: Dict):
        """Configura respuesta para prompts que contengan cierto texto"""
        self.responses[prompt_contains] = response

    def set_default_response(self, response: Dict):
        """Configura la respuesta por defecto"""
        self.default_response = response

    def set_failure(self, should_fail: bool = True, message: str = "Mock failure"):
        """Configura para simular fallo"""
        self.should_fail = should_fail
        self.failure_message = message

    def generate(self, prompt: str) -> Dict:
        """Retorna la respuesta configurada"""
        self.calls.append(prompt)

        if self.should_fail:
            raise Exception(self.failure_message)

        for key, response in self.responses.items():
            if key in prompt:
                return response

        return self.default_response

    def get_calls(self) -> List[str]:
        """Retorna los prompts recibidos"""
        return self.calls

    def clear(self):
        """Limpia configuraciones y llamadas"""
        self.responses.clear()
        self.calls.clear()
        self.should_fail = False


def create_provider_from_config(config: AIProviderConfig = None) -> AIProviderManager:
    """
    Crea un gestor de proveedores basado en la configuración.

    Args:
        config: Configuración de proveedores. Si es None, carga desde .env

    Returns:
        AIProviderManager configurado con los proveedores disponibles
    """
    if config is None:
        from config import load_config_from_env
        app_config = load_config_from_env()
        config = app_config.ai_provider

    manager = AIProviderManager()
    provider_type = config.provider_type.lower()

    print(f"\nConfigurando proveedores de IA (modo: {provider_type})")
    print("=" * 60)

    if provider_type == 'ollama':
        manager.add_provider(OllamaProvider(config=config.ollama))

    elif provider_type == 'api':
        added = False

        if config.groq.api_key:
            manager.add_provider(GroqProvider(config=config.groq))
            added = True

        if config.cerebras.api_key:
            manager.add_provider(CerebrasProvider(config=config.cerebras))
            added = True

        if config.gemini.api_key:
            manager.add_provider(GeminiProvider(config=config.gemini))
            added = True

        if config.openrouter.api_key:
            manager.add_provider(OpenRouterProvider(config=config.openrouter))
            added = True

        if not added:
            raise Exception("Modo 'api' seleccionado pero no hay API keys configuradas")

    elif provider_type == 'auto':
        added = False

        if config.groq.api_key:
            manager.add_provider(GroqProvider(config=config.groq))
            added = True

        if config.cerebras.api_key:
            manager.add_provider(CerebrasProvider(config=config.cerebras))
            added = True

        if config.gemini.api_key:
            manager.add_provider(GeminiProvider(config=config.gemini))
            added = True

        if config.openrouter.api_key:
            manager.add_provider(OpenRouterProvider(config=config.openrouter))
            added = True

        if not added:
            print("No hay API keys, usando Ollama local como fallback")
            manager.add_provider(OllamaProvider(config=config.ollama))

    else:
        raise Exception(f"AI_PROVIDER inválido: {provider_type}. Usa 'ollama', 'api' o 'auto'")

    print("=" * 60)
    print(f"Total de proveedores configurados: {len(manager.providers)}\n")

    return manager
