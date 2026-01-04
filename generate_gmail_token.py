#!/usr/bin/env python3
"""
Script para generar token de Gmail localmente.

Este script te permite autenticarte con Gmail en tu máquina local (con navegador)
y luego exportar el token para usarlo en un servidor cloud sin GUI.

Uso:
    1. Ejecuta este script localmente: python generate_gmail_token.py
    2. Se abrirá el navegador para autorizar la aplicación
    3. El script generará el token y mostrará cómo usarlo en el servidor

Opciones:
    --manual    Usa modo manual (sin navegador, te da una URL para copiar)
    --export    Muestra el token en formato para variable de entorno
"""

import argparse
import base64
import json
import sys
from pathlib import Path


def generate_token(manual_mode: bool = False) -> dict:
    """Genera un token de Gmail"""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow, Flow
    except ImportError:
        print("Error: Instala las dependencias primero:")
        print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    credentials_path = Path("./config/credentials.json")
    token_path = Path("./config/token.json")
    scopes = ['https://www.googleapis.com/auth/gmail.modify']

    if not credentials_path.exists():
        print(f"Error: No se encontró {credentials_path}")
        print("\nPasos para obtener credentials.json:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. Crea un proyecto o selecciona uno existente")
        print("3. Habilita la Gmail API")
        print("4. Ve a 'Credenciales' -> 'Crear credenciales' -> 'ID de cliente OAuth'")
        print("5. Selecciona 'Aplicación de escritorio'")
        print("6. Descarga el archivo JSON y guárdalo como config/credentials.json")
        sys.exit(1)

    creds = None

    # Verificar si ya existe un token válido
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if creds and creds.valid:
        print("Ya existe un token válido en", token_path)
        return json.loads(token_path.read_text())

    if creds and creds.expired and creds.refresh_token:
        print("Refrescando token expirado...")
        creds.refresh(Request())
    else:
        if manual_mode:
            # Modo manual: genera URL
            flow = Flow.from_client_secrets_file(
                str(credentials_path),
                scopes=scopes,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )

            print("\n" + "=" * 60)
            print("AUTENTICACIÓN GMAIL - MODO MANUAL")
            print("=" * 60)
            print("\n1. Abre esta URL en tu navegador:\n")
            print(auth_url)
            print("\n2. Autoriza la aplicación con tu cuenta de Google")
            print("3. Copia el código de autorización que aparece")
            print("4. Pega el código aquí:\n")

            auth_code = input("Código de autorización: ").strip()

            if not auth_code:
                print("Error: No se proporcionó código")
                sys.exit(1)

            flow.fetch_token(code=auth_code)
            creds = flow.credentials
        else:
            # Modo navegador
            print("Abriendo navegador para autorización...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), scopes
            )
            creds = flow.run_local_server(port=0)

    # Guardar token
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"\nToken guardado en {token_path}")

    return json.loads(creds.to_json())


def export_token(token_data: dict) -> str:
    """Exporta el token como string base64 para variable de entorno"""
    token_json = json.dumps(token_data)
    token_b64 = base64.b64encode(token_json.encode()).decode()
    return token_b64


def main():
    parser = argparse.ArgumentParser(
        description='Genera token de Gmail para uso en servidores cloud'
    )
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='Usa modo manual (sin navegador)'
    )
    parser.add_argument(
        '--export', '-e',
        action='store_true',
        help='Muestra el token para variable de entorno'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("GENERADOR DE TOKEN GMAIL")
    print("=" * 60)

    token_data = generate_token(manual_mode=args.manual)

    if args.export or True:  # Siempre mostrar instrucciones de export
        token_b64 = export_token(token_data)

        print("\n" + "=" * 60)
        print("INSTRUCCIONES PARA SERVIDOR CLOUD")
        print("=" * 60)

        print("\n[OPCIÓN 1] Variable de entorno (recomendado para cloud):")
        print("-" * 50)
        print("\nExporta esta variable de entorno en tu servidor:\n")
        print(f"export GMAIL_TOKEN_JSON='{token_b64}'")
        print("\nY configura el modo de autenticación:")
        print("export GMAIL_AUTH_MODE='token_env'")

        print("\n\n[OPCIÓN 2] Copiar archivo token.json:")
        print("-" * 50)
        print("\nCopia el archivo ./config/token.json a tu servidor")
        print("en la misma ruta relativa.")

        print("\n\n[OPCIÓN 3] Usar en Docker/docker-compose:")
        print("-" * 50)
        print("\nEn docker-compose.yml:")
        print("""
services:
  email-bot:
    environment:
      - GMAIL_AUTH_MODE=token_env
      - GMAIL_TOKEN_JSON=${GMAIL_TOKEN_JSON}
""")

        print("\n\n[OPCIÓN 4] Usar en GitHub Actions / CI:")
        print("-" * 50)
        print("\n1. Guarda el token como secreto: GMAIL_TOKEN_JSON")
        print("2. Úsalo en tu workflow:")
        print("""
env:
  GMAIL_AUTH_MODE: token_env
  GMAIL_TOKEN_JSON: ${{ secrets.GMAIL_TOKEN_JSON }}
""")

        print("\n" + "=" * 60)
        print("¡Token generado correctamente!")
        print("=" * 60)


if __name__ == '__main__':
    main()
