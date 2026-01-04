# 📧 Clasificador Automático de Correos Bancarios con LLM

Sistema inteligente que clasifica automáticamente tus correos bancarios usando un LLM local (Ollama) y te notifica a Telegram sobre pagos importantes.

## 🎯 Características

- ✅ **Flexible** - Usa Ollama local O APIs gratuitas en la nube (Groq, Cerebras, Gemini, OpenRouter)
- ✅ **Rotación Automática** - Si usas múltiples APIs, rota entre ellas para maximizar llamadas gratuitas
- ✅ **100% Gratis** - Sin tarjeta de crédito, aprovecha las capas gratuitas de los servicios
- ✅ **Clasificación Inteligente** - Identifica pagos, transferencias, promociones, etc.
- ✅ **Sistema de Prioridades** - Urgente / Normal / Sin prioridad
- ✅ **Extracción de Montos** - Detecta automáticamente cantidades en los correos
- ✅ **Notificaciones Telegram** - Alertas instantáneas de correos importantes
- ✅ **Resumen Diario** - Recibe un resumen de todos tus correos del día
- ✅ **Base de Datos** - Guarda historial y evita procesar correos duplicados

## 📋 Requisitos Previos

1. **Python 3.8+** instalado
2. **Cuenta de Gmail**
3. **Opción A (100% local):** [Ollama](https://ollama.ai) instalado y corriendo
4. **Opción B (en la nube - gratis):** API keys de servicios gratuitos:
   - [Groq](https://console.groq.com/keys) - 60 llamadas/min gratis
   - [Cerebras](https://cloud.cerebras.ai/) - 30 llamadas/min gratis
   - [Google Gemini](https://aistudio.google.com/app/apikey) - 60 llamadas/min gratis
   - [OpenRouter](https://openrouter.ai/keys) - Varios modelos gratis
5. **Cuenta de Telegram** (opcional pero recomendado)

## 🚀 Instalación

### Paso 1: Clonar o descargar el proyecto

```bash
# Crear directorio del proyecto
mkdir clasificador-correos
cd clasificador-correos
```

### Paso 2: Instalar dependencias de Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install requests python-dotenv
```

### Paso 3: Configurar IA (Elige una opción)

#### Opción A: Ollama Local (100% Privado - Recomendado para privacidad)

```bash
# Verificar que Ollama está corriendo
ollama --version

# Descargar modelo recomendado (elige uno)
ollama pull llama3.2        # Ligero y rápido (2GB)
# O
ollama pull qwen2.5:7b      # Más preciso (4.7GB)

# Verificar que funciona
ollama run llama3.2 "Hola, eres un asistente de correos"
```

#### Opción B: APIs Gratuitas (Sin instalar nada - Recomendado para rapidez)

Obtén API keys gratuitas (sin tarjeta de crédito):

1. **Groq** (60 llamadas/min):
   - Ve a: https://console.groq.com/keys
   - Inicia sesión → Create API Key → Copia el token

2. **Cerebras** (30 llamadas/min):
   - Ve a: https://cloud.cerebras.ai/
   - Inicia sesión → API Keys → Create → Copia el token

3. **Google Gemini** (60 llamadas/min):
   - Ve a: https://aistudio.google.com/app/apikey
   - Get API Key → Copia el token

4. **OpenRouter** (varios modelos):
   - Ve a: https://openrouter.ai/keys
   - Create Key → Copia el token

**Tip:** Puedes usar múltiples APIs al mismo tiempo. El sistema rotará entre ellas automáticamente para aprovechar todas las capas gratuitas (¡hasta ~170 llamadas/minuto gratis!)

### Paso 4: Configurar Gmail API

#### 4.1 Crear proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto: **"Clasificador Correos"**
3. Habilita **Gmail API**:
   - Menú → APIs y Servicios → Biblioteca
   - Busca "Gmail API"
   - Click en "Habilitar"

#### 4.2 Configurar pantalla de consentimiento OAuth

1. APIs y Servicios → Pantalla de consentimiento de OAuth
2. Selecciona **Externo** → Crear
3. Completa:
   - Nombre de la app: **Clasificador Correos**
   - Correo de asistencia: tu correo
   - Correo del desarrollador: tu correo
4. Click en **Guardar y continuar**
5. En **Ámbitos**, agrega:
   - `https://www.googleapis.com/auth/gmail.modify`
6. En **Usuarios de prueba**, agrega tu correo de Gmail
7. Guardar y continuar

#### 4.3 Crear credenciales OAuth

1. APIs y Servicios → Credenciales
2. Crear credenciales → ID de cliente de OAuth
3. Tipo: **Aplicación de escritorio**
4. Nombre: **Clasificador Correos Desktop**
5. Crear
6. **Descargar JSON** → guardar como `credentials.json` en la carpeta `config/`

```bash
# Crear directorio de configuración
mkdir config
# Mover credentials.json aquí
mv ~/Downloads/credentials.json config/
```

### Paso 5: Configurar Bot de Telegram (Opcional)

#### 5.1 Crear el bot

1. Abre Telegram y busca: **@BotFather**
2. Envía: `/newbot`
3. Sigue las instrucciones:
   - Nombre: **Mi Clasificador de Correos**
   - Usuario: **miclasificador_correos_bot** (debe terminar en _bot)
4. **Guarda el token** que te da BotFather

#### 5.2 Obtener tu Chat ID

1. Envía `/start` a tu nuevo bot
2. Abre en el navegador (reemplaza TU_TOKEN):
   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```
3. Busca `"chat":{"id":123456789}` y copia ese número
4. Ese es tu **CHAT_ID**

### Paso 6: Configurar variables de entorno

```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con tus datos
nano .env  # o usa tu editor favorito
```

#### Configuración según tu elección:

**Si usas Ollama local (Opción A):**
```env
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

TELEGRAM_BOT_TOKEN=123456:ABC-DEF...  # Opcional
TELEGRAM_CHAT_ID=123456789            # Opcional
```

**Si usas APIs gratuitas (Opción B):**
```env
AI_PROVIDER=api

# Agrega las API keys que obtuviste (al menos una)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxx

TELEGRAM_BOT_TOKEN=123456:ABC-DEF...  # Opcional
TELEGRAM_CHAT_ID=123456789            # Opcional
```

**Modo automático (Opción C - usa APIs si están disponibles, sino Ollama):**
```env
AI_PROVIDER=auto

# APIs (opcional - si no están, usa Ollama)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx

# Ollama como fallback
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

TELEGRAM_BOT_TOKEN=123456:ABC-DEF...  # Opcional
TELEGRAM_CHAT_ID=123456789            # Opcional
```

**💡 Tip:** Con múltiples APIs configuradas, el sistema rota automáticamente entre ellas:
- 1 API = ~30-60 llamadas/minuto gratis
- 2 APIs = ~90-120 llamadas/minuto gratis
- 4 APIs = ~160-180 llamadas/minuto gratis 🚀

## 🎮 Uso

### Probar que todo funciona

```bash
# 1. Probar Ollama
python bank_classifier.py

# 2. Probar Telegram
python telegram_notifier.py

# 3. Primera autenticación con Gmail (abrirá el navegador)
python email_processor.py
```

La primera vez te pedirá permisos en Gmail. Acepta y se guardará un `token.json` para futuros usos.

### Procesar correos manualmente

```bash
python email_processor.py
```

Esto:
1. ✅ Lee tus correos no leídos
2. ✅ Los clasifica con el LLM
3. ✅ Extrae montos si los hay
4. ✅ Envía notificaciones de correos urgentes a Telegram
5. ✅ Guarda todo en la base de datos

### Enviar resumen diario

Al final del script te preguntará si quieres enviar el resumen diario. También puedes crear un cron job o tarea programada.

## ⏰ Automatización

### En Linux/Mac (crontab)

```bash
# Editar crontab
crontab -e

# Agregar estas líneas:
# Procesar correos cada 15 minutos
*/15 * * * * cd /ruta/al/proyecto && ./venv/bin/python email_processor.py

# Resumen diario a las 8 PM
0 20 * * * cd /ruta/al/proyecto && ./venv/bin/python -c "from email_processor import EmailProcessor; p = EmailProcessor(); p.setup_telegram(); p.send_daily_summary()"
```

### En Windows (Programador de tareas)

1. Abre **Programador de tareas**
2. Crear tarea básica
3. Nombre: **Clasificador de Correos**
4. Desencadenador: **Diariamente** o **cada X minutos**
5. Acción: **Iniciar un programa**
   - Programa: `C:\ruta\al\venv\Scripts\python.exe`
   - Argumentos: `email_processor.py`
   - Iniciar en: `C:\ruta\al\proyecto`

## 📊 Categorías y Prioridades

### Categorías detectadas:
- **pago**: Pagos pendientes, cargos, domiciliaciones
- **transferencia**: Transferencias enviadas o recibidas
- **estado_cuenta**: Estados de cuenta, resúmenes mensuales
- **movimiento**: Retiros, depósitos, movimientos generales
- **promocion**: Ofertas, descuentos, publicidad
- **notificacion**: Notificaciones generales del banco

### Prioridades:
- 🚨 **Urgente**: Requiere acción inmediata (pago vencido, verificación)
- 📧 **Normal**: Informativo importante (movimientos, transferencias)
- 📭 **Sin prioridad**: No requiere acción (promociones, newsletters)

## 🗂️ Estructura del Proyecto

```
clasificador-correos/
├── bank_classifier.py       # Clasificador de correos bancarios
├── telegram_notifier.py     # Envío de notificaciones
├── email_processor.py       # Procesador principal
├── .env.example             # Plantilla de configuración
├── .env                     # Tu configuración (no subir a git)
├── README.md                # Esta guía
├── requirements.txt         # Dependencias Python
├── config/
│   ├── credentials.json     # Credenciales de Google (no subir)
│   └── token.json           # Token de Gmail (se genera automático)
└── emails.db                # Base de datos SQLite (se crea automático)
```

## 🔧 Personalización

### Cambiar categorías o palabras clave

Edita `bank_classifier.py` y modifica:
```python
URGENT_KEYWORDS = [
    'pago pendiente',
    'pago vencido',
    # Agrega tus propias palabras clave
]
```

### Cambiar formato de notificaciones

Edita `telegram_notifier.py` en las funciones:
- `send_urgent_email_alert()`
- `send_daily_summary()`

### Cambiar proveedor de IA

En [.env](c:\code\email-classifier\.env):
```env
# Cambiar entre proveedores
AI_PROVIDER=ollama      # Solo Ollama local
AI_PROVIDER=api         # Solo APIs gratuitas
AI_PROVIDER=auto        # Automático (APIs primero, Ollama si no hay)

# Modelos de Ollama disponibles
OLLAMA_MODEL=llama3.2      # Ligero, rápido
OLLAMA_MODEL=qwen2.5:7b    # Más preciso
OLLAMA_MODEL=mistral       # Alternativa
OLLAMA_MODEL=gemma2:2b     # Muy ligero

# Modelos de Groq disponibles
GROQ_MODEL=mixtral-8x7b-32768
GROQ_MODEL=llama-3.1-70b-versatile

# Modelos de Cerebras disponibles
CEREBRAS_MODEL=llama3.1-8b
CEREBRAS_MODEL=llama3.1-70b

# Modelos de Gemini disponibles
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MODEL=gemini-1.5-pro
```

## 🐛 Solución de Problemas

### Error: "No hay proveedores configurados"
- Verifica que `AI_PROVIDER` esté configurado en [.env](c:\code\email-classifier\.env)
- Si usas `AI_PROVIDER=api`, asegúrate de tener al menos una API key configurada
- Si usas `AI_PROVIDER=ollama`, asegúrate de que Ollama esté corriendo

### Error: "Ollama connection refused"
```bash
# Verifica que Ollama está corriendo
ollama serve

# O reinícialo
pkill ollama
ollama serve
```

### Error: "Groq/Cerebras/Gemini error: 401 Unauthorized"
- Verifica que la API key sea correcta (sin espacios)
- Asegúrate de que la API key esté activa en la plataforma
- Verifica que no hayas excedido el rate limit gratuito

### Error: "Todos los proveedores fallaron"
- El sistema intentó con todos los proveedores disponibles y todos fallaron
- Verifica tu conexión a internet
- Si usas APIs, verifica que las API keys sean válidas
- Si usas Ollama, verifica que esté corriendo: `ollama list`

### Error: "Telegram bot token invalid"
- Verifica que copiaste el token completo de @BotFather
- Asegúrate de no tener espacios al inicio/final
- El token tiene formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Error: "Gmail authentication failed"
- Borra `config/token.json` y vuelve a autenticar
- Verifica que agregaste tu correo como "usuario de prueba"
- Revisa que el ámbito sea: `gmail.modify`

### No clasifica bien los correos
- Si usas Ollama: Prueba con un modelo más grande (qwen2.5:7b)
- Si usas APIs: Prueba cambiar el modelo en [.env](c:\code\email-classifier\.env)
- Ajusta las palabras clave en [bank_classifier.py](c:\code\email-classifier\bank_classifier.py)
- Revisa que el correo tenga suficiente texto para analizar

### Rotación de proveedores no funciona
- Verifica que tengas múltiples API keys configuradas en [.env](c:\code\email-classifier\.env)
- Revisa los logs para ver qué proveedor está usando en cada llamada
- El sistema muestra `🤖 Usando: [Proveedor]` en cada clasificación

## 📝 Ejemplos de Notificaciones

### Correo Urgente (Telegram)
```
🚨 CORREO URGENTE

De: notificaciones@banco.com
Asunto: Recordatorio: Pago de tarjeta vence mañana
💰 Monto: $2,500.00

📝 Resumen:
Pago de $2,500.00 vence el 03/01/2026
```

### Resumen Diario (Telegram)
```
📊 RESUMEN DIARIO - 02/01/2026
==============================

📬 Total de correos procesados: 15

🚨 URGENTES (2):
  • Pago de $2,500.00 vence mañana
  • Transferencia de $10,000.00 pendiente

📧 Normales (8):
  • Estado de cuenta diciembre
  • Confirmación de transferencia
  • Movimiento en cuenta de ahorros
  ... y 5 más

📭 Sin prioridad: 5 correos
```

## 🔐 Seguridad y Privacidad

### Modo Ollama (AI_PROVIDER=ollama)
- ✅ **100% Local** - Todo el procesamiento es en tu computadora
- ✅ Los correos **NO se envían a ningún servidor externo**
- ✅ Máxima privacidad - Los datos nunca salen de tu máquina

### Modo API (AI_PROVIDER=api)
- ⚠️ Los correos se envían a servicios de terceros (Groq, Cerebras, etc.)
- ✅ Solo se envía el asunto y primeros 1000 caracteres del cuerpo
- ✅ Servicios de confianza con políticas de privacidad estrictas
- ℹ️ Si te preocupa la privacidad, usa `AI_PROVIDER=ollama`

### General
- ✅ Solo se usa la API de Gmail para leer correos
- ✅ Las credenciales se guardan localmente en `config/`
- ⚠️ **Nunca subas** `credentials.json` o `token.json` a internet
- ⚠️ **Nunca subas** tu archivo [.env](c:\code\email-classifier\.env) con las API keys
- ⚠️ **Nunca compartas** tu token de Telegram

## 📚 Recursos Adicionales

- [Documentación Ollama](https://ollama.ai/docs)
- [Gmail API Python](https://developers.google.com/gmail/api/quickstart/python)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Algunas ideas:
- [ ] Soporte para más tipos de correos (vuelos, paquetería, etc.)
- [ ] Interfaz web para configuración
- [ ] Dashboard de estadísticas
- [ ] Soporte para múltiples cuentas de Gmail
- [ ] Exportar reportes en Excel

## 📄 Licencia

MIT License - Úsalo libremente, modifícalo como quieras.

## ❓ Preguntas Frecuentes

**P: ¿Necesito dejar Ollama corriendo siempre?**
R: Sí, para que el script pueda clasificar correos. Usa `ollama serve` para iniciarlo.

**P: ¿Cuánto espacio en disco necesito?**
R: ~5GB para Ollama + modelo + espacio para la base de datos (<100MB)

**P: ¿Funciona con otros servicios de correo?**
R: Actualmente solo Gmail, pero se puede adaptar a Outlook u otros.

**P: ¿Es gratis?**
R: 100% gratis. Solo usas tu propia computadora y conexión a internet.

**P: ¿Puedo usarlo sin Telegram?**
R: Sí, simplemente no configures las variables de Telegram en `.env`

---

**¿Necesitas ayuda?** Abre un issue en GitHub o consulta la documentación.

¡Disfruta de tu bandeja de entrada organizada automáticamente! 🎉
