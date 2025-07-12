#!/usr/bin/env python3

"""
Mail Pilot Web Application
Flask web interface for Gmail registration and manual email processing
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
import tempfile
import threading
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import load_config, AppConfig
from src.gmail_client import GmailClient
from src.ollama_client import OllamaClient
from src.email_processor import EmailProcessor
from src.email_sender import EmailSender
from src.voice_generator import VoiceGenerator
from src.scheduler import EmailSummaryScheduler

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'mailpilot:'
Session(app)

# Global service instance
mail_service = None
scheduler = None
processing_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'error': None
}

class WebMailPilotService:
    """Web-enabled version of MailPilotService"""
    
    def __init__(self):
        self.config = None
        self.gmail_client = None
        self.ollama_client = None
        self.email_processor = None
        self.email_sender = None
        self.voice_generator = None
        self.initialized = False
    
    def initialize_from_session(self, session_data):
        """Initialize service from web session data"""
        try:
            # Create temporary config
            self.config = self._create_config_from_session(session_data)
            
            # Initialize components
            self.gmail_client = GmailClient(
                credentials_path=session_data.get('credentials_path'),
                token_path=session_data.get('token_path')
            )
            
            self.ollama_client = OllamaClient(
                base_url=session_data.get('ollama_url', 'http://localhost:11434'),
                model=session_data.get('ollama_model', 'llama3.1')
            )
            
            if not self.ollama_client.test_connection():
                raise Exception("Could not connect to Ollama service")
            
            self.email_processor = EmailProcessor(
                gmail_client=self.gmail_client,
                ollama_client=self.ollama_client
            )
            
            self.email_sender = EmailSender(
                smtp_server=session_data.get('smtp_server', 'smtp.gmail.com'),
                smtp_port=int(session_data.get('smtp_port', 587)),
                email_address=session_data.get('email_address'),
                email_password=session_data.get('email_password')
            )
            
            self.voice_generator = VoiceGenerator(
                language=session_data.get('voice_language', 'en'),
                enabled=session_data.get('voice_enabled', True)
            )
            
            self.initialized = True
            logging.info("Web service initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize web service: {e}")
            return False
    
    def _create_config_from_session(self, session_data):
        """Create a config object from session data"""
        # This is a simplified config for web usage
        class WebConfig:
            def __init__(self, data):
                self.email_address = data.get('email_address')
                self.voice_enabled = data.get('voice_enabled', True)
                self.voice_language = data.get('voice_language', 'en')
        
        return WebConfig(session_data)
    
    def process_emails_async(self):
        """Process emails asynchronously for web interface"""
        global processing_status
        
        try:
            processing_status['running'] = True
            processing_status['error'] = None
            
            # Process emails
            result = self.email_processor.process_unread_emails()
            
            if result['total_emails'] > 0:
                # Generate summaries
                text_summary = self.email_processor.format_email_summary_text(result)
                html_summary = self.email_processor.format_email_summary_html(result)
                
                # Generate voice if enabled
                voice_file_path = None
                if self.config.voice_enabled:
                    voice_text = self.voice_generator.create_voice_summary_text(result)
                    voice_file_path = self.voice_generator.generate_voice_summary(voice_text)
                
                # Send email
                success = self.email_sender.send_summary_email(
                    recipient=self.config.email_address,
                    text_summary=text_summary,
                    html_summary=html_summary,
                    voice_file_path=voice_file_path
                )
                
                # Cleanup
                if voice_file_path:
                    self.voice_generator.cleanup_temp_file(voice_file_path)
                
                processing_status['last_result'] = {
                    'success': success,
                    'total_emails': result['total_emails'],
                    'high_priority': result['high_priority_count'],
                    'action_items': result['action_items_total'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                processing_status['last_result'] = {
                    'success': True,
                    'total_emails': 0,
                    'message': 'No unread emails found',
                    'timestamp': datetime.now().isoformat()
                }
            
            processing_status['last_run'] = datetime.now().isoformat()
            
        except Exception as e:
            logging.error(f"Email processing error: {e}")
            processing_status['error'] = str(e)
            processing_status['last_result'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            processing_status['running'] = False

# Initialize global service
mail_service = WebMailPilotService()

@app.route('/')
def index():
    """Home page - check if user is registered"""
    if 'gmail_registered' in session and session['gmail_registered']:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register')
def register():
    """Gmail registration page"""
    return render_template('register.html')

@app.route('/oauth/gmail')
def oauth_gmail():
    """Start Gmail OAuth flow"""
    try:
        # Clear any existing session data
        session.clear()
        
        # Create temporary credentials for OAuth
        temp_dir = tempfile.mkdtemp()
        credentials_path = os.path.join(temp_dir, 'credentials.json')
        token_path = os.path.join(temp_dir, 'token.json')
        
        # Check if credentials.json exists one folder above (for privacy)
        project_credentials = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if not os.path.exists(project_credentials):
            flash('Gmail API credentials not found. Please set up credentials.json first.', 'error')
            return redirect(url_for('register'))
        
        # Copy credentials to temp location
        import shutil
        shutil.copy2(project_credentials, credentials_path)
        
        # Store paths in session
        session['temp_dir'] = temp_dir
        session['credentials_path'] = credentials_path
        session['token_path'] = token_path
        
        # Initiate OAuth flow
        gmail_client = GmailClient(credentials_path, token_path)
        
        # If we get here, OAuth was successful
        session['gmail_registered'] = True
        session['email_address'] = gmail_client.service.users().getProfile(userId='me').execute().get('emailAddress')
        
        flash('Gmail registration successful!', 'success')
        return redirect(url_for('setup'))
        
    except Exception as e:
        logging.error(f"Gmail OAuth error: {e}")
        flash(f'Gmail registration failed: {str(e)}', 'error')
        return redirect(url_for('register'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Service configuration setup"""
    if 'gmail_registered' not in session:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        # Save configuration to session
        session.update({
            'email_password': request.form.get('email_password'),
            'ollama_url': request.form.get('ollama_url', 'http://localhost:11434'),
            'ollama_model': request.form.get('ollama_model', 'llama3.1'),
            'smtp_server': request.form.get('smtp_server', 'smtp.gmail.com'),
            'smtp_port': request.form.get('smtp_port', '587'),
            'voice_enabled': 'voice_enabled' in request.form,
            'voice_language': request.form.get('voice_language', 'en'),
            'setup_complete': True
        })
        
        flash('Configuration saved successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('setup.html', 
                         email_address=session.get('email_address', ''))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if not session.get('gmail_registered') or not session.get('setup_complete'):
        return redirect(url_for('register'))
    
    return render_template('dashboard.html',
                         email_address=session.get('email_address'),
                         processing_status=processing_status)

