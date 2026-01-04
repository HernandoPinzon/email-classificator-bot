# 🚀 Guía Rápida de Inicio

## Instalación en 5 Pasos

### 1. Descargar el proyecto
```bash
cd ~
mkdir clasificador-correos
cd clasificador-correos
# Copiar todos los archivos aquí
```

### 2. Ejecutar instalación automática
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Configurar Gmail API
1. Ve a: https://console.cloud.google.com/
2. Crea proyecto → Habilita Gmail API
3. Credenciales → OAuth 2.0
4. Descarga JSON → guarda como `config/credentials.json`

### 4. Configurar Telegram
1. Abre Telegram → busca `@BotFather`
2. Envía: `/newbot`
3. Copia el TOKEN
4. Envía `/start` a tu bot
5. Abre: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
6. Copia tu `chat_id`

### 5. Editar configuración
```bash
nano .env
```

Completa:
```
TELEGRAM_BOT_TOKEN=tu_token_aquí
TELEGRAM_CHAT_ID=tu_chat_id_aquí
```

## Uso Diario

```bash
# Activar entorno
source venv/bin/activate

# Procesar correos
python email_processor.py
```

## Automatización

### Linux/Mac - Cada 15 minutos
```bash
crontab -e
```

Agregar:
```
*/15 * * * * cd /ruta/al/proyecto && ./venv/bin/python email_processor.py
0 20 * * * cd /ruta/al/proyecto && ./venv/bin/python -c "from email_processor import EmailProcessor; p=EmailProcessor(); p.authenticate_gmail(); p.setup_telegram(); p.send_daily_summary()"
```

### Windows - Programador de tareas
1. Crear tarea → Diariamente
2. Acción: Iniciar programa
3. Programa: `C:\...\venv\Scripts\python.exe`
4. Argumentos: `email_processor.py`
5. Directorio: `C:\...\clasificador-correos`

## Solución Rápida de Problemas

### Ollama no conecta
```bash
ollama serve
# En otra terminal:
ollama pull llama3.2
```

### Gmail no autentica
```bash
rm config/token.json
python email_processor.py
```

### Telegram no envía
```bash
python telegram_notifier.py
# Verifica el TOKEN y CHAT_ID en .env
```

## Comandos Útiles

```bash
# Ver correos en la BD
sqlite3 emails.db "SELECT subject, priority FROM processed_emails ORDER BY processed_at DESC LIMIT 10"

# Limpiar correos procesados
sqlite3 emails.db "DELETE FROM processed_emails"

# Ver estadísticas
sqlite3 emails.db "SELECT priority, COUNT(*) FROM processed_emails GROUP BY priority"
```

## ¿Necesitas Ayuda?

Consulta el README.md completo para más detalles.
