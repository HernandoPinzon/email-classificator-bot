# 🤖 Guía Rápida: Configurar Telegram Bot

## Paso 1: Crear el bot

1. Abre **Telegram** (web, móvil o desktop)
2. Busca **@BotFather** en el buscador
3. Inicia una conversación y envía: `/start`
4. Envía el comando: `/newbot`
5. Sigue las instrucciones:
   - **Nombre del bot**: "Mi Clasificador Gmail" (o el que quieras)
   - **Username del bot**: Debe terminar en "bot", ej: `miclasificador_bot`

6. **¡Importante!** BotFather te dará un token como este:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   **Copia este token**, lo necesitarás para el `.env`

## Paso 2: Obtener tu Chat ID

Hay 2 formas de hacerlo:

### Opción A: Usando un bot auxiliar (más fácil)

1. Busca **@userinfobot** en Telegram
2. Envíale `/start`
3. Te responderá con tu información, incluyendo tu **ID**
4. Copia ese número (ej: `123456789`)

### Opción B: Usando la API (manual)

1. Primero, envía **cualquier mensaje** a tu bot recién creado
2. Luego, en tu navegador, ve a esta URL (reemplaza `<TOKEN>` con tu token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   
3. Verás algo así:
   ```json
   {
     "ok": true,
     "result": [{
       "message": {
         "chat": {
           "id": 123456789,  ← Este es tu chat_id
           "first_name": "Tu Nombre",
           "username": "tu_usuario"
         }
       }
     }]
   }
   ```

4. Copia el número que aparece en `"id"`

## Paso 3: Configurar el archivo .env

1. Abre el archivo `.env` en tu editor favorito
2. Reemplaza los valores:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

## Paso 4: Probar la configuración

```bash
python gmail_classifier.py --test
```

Deberías recibir un mensaje en Telegram que diga:
```
✅ Conexión exitosa!

Tu bot de clasificación de Gmail está funcionando correctamente.
```

## 🎯 Tips

### Para silenciar notificaciones normales
El script ya está configurado para:
- ✅ **Urgentes**: Con sonido (inmediato)
- 🔕 **Resumen diario**: Sin sonido

### Cambiar la hora del resumen diario
Edita `.env`:
```bash
DAILY_SUMMARY_TIME=20:00  # Formato 24 horas
```

### Usar el bot en un grupo
1. Agrega tu bot al grupo
2. En lugar del chat_id personal, usa el ID del grupo
3. Los IDs de grupo empiezan con `-` (negativo)

Ejemplo:
```bash
TELEGRAM_CHAT_ID=-1001234567890
```

## ❓ Solución de problemas

### "Unauthorized" o "Bot not found"
- Verifica que copiaste bien el token (sin espacios)
- Asegúrate de usar el token del bot correcto

### "Chat not found"
- Primero debes enviar un mensaje a tu bot
- Verifica que el chat_id sea correcto
- Si es un grupo, asegúrate que el ID tenga el `-` al inicio

### El bot no responde
- Verifica que Ollama esté corriendo: `ollama serve`
- Revisa los logs: `tail -f gmail_classifier.log`

## 🔒 Seguridad

⚠️ **NUNCA** compartas tu token de bot. Es como una contraseña.

Si accidentalmente lo expones:
1. Ve a @BotFather
2. Envía `/mybots`
3. Selecciona tu bot
4. Ve a "API Token"
5. Haz click en "Revoke current token"
6. Copia el nuevo token y actualiza tu `.env`

---

**¿Listo?** 🚀 Ahora puedes ejecutar `python gmail_classifier.py --test`