@app.route('/api/process-emails', methods=['POST'])
def api_process_emails():
    """API endpoint to manually trigger email processing"""
    if not session.get('gmail_registered') or not session.get('setup_complete'):
        return jsonify({'error': 'Not registered or configured'}), 400
    
    if processing_status['running']:
        return jsonify({'error': 'Processing already in progress'}), 400
    
    try:
        # Initialize service from session
        if not mail_service.initialize_from_session(session):
            return jsonify({'error': 'Failed to initialize service'}), 500
        
        # Start processing in background thread
        thread = threading.Thread(target=mail_service.process_emails_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Email processing started', 'status': 'running'})
        
    except Exception as e:
        logging.error(f"API process emails error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Get current processing status"""
    return jsonify(processing_status)

@app.route('/api/test-ollama')
def api_test_ollama():
    """Test Ollama connection"""
    try:
        ollama_url = session.get('ollama_url', 'http://localhost:11434')
        ollama_model = session.get('ollama_model', 'llama3.1')
        
        ollama_client = OllamaClient(ollama_url, ollama_model)
        connected = ollama_client.test_connection()
        
        return jsonify({
            'connected': connected,
            'url': ollama_url,
            'model': ollama_model
        })
        
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

@app.route('/logout')
def logout():
    """Clear session and logout"""
    # Cleanup temp files
    temp_dir = session.get('temp_dir')
    if temp_dir and os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)