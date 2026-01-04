#!/bin/bash

# Script de instalación automatizada para el Clasificador de Correos
# Clasificador Automático de Correos Bancarios con LLM

echo "================================================"
echo "📧 Clasificador de Correos Bancarios con LLM"
echo "================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Verificar Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado"
    echo "Instala Python 3.8+ desde https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION encontrado"

# Verificar Ollama
echo ""
echo "Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama no está instalado"
    echo "Instálalo desde: https://ollama.ai"
    echo ""
    read -p "¿Quieres continuar sin Ollama? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
else
    print_success "Ollama encontrado"
    
    # Verificar si Ollama está corriendo
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama está corriendo"
        
        # Listar modelos instalados
        echo ""
        print_info "Modelos instalados:"
        ollama list
        
        # Verificar si tiene algún modelo
        if ! ollama list | grep -q "llama\|qwen\|mistral\|gemma"; then
            echo ""
            print_warning "No se encontraron modelos recomendados"
            echo "Descarga un modelo con: ollama pull llama3.2"
            echo ""
            read -p "¿Descargar llama3.2 ahora? (s/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Ss]$ ]]; then
                ollama pull llama3.2
                print_success "Modelo llama3.2 descargado"
            fi
        else
            print_success "Modelos encontrados"
        fi
    else
        print_warning "Ollama no está corriendo"
        echo "Inicia Ollama con: ollama serve"
    fi
fi

# Crear entorno virtual
echo ""
echo "Configurando entorno virtual..."
if [ -d "venv" ]; then
    print_warning "El entorno virtual ya existe"
    read -p "¿Recrear entorno virtual? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Entorno virtual recreado"
    fi
else
    python3 -m venv venv
    print_success "Entorno virtual creado"
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
echo ""
echo "Instalando dependencias de Python..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "Dependencias instaladas"
else
    print_error "Error instalando dependencias"
    exit 1
fi

# Crear directorios necesarios
echo ""
echo "Creando estructura de directorios..."
mkdir -p config
print_success "Directorio config/ creado"

# Configurar archivo .env
echo ""
if [ -f ".env" ]; then
    print_warning "El archivo .env ya existe"
    read -p "¿Sobrescribir con valores por defecto? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Conservando .env existente"
    else
        cp .env.example .env
        print_success "Archivo .env creado desde .env.example"
    fi
else
    cp .env.example .env
    print_success "Archivo .env creado desde .env.example"
fi

# Instrucciones de configuración
echo ""
echo "================================================"
echo "📝 PRÓXIMOS PASOS"
echo "================================================"
echo ""

# 1. Configurar Gmail
echo "1️⃣  CONFIGURAR GMAIL API:"
echo "   • Ve a https://console.cloud.google.com/"
echo "   • Crea un proyecto nuevo"
echo "   • Habilita Gmail API"
echo "   • Crea credenciales OAuth 2.0"
echo "   • Descarga el JSON como: config/credentials.json"
echo ""

# 2. Configurar Telegram
echo "2️⃣  CONFIGURAR TELEGRAM (opcional):"
echo "   • Abre Telegram y busca @BotFather"
echo "   • Envía: /newbot"
echo "   • Copia el token que te da"
echo "   • Envía /start a tu bot"
echo "   • Obtén tu chat_id desde:"
echo "     https://api.telegram.org/bot<TOKEN>/getUpdates"
echo "   • Agrega TOKEN y CHAT_ID en el archivo .env"
echo ""

# 3. Editar .env
echo "3️⃣  EDITAR CONFIGURACIÓN:"
echo "   • Edita el archivo .env con tus credenciales:"
echo "     nano .env"
echo "     (o usa tu editor favorito)"
echo ""

# 4. Probar
echo "4️⃣  PROBAR EL SISTEMA:"
echo "   • Activar entorno virtual:"
echo "     source venv/bin/activate"
echo ""
echo "   • Probar clasificador:"
echo "     python bank_classifier.py"
echo ""
echo "   • Probar Telegram:"
echo "     python telegram_notifier.py"
echo ""
echo "   • Procesar correos:"
echo "     python email_processor.py"
echo ""

# Verificar si credentials.json existe
if [ -f "config/credentials.json" ]; then
    print_success "credentials.json encontrado en config/"
    echo ""
    read -p "¿Probar autenticación con Gmail ahora? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        python email_processor.py
    fi
else
    print_warning "No se encontró config/credentials.json"
    echo "Completa el paso 1 antes de continuar"
fi

echo ""
echo "================================================"
print_success "¡Instalación completada!"
echo "================================================"
echo ""
echo "Para más información, consulta README.md"
echo ""
