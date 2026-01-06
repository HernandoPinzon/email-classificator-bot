"""
Gestor de proveedores de IA y clases base
"""

from typing import Dict, List

from ..core.interfaces import AIProvider
from ..config import AIProviderConfig


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
    from .ollama import OllamaProvider
    from .groq import GroqProvider
    from .cerebras import CerebrasProvider
    from .gemini import GeminiProvider
    from .openrouter import OpenRouterProvider

    if config is None:
        from ..config import load_config_from_env
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
