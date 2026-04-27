from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings
from email_validator import validate_email, EmailNotValidError
from pathlib import Path

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True
        )
    
    def check_email_exists(self, email: str):
        """Verifica si el formato y el dominio del email son válidos"""
        try:
            valid = validate_email(email, check_deliverability=True)
            return True, valid.normalized
        except EmailNotValidError as e:
            return False, str(e)
    from pathlib import Path
    
    async def send_report_email(self, file_path: str, recipient: str = None, body: str = None):
        recipient = recipient or settings.contact_email

        is_valid, msg_error = self.check_email_exists(recipient)
        if not is_valid:
            raise Exception(f"Email inválido: {msg_error}")
        
        email_body = body or "Hola, adjunto encontrarás el reporte empresarial generado automáticamente."

        message = MessageSchema(
            subject=f"📊 Reporte Inteligente - {settings.company_name}",
            recipients=[recipient],
            body=email_body,
            subtype=MessageType.plain,
            attachments=[file_path]
        )

        fm = FastMail(self.conf)
        await fm.send_message(message)
        print(f"Email enviado con éxito a {recipient}")
    