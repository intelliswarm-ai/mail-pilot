#!/usr/bin/env python3
"""
Email Processing Service - Backend API for Mail Pilot
Provides menu-driven email processing functionality via REST API
"""

import logging
import threading
import time
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from .config import load_config
from .gmail_client import GmailClient
from .ollama_client import OllamaClient
from .email_processor import EmailProcessor
from .email_sender import EmailSender
from .voice_generator import VoiceGenerator
from .file_saver import FileSaver
from .email_menu import EmailMenu
from .progress_tracker import progress_tracker


class EmailProcessingService:
    """
    Backend service that replicates the CLI menu-driven email processing
    and exposes it via REST API for the web application
    """
    
    def __init__(self, config_file: str = '../.env'):
        self.config = load_config(config_file)
        self.gmail_client = None
        self.ollama_client = None
        self.email_processor = None
        self.email_sender = None
        self.voice_generator = None
        self.file_saver = None
        self.menu = EmailMenu()
        
        # Flask app for API endpoints
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_api_routes()
        
        # Processing state
        self.processing_thread = None
        self.is_initialized = False
        
    def initialize_services(self) -> bool:
        """Initialize all email processing services"""
        try:
            logging.info("🔧 Initializing Email Processing Service...")
            
            # Initialize Gmail client
            logging.info("🔐 Starting Gmail authentication process...")
            self.gmail_client = GmailClient(
                credentials_path=self.config.gmail.credentials_path,
                token_path=self.config.gmail.token_path
            )
            
            # Initialize Ollama client
            logging.info("⏳ Testing Ollama connection...")
            self.ollama_client = OllamaClient(
                base_url=self.config.ollama.url,
                model=self.config.ollama.model
            )
            
            if not self.ollama_client.test_connection():
                logging.error("❌ Failed to connect to Ollama service")
                return False
                
            # Initialize email processor
            self.email_processor = EmailProcessor(
                gmail_client=self.gmail_client,
                ollama_client=self.ollama_client
            )
            
            # Initialize optional services
            if self.config.email.enabled:
                self.email_sender = EmailSender(
                    smtp_server=self.config.email.smtp_server,
                    smtp_port=self.config.email.smtp_port,
                    email_address=self.config.email.email_address,
                    email_password=self.config.email.email_password
                )
            
            self.voice_generator = VoiceGenerator(
                language=self.config.voice.language,
                enabled=self.config.voice.enabled
            )
            
            self.file_saver = FileSaver()
            
            self.is_initialized = True
            logging.info("✅ Email Processing Service initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Email Processing Service: {e}")
            return False
    
    def _setup_api_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/api/service-info', methods=['GET'])
        def get_service_info():
            """Get service information and initialization status"""
            try:
                gmail_connected = self.gmail_client is not None
                ollama_connected = self.ollama_client is not None and self.ollama_client.test_connection()
                
                return jsonify({
                    'service': 'Email Processing Service',
                    'version': '1.0.0',
                    'initialized': self.is_initialized,
                    'gmail_connected': gmail_connected,
                    'ollama_connected': ollama_connected,
                    'config': {
                        'ollama_model': self.config.ollama.model,
                        'voice_enabled': self.config.voice.enabled,
                        'email_enabled': self.config.email.enabled
                    }
                }), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/timeframe-options', methods=['GET'])
        def get_timeframe_options():
            """Get available timeframe options (replicates CLI menu)"""
            return jsonify({
                'timeframes': [
                    {'id': 1, 'label': 'Last 12 hours', 'hours': 12},
                    {'id': 2, 'label': 'Last 24 hours', 'hours': 24},
                    {'id': 3, 'label': 'Last 48 hours', 'hours': 48},
                    {'id': 4, 'label': 'Last 3 days', 'hours': 72},
                    {'id': 5, 'label': 'Last 7 days', 'hours': 168},
                    {'id': 6, 'label': 'All unread emails', 'hours': 0}
                ]
            }), 200
        
        @self.app.route('/api/processing-options', methods=['GET'])
        def get_processing_options():
            """Get available processing options (replicates CLI menu)"""
            return jsonify({
                'categorization_methods': [
                    {
                        'id': 'none',
                        'label': 'Process all emails together',
                        'description': 'Basic processing without categorization'
                    },
                    {
                        'id': 'enhanced',
                        'label': 'Use intelligent NLP clustering (recommended)',
                        'description': 'TF-IDF vectorization + adaptive clustering\\nCreates categories like Professional, GitHub, Shopping, etc.\\nFast and efficient processing'
                    },
                    {
                        'id': 'llm',
                        'label': 'Use hybrid categorization (best of both worlds)',
                        'description': 'Fast clustering with Enhanced NLP\\nIntelligent category naming with LLM\\nOptimal balance of speed and accuracy'
                    }
                ],
                'voice_options': [
                    {'id': True, 'label': 'Enable voice summaries'},
                    {'id': False, 'label': 'Disable voice summaries'}
                ],
                'detail_levels': [
                    {'id': 'brief', 'label': 'Brief summaries (faster)'},
                    {'id': 'detailed', 'label': 'Detailed summaries (slower)'}
                ]
            }), 200
        
        @self.app.route('/api/start-processing', methods=['POST'])
        def start_processing():
            """Start email processing with specified options (replicates CLI flow)"""
            try:
                if not self.is_initialized:
                    if not self.initialize_services():
                        return jsonify({'error': 'Failed to initialize services'}), 500
                
                # Check if already processing
                current_state = progress_tracker.get_state()
                if current_state.get('is_running', False):
                    return jsonify({'error': 'Processing already in progress'}), 409
                
                # Get request data
                data = request.get_json() or {}
                timeframe_hours = data.get('timeframe_hours', 24)
                categorization_method = data.get('categorization_method', 'enhanced')
                voice_enabled = data.get('voice_enabled', True)
                detail_level = data.get('detail_level', 'brief')
                
                # Validate options
                if categorization_method not in ['none', 'enhanced', 'llm']:
                    return jsonify({'error': 'Invalid categorization method'}), 400
                
                # Build query like CLI does
                query = self.menu.calculate_date_query(timeframe_hours)
                timeframe_desc = self.menu.get_timeframe_description(timeframe_hours)
                
                # Build processing options
                processing_options = {
                    'categorize_emails': categorization_method != 'none',
                    'categorization_method': categorization_method,
                    'voice_enabled': voice_enabled and self.config.voice.enabled,
                    'detailed_summaries': detail_level == 'detailed'
                }
                
                # Log the processing start (like CLI does)
                logging.info("=" * 80)
                logging.info("📧 MAIL PILOT - EMAIL PROCESSING STARTED")
                logging.info("=" * 80)
                logging.info(f"📅 Timeframe: {timeframe_desc}")
                logging.info(f"🔬 Method: {categorization_method}")
                logging.info(f"🎵 Voice: {'Enabled' if processing_options['voice_enabled'] else 'Disabled'}")
                logging.info(f"📝 Detail: {detail_level}")
                logging.info("=" * 80)
                
                # Start processing in background thread
                self.processing_thread = threading.Thread(
                    target=self._background_process_emails,
                    args=(query, processing_options, timeframe_desc),
                    daemon=True
                )
                self.processing_thread.start()
                
                return jsonify({
                    'status': 'processing_started',
                    'message': f'Starting email processing for {timeframe_desc}',
                    'query': query,
                    'options': processing_options,
                    'timeframe_description': timeframe_desc
                }), 200
                
            except Exception as e:
                logging.error(f"Failed to start processing: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/processing-status', methods=['GET'])
        def get_processing_status():
            """Get current processing status and progress"""
            try:
                state = progress_tracker.get_state()
                
                # Add service-specific information
                state['service_initialized'] = self.is_initialized
                state['gmail_connected'] = self.gmail_client is not None
                state['ollama_connected'] = self.ollama_client is not None
                
                return jsonify(state), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop-processing', methods=['POST'])
        def stop_processing():
            """Stop current processing"""
            try:
                current_state = progress_tracker.get_state()
                if not current_state.get('is_running', False):
                    return jsonify({'error': 'No processing currently running'}), 400
                
                # Set error state to stop processing
                progress_tracker.set_error("Processing stopped by user request")
                
                return jsonify({
                    'status': 'stop_requested',
                    'message': 'Processing stop requested'
                }), 200
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _background_process_emails(self, query: str, options: Dict, timeframe_desc: str):
        """Background email processing (replicates CLI processing)"""
        try:
            # Initialize progress tracking
            progress_tracker.start_processing()
            progress_tracker.update_stage('initializing', 0, f'Starting processing for {timeframe_desc}')
            
            logging.info(f"🚀 Starting email processing for {timeframe_desc}...")
            
            # Process emails using the same logic as CLI
            result = self.email_processor.process_unread_emails(query, options)
            
            if result['total_emails'] == 0:
                progress_tracker.complete_processing({
                    'total_emails': 0,
                    'message': 'No emails found for the specified timeframe'
                })
                return
            
            # Generate summaries like CLI does
            progress_tracker.update_stage('generating', 80, 'Generating summaries...')
            
            text_summary = self.email_processor.format_email_summary_text(result)
            html_summary = self.email_processor.format_email_summary_html(result)
            
            # Generate voice summary if enabled
            voice_file_path = None
            if options.get('voice_enabled', False):
                progress_tracker.update_stage('generating', 85, 'Generating voice summary...')
                voice_text = self.voice_generator.create_voice_summary_text(result)
                voice_file_path = self.voice_generator.generate_voice_summary(voice_text)
            
            # Save summaries like CLI does
            progress_tracker.update_stage('saving', 90, 'Saving summaries...')
            saved_files = self.file_saver.save_summary(result, text_summary, html_summary, voice_file_path)
            
            # Send email if enabled
            if self.config.email.enabled and self.email_sender:
                progress_tracker.update_stage('sending', 95, 'Sending email summary...')
                self.email_sender.send_summary_email(
                    recipient=self.config.email.email_address,
                    text_summary=text_summary,
                    html_summary=html_summary,
                    voice_file_path=voice_file_path
                )
            
            # Cleanup
            if voice_file_path:
                self.voice_generator.cleanup_temp_file(voice_file_path)
            
            # Complete processing
            final_result = {
                'total_emails': result['total_emails'],
                'categories': len(result.get('categorized_emails', {})),
                'email_summaries': result.get('email_summaries', []),
                'saved_files': saved_files,
                'processing_time': result.get('processing_time', 'Unknown'),
                'timeframe_description': timeframe_desc
            }
            
            progress_tracker.complete_processing(final_result)
            
            logging.info("=" * 80)
            logging.info("📧 EMAIL PROCESSING COMPLETED SUCCESSFULLY")
            logging.info("=" * 80)
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"❌ Background processing error: {error_msg}")
            progress_tracker.set_error(error_msg)
    
    def start_api_server(self, host='0.0.0.0', port=5002):
        """Start the Flask API server"""
        logging.info(f"🚀 Starting Email Processing Service API")
        logging.info(f"🌐 Server: {host}:{port}")
        logging.info("📡 Available endpoints:")
        logging.info("   GET  /api/service-info")
        logging.info("   GET  /api/timeframe-options")
        logging.info("   GET  /api/processing-options")
        logging.info("   POST /api/start-processing")
        logging.info("   GET  /api/processing-status")
        logging.info("   POST /api/stop-processing")
        logging.info("=" * 50)
        
        try:
            self.app.run(host=host, port=port, debug=False, threaded=True)
        except Exception as e:
            logging.error(f"API server error: {e}")


def main():
    """Main entry point for the Email Processing Service"""
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Email Processing Service - Backend API')
    parser.add_argument('--config', default='../.env', help='Configuration file path')
    parser.add_argument('--port', type=int, default=5002, help='API server port (default: 5002)')
    parser.add_argument('--host', default='0.0.0.0', help='API server host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    try:
        service = EmailProcessingService(config_file=args.config)
        service.start_api_server(host=args.host, port=args.port)
        
    except KeyboardInterrupt:
        logging.info("👋 Email Processing Service stopped by user")
    except Exception as e:
        logging.error(f"Service failed: {e}")


if __name__ == '__main__':
    main()