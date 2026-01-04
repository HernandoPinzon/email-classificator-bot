# 🚀 Guía Rápida - Cambiar entre Ollama y APIs

## ¿Qué cambió?

Ahora puedes elegir entre usar **Ollama local** (100% privado) o **APIs gratuitas en la nube** (Groq, Cerebras, Gemini, OpenRouter).

## 📝 Cambio Rápido en 3 Pasos

### 1️⃣ Edita el archivo `.env`

```bash
# Abre el archivo .env
notepad .env  # En Windows
nano .env     # En Linux/Mac
```

### 2️⃣ Cambia `AI_PROVIDER`

**Opción A - Solo Ollama (100% privado):**
```env
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Opción B - Solo APIs gratuitas:**
```env
AI_PROVIDER=api

# Agrega al menos una API key
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
# O cualquiera de estas:
# CEREBRAS_API_KEY=csk-xxxxxxxxxxxxx
# GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxx
# OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxx
```

**Opción C - Automático (APIs primero, Ollama si no hay):**
```env
AI_PROVIDER=auto

GROQ_API_KEY=gsk_xxxxxxxxxxxxx  # Opcional
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3️⃣ Prueba la configuración

```bash
python test_providers.py
```

¡Eso es todo! El sistema usará el proveedor que configuraste.

---

## 🔑 Obtener API Keys Gratis (sin tarjeta de crédito)

### Groq (60 llamadas/min - Recomendado)
1. Ve a: https://console.groq.com/keys
2. Inicia sesión con Google/GitHub
3. Click en "Create API Key"
4. Copia y pega en `.env`

### Cerebras (30 llamadas/min)
1. Ve a: https://cloud.cerebras.ai/
2. Sign up / Login
3. API Keys → Create
4. Copia y pega en `.env`

### Google Gemini (60 llamadas/min)
1. Ve a: https://aistudio.google.com/app/apikey
2. Get API Key
3. Copia y pega en `.env`

### OpenRouter (varios modelos)
1. Ve a: https://openrouter.ai/keys
2. Sign up / Login
3. Create Key
4. Copia y pega en `.env`

---

## 💰 Ventajas de cada opción

### Ollama Local
✅ **100% privado** - Los datos no salen de tu computadora
✅ **Sin límites** - Usa cuanto quieras
✅ **Sin internet** - Funciona offline
❌ Requiere instalación y recursos (2-5GB)
❌ Más lento en computadoras viejas

### APIs Gratuitas
✅ **Más rápido** - Servidores potentes
✅ **Sin instalación** - Solo necesitas internet
✅ **Rotación automática** - Maximiza llamadas gratis
❌ Requiere internet
❌ Los correos se envían a terceros (solo asunto + 1000 chars)
❌ Límites de rate (pero puedes usar múltiples APIs)

### Modo Automático
✅ **Lo mejor de ambos** - APIs cuando hay internet, Ollama si no
✅ **Fallback automático** - Si las APIs fallan, usa Ollama
✅ **Máxima disponibilidad**

---

## 🎯 ¿Cuál elegir?

- **¿Te importa mucho la privacidad?** → `AI_PROVIDER=ollama`
- **¿Quieres velocidad y facilidad?** → `AI_PROVIDER=api`
- **¿Quieres lo mejor de ambos?** → `AI_PROVIDER=auto`

---

## 🔄 Rotación Automática (Solo en modo API)

Si configuras **múltiples API keys**, el sistema rotará entre ellas automáticamente:

```env
AI_PROVIDER=api

GROQ_API_KEY=gsk_xxxxx        # +60 llamadas/min
CEREBRAS_API_KEY=csk-xxxxx    # +30 llamadas/min
GEMINI_API_KEY=AIzaSyxxxxx    # +60 llamadas/min
OPENROUTER_API_KEY=sk-or-xxx  # +10 llamadas/min
```

**Resultado:** ~160 llamadas/minuto GRATIS 🚀

El sistema irá rotando: Groq → Cerebras → Gemini → OpenRouter → Groq → ...

---

## 🧪 Probar configuración

```bash
# Prueba rápida de proveedores
python test_providers.py

# Prueba completa del sistema
python email_processor.py
```

---

## 🐛 Problemas comunes

### "No hay proveedores configurados"
→ Verifica que `AI_PROVIDER` esté en `.env`
→ Si usas `api`, agrega al menos una API key

### "Ollama connection refused"
→ Inicia Ollama: `ollama serve`
→ Verifica que esté corriendo: `ollama list`

### "API error: 401 Unauthorized"
→ Verifica que la API key sea correcta
→ Asegúrate de no tener espacios

### "Todos los proveedores fallaron"
→ Verifica tu conexión a internet (si usas APIs)
→ Verifica que Ollama esté corriendo (si usas Ollama)
→ Prueba con `python test_providers.py`

---

## 📚 Más información

Ver el [README.md](README.md) completo para:
- Instalación detallada
- Configuración de Gmail
- Configuración de Telegram
- Personalización avanzada
