"""
Implementaciones de EmailFetcher para obtener correos de diferentes fuentes.
"""

import base64
from typing import List, Optional
from pathlib import Path

from interfaces import EmailFetcher, Email
from config import GmailConfig


class GmailFetcher(EmailFetcher):
    """
    Implementación de EmailFetcher para Gmail API.
    Esta es la implementación real para producción.
    """

    def __init__(self, config: GmailConfig):
        self.config = config
        self.credentials_path = Path(config.credentials_path)
        self.token_path = Path(config.token_path)
        self.scopes = config.scopes
        self.service = None

    def authenticate(self) -> bool:
        """Autentica con Gmail API"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), self.scopes
                )

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        print(f"No se encontró {self.credentials_path}")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.scopes
                    )
                    creds = flow.run_local_server(port=0)

                self.token_path.write_text(creds.to_json())

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

    def set_emails(self, emails: List[Email]):
        """Configura los correos que retornará get_unread_emails"""
        self.emails = emails

    def add_email(self, email: Email):
        """Agrega un correo a la lista"""
        self.emails.append(email)

    def authenticate(self) -> bool:
        """Simula autenticación exitosa"""
        self.authenticated = True
        return True

    def set_auth_failure(self):
        """Configura para que la autenticación falle"""
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
