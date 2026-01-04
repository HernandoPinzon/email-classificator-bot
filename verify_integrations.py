#!/usr/bin/env python3
"""
Script de verificación de integraciones.

Prueba todas las conexiones reales:
- Telegram Bot
- Ollama (IA local)
- APIs de IA (Groq, Cerebras, Gemini, OpenRouter)
- Gmail API

Uso:
    python verify_integrations.py           # Prueba todo
    python verify_integrations.py telegram  # Solo Telegram
    python verify_integrations.py ai        # Solo proveedores de IA
    python verify_integrations.py gmail     # Solo Gmail
"""

import os
import sys
import json
from pathlib import Path

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def verify_telegram() -> bool:
    """Verifica la conexión con Telegram."""
    print_header("TELEGRAM")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

    # Verificar configuración
    if not bot_token or bot_token == 'tu_token_aquí':
        print_error("TELEGRAM_BOT_TOKEN no configurado en .env")
        return False

    if not chat_id or chat_id == 'tu_chat_id_aquí':
        print_error("TELEGRAM_CHAT_ID no configurado en .env")
        return False

    print_info(f"Bot Token: {bot_token[:20]}...")
    print_info(f"Chat ID: {chat_id}")

    # Probar envío de mensaje
    try:
        import requests

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "🧪 Test de integración - Email Classificator Bot\n\n✅ Telegram está funcionando correctamente."
        }

        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if result.get('ok'):
            print_success("Mensaje de prueba enviado correctamente")
            print_success("Revisa tu Telegram para confirmar")
            return True
        else:
            print_error(f"Error de Telegram: {result.get('description', 'Unknown error')}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("No se pudo conectar a Telegram. Verifica tu conexión a internet.")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_ollama() -> bool:
    """Verifica la conexión con Ollama local."""
    print_header("OLLAMA (IA LOCAL)")

    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')

    print_info(f"Host: {ollama_host}")
    print_info(f"Modelo: {ollama_model}")

    try:
        import requests

        # Verificar que Ollama está corriendo
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)

        if response.status_code != 200:
            print_error("Ollama no está respondiendo")
            print_warning("Ejecuta: ollama serve")
            return False

        models = response.json().get('models', [])
        model_names = [m.get('name', '').split(':')[0] for m in models]

        print_success(f"Ollama está corriendo")
        print_info(f"Modelos disponibles: {', '.join(model_names) if model_names else 'ninguno'}")

        # Verificar que el modelo está instalado
        if ollama_model.split(':')[0] not in [m.split(':')[0] for m in model_names]:
            print_warning(f"Modelo '{ollama_model}' no instalado")
            print_info(f"Ejecuta: ollama pull {ollama_model}")
            return False

        # Probar generación
        print_info("Probando generación de texto...")

        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": ollama_model,
                "prompt": "Responde solo con 'OK' si funciona:",
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json().get('response', '')
            print_success(f"Generación exitosa: {result[:50]}...")
            return True
        else:
            print_error(f"Error en generación: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("No se pudo conectar a Ollama")
        print_warning("Asegúrate de que Ollama esté corriendo: ollama serve")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_groq() -> bool:
    """Verifica la API de Groq."""
    api_key = os.getenv('GROQ_API_KEY', '')
    model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')

    if not api_key:
        print_warning("GROQ_API_KEY no configurada (opcional)")
        return None

    print_info(f"Modelo: {model}")

    try:
        import requests

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Responde solo: OK"}],
                "max_tokens": 10
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print_success(f"Groq funcionando: {text[:30]}")
            return True
        elif response.status_code == 401:
            print_error("API key inválida")
            return False
        elif response.status_code == 429:
            print_warning("Rate limit excedido (prueba más tarde)")
            return True  # La key es válida, solo rate limited
        else:
            print_error(f"Error: {response.status_code} - {response.text[:100]}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_cerebras() -> bool:
    """Verifica la API de Cerebras."""
    api_key = os.getenv('CEREBRAS_API_KEY', '')
    model = os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')

    if not api_key:
        print_warning("CEREBRAS_API_KEY no configurada (opcional)")
        return None

    print_info(f"Modelo: {model}")

    try:
        import requests

        response = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Responde solo: OK"}],
                "max_tokens": 10
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print_success(f"Cerebras funcionando: {text[:30]}")
            return True
        elif response.status_code == 401:
            print_error("API key inválida")
            return False
        elif response.status_code == 429:
            print_warning("Rate limit excedido (prueba más tarde)")
            return True
        else:
            print_error(f"Error: {response.status_code} - {response.text[:100]}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_gemini() -> bool:
    """Verifica la API de Google Gemini."""
    api_key = os.getenv('GEMINI_API_KEY', '')
    model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

    if not api_key:
        print_warning("GEMINI_API_KEY no configurada (opcional)")
        return None

    print_info(f"Modelo: {model}")

    try:
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": "Responde solo: OK"}]}]
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            print_success(f"Gemini funcionando: {text[:30]}")
            return True
        elif response.status_code == 400:
            print_error("API key inválida o modelo incorrecto")
            return False
        elif response.status_code == 429:
            print_warning("Rate limit excedido (prueba más tarde)")
            return True
        else:
            print_error(f"Error: {response.status_code} - {response.text[:100]}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_openrouter() -> bool:
    """Verifica la API de OpenRouter."""
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')

    if not api_key:
        print_warning("OPENROUTER_API_KEY no configurada (opcional)")
        return None

    print_info(f"Modelo: {model}")

    try:
        import requests

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Responde solo: OK"}],
                "max_tokens": 10
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print_success(f"OpenRouter funcionando: {text[:30]}")
            return True
        elif response.status_code == 401:
            print_error("API key inválida")
            return False
        elif response.status_code == 429:
            print_warning("Rate limit excedido (prueba más tarde)")
            return True
        else:
            print_error(f"Error: {response.status_code} - {response.text[:100]}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def verify_ai_providers() -> dict:
    """Verifica todos los proveedores de IA."""
    print_header("PROVEEDORES DE IA")

    ai_provider = os.getenv('AI_PROVIDER', 'ollama')
    print_info(f"Modo configurado: {ai_provider}")

    results = {}

    # Ollama
    if ai_provider in ['ollama', 'auto']:
        results['ollama'] = verify_ollama()

    # APIs
    print_header("APIs DE IA (NUBE)")

    print("\n--- Groq ---")
    results['groq'] = verify_groq()

    print("\n--- Cerebras ---")
    results['cerebras'] = verify_cerebras()

    print("\n--- Google Gemini ---")
    results['gemini'] = verify_gemini()

    print("\n--- OpenRouter ---")
    results['openrouter'] = verify_openrouter()

    return results


def verify_gmail() -> bool:
    """Verifica la conexión con Gmail."""
    print_header("GMAIL")

    credentials_path = Path("config/credentials.json")
    token_path = Path("config/token.json")

    # Verificar credentials.json
    if not credentials_path.exists():
        print_error("No se encontró config/credentials.json")
        print_info("Descarga las credenciales OAuth de Google Cloud Console")
        print_info("Guárdalas en: config/credentials.json")
        return False

    print_success("credentials.json encontrado")

    # Verificar token.json
    if not token_path.exists():
        print_warning("No se encontró config/token.json")
        print_info("Se creará automáticamente al ejecutar main.py o email_processor.py")
        print_info("Se abrirá el navegador para autenticar con Gmail")
        return None

    print_success("token.json encontrado")

    # Intentar conectar
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(token_path))

        if creds.expired and creds.refresh_token:
            print_info("Token expirado, renovando...")
            creds.refresh(Request())
            # Guardar token renovado
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
            print_success("Token renovado")

        # Probar conexión
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()

        email = profile.get('emailAddress', 'desconocido')
        total_messages = profile.get('messagesTotal', 0)

        print_success(f"Conectado a: {email}")
        print_info(f"Total de mensajes: {total_messages:,}")

        # Contar no leídos
        results = service.users().messages().list(
            userId='me',
            labelIds=['UNREAD', 'INBOX'],
            maxResults=1
        ).execute()

        unread_count = results.get('resultSizeEstimate', 0)
        print_info(f"Correos no leídos: {unread_count}")

        return True

    except Exception as e:
        print_error(f"Error al conectar: {e}")
        print_info("Intenta eliminar config/token.json y volver a autenticar")
        return False


def verify_all():
    """Ejecuta todas las verificaciones."""
    print(f"\n{Colors.BOLD}🧪 VERIFICACIÓN DE INTEGRACIONES{Colors.END}")
    print(f"{Colors.BOLD}Email Classificator Bot{Colors.END}\n")

    results = {
        'telegram': None,
        'ai': {},
        'gmail': None
    }

    # Telegram
    results['telegram'] = verify_telegram()

    # IA
    results['ai'] = verify_ai_providers()

    # Gmail
    results['gmail'] = verify_gmail()

    # Resumen
    print_header("RESUMEN")

    # Telegram
    if results['telegram']:
        print_success("Telegram: Funcionando")
    elif results['telegram'] is None:
        print_warning("Telegram: No configurado")
    else:
        print_error("Telegram: Error")

    # IA
    ai_working = [k for k, v in results['ai'].items() if v is True]
    ai_failed = [k for k, v in results['ai'].items() if v is False]

    if ai_working:
        print_success(f"IA funcionando: {', '.join(ai_working)}")
    if ai_failed:
        print_error(f"IA con error: {', '.join(ai_failed)}")
    if not ai_working and not ai_failed:
        print_warning("IA: Ningún proveedor configurado")

    # Gmail
    if results['gmail']:
        print_success("Gmail: Conectado")
    elif results['gmail'] is None:
        print_warning("Gmail: Requiere autenticación inicial")
    else:
        print_error("Gmail: Error")

    # Estado final
    all_ok = (
        results['telegram'] in [True, None] and
        (ai_working or results['ai'].get('ollama') is True) and
        results['gmail'] in [True, None]
    )

    if all_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Sistema listo para usar{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Revisa los errores arriba{Colors.END}")

    return results


def main():
    args = sys.argv[1:]

    if not args:
        verify_all()
    elif 'telegram' in args:
        verify_telegram()
    elif 'ai' in args:
        verify_ai_providers()
    elif 'gmail' in args:
        verify_gmail()
    elif 'ollama' in args:
        verify_ollama()
    elif 'help' in args or '-h' in args or '--help' in args:
        print(__doc__)
    else:
        print(f"Opción desconocida: {args}")
        print("Opciones: telegram, ai, gmail, ollama (o sin argumentos para todo)")


if __name__ == "__main__":
    main()
