"""
Progress tracking system for Mail Pilot Service
Provides real-time progress updates for email processing
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os


class ProgressTracker:
    """Thread-safe progress tracker for email processing"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            'is_running': False,
            'progress': 0,
            'status': 'idle',  # idle, running, completed, error
            'current_step': '',
            'total_emails': 0,
            'processed_emails': 0,
            'current_email': None,
            'email_progress': [],  # List of email processing states
            'stage': 'idle',  # idle, fetching, categorizing, analyzing, generating_replies, saving, complete
            'stage_progress': 0,
            'detailed_log': [],  # Detailed processing log
            'results': None,
            'error': None,
            'started_at': None,
            'completed_at': None
        }
    
    def start_processing(self, total_emails: int = 0):
        """Start a new processing session"""
        with self._lock:
            self._state.update({
                'is_running': True,
                'progress': 0,
                'status': 'running',
                'current_step': 'Initializing...',
                'total_emails': total_emails,
                'processed_emails': 0,
                'current_email': None,
                'email_progress': [],
                'stage': 'fetching',
                'stage_progress': 0,
                'detailed_log': [],
                'results': None,
                'error': None,
                'started_at': datetime.now().isoformat(),
                'completed_at': None
            })
            
            self.add_log("Starting email processing session", 'info')
    
    def update_stage(self, stage: str, progress: int, step: str):
        """Update the current processing stage"""
        with self._lock:
            self._state.update({
                'stage': stage,
                'stage_progress': progress,
                'current_step': step,
                'progress': self._calculate_overall_progress()
            })
            
            self.add_log(f"Stage: {stage} - {step}", 'info')
    
    def update_email_progress(self, email_id: str, subject: str, sender: str, status: str, details: Dict = None):
        """Update progress for individual email"""
        with self._lock:
            email_progress = {
                'email_id': email_id,
                'subject': subject[:50] + '...' if len(subject) > 50 else subject,
                'sender': sender,
                'status': status,  # pending, fetching, categorizing, analyzing, generating_reply, completed, error
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }
            
            # Update existing email or add new one
            found = False
            for i, email in enumerate(self._state['email_progress']):
                if email['email_id'] == email_id:
                    self._state['email_progress'][i] = email_progress
                    found = True
                    break
            
            if not found:
                self._state['email_progress'].append(email_progress)
            
            # Update current email if it's being processed
            if status in ['categorizing', 'analyzing', 'generating_reply']:
                self._state['current_email'] = {
                    'id': email_id,
                    'subject': subject,
                    'sender': sender,
                    'status': status
                }
    
    def update_processed_count(self, count: int):
        """Update the number of processed emails"""
        with self._lock:
            self._state['processed_emails'] = count
            self._state['progress'] = self._calculate_overall_progress()
    
    def add_log(self, message: str, level: str = 'info'):
        """Add a log entry with timestamp"""
        with self._lock:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'level': level
            }
            self._state['detailed_log'].append(log_entry)
            
            # Keep only last 100 log entries
            if len(self._state['detailed_log']) > 100:
                self._state['detailed_log'] = self._state['detailed_log'][-100:]
    
    def complete_processing(self, results: Dict = None):
        """Mark processing as completed"""
        with self._lock:
            self._state.update({
                'is_running': False,
                'status': 'completed',
                'stage': 'complete',
                'stage_progress': 100,
                'progress': 100,
                'current_step': 'Processing completed successfully',
                'results': results,
                'completed_at': datetime.now().isoformat()
            })
            
            self.add_log("Email processing completed successfully", 'success')
    
    def set_error(self, error_message: str):
        """Mark processing as failed with error"""
        with self._lock:
            self._state.update({
                'is_running': False,
                'status': 'error',
                'stage': 'error',
                'error': error_message,
                'current_step': f'Error: {error_message}',
                'completed_at': datetime.now().isoformat()
            })
            
            self.add_log(f"Processing failed: {error_message}", 'error')
    
    def get_state(self) -> Dict:
        """Get current processing state (thread-safe)"""
        with self._lock:
            return self._state.copy()
    
    def _calculate_overall_progress(self) -> int:
        """Calculate overall progress based on stage and email count"""
        stage_weights = {
            'idle': 0.0,
            'fetching': 0.1,     # 10%
            'categorizing': 0.4,  # 40%
            'analyzing': 0.3,     # 30%
            'generating_replies': 0.15,  # 15%
            'saving': 0.05,      # 5%
            'complete': 1.0
        }
        
        current_stage = self._state['stage']
        stage_progress = self._state['stage_progress']
        
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
    
    def save_state_to_file(self, file_path: str = 'processing_state.json'):
        """Save current state to file for persistence"""
        try:
            with self._lock:
                with open(file_path, 'w') as f:
                    json.dump(self._state, f, indent=2)
        except Exception as e:
            print(f"Failed to save state to file: {e}")
    
    def load_state_from_file(self, file_path: str = 'processing_state.json'):
        """Load state from file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    saved_state = json.load(f)
                    with self._lock:
                        self._state.update(saved_state)
                        # Reset running state if loaded from file
                        if self._state['is_running']:
                            self._state['is_running'] = False
                            self._state['status'] = 'idle'
                return True
        except Exception as e:
            print(f"Failed to load state from file: {e}")
        return False


# Global progress tracker instance
progress_tracker = ProgressTracker()