"""
Implementaciones de EmailFetcher para obtener correos de diferentes fuentes.
"""

import base64
import json
import os
from typing import List, Optional
from pathlib import Path

from interfaces import EmailFetcher, Email
from config import GmailConfig


class GmailFetcher(EmailFetcher):
    """
    Implementación de EmailFetcher para Gmail API.
    Esta es la implementación real para producción.

    Soporta múltiples modos de autenticación para entornos cloud/headless:
    - auto: intenta navegador, si falla usa modo manual
    - browser: usa navegador local (requiere GUI)
    - manual: muestra URL y pide código manualmente (para servidores sin GUI)
    - token_env: usa token desde variable de entorno GMAIL_TOKEN_JSON
    """

    def __init__(self, config: GmailConfig):
        self.config = config
        self.credentials_path = Path(config.credentials_path)
        self.token_path = Path(config.token_path)
        self.scopes = config.scopes
        self.auth_mode = getattr(config, 'auth_mode', 'auto')
        self.service = None

    def _load_token_from_env(self):
        """Carga credenciales desde variable de entorno GMAIL_TOKEN_JSON"""
        from google.oauth2.credentials import Credentials

        token_json = os.getenv('GMAIL_TOKEN_JSON')
        if not token_json:
            return None

        try:
            # Intenta decodificar como base64 primero
            try:
                token_json = base64.b64decode(token_json).decode('utf-8')
            except Exception:
                pass  # Asume que ya es JSON directo

            token_data = json.loads(token_json)
            return Credentials.from_authorized_user_info(token_data, self.scopes)
        except Exception as e:
            print(f"Error cargando token desde GMAIL_TOKEN_JSON: {e}")
            return None

    def _authenticate_manual(self, flow):
        """Autenticación manual: muestra URL y pide código de autorización"""
        # Genera URL de autorización
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        print("\n" + "=" * 60)
        print("AUTENTICACIÓN GMAIL - MODO MANUAL (HEADLESS)")
        print("=" * 60)
        print("\n1. Abre esta URL en cualquier navegador:\n")
        print(auth_url)
        print("\n2. Autoriza la aplicación con tu cuenta de Google")
        print("3. Copia el código de autorización que aparece")
        print("4. Pega el código aquí:\n")

        auth_code = input("Código de autorización: ").strip()

        if not auth_code:
            print("No se proporcionó código de autorización")
            return None

        # Intercambia el código por tokens
        flow.fetch_token(code=auth_code)
        return flow.credentials

    def _authenticate_browser(self, flow):
        """Autenticación con navegador local"""
        return flow.run_local_server(port=0)

    def authenticate(self) -> bool:
        """
        Autentica con Gmail API.

        Modos de autenticación:
        - 'auto': intenta navegador, si falla usa manual
        - 'browser': usa navegador local (requiere GUI)
        - 'manual': muestra URL y pide código (para servidores)
        - 'token_env': usa GMAIL_TOKEN_JSON del entorno
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow, Flow
            from googleapiclient.discovery import build

            creds = None

            # 1. Intentar cargar token desde variable de entorno
            if self.auth_mode == 'token_env' or self.auth_mode == 'auto':
                creds = self._load_token_from_env()
                if creds:
                    print("Token cargado desde variable de entorno GMAIL_TOKEN_JSON")

            # 2. Intentar cargar token desde archivo
            if not creds and self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), self.scopes
                )

            # 3. Verificar validez y refrescar si es necesario
            if creds and not creds.valid:
                if creds.expired and creds.refresh_token:
                    print("Refrescando token expirado...")
                    creds.refresh(Request())
                    # Guardar token refrescado
                    self.token_path.parent.mkdir(parents=True, exist_ok=True)
                    self.token_path.write_text(creds.to_json())
                else:
                    creds = None  # Token inválido sin refresh_token

            # 4. Si no hay credenciales válidas, autenticar
            if not creds or not creds.valid:
                if self.auth_mode == 'token_env':
                    print("Error: modo 'token_env' pero no se encontró GMAIL_TOKEN_JSON válido")
                    return False

                if not self.credentials_path.exists():
                    print(f"No se encontró {self.credentials_path}")
                    print("Descarga credentials.json desde Google Cloud Console")
                    return False

                # Crear flow para OAuth
                flow = Flow.from_client_secrets_file(
                    str(self.credentials_path),
                    scopes=self.scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Para modo manual
                )

                if self.auth_mode == 'manual':
                    creds = self._authenticate_manual(flow)
                elif self.auth_mode == 'browser':
                    # Usar InstalledAppFlow para navegador
                    browser_flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.scopes
                    )
                    creds = self._authenticate_browser(browser_flow)
                else:  # auto
                    try:
                        # Intentar con navegador primero
                        browser_flow = InstalledAppFlow.from_client_secrets_file(
                            str(self.credentials_path), self.scopes
                        )
                        creds = self._authenticate_browser(browser_flow)
                    except Exception as browser_error:
                        print(f"No se pudo abrir navegador: {browser_error}")
                        print("Cambiando a modo manual...")
                        creds = self._authenticate_manual(flow)

                if not creds:
                    print("No se pudo obtener credenciales")
                    return False

                # Guardar token para uso futuro
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                self.token_path.write_text(creds.to_json())
                print(f"Token guardado en {self.token_path}")

            self.service = build('gmail', 'v1', credentials=creds)
            return True

        except Exception as e:
            print(f"Error en autenticación Gmail: {e}")
            return False

    def get_unread_emails(self, max_results: int = 50, query: str = "is:unread") -> List[Email]:
        """Obtiene correos no leídos de Gmail"""
        if not self.service:
            print("Gmail no autenticado. Llama a authenticate() primero")
            return []

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return []

            emails = []
            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = msg_data['payload']['headers']
                subject = next(
                    (h['value'] for h in headers if h['name'] == 'Subject'),
                    'Sin asunto'
                )
                sender = next(
                    (h['value'] for h in headers if h['name'] == 'From'),
                    'Desconocido'
                )
                date = next(
                    (h['value'] for h in headers if h['name'] == 'Date'),
                    ''
                )

                body = self._get_email_body(msg_data['payload'])

                emails.append(Email(
                    id=msg['id'],
                    subject=subject,
                    sender=sender,
                    body=body,
                    date=date
                ))

            return emails

        except Exception as e:
            print(f"Error obteniendo correos: {e}")
            return []

    def mark_as_read(self, email_id: str) -> bool:
        """Marca un correo como leído"""
        if not self.service:
            return False

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marcando correo como leído: {e}")
            return False

    def _get_email_body(self, payload: dict) -> str:
        """Extrae el cuerpo del correo del payload"""
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')

        return body[:2000]


class MockEmailFetcher(EmailFetcher):
    """
    Implementación mock de EmailFetcher para testing.
    Permite configurar correos de prueba.
    """

    def __init__(self):
        self.authenticated = False
        self.emails: List[Email] = []
        self.read_emails: List[str] = []
        self._should_fail_auth = False

    def set_emails(self, emails: List[Email]):
        """Configura los correos que retornará get_unread_emails"""
        self.emails = emails

    def add_email(self, email: Email):
        """Agrega un correo a la lista"""
        self.emails.append(email)

    def authenticate(self) -> bool:
        """Simula autenticación"""
        if self._should_fail_auth:
            self.authenticated = False
            return False
        self.authenticated = True
        return True

    def set_auth_failure(self):
        """Configura para que la autenticación falle"""
        self._should_fail_auth = True
        self.authenticated = False

    def get_unread_emails(self, max_results: int = 50, query: str = "") -> List[Email]:
        """Retorna los correos configurados"""
        if not self.authenticated:
            return []

        unread = [e for e in self.emails if e.id not in self.read_emails]
        return unread[:max_results]

    def mark_as_read(self, email_id: str) -> bool:
        """Marca un correo como leído"""
        if email_id not in self.read_emails:
            self.read_emails.append(email_id)
        return True

    def clear(self):
        """Limpia todos los datos"""
        self.emails.clear()
        self.read_emails.clear()
        self.authenticated = False
