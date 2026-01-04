#!/bin/bash
# Script de instalación rápida para Gmail Bank Classifier

set -e  # Salir si hay error

echo "================================================"
echo "  Gmail Bank Classifier - Instalación Rápida"
echo "================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python encontrado: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 no encontrado. Por favor instálalo primero."
    exit 1
fi

# Verificar Ollama
echo ""
echo "2. Verificando Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama encontrado"
    
    # Verificar si el modelo está descargado
    if ollama list | grep -q "llama3.2:3b"; then
        echo -e "${GREEN}✓${NC} Modelo llama3.2:3b ya descargado"
    else
        echo -e "${YELLOW}⚠${NC} Descargando modelo llama3.2:3b (esto puede tardar)..."
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓${NC} Modelo descargado"
    fi
else
    echo -e "${RED}✗${NC} Ollama no encontrado."
    echo "   Instálalo desde: https://ollama.ai"
    exit 1
fi

# Crear entorno virtual
echo ""
echo "3. Creando entorno virtual..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} Entorno virtual ya existe, usando el existente"
else
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
echo ""
echo "4. Instalando dependencias..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencias instaladas"

# Crear archivo .env si no existe
echo ""
echo "5. Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC} Archivo .env creado desde .env.example"
    echo "   ${YELLOW}IMPORTANTE:${NC} Edita .env con tus credenciales:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - TELEGRAM_CHAT_ID"
else
    echo -e "${GREEN}✓${NC} Archivo .env ya existe"
fi

# Verificar credentials.json
echo ""
echo "6. Verificando credenciales de Gmail..."
if [ ! -f "credentials.json" ]; then
    echo -e "${YELLOW}⚠${NC} credentials.json NO encontrado"
    echo ""
    echo "   Para configurar Gmail API:"
    echo "   1. Ve a: https://console.cloud.google.com/"
    echo "   2. Crea un proyecto y habilita Gmail API"
    echo "   3. Crea credenciales OAuth 2.0 (Desktop app)"
    echo "   4. Descarga el JSON y guárdalo como 'credentials.json'"
    echo ""
else
    echo -e "${GREEN}✓${NC} credentials.json encontrado"
fi

# Resumen
echo ""
echo "================================================"
echo "  Instalación completada"
echo "================================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. ${YELLOW}Configurar Telegram:${NC}"
echo "   - Abre Telegram y busca @BotFather"
echo "   - Crea un bot con /newbot"
echo "   - Copia el token al archivo .env"
echo "   - Envía un mensaje a tu bot"
echo "   - Obtén tu chat_id y agrégalo a .env"
echo ""
echo "2. ${YELLOW}Configurar Gmail API:${NC}"
echo "   - Sigue las instrucciones en README.md"
echo "   - Coloca credentials.json en este directorio"
echo ""
echo "3. ${YELLOW}Probar la configuración:${NC}"
echo "   ${GREEN}python gmail_classifier.py --test${NC}"
echo ""
echo "4. ${YELLOW}Procesar correos:${NC}"
echo "   ${GREEN}python gmail_classifier.py${NC}"
echo ""
echo "Para más información, lee el README.md"
echo ""
