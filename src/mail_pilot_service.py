import logging
import os
import signal
import sys
from typing import Optional
import tempfile

from .config import load_config, AppConfig
from .gmail_client import GmailClient
from .ollama_client import OllamaClient
from .email_processor import EmailProcessor
from .email_sender import EmailSender
from .voice_generator import VoiceGenerator
from .scheduler import EmailSummaryScheduler, ManualRunner

class MailPilotService:
    def __init__(self, config_file: str = '.env'):
        self.config = load_config(config_file)
        self.gmail_client = None
        self.ollama_client = None
        self.email_processor = None
        self.email_sender = None
        self.voice_generator = None
        self.scheduler = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self) -> bool:
        """Initialize all service components"""
        try:
            logging.info("Initializing Mail Pilot Service...")
            
            # Initialize Gmail client
            self.gmail_client = GmailClient(
                credentials_path=self.config.gmail.credentials_path,
                token_path=self.config.gmail.token_path
            )
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient(
                base_url=self.config.ollama.url,
                model=self.config.ollama.model
            )
            
            # Test Ollama connection
            if not self.ollama_client.test_connection():
                logging.error("Failed to connect to Ollama service")
                return False
            
            # Initialize email processor
            self.email_processor = EmailProcessor(
                gmail_client=self.gmail_client,
                ollama_client=self.ollama_client
            )
            
            # Initialize email sender
            self.email_sender = EmailSender(
                smtp_server=self.config.email.smtp_server,
                smtp_port=self.config.email.smtp_port,
                email_address=self.config.email.email_address,
                email_password=self.config.email.email_password
            )
            
            # Test email connection
            if not self.email_sender.test_connection():
                logging.error("Failed to connect to email service")
                return False
            
            # Initialize voice generator
            self.voice_generator = VoiceGenerator(
                language=self.config.voice.language,
                enabled=self.config.voice.enabled
            )
            
            # Initialize scheduler
            self.scheduler = EmailSummaryScheduler(
                interval_hours=self.config.scheduler.interval_hours
            )
            self.scheduler.set_job_function(self.process_emails)
            
            logging.info("Mail Pilot Service initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize service: {e}")
            return False
    
    def process_emails(self):
        """Main email processing function"""
        try:
            logging.info("Starting email processing cycle")
            
            # Process unread emails
            result = self.email_processor.process_unread_emails()
            
            if result['total_emails'] == 0:
                logging.info("No unread emails to process")
                return
            
            # Generate text and HTML summaries
            text_summary = self.email_processor.format_email_summary_text(result)
            html_summary = self.email_processor.format_email_summary_html(result)
            
            # Generate voice summary if enabled
            voice_file_path = None
            if self.config.voice.enabled:
                voice_text = self.voice_generator.create_voice_summary_text(result)
                voice_file_path = self.voice_generator.generate_voice_summary(voice_text)
            
            # Send summary email
            success = self.email_sender.send_summary_email(
                recipient=self.config.email.email_address,
                text_summary=text_summary,
                html_summary=html_summary,
                voice_file_path=voice_file_path
            )
            
            if success:
                logging.info(f"Email summary sent successfully for {result['total_emails']} emails")
            else:
                logging.error("Failed to send email summary")
            
            # Cleanup voice file if created
            if voice_file_path:
                self.voice_generator.cleanup_temp_file(voice_file_path)
                
        except Exception as e:
            logging.error(f"Error during email processing: {e}")
            # Send error notification
            try:
                self.email_sender.send_error_notification(
                    recipient=self.config.email.email_address,
                    error_message=str(e)
                )
            except Exception as notification_error:
                logging.error(f"Failed to send error notification: {notification_error}")
    
    def start_service(self):
        """Start the scheduled service"""
        if not self.initialize():
            logging.error("Failed to initialize service")
            return False
        
        try:
            self.running = True
            logging.info("Starting Mail Pilot Service in scheduled mode")
            
            self.scheduler.start()
            
            # Keep the main thread alive
            while self.running:
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("Service interrupted by user")
        except Exception as e:
            logging.error(f"Service error: {e}")
        finally:
            self.stop_service()
        
        return True
    
    def run_once(self):
        """Run email processing once without scheduling"""
        if not self.initialize():
            logging.error("Failed to initialize service")
            return False
        
        try:
            logging.info("Running Mail Pilot Service once")
            self.process_emails()
            return True
            
        except Exception as e:
            logging.error(f"Error during single run: {e}")
            return False
    
    def stop_service(self):
        """Stop the service gracefully"""
        logging.info("Stopping Mail Pilot Service...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.stop()
        
        logging.info("Mail Pilot Service stopped")
    
    def get_status(self) -> dict:
        """Get service status"""
        status = {
            'running': self.running,
            'initialized': self.gmail_client is not None,
            'config': {
                'interval_hours': self.config.scheduler.interval_hours,
                'voice_enabled': self.config.voice.enabled,
                'ollama_model': self.config.ollama.model
            }
        }
        
        if self.scheduler:
            status['scheduler'] = self.scheduler.get_status()
        
        return status
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, shutting down...")
        self.stop_service()
        sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mail Pilot - AI Email Summary Service')
    parser.add_argument('--config', default='.env', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once instead of scheduling')
    parser.add_argument('--status', action='store_true', help='Show service status')
    
    args = parser.parse_args()
    
    try:
        service = MailPilotService(config_file=args.config)
        
        if args.status:
            status = service.get_status()
            print(f"Service Status: {status}")
            return
        
        if args.once:
            success = service.run_once()
            sys.exit(0 if success else 1)
        else:
            service.start_service()
            
    except Exception as e:
        logging.error(f"Service failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()