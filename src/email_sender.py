import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Optional
import os

class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, email_address: str, email_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
    
    def send_summary_email(self, 
                          recipient: str, 
                          text_summary: str, 
                          html_summary: str,
                          voice_file_path: Optional[str] = None) -> bool:
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"📧 Email Summary - {self._get_current_time()}"
            message["From"] = self.email_address
            message["To"] = recipient
            
            # Create text and HTML parts
            text_part = MIMEText(text_summary, "plain")
            html_part = MIMEText(html_summary, "html")
            
            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)
            
            # Add voice file attachment if provided
            if voice_file_path and os.path.exists(voice_file_path):
                self._attach_voice_file(message, voice_file_path)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, recipient, message.as_string())
            
            logging.info(f"Summary email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send summary email: {e}")
            return False
    
    def send_error_notification(self, recipient: str, error_message: str) -> bool:
        try:
            message = MIMEMultipart()
            message["Subject"] = "🚨 Mail Pilot Service Error"
            message["From"] = self.email_address
            message["To"] = recipient
            
            body = f"""
            Mail Pilot Service encountered an error:
            
            Error: {error_message}
            Time: {self._get_current_time()}
            
            Please check the service logs for more details.
            """
            
            message.attach(MIMEText(body, "plain"))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, recipient, message.as_string())
            
            logging.info(f"Error notification sent to {recipient}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send error notification: {e}")
            return False
    
    def _attach_voice_file(self, message: MIMEMultipart, voice_file_path: str):
        try:
            with open(voice_file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= "email_summary_voice.mp3"'
            )
            
            message.attach(part)
            logging.info("Voice file attached to email")
            
        except Exception as e:
            logging.error(f"Failed to attach voice file: {e}")
    
    def _get_current_time(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def test_connection(self) -> bool:
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
            
            logging.info("Email service connection test successful")
            return True
            
        except Exception as e:
            logging.error(f"Email service connection test failed: {e}")
            return False