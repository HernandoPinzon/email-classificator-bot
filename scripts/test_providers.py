"""
Script de prueba para verificar la configuración de proveedores de IA
Prueba que los proveedores estén configurados correctamente y funcionando
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_providers():
    """Prueba la configuración de proveedores"""

    print("="*70)
    print("🧪 PRUEBA DE PROVEEDORES DE IA")
    print("="*70)
    print()

    # Verificar configuración
    ai_provider = os.getenv('AI_PROVIDER', 'ollama')
    print(f"📋 Modo configurado: {ai_provider}")
    print()

    # Importar y crear gestor
    try:
        from ai_providers import create_provider_from_config

        print("🔧 Creando gestor de proveedores...")
        print()
        manager = create_provider_from_config()
        print()

        # Prompt de prueba simple
        test_prompt = """Eres un asistente que clasifica correos bancarios en español.

Analiza este correo y responde SOLO con un JSON:

Remitente: notificaciones@banco.com
Asunto: Pago de tarjeta pendiente
Cuerpo: Tu pago mínimo de $1,500.00 vence mañana.

Responde EXACTAMENTE en este formato JSON:
{
  "category": "pago",
  "priority": "urgente",
  "summary": "Pago de $1,500.00 vence mañana",
  "action_required": true
}"""

        print("🧪 Realizando prueba de clasificación...")
        print()

        # Hacer una prueba
        result = manager.generate(test_prompt)

        print("="*70)
        print("✅ PRUEBA EXITOSA")
        print("="*70)
        print()
        print("📄 Resultado de la clasificación:")
        print(f"   Categoría: {result.get('category')}")
        print(f"   Prioridad: {result.get('priority')}")
        print(f"   Resumen: {result.get('summary')}")
        print(f"   Acción requerida: {result.get('action_required')}")
        print()

        # Si hay múltiples proveedores, probar rotación
        if len(manager.providers) > 1:
            print("🔄 Probando rotación entre proveedores...")
            print()
            for i in range(min(3, len(manager.providers))):
                print(f"--- Prueba {i+1} ---")
                manager.generate(test_prompt)
                print()

        print("="*70)
        print("🎉 Configuración correcta. El sistema está listo para usar.")
        print("="*70)
        print()
        print("💡 Siguiente paso:")
        print("   Ejecuta: python email_processor.py")
        print()

        return True

    except Exception as e:
        print("="*70)
        print("❌ ERROR EN LA CONFIGURACIÓN")
        print("="*70)
        print()
        print(f"Error: {e}")
        print()
        print("🔍 Posibles soluciones:")
        print()

        if ai_provider == 'ollama':
            print("1. Verifica que Ollama esté corriendo:")
            print("   ollama serve")
            print()
            print("2. Verifica que tengas un modelo descargado:")
            print("   ollama pull llama3.2")
            print()
            print("3. Verifica OLLAMA_HOST en .env:")
            print(f"   Actual: {os.getenv('OLLAMA_HOST', 'No configurado')}")
            print()

        elif ai_provider == 'api':
            print("1. Verifica que tengas al menos una API key en .env:")
            print(f"   GROQ_API_KEY: {'✅ Configurada' if os.getenv('GROQ_API_KEY') else '❌ No configurada'}")
            print(f"   CEREBRAS_API_KEY: {'✅ Configurada' if os.getenv('CEREBRAS_API_KEY') else '❌ No configurada'}")
            print(f"   GEMINI_API_KEY: {'✅ Configurada' if os.getenv('GEMINI_API_KEY') else '❌ No configurada'}")
            print(f"   OPENROUTER_API_KEY: {'✅ Configurada' if os.getenv('OPENROUTER_API_KEY') else '❌ No configurada'}")
            print()
            print("2. Verifica que las API keys sean válidas")
            print()
            print("3. Verifica tu conexión a internet")
            print()

        elif ai_provider == 'auto':
            print("1. El modo 'auto' intenta usar APIs primero, luego Ollama")
            print()
            print("2. APIs disponibles:")
            print(f"   GROQ_API_KEY: {'✅ Configurada' if os.getenv('GROQ_API_KEY') else '❌ No configurada'}")
            print(f"   CEREBRAS_API_KEY: {'✅ Configurada' if os.getenv('CEREBRAS_API_KEY') else '❌ No configurada'}")
            print(f"   GEMINI_API_KEY: {'✅ Configurada' if os.getenv('GEMINI_API_KEY') else '❌ No configurada'}")
            print(f"   OPENROUTER_API_KEY: {'✅ Configurada' if os.getenv('OPENROUTER_API_KEY') else '❌ No configurada'}")
            print()
            print("3. Si no hay APIs, verifica Ollama:")
            print("   ollama serve")
            print()

        print("4. Revisa el archivo .env y verifica la configuración")
        print()

        return False


if __name__ == "__main__":
    test_providers()
