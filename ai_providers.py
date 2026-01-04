"""
Proveedores de IA - Soporte para Ollama local y APIs gratuitas
Implementa rotación entre servicios para aprovechar capas gratuitas
"""

import os
import json
import requests
from typing import Dict, Optional, AsyncIterator
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Interfaz base para todos los proveedores de IA"""

    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre del proveedor"""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> Dict:
        """
        Genera una respuesta del modelo

        Args:
            prompt: El prompt a enviar al modelo

        Returns:
            Dict con la respuesta del modelo
        """
        pass


class OllamaProvider(AIProvider):
    """Proveedor para Ollama local"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host
        self.model = model

    def get_name(self) -> str:
        return f"Ollama ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Ollama local"""
        try:
            response = requests.post(
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
        import re
        response_text = response_text.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return json.loads(response_text)


class GroqProvider(AIProvider):
    """Proveedor para Groq API - Hasta 60 llamadas/minuto gratis"""

    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"

    def get_name(self) -> str:
        return f"Groq ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Groq API"""
        try:
            response = requests.post(
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

    def __init__(self, api_key: str, model: str = "llama3.1-8b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.cerebras.ai/v1"

    def get_name(self) -> str:
        return f"Cerebras ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Cerebras API"""
        try:
            response = requests.post(
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

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def get_name(self) -> str:
        return f"Gemini ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Gemini API"""
        try:
            # Gemini usa un formato diferente
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            response = requests.post(
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

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.2-3b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"

    def get_name(self) -> str:
        return f"OpenRouter ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando OpenRouter API"""
        try:
            response = requests.post(
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


class AIProviderManager:
    """
    Gestor de proveedores de IA con rotación automática (Round Robin)
    Permite usar múltiples servicios gratuitos alternándolos
    """

    def __init__(self):
        self.providers = []
        self.current_index = 0

    def add_provider(self, provider: AIProvider):
        """Agrega un proveedor a la lista"""
        self.providers.append(provider)
        print(f"✅ Proveedor agregado: {provider.get_name()}")

    def get_next_provider(self) -> AIProvider:
        """
        Obtiene el siguiente proveedor en rotación (Round Robin)

        Returns:
            El siguiente proveedor disponible
        """
        if not self.providers:
            raise Exception("No hay proveedores configurados")

        provider = self.providers[self.current_index]

        # Rotar al siguiente proveedor para la próxima llamada
        self.current_index = (self.current_index + 1) % len(self.providers)

        return provider

    def generate(self, prompt: str) -> Dict:
        """
        Genera una respuesta usando el siguiente proveedor en rotación
        Si falla, intenta con el siguiente proveedor

        Args:
            prompt: El prompt a enviar

        Returns:
            Dict con la respuesta del modelo
        """
        if not self.providers:
            raise Exception("No hay proveedores configurados")

        # Intentar con todos los proveedores si es necesario
        attempts = len(self.providers)
        last_error = None

        for _ in range(attempts):
            provider = self.get_next_provider()

            try:
                print(f"🤖 Usando: {provider.get_name()}")
                return provider.generate(prompt)
            except Exception as e:
                print(f"⚠️ Error con {provider.get_name()}: {e}")
                last_error = e
                continue

        # Si todos fallaron
        raise Exception(f"Todos los proveedores fallaron. Último error: {last_error}")


def create_provider_from_config() -> AIProviderManager:
    """
    Crea un gestor de proveedores basado en las variables de entorno

    Variables de entorno soportadas:
        AI_PROVIDER: Tipo de proveedor ('ollama', 'api', 'auto')

        Para Ollama:
            OLLAMA_HOST: Host de Ollama (default: http://localhost:11434)
            OLLAMA_MODEL: Modelo a usar (default: llama3.2)

        Para APIs (se agregan todos los que tengan API key):
            GROQ_API_KEY: API key de Groq
            GROQ_MODEL: Modelo de Groq (default: mixtral-8x7b-32768)

            CEREBRAS_API_KEY: API key de Cerebras
            CEREBRAS_MODEL: Modelo de Cerebras (default: llama3.1-8b)

            GEMINI_API_KEY: API key de Google Gemini
            GEMINI_MODEL: Modelo de Gemini (default: gemini-1.5-flash)

            OPENROUTER_API_KEY: API key de OpenRouter
            OPENROUTER_MODEL: Modelo de OpenRouter (default: meta-llama/llama-3.2-3b-instruct:free)

    Returns:
        AIProviderManager configurado con los proveedores disponibles
    """
    from dotenv import load_dotenv
    load_dotenv()

    manager = AIProviderManager()
    provider_type = os.getenv('AI_PROVIDER', 'ollama').lower()

    print(f"\n🔧 Configurando proveedores de IA (modo: {provider_type})")
    print("="*60)

    if provider_type == 'ollama':
        # Solo usar Ollama local
        host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        manager.add_provider(OllamaProvider(host, model))

    elif provider_type == 'api':
        # Solo usar APIs externas
        added = False

        # Groq
        if os.getenv('GROQ_API_KEY'):
            model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
            manager.add_provider(GroqProvider(os.getenv('GROQ_API_KEY'), model))
            added = True

        # Cerebras
        if os.getenv('CEREBRAS_API_KEY'):
            model = os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')
            manager.add_provider(CerebrasProvider(os.getenv('CEREBRAS_API_KEY'), model))
            added = True

        # Gemini
        if os.getenv('GEMINI_API_KEY'):
            model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
            manager.add_provider(GeminiProvider(os.getenv('GEMINI_API_KEY'), model))
            added = True

        # OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
            manager.add_provider(OpenRouterProvider(os.getenv('OPENROUTER_API_KEY'), model))
            added = True

        if not added:
            raise Exception("Modo 'api' seleccionado pero no hay API keys configuradas")

    elif provider_type == 'auto':
        # Usar todo lo disponible (APIs primero, luego Ollama como fallback)
        added = False

        # Intentar agregar APIs
        if os.getenv('GROQ_API_KEY'):
            model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
            manager.add_provider(GroqProvider(os.getenv('GROQ_API_KEY'), model))
            added = True

        if os.getenv('CEREBRAS_API_KEY'):
            model = os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')
            manager.add_provider(CerebrasProvider(os.getenv('CEREBRAS_API_KEY'), model))
            added = True

        if os.getenv('GEMINI_API_KEY'):
            model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
            manager.add_provider(GeminiProvider(os.getenv('GEMINI_API_KEY'), model))
            added = True

        if os.getenv('OPENROUTER_API_KEY'):
            model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
            manager.add_provider(OpenRouterProvider(os.getenv('OPENROUTER_API_KEY'), model))
            added = True

        # Si no hay APIs, usar Ollama
        if not added:
            print("ℹ️ No hay API keys, usando Ollama local como fallback")
            host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            model = os.getenv('OLLAMA_MODEL', 'llama3.2')
            manager.add_provider(OllamaProvider(host, model))

    else:
        raise Exception(f"AI_PROVIDER inválido: {provider_type}. Usa 'ollama', 'api' o 'auto'")

    print("="*60)
    print(f"✅ Total de proveedores configurados: {len(manager.providers)}\n")

    return manager


# Prueba de proveedores
if __name__ == "__main__":
    # Crear gestor desde configuración
    manager = create_provider_from_config()

    # Prompt de prueba
    test_prompt = """Eres un asistente que clasifica correos bancarios en español.

Analiza este correo y responde SOLO con un JSON:

Remitente: notificaciones@banco.com
Asunto: Recordatorio: Pago de tarjeta vence mañana
Cuerpo: Tu pago mínimo de $2,500.00 vence el 03/01/2026.

Responde EXACTAMENTE en este formato JSON:
{
  "category": "pago",
  "priority": "urgente",
  "summary": "Pago de $2,500.00 vence mañana",
  "action_required": true
}"""

    # Hacer 3 llamadas para ver la rotación
    print("\n🧪 Probando rotación de proveedores...\n")
    for i in range(3):
        print(f"\n--- Llamada {i+1} ---")
        try:
            result = manager.generate(test_prompt)
            print(f"✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ Error: {e}")
