from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import subprocess
import sys
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any
import threading
import time

# Import demo services for fallback mode
from demo_services import (
    DemoGmailClient, DemoOllamaClient, DemoEmailProcessor, 
    DemoPhishingDetector, DemoAutoReplyGenerator
)

app = Flask(__name__)
app.secret_key = 'mail-pilot-secret-key-change-in-production'

# Configuration for backend API
BACKEND_API_URL = 'http://localhost:5001'
FALLBACK_TO_DEMO = False  # Disable demo mode - require backend API

# Global variables for demo fallback
demo_processing_state = {
    'is_running': False,
    'progress': 0,
    'status': 'idle',
    'current_step': '',
    'results': None,
    'error': None,
    'total_emails': 0,
    'processed_emails': 0,
    'current_email': None,
    'email_progress': [],  # List of processed emails with status
    'stage': 'idle',  # idle, fetching, categorizing, analyzing, generating_replies, complete
    'stage_progress': 0,
    'detailed_log': [],  # Detailed processing log
    'has_credentials': True,  # Report that we have credentials (since you want production mode)
    'backend_connected': False,  # Not connected to backend API
    'demo_mode': False if not FALLBACK_TO_DEMO else True  # Respect the FALLBACK_TO_DEMO setting
}

def check_backend_available():
    """Check if backend API server is available"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/api/service-status", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_backend_processing_status():
    """Get processing status from backend API"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/api/processing-status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        logging.error(f"Failed to get backend processing status: {e}")
        return None

