import logging
import os
import signal
import sys
from typing import Optional, Dict
import tempfile

from .config import load_config, AppConfig
from .gmail_client import GmailClient
from .ollama_client import OllamaClient
from .email_processor import EmailProcessor
from .email_sender import EmailSender
from .voice_generator import VoiceGenerator
from .scheduler import EmailSummaryScheduler, ManualRunner
from .file_saver import FileSaver
from .email_menu import EmailMenu

class MailPilotService:
    def __init__(self, config_file: str = '../.env'):
        self.config = load_config(config_file)
        self.gmail_client = None
        self.ollama_client = None
        self.email_processor = None
        self.email_sender = None
        self.voice_generator = None
        self.scheduler = None
        self.file_saver = None
        self.menu = EmailMenu()
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
            
            # Test Ollama connection thoroughly
            logging.info("🔍 Testing Ollama connection and model availability...")
            if not self.ollama_client.test_connection():
                logging.error("❌ Failed to connect to Ollama service or model not available")
                logging.error("🔧 Troubleshooting steps:")
                logging.error("   1. Check if Ollama is running: ollama list")
                logging.error("   2. If not running, Ollama should start automatically")
                logging.error("   3. If model missing, run: ollama pull mistral")
                logging.error("   4. Check Ollama URL in .env file")
                return False
            
            # Initialize email processor
            self.email_processor = EmailProcessor(
                gmail_client=self.gmail_client,
                ollama_client=self.ollama_client
            )
            
            # Initialize email sender (only if enabled)
            if self.config.email.enabled:
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
                    
                logging.info("Email sending is enabled and configured")
            else:
                logging.info("Email sending is disabled - summaries will be saved locally only")
            
            # Initialize voice generator
            self.voice_generator = VoiceGenerator(
                language=self.config.voice.language,
                enabled=self.config.voice.enabled
            )
            
            # Initialize file saver
            self.file_saver = FileSaver()
            
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
    
    def process_emails(self, query: str = 'is:unread', options: Dict = None):
        """Main email processing function"""
        try:
            logging.info("=" * 60)
            logging.info("STARTING EMAIL PROCESSING CYCLE")
            logging.info("=" * 60)
            
            if options is None:
                options = {'categorize_emails': True, 'voice_enabled': self.config.voice.enabled}
            
            # Process emails with categorization enabled by default
            logging.info("Step 1/6: Processing emails with AI and automatic categorization")
            result = self.email_processor.process_unread_emails(query, options)
            
            if result['total_emails'] == 0:
                logging.info("✅ No unread emails found - processing complete")
                logging.info("=" * 60)
                return
            
            logging.info(f"✅ Found {result['total_emails']} emails to process")
            
            # Generate text and HTML summaries
            logging.info("Step 2/6: Generating text and HTML summaries")
            text_summary = self.email_processor.format_email_summary_text(result)
            html_summary = self.email_processor.format_email_summary_html(result)
            logging.info("✅ Text and HTML summaries generated")
            
            # Generate voice summary if enabled
            voice_file_path = None
            if self.config.voice.enabled:
                logging.info("Step 3/6: Generating voice summary")
                voice_text = self.voice_generator.create_voice_summary_text(result)
                voice_file_path = self.voice_generator.generate_voice_summary(voice_text)
                if voice_file_path:
                    logging.info("✅ Voice summary generated")
                else:
                    logging.warning("⚠️ Voice summary generation failed")
            else:
                logging.info("Step 3/6: Skipping voice generation (disabled)")
            
            # Save summary locally (always)
            logging.info("Step 4/6: Saving summaries to local files")
            saved_files = self.file_saver.save_summary(result, text_summary, html_summary, voice_file_path)
            
            if saved_files:
                logging.info(f"✅ Email summary saved locally for {result['total_emails']} emails")
                logging.info(f"📁 Files saved: {', '.join(saved_files.keys())}")
                for file_type, file_path in saved_files.items():
                    logging.info(f"   {file_type}: {file_path}")
            else:
                logging.error("❌ Failed to save email summary locally")
            
            # Send summary email (only if enabled)
            if self.config.email.enabled and self.email_sender:
                logging.info("Step 5/6: Sending email summary")
                success = self.email_sender.send_summary_email(
                    recipient=self.config.email.email_address,
                    text_summary=text_summary,
                    html_summary=html_summary,
                    voice_file_path=voice_file_path
                )
                
                if success:
                    logging.info(f"✅ Email summary sent successfully for {result['total_emails']} emails")
                else:
                    logging.error("❌ Failed to send email summary")
            else:
                logging.info("Step 5/6: Skipping email sending (disabled - summary saved locally only)")
            
            # Cleanup voice file if created
            logging.info("Step 6/6: Cleaning up temporary files")
            if voice_file_path:
                self.voice_generator.cleanup_temp_file(voice_file_path)
                logging.info("✅ Temporary files cleaned up")
            
            logging.info("=" * 60)
            logging.info("EMAIL PROCESSING CYCLE COMPLETED SUCCESSFULLY")
            logging.info("=" * 60)
                
        except Exception as e:
            logging.error(f"❌ Error during email processing: {e}")
            # Send error notification (only if email is enabled)
            if self.config.email.enabled and self.email_sender:
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
            logging.info("🚀 Starting Mail Pilot Service in scheduled mode")
            logging.info(f"📅 Service will run every {self.config.scheduler.interval_hours} hours")
            logging.info("Press Ctrl+C to stop the service")
            logging.info("=" * 60)
            
            self.scheduler.start()
            
            # Keep the main thread alive with better interrupt handling
            import time
            while self.running:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    logging.info("🛑 Keyboard interrupt received - stopping service...")
                    break
                
        except KeyboardInterrupt:
            logging.info("Service interrupted by user")
        except Exception as e:
            logging.error(f"Service error: {e}")
        finally:
            self.stop_service()
        
        return True
    
    def run_once_with_menu(self):
        """Run email processing once with interactive menu"""
        if not self.initialize():
            logging.error("Failed to initialize service")
            return False
        
        try:
            logging.info("Running Mail Pilot Service with interactive menu")
            
            # Show timeframe selection menu
            hours = self.menu.show_timeframe_menu()
            query = self.menu.calculate_date_query(hours)
            timeframe_desc = self.menu.get_timeframe_description(hours)
            
            # Show processing options menu
            options = self.menu.show_processing_options()
            
            print(f"\n🚀 Starting email processing for {timeframe_desc}...")
            
            # Process emails with selected options
            self.process_emails(query, options)
            return True
            
        except Exception as e:
            logging.error(f"Error during single run: {e}")
            return False
    
    def run_once(self):
        """Run email processing once without scheduling"""
        if not self.initialize():
            logging.error("Failed to initialize service")
            return False
        
        try:
            logging.info("Running Mail Pilot Service once")
            # Use categorization by default for programmatic runs
            options = {'categorize_emails': True, 'voice_enabled': self.config.voice.enabled}
            self.process_emails('is:unread', options)
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
        """Get comprehensive service status including Ollama connection"""
        status = {
            'running': self.running,
            'initialized': self.gmail_client is not None,
            'config': {
                'interval_hours': self.config.scheduler.interval_hours,
                'voice_enabled': self.config.voice.enabled,
                'ollama_model': self.config.ollama.model,
                'ollama_url': self.config.ollama.url,
                'email_enabled': self.config.email.enabled
            }
        }
        
        # Test Ollama connection status
        if self.ollama_client:
            logging.info("🔍 Checking Ollama connection status...")
            ollama_status = self._check_ollama_status()
            status['ollama'] = ollama_status
        else:
            status['ollama'] = {
                'connected': False,
                'error': 'Ollama client not initialized'
            }
        
        # Gmail connection status
        if self.gmail_client:
            status['gmail'] = {'connected': True, 'authenticated': True}
        else:
            status['gmail'] = {'connected': False, 'authenticated': False}
        
        # Email service status
        if self.config.email.enabled and self.email_sender:
            status['email_service'] = {'enabled': True, 'configured': True}
        else:
            status['email_service'] = {
                'enabled': self.config.email.enabled,
                'configured': False if self.config.email.enabled else 'N/A'
            }
        
        if self.scheduler:
            status['scheduler'] = self.scheduler.get_status()
        
        return status
    
    def _check_ollama_status(self) -> dict:
        """Check detailed Ollama connection and model status"""
        try:
            import requests
            
            # Test basic connection
            response = requests.get(f"{self.config.ollama.url}/api/tags", timeout=5)
            
            if response.status_code != 200:
                return {
                    'connected': False,
                    'error': f'Server returned status {response.status_code}',
                    'url': self.config.ollama.url
                }
            
            # Get available models
            models_data = response.json()
            models = models_data.get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            # Check if our model is available
            model_available = any(self.config.ollama.model in name for name in model_names)
            
            # Test model generation (quick test)
            generation_test = False
            generation_error = None
            
            if model_available:
                try:
                    test_payload = {
                        "model": self.config.ollama.model,
                        "prompt": "Say 'OK'",
                        "stream": False
                    }
                    
                    test_response = requests.post(
                        f"{self.config.ollama.url}/api/generate",
                        json=test_payload,
                        timeout=10
                    )
                    
                    if test_response.status_code == 200:
                        result = test_response.json().get('response', '').strip()
                        generation_test = len(result) > 0
                    else:
                        generation_error = f"Generation test failed: HTTP {test_response.status_code}"
                        
                except Exception as e:
                    generation_error = f"Generation test error: {str(e)}"
            
            return {
                'connected': True,
                'url': self.config.ollama.url,
                'model': self.config.ollama.model,
                'model_available': model_available,
                'available_models': model_names,
                'generation_test': generation_test,
                'generation_error': generation_error,
                'status': 'healthy' if (model_available and generation_test) else 'issues_detected'
            }
            
        except requests.exceptions.ConnectionError:
            return {
                'connected': False,
                'error': 'Cannot connect to Ollama server',
                'url': self.config.ollama.url,
                'suggestion': 'Check if Ollama is running'
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'url': self.config.ollama.url
            }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.stop_service()
        logging.info("👋 Mail Pilot Service stopped")
        sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mail Pilot - AI Email Summary Service')
    parser.add_argument('--config', default='../.env', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once instead of scheduling')
    parser.add_argument('--menu', action='store_true', help='Run once with interactive menu')
    parser.add_argument('--status', action='store_true', help='Show service status')
    
    args = parser.parse_args()
    
    try:
        service = MailPilotService(config_file=args.config)
        
        if args.status:
            status = service.get_status()
            print(f"Service Status: {status}")
            return
        
        if args.menu:
            success = service.run_once_with_menu()
            sys.exit(0 if success else 1)
        elif args.once:
            success = service.run_once()
            sys.exit(0 if success else 1)
        else:
            service.start_service()
            
    except Exception as e:
        logging.error(f"Service failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()