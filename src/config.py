import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import logging

@dataclass
class GmailConfig:
    credentials_path: str
    token_path: str

@dataclass  
class OllamaConfig:
    url: str
    model: str

@dataclass
class EmailConfig:
    enabled: bool
    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str

@dataclass
class SchedulerConfig:
    interval_hours: int

@dataclass
class VoiceConfig:
    enabled: bool
    language: str

@dataclass
class AppConfig:
    gmail: GmailConfig
    ollama: OllamaConfig
    email: EmailConfig
    scheduler: SchedulerConfig
    voice: VoiceConfig
    log_level: str

class ConfigManager:
    def __init__(self, env_file: str = '../.env'):
        self.env_file = env_file
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            logging.info(f"Loaded environment from {self.env_file}")
        else:
            logging.warning(f"Environment file {self.env_file} not found, using system environment")
    
    def get_config(self) -> AppConfig:
        """Get complete application configuration"""
        
        # Gmail configuration
        gmail_config = GmailConfig(
            credentials_path=self._get_env('GMAIL_CREDENTIALS_PATH', '../credentials.json'),
            token_path=self._get_env('GMAIL_TOKEN_PATH', '../token.json')
        )
        
        # Ollama configuration
        ollama_url = self._get_env('OLLAMA_URL', 'http://localhost:11434')
        ollama_model = self._get_env('OLLAMA_MODEL', 'mistral')
        
        # Debug output
        logging.info(f"🤖 Ollama URL: {ollama_url}")
        logging.info(f"🤖 Ollama Model: {ollama_model}")
        
        ollama_config = OllamaConfig(
            url=ollama_url,
            model=ollama_model
        )
        
        # Email configuration
        email_enabled = self._get_env('EMAIL_SENDING_ENABLED', 'false').lower() == 'true'
        email_config = EmailConfig(
            enabled=email_enabled,
            smtp_server=self._get_env('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(self._get_env('SMTP_PORT', '587')),
            email_address=self._get_env('EMAIL_ADDRESS', '') if email_enabled else '',
            email_password=self._get_env('EMAIL_PASSWORD', '') if email_enabled else ''
        )
        
        # Scheduler configuration
        scheduler_config = SchedulerConfig(
            interval_hours=int(self._get_env('SUMMARY_INTERVAL', '6'))
        )
        
        # Voice configuration
        voice_config = VoiceConfig(
            enabled=self._get_env('VOICE_ENABLED', 'true').lower() == 'true',
            language=self._get_env('VOICE_LANGUAGE', 'en')
        )
        
        return AppConfig(
            gmail=gmail_config,
            ollama=ollama_config,
            email=email_config,
            scheduler=scheduler_config,
            voice=voice_config,
            log_level=self._get_env('LOG_LEVEL', 'DEBUG')
        )
    
    def _get_env(self, key: str, default: str = None) -> str:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is required")
        return value
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def validate_config(self, config: AppConfig) -> bool:
        """Validate configuration values"""
        errors = []
        
        # Validate Gmail config - handle relative paths properly
        credentials_path = config.gmail.credentials_path
        if not os.path.isabs(credentials_path):
            # For relative paths, resolve from the current working directory
            credentials_path = os.path.abspath(credentials_path)
        
        if not os.path.exists(credentials_path):
            errors.append(f"Gmail credentials file not found: {config.gmail.credentials_path} (resolved to: {credentials_path})")
        
        # Validate scheduler interval
        if config.scheduler.interval_hours < 1 or config.scheduler.interval_hours > 24:
            errors.append("Scheduler interval must be between 1 and 24 hours")
        
        # Validate email config (only if email sending is enabled)
        if config.email.enabled:
            if not config.email.email_address or '@' not in config.email.email_address:
                errors.append("Invalid email address (required when EMAIL_SENDING_ENABLED=true)")
            
            if not config.email.email_password:
                errors.append("Email password is required (required when EMAIL_SENDING_ENABLED=true)")
        
        # Validate voice language
        valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        if config.voice.language not in valid_languages:
            logging.warning(f"Voice language '{config.voice.language}' may not be supported")
        
        if errors:
            for error in errors:
                logging.error(f"Configuration error: {error}")
            return False
        
        logging.info("Configuration validation passed")
        return True
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mail_pilot.log'),
                logging.StreamHandler()
            ]
        )
        
        logging.info(f"Logging configured with level: {log_level}")


def load_config(env_file: str = '../.env') -> AppConfig:
    """Convenience function to load and validate configuration"""
    config_manager = ConfigManager(env_file)
    config = config_manager.get_config()
    
    # Setup logging
    config_manager.setup_logging(config.log_level)
    
    # Validate configuration
    if not config_manager.validate_config(config):
        raise ValueError("Configuration validation failed")
    
    return config