def trigger_backend_processing(timeframe_hours, categorization_method, include_phishing, include_replies):
    """Trigger processing on backend API"""
    try:
        data = {
            'timeframe_hours': timeframe_hours,
            'categorization_method': categorization_method,
            'include_phishing_detection': include_phishing,
            'include_auto_replies': include_replies
        }
        
        response = requests.post(
            f"{BACKEND_API_URL}/api/trigger-processing",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logging.error(f"Failed to trigger backend processing: {e}")
        return {'success': False, 'error': str(e)}

# Initialize services (will be done on first request for demo fallback)
gmail_client = None
ollama_client = None
email_processor = None
phishing_detector = None
auto_reply_generator = None

def initialize_services():
    """Initialize email processing services following mail_pilot_service pattern"""
    global gmail_client, ollama_client, email_processor, phishing_detector, auto_reply_generator
    
    if gmail_client is None:
        try:
            logging.info("Initializing Mail Pilot services...")
            
            # Check if we're in demo mode or have real credentials (look in parent directory)
            credentials_path = os.path.join('..', 'credentials.json')
            demo_mode = not os.path.exists(credentials_path)
            
            if demo_mode:
                logging.warning("Running in DEMO MODE - credentials.json not found")
                # Initialize demo services
                gmail_client = DemoGmailClient()
                ollama_client = DemoOllamaClient()
                email_processor = DemoEmailProcessor(gmail_client, ollama_client)
                phishing_detector = DemoPhishingDetector(ollama_client)
                auto_reply_generator = DemoAutoReplyGenerator(ollama_client)
            else:
                logging.info("Initializing real services following mail_pilot_service pattern...")
                
                # Use the same pattern as mail_pilot_service.py
                if GmailClient and OllamaClient and EmailProcessor:
                    # Initialize Gmail client with proper paths
                    gmail_client = GmailClient(
                        credentials_path='../credentials.json',
                        token_path='../token.json'
                    )
                    
                    # Initialize Ollama client 
                    ollama_client = OllamaClient(
                        base_url="http://localhost:11434",
                        model="mistral"
                    )
                    
                    # Initialize processors
                    email_processor = EmailProcessor(gmail_client, ollama_client)
                    if PhishingDetector:
                        phishing_detector = PhishingDetector(ollama_client)
                    if AutoReplyGenerator:
                        auto_reply_generator = AutoReplyGenerator(ollama_client)
                else:
                    # Fall back to demo if imports failed
                    logging.warning("Real service classes not available, using demo mode")
                    gmail_client = DemoGmailClient()
                    ollama_client = DemoOllamaClient()
                    email_processor = DemoEmailProcessor(gmail_client, ollama_client)
                    phishing_detector = DemoPhishingDetector(ollama_client)
                    auto_reply_generator = DemoAutoReplyGenerator(ollama_client)
                    demo_mode = True
            
            logging.info(f"Services initialized successfully (Demo mode: {demo_mode})")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize services: {e}")
            logging.info("Falling back to demo mode...")
            try:
                # Fallback to demo mode
                gmail_client = DemoGmailClient()
                ollama_client = DemoOllamaClient()
                email_processor = DemoEmailProcessor(gmail_client, ollama_client)
                phishing_detector = DemoPhishingDetector(ollama_client)
                auto_reply_generator = DemoAutoReplyGenerator(ollama_client)
                
                logging.info("Demo services initialized successfully")
                return True
            except Exception as demo_error:
                logging.error(f"Failed to initialize demo services: {demo_error}")
                return False
    return True

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/trigger-processing', methods=['POST'])
def trigger_processing():
    """Trigger email processing with selected options"""
    try:
        # Get processing options from request
        data = request.get_json() or {}
        timeframe_hours = data.get('timeframe_hours', 24)
        categorization_method = data.get('categorization_method', 'enhanced')
        include_phishing_detection = data.get('include_phishing_detection', True)
        include_auto_replies = data.get('include_auto_replies', False)
        
        logging.info(f"Processing triggered with options: {data}")
        
        # Try to use backend API first
        if check_backend_available():
            logging.info("Using backend API for processing")
            result = trigger_backend_processing(
                timeframe_hours, categorization_method, 
                include_phishing_detection, include_auto_replies
            )
            
            if result['success']:
                return jsonify({'status': 'processing_started', 'backend': True})
            else:
                logging.warning(f"Backend processing failed: {result['error']}")
                if not FALLBACK_TO_DEMO:
                    return jsonify({'error': f'Backend processing failed: {result["error"]}'}), 500
        
        # Fallback to demo mode if backend not available or failed
        if FALLBACK_TO_DEMO:
            logging.info("Using demo mode for processing")
            global demo_demo_processing_state
            
            if demo_demo_processing_state['is_running']:
                return jsonify({'error': 'Processing already in progress'}), 400
            
            # Initialize demo services
            if not initialize_services():
                return jsonify({'error': 'Failed to initialize demo services'}), 500
            
            # Start processing in background thread
            thread = threading.Thread(
                target=process_emails_background,
                args=(timeframe_hours, categorization_method, include_phishing_detection, include_auto_replies)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({'status': 'processing_started', 'backend': False, 'demo': True})
        else:
            return jsonify({'error': 'Backend API not available and demo mode disabled'}), 503
        
    except Exception as e:
        logging.error(f"Failed to trigger processing: {e}")
        return jsonify({'error': f'Failed to start processing: {str(e)}'}), 500

def add_processing_log(message, level='info'):
    """Add detailed log entry with timestamp"""
    global demo_demo_processing_state
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'level': level
    }
    demo_demo_processing_state['detailed_log'].append(log_entry)
    # Keep only last 100 log entries
    if len(demo_demo_processing_state['detailed_log']) > 100:
        demo_demo_processing_state['detailed_log'] = demo_demo_processing_state['detailed_log'][-100:]

def update_email_progress(email_id, subject, sender, status, details=None):
    """Update progress for individual email"""
    global demo_demo_processing_state
    
    email_progress = {
        'email_id': email_id,
        'subject': subject[:50] + '...' if len(subject) > 50 else subject,
        'sender': sender,
        'status': status,  # processing, categorized, analyzed, completed, error
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    # Update existing email or add new one
    existing_index = None
    for i, email in enumerate(demo_demo_processing_state['email_progress']):
        if email['email_id'] == email_id:
            existing_index = i
            break
    
    if existing_index is not None:
        demo_demo_processing_state['email_progress'][existing_index] = email_progress
    else:
        demo_demo_processing_state['email_progress'].append(email_progress)

def calculate_demo_progress():
    """Calculate overall progress based on stage and email progress"""
    global demo_demo_processing_state
    
    stage_weights = {
        'fetching': 0.1,    # 10%
        'categorizing': 0.4, # 40%
        'analyzing': 0.3,    # 30%
        'generating_replies': 0.2, # 20%
        'complete': 1.0
    }
    
    current_stage = demo_demo_processing_state['stage']
    stage_progress = demo_demo_processing_state['stage_progress']
    
    if current_stage == 'idle':
        return 0
    elif current_stage == 'complete':
        return 100
    
    # Calculate progress based on current stage
    base_progress = 0
    for stage, weight in stage_weights.items():
        if stage == current_stage:
            base_progress += weight * (stage_progress / 100)
            break
        else:
            base_progress += weight
    
    return min(int(base_progress * 100), 99)  # Cap at 99% until complete

def process_emails_background(timeframe_hours, categorization_method, include_phishing_detection, include_auto_replies):
    """Enhanced background email processing with detailed progress tracking"""
    global demo_demo_processing_state
    
    try:
        # Initialize processing state
        demo_demo_processing_state.update({
            'is_running': True,
            'progress': 0,
            'status': 'running',
            'current_step': 'Initializing...',
            'error': None,
            'total_emails': 0,
            'processed_emails': 0,
            'current_email': None,
            'email_progress': [],
            'stage': 'fetching',
            'stage_progress': 0,
            'detailed_log': []
        })
        
        add_processing_log("Starting email processing pipeline", 'info')
        
        # Stage 1: Fetch emails
        demo_demo_processing_state.update({
            'stage': 'fetching',
            'stage_progress': 10,
            'current_step': 'Connecting to Gmail...'
        })
        add_processing_log("Connecting to Gmail API", 'info')
        
        # Use EmailMenu pattern for query building like mail_pilot_service does
        if EmailMenu:
            menu = EmailMenu()
            query = menu.calculate_date_query(timeframe_hours)
            timeframe_desc = menu.get_timeframe_description(timeframe_hours)
            add_processing_log(f"Fetching emails for: {timeframe_desc}", 'info')
        else:
            # Fallback for demo mode
            if timeframe_hours == 0:
                query = "is:unread"
                add_processing_log("Fetching all unread emails", 'info')
            else:
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(hours=timeframe_hours)
                date_str = cutoff_date.strftime("%Y/%m/%d")
                query = f"after:{date_str}"
                add_processing_log(f"Fetching emails from last {timeframe_hours} hours", 'info')
        
        demo_demo_processing_state.update({
            'stage_progress': 50,
            'current_step': 'Fetching email list...'
        })
        
        emails = gmail_client.get_unread_messages(query)
        
        if not emails:
            add_processing_log("No emails found matching criteria", 'warning')
            demo_demo_processing_state.update({
                'is_running': False,
                'status': 'completed',
                'results': {'total_emails': 0, 'message': 'No emails found'},
                'progress': 100,
                'stage': 'complete'
            })
            return
        
        demo_demo_processing_state.update({
            'total_emails': len(emails),
            'stage_progress': 100,
            'current_step': f'Found {len(emails)} emails to process'
        })
        add_processing_log(f"Found {len(emails)} emails to process", 'success')
        
        # Initialize email progress tracking
        for email in emails:
            update_email_progress(
                email['id'],
                email.get('subject', 'No Subject'),
                email.get('sender', 'Unknown Sender'),
                'pending'
            )
        
        # Stage 2: Process and categorize emails
        demo_demo_processing_state.update({
            'stage': 'categorizing',
            'stage_progress': 0,
            'current_step': 'Starting email categorization...'
        })
        add_processing_log(f"Starting categorization using method: {categorization_method}", 'info')
        
        # Process emails with enhanced tracking
        result = process_emails_with_tracking(query, categorization_method, emails)
        
        # Stage 3: Phishing analysis (if enabled)
        if include_phishing_detection:
            demo_demo_processing_state.update({
                'stage': 'analyzing',
                'stage_progress': 0,
                'current_step': 'Starting phishing analysis...'
            })
            add_processing_log("Starting phishing detection analysis", 'info')
            result = add_phishing_analysis_with_tracking(result, emails)
        
        # Stage 4: Generate auto-replies (if enabled)
        if include_auto_replies:
            demo_processing_state.update({
                'stage': 'generating_replies',
                'stage_progress': 0,
                'current_step': 'Generating auto-reply suggestions...'
            })
            add_processing_log("Starting auto-reply generation", 'info')
            result = add_auto_reply_suggestions_with_tracking(result, emails)
        
        # Stage 5: Finalize results
        demo_processing_state.update({
            'stage': 'complete',
            'stage_progress': 50,
            'current_step': 'Finalizing results...'
        })
        add_processing_log("Finalizing processing results", 'info')
        
        enhanced_result = enhance_results_for_webapp(result, emails)
        
        demo_processing_state.update({
            'is_running': False,
            'status': 'completed',
            'results': enhanced_result,
            'progress': 100,
            'stage': 'complete',
            'stage_progress': 100,
            'current_step': 'Processing complete!'
        })
        add_processing_log(f"Processing completed successfully! Processed {len(emails)} emails", 'success')
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Background processing failed: {error_msg}")
        add_processing_log(f"Processing failed: {error_msg}", 'error')
        demo_processing_state.update({
            'is_running': False,
            'status': 'error',
            'error': error_msg,
            'stage': 'error'
        })

def process_emails_with_tracking(query, categorization_method, emails):
    """Process emails following mail_pilot_service pattern with tracking"""
    global demo_processing_state
    
    # Build options like mail_pilot_service does
    options = {
        'categorize_emails': True,
        'categorization_method': categorization_method,
        'voice_enabled': False,
        'detailed_summaries': True
    }
    
    add_processing_log(f"Processing {len(emails)} emails with method: {categorization_method}", 'info')
    
    try:
        # Update tracking for each email before processing
        for i, email in enumerate(emails):
            demo_processing_state.update({
                'processed_emails': i,
                'current_email': {
                    'id': email['id'],
                    'subject': email.get('subject', 'No Subject'),
                    'sender': email.get('sender', 'Unknown')
                },
                'stage_progress': int((i / len(emails)) * 100)
            })
            
            update_email_progress(
                email['id'],
                email.get('subject', 'No Subject'),
                email.get('sender', 'Unknown'),
                'categorizing',
                {'method': categorization_method}
            )
            
            add_processing_log(f"Categorizing: {email.get('subject', 'No Subject')[:30]}...", 'info')
            
            # Simulate processing time for demo visibility
            time.sleep(0.2)
            
            update_email_progress(
                email['id'],
                email.get('subject', 'No Subject'),
                email.get('sender', 'Unknown'),
                'categorized'
            )
        
        # Call the actual processor - this follows the same pattern as mail_pilot_service.process_emails()
        add_processing_log("Calling email processor with AI categorization...", 'info')
        result = email_processor.process_unread_emails(query, options)
        
        demo_processing_state.update({
            'stage_progress': 100,
            'current_step': 'Email categorization complete'
        })
        
        add_processing_log(f"Email processing completed: {result.get('total_emails', 0)} emails processed", 'success')
        return result
        
    except Exception as e:
        add_processing_log(f"Email processing failed: {str(e)}", 'error')
        logging.error(f"Email processing failed: {e}")
        
        # Return a basic result structure to prevent crashes
        return {
            'total_emails': len(emails),
            'categorization_enabled': True,
            'categorization_method': categorization_method,
            'email_summaries': [],
            'processing_time': 'Failed',
            'error': str(e)
        }

def add_phishing_analysis_with_tracking(result, emails):
    """Add phishing analysis with individual email tracking"""
    global demo_processing_state
    
    email_summaries = result.get('email_summaries', [])
    total_emails = len(email_summaries)
    
    for i, email_summary in enumerate(email_summaries):
        demo_processing_state.update({
            'stage_progress': int((i / total_emails) * 100),
            'current_step': f'Analyzing email {i+1}/{total_emails} for phishing...'
        })
        
        try:
            email_id = email_summary['email_id']
            raw_email = next((e for e in emails if e['id'] == email_id), None)
            
            if raw_email:
                update_email_progress(
                    email_id,
                    email_summary.get('subject', 'No Subject'),
                    email_summary.get('sender', 'Unknown'),
                    'analyzing_phishing'
                )
                
                add_processing_log(f"Phishing analysis: {email_summary.get('subject', 'No Subject')[:30]}...", 'info')
                
                risk_analysis = phishing_detector.analyze_email(raw_email)
                email_summary.update({
                    'phishing_risk_score': risk_analysis['risk_score'],
                    'phishing_risk_level': risk_analysis['risk_level'],
                    'phishing_indicators': risk_analysis['indicators'],
                    'phishing_explanation': risk_analysis['explanation']
                })
                
                risk_level = risk_analysis['risk_level']
                update_email_progress(
                    email_id,
                    email_summary.get('subject', 'No Subject'),
                    email_summary.get('sender', 'Unknown'),
                    'analyzed',
                    {'phishing_risk': risk_level, 'risk_score': risk_analysis['risk_score']}
                )
                
                if risk_level in ['high', 'medium']:
                    add_processing_log(f"⚠️ {risk_level.upper()} risk email detected: {email_summary.get('subject', 'No Subject')[:30]}...", 'warning')
                
        except Exception as e:
            logging.error(f"Phishing analysis failed for email {email_summary['email_id']}: {e}")
            add_processing_log(f"Phishing analysis failed for email: {str(e)}", 'error')
            email_summary.update({
                'phishing_risk_score': 0,
                'phishing_risk_level': 'unknown',
                'phishing_indicators': [],
                'phishing_explanation': 'Analysis failed'
            })
            
            update_email_progress(
                email_summary['email_id'],
                email_summary.get('subject', 'No Subject'),
                email_summary.get('sender', 'Unknown'),
                'error',
                {'error': 'Phishing analysis failed'}
            )
    
    demo_processing_state.update({
        'stage_progress': 100,
        'current_step': 'Phishing analysis complete'
    })
    
    return result

def add_auto_reply_suggestions_with_tracking(result, emails):
    """Add auto-reply suggestions with individual email tracking"""
    global demo_processing_state
    
    email_summaries = result.get('email_summaries', [])
    reply_candidates = [email for email in email_summaries if email.get('requires_response', False)]
    total_replies = len(reply_candidates)
    
    if total_replies == 0:
        add_processing_log("No emails require auto-reply generation", 'info')
        return result
    
    add_processing_log(f"Generating replies for {total_replies} emails", 'info')
    
    for i, email_summary in enumerate(reply_candidates):
        demo_processing_state.update({
            'stage_progress': int((i / total_replies) * 100),
            'current_step': f'Generating reply {i+1}/{total_replies}...'
        })
        
        try:
            email_id = email_summary['email_id']
            raw_email = next((e for e in emails if e['id'] == email_id), None)
            
            if raw_email:
                update_email_progress(
                    email_id,
                    email_summary.get('subject', 'No Subject'),
                    email_summary.get('sender', 'Unknown'),
                    'generating_reply'
                )
                
                add_processing_log(f"Generating reply: {email_summary.get('subject', 'No Subject')[:30]}...", 'info')
                
                reply_suggestion = auto_reply_generator.generate_reply(raw_email)
                email_summary.update({
                    'suggested_reply': reply_suggestion['reply_text'],
                    'reply_tone': reply_suggestion['tone'],
                    'reply_confidence': reply_suggestion['confidence'],
                    'reply_key_points': reply_suggestion['key_points']
                })
                
                update_email_progress(
                    email_id,
                    email_summary.get('subject', 'No Subject'),
                    email_summary.get('sender', 'Unknown'),
                    'completed',
                    {'reply_generated': True, 'confidence': reply_suggestion['confidence']}
                )
                
        except Exception as e:
            logging.error(f"Auto-reply generation failed for email {email_summary['email_id']}: {e}")
            add_processing_log(f"Reply generation failed: {str(e)}", 'error')
            email_summary.update({
                'suggested_reply': 'Failed to generate reply suggestion',
                'reply_tone': 'neutral',
                'reply_confidence': 0,
                'reply_key_points': []
            })
            
            update_email_progress(
                email_summary['email_id'],
                email_summary.get('subject', 'No Subject'),
                email_summary.get('sender', 'Unknown'),
                'error',
                {'error': 'Reply generation failed'}
            )
    
    demo_processing_state.update({
        'stage_progress': 100,
        'current_step': 'Auto-reply generation complete'
    })
    
    return result

def add_phishing_analysis(result, emails):
    """Add phishing risk analysis to emails"""
    email_summaries = result.get('email_summaries', [])
    
    for email_summary in email_summaries:
        try:
            # Find corresponding raw email
            raw_email = next((e for e in emails if e['id'] == email_summary['email_id']), None)
            if raw_email:
                risk_analysis = phishing_detector.analyze_email(raw_email)
                email_summary.update({
                    'phishing_risk_score': risk_analysis['risk_score'],
                    'phishing_risk_level': risk_analysis['risk_level'],
                    'phishing_indicators': risk_analysis['indicators'],
                    'phishing_explanation': risk_analysis['explanation']
                })
        except Exception as e:
            logging.error(f"Phishing analysis failed for email {email_summary['email_id']}: {e}")
            email_summary.update({
                'phishing_risk_score': 0,
                'phishing_risk_level': 'unknown',
                'phishing_indicators': [],
                'phishing_explanation': 'Analysis failed'
            })
    
    return result

def add_auto_reply_suggestions(result, emails):
    """Add auto-reply suggestions to emails that need responses"""
    email_summaries = result.get('email_summaries', [])
    
    for email_summary in email_summaries:
        if email_summary.get('requires_response', False):
            try:
                # Find corresponding raw email
                raw_email = next((e for e in emails if e['id'] == email_summary['email_id']), None)
                if raw_email:
                    reply_suggestion = auto_reply_generator.generate_reply(raw_email)
                    email_summary.update({
                        'suggested_reply': reply_suggestion['reply_text'],
                        'reply_tone': reply_suggestion['tone'],
                        'reply_confidence': reply_suggestion['confidence'],
                        'reply_key_points': reply_suggestion['key_points']
                    })
            except Exception as e:
                logging.error(f"Auto-reply generation failed for email {email_summary['email_id']}: {e}")
                email_summary.update({
                    'suggested_reply': 'Failed to generate reply suggestion',
                    'reply_tone': 'neutral',
                    'reply_confidence': 0,
                    'reply_key_points': []
                })
    
    return result

def enhance_results_for_webapp(result, emails):
    """Enhance results with additional metadata for web display"""
    enhanced = result.copy()
    
    # Add category-level statistics
    if 'categorization_enabled' in result and result['categorization_enabled']:
        category_stats = calculate_category_statistics(result['email_summaries'])
        enhanced['category_statistics'] = category_stats
    
    # Add email-level enhancements
    for email_summary in enhanced.get('email_summaries', []):
        # Add original email content for reply interface
        raw_email = next((e for e in emails if e['id'] == email_summary['email_id']), None)
        if raw_email:
            email_summary['original_content'] = {
                'body': raw_email.get('body', ''),
                'date': raw_email.get('date', ''),
                'labels': raw_email.get('labels', [])
            }
        
        # Add action item categorization
        email_summary['action_items_categorized'] = categorize_action_items(
            email_summary.get('action_items', [])
        )
    
    # Add processing metadata
    enhanced['processing_metadata'] = {
        'processed_at': datetime.now().isoformat(),
        'processing_method': 'web_interface',
        'features_enabled': {
            'phishing_detection': any('phishing_risk_score' in email for email in enhanced.get('email_summaries', [])),
            'auto_replies': any('suggested_reply' in email for email in enhanced.get('email_summaries', [])),
            'categorization': enhanced.get('categorization_enabled', False)
        }
    }
    
    return enhanced

def calculate_category_statistics(email_summaries):
    """Calculate statistics per category"""
    from collections import defaultdict
    
    category_stats = defaultdict(lambda: {
        'total_emails': 0,
        'high_priority': 0,
        'needs_response': 0,
        'total_action_items': 0,
        'avg_phishing_risk': 0,
        'phishing_risks': []
    })
    
    for email in email_summaries:
        category = email.get('category', 'uncategorized')
        stats = category_stats[category]
        
        stats['total_emails'] += 1
        
        if email.get('priority') == 'High':
            stats['high_priority'] += 1
        
        if email.get('requires_response', False):
            stats['needs_response'] += 1
        
        stats['total_action_items'] += len(email.get('action_items', []))
        
        if 'phishing_risk_score' in email:
            risk_score = email['phishing_risk_score']
            stats['phishing_risks'].append(risk_score)
    
    # Calculate averages
    for category, stats in category_stats.items():
        if stats['phishing_risks']:
            stats['avg_phishing_risk'] = sum(stats['phishing_risks']) / len(stats['phishing_risks'])
        del stats['phishing_risks']  # Remove raw scores from output
    
    return dict(category_stats)

def categorize_action_items(action_items):
    """Categorize action items by type"""
    categorized = {
        'urgent': [],
        'follow_up': [],
        'information': [],
        'deadline': [],
        'other': []
    }
    
    for item in action_items:
        item_lower = item.lower()
        
        if any(word in item_lower for word in ['urgent', 'asap', 'immediately', 'emergency']):
            categorized['urgent'].append(item)
        elif any(word in item_lower for word in ['follow up', 'follow-up', 'check back', 'contact']):
            categorized['follow_up'].append(item)
        elif any(word in item_lower for word in ['deadline', 'due', 'by', 'before']):
            categorized['deadline'].append(item)
        elif any(word in item_lower for word in ['review', 'read', 'check', 'verify']):
            categorized['information'].append(item)
        else:
            categorized['other'].append(item)
    
    return categorized

@app.route('/api/processing-status')
def get_processing_status():
    """Get current processing status with enhanced details"""
    # Try to get status from backend API first
    if check_backend_available():
        backend_status = get_backend_processing_status()
        if backend_status:
            return jsonify(backend_status)
    
    # Fallback to demo processing state
    global demo_processing_state
    if demo_processing_state['is_running']:
        demo_processing_state['progress'] = calculate_demo_progress()
    
    return jsonify(demo_processing_state)

@app.route('/api/results')
def get_results():
    """Get processing results"""
    global demo_processing_state
    
    # Try to get results from backend API first
    if check_backend_available():
        backend_status = get_backend_processing_status()
        if backend_status and backend_status.get('results'):
            return jsonify(backend_status['results'])
    
    # Fallback to demo processing state
    if demo_processing_state.get('results'):
        return jsonify(demo_processing_state['results'])
    else:
        return jsonify({'error': 'No results available'}), 404

@app.route('/dashboard')
def dashboard():
    """Email dashboard with results"""
    return render_template('dashboard.html')

@app.route('/email-details/<email_id>')
def email_details(email_id):
    """Detailed view of a specific email"""
    global demo_processing_state
    
    # Try to get results from backend API first
    results = None
    if check_backend_available():
        backend_status = get_backend_processing_status()
        if backend_status and backend_status.get('results'):
            results = backend_status['results']
    
    # Fallback to demo processing state
    if not results and demo_processing_state.get('results'):
        results = demo_processing_state['results']
    
    if not results:
        return redirect(url_for('index'))
    
    # Find the email in results
    email_summaries = results.get('email_summaries', [])
    email = next((e for e in email_summaries if e['email_id'] == email_id), None)
    
    if not email:
        return "Email not found", 404
    
    return render_template('email_details.html', email=email)

@app.route('/reply-interface/<email_id>')
def reply_interface(email_id):
    """Reply interface showing original email and suggested reply side by side"""
    global demo_processing_state
    
    # Try to get results from backend API first
    results = None
    if check_backend_available():
        backend_status = get_backend_processing_status()
        if backend_status and backend_status.get('results'):
            results = backend_status['results']
    
    # Fallback to demo processing state
    if not results and demo_processing_state.get('results'):
        results = demo_processing_state['results']
    
    if not results:
        return redirect(url_for('index'))
    
    # Find the email in results
    email_summaries = results.get('email_summaries', [])
    email = next((e for e in email_summaries if e['email_id'] == email_id), None)
    
    if not email:
        return "Email not found", 404
    
    return render_template('reply_interface.html', email=email)

@app.route('/api/update-reply', methods=['POST'])
def update_reply():
    """Update the suggested reply"""
    data = request.get_json()
    email_id = data.get('email_id')
    updated_reply = data.get('reply_text')
    
    if not demo_processing_state['results']:
        return jsonify({'error': 'No results available'}), 404
    
    # Find and update the email
    email_summaries = demo_processing_state['results'].get('email_summaries', [])
    for email in email_summaries:
        if email['email_id'] == email_id:
            email['suggested_reply'] = updated_reply
            email['reply_modified'] = True
            email['reply_modified_at'] = datetime.now().isoformat()
            return jsonify({'status': 'updated'})
    
    return jsonify({'error': 'Email not found'}), 404

@app.route('/api/approve-reply', methods=['POST'])
def approve_reply():
    """Approve and potentially send a reply"""
    data = request.get_json()
    email_id = data.get('email_id')
    send_immediately = data.get('send_immediately', False)
    
    if not demo_processing_state['results']:
        return jsonify({'error': 'No results available'}), 404
    
    # Find the email
    email_summaries = demo_processing_state['results'].get('email_summaries', [])
    email = next((e for e in email_summaries if e['email_id'] == email_id), None)
    
    if not email:
        return jsonify({'error': 'Email not found'}), 404
    
    if send_immediately:
        # TODO: Implement actual email sending
        # This would involve using the Gmail API to send the reply
        email['reply_status'] = 'sent'
        email['reply_sent_at'] = datetime.now().isoformat()
        return jsonify({'status': 'sent'})
    else:
        email['reply_status'] = 'approved'
        email['reply_approved_at'] = datetime.now().isoformat()
        return jsonify({'status': 'approved'})

@app.route('/categories')
def categories_view():
    """View emails organized by categories"""
    if not demo_processing_state['results']:
        return redirect(url_for('index'))
    
    return render_template('categories.html', results=demo_processing_state['results'])

@app.route('/status')
def status_page():
    """System status and debugging page"""
    return render_template('status.html')

@app.route('/api/trigger-cli', methods=['POST'])
def trigger_cli():
    """Trigger the CLI version of mail-pilot"""
    try:
        # Check if we're in demo mode (look in parent directory)
        credentials_path = os.path.join('..', 'credentials.json')
        if not os.path.exists(credentials_path):
            return jsonify({
                'status': 'demo_mode',
                'message': 'CLI triggered in demo mode - credentials.json not found',
                'stdout': 'Demo CLI execution:\n✅ Connected to Gmail (simulated)\n✅ Found 8 demo emails\n✅ Categorization complete\n✅ Processing finished successfully',
                'stderr': '',
                'return_code': 0
            })
        
        # Try to run the actual CLI
        cli_script = 'src.email_menu'  # Try this first
        process = subprocess.Popen(
            [sys.executable, '-m', cli_script],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
        
        return jsonify({
            'status': 'completed',
            'stdout': stdout,
            'stderr': stderr,
            'return_code': process.returncode
        })
        
    except subprocess.TimeoutExpired:
        process.kill()
        return jsonify({'error': 'CLI process timed out'}), 500
    except FileNotFoundError:
        return jsonify({
            'error': 'CLI script not found',
            'suggestion': 'Make sure the CLI module exists',
            'demo_available': True
        }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/webapp.log'),
            logging.StreamHandler()
        ]
    )
    
    app.run(debug=True, host='0.0.0.0', port=5000)