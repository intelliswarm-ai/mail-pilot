"""
Demo services for Mail Pilot Web Application
Provides simulated email processing for demonstration and testing
"""

import time
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta


class DemoGmailClient:
    """Demo Gmail client that generates sample emails"""
    
    def __init__(self):
        self.demo_emails = [
            {
                'id': 'demo_001',
                'subject': 'Meeting request for project review',
                'sender': 'sarah.wilson@company.com',
                'body': 'Hi there,\n\nI would like to schedule a meeting to review the Q4 project deliverables. Are you available next Tuesday at 2 PM?\n\nBest regards,\nSarah Wilson\nProject Manager',
                'date': (datetime.now() - timedelta(hours=2)).isoformat(),
                'labels': ['INBOX', 'IMPORTANT']
            },
            {
                'id': 'demo_002', 
                'subject': 'Urgent: Account verification required',
                'sender': 'noreply@suspicious-bank.tk',
                'body': 'URGENT SECURITY ALERT!\n\nYour account has been temporarily suspended. Click here immediately to verify: http://fake-bank.tk/verify\n\nFailure to act within 24 hours will result in permanent account closure.',
                'date': (datetime.now() - timedelta(hours=1)).isoformat(),
                'labels': ['INBOX']
            },
            {
                'id': 'demo_003',
                'subject': 'Weekly team standup notes',
                'sender': 'team-lead@company.com',
                'body': 'Hi team,\n\nHere are the notes from today\'s standup:\n\n- Sprint progress: 80% complete\n- Blockers: None\n- Next deliverables: Frontend updates\n\nThanks!\nTeam Lead',
                'date': (datetime.now() - timedelta(hours=4)).isoformat(),
                'labels': ['INBOX', 'TEAM']
            },
            {
                'id': 'demo_004',
                'subject': 'Invoice #INV-2024-001 - Payment due',
                'sender': 'billing@vendor-corp.com',
                'body': 'Dear Customer,\n\nPlease find attached invoice INV-2024-001 for services rendered.\n\nAmount due: $2,500.00\nDue date: January 30, 2024\n\nThank you for your business.',
                'date': (datetime.now() - timedelta(hours=6)).isoformat(),
                'labels': ['INBOX', 'FINANCE']
            },
            {
                'id': 'demo_005',
                'subject': 'RE: Proposal feedback needed',
                'sender': 'client@partner-org.com',
                'body': 'Thank you for the detailed proposal. We have reviewed it and have a few questions:\n\n1. Can you adjust the timeline?\n2. What about the budget flexibility?\n\nLooking forward to your response.\n\nBest,\nClient Representative',
                'date': (datetime.now() - timedelta(hours=8)).isoformat(),
                'labels': ['INBOX', 'CLIENTS']
            },
            {
                'id': 'demo_006',
                'subject': 'Congratulations! You have won $1,000,000',
                'sender': 'winner@lottery-scam.ml',
                'body': 'CONGRATULATIONS!!!\n\nYou have been selected as the WINNER of our international lottery!\n\nTo claim your prize of $1,000,000, please send us your bank details immediately.\n\nDon\'t delay - this offer expires in 24 hours!',
                'date': (datetime.now() - timedelta(hours=12)).isoformat(),
                'labels': ['INBOX', 'SPAM']
            },
            {
                'id': 'demo_007',
                'subject': 'Security alert for your online banking',
                'sender': 'security@legitimate-bank.com',
                'body': 'We detected unusual activity on your account from IP address 192.168.1.100.\n\nIf this was not you, please contact us immediately at 1-800-BANK-HELP.\n\nFor your security, we recommend changing your password.\n\nBank Security Team',
                'date': (datetime.now() - timedelta(hours=16)).isoformat(),
                'labels': ['INBOX', 'SECURITY']
            },
            {
                'id': 'demo_008',
                'subject': 'Tech Summit 2024 - Conference invitation',
                'sender': 'events@techsummit2024.com',
                'body': 'You\'re invited to Tech Summit 2024!\n\nJoin industry leaders for 3 days of innovation and networking.\n\nDate: March 15-17, 2024\nLocation: San Francisco Convention Center\n\nEarly bird registration ends soon. Register now!',
                'date': (datetime.now() - timedelta(hours=20)).isoformat(),
                'labels': ['INBOX', 'EVENTS']
            }
        ]
    
    def get_unread_messages(self, query=''):
        """Return demo emails"""
        print(f"[DEMO] Fetching emails with query: {query}")
        # Simulate some processing time
        time.sleep(1)
        return self.demo_emails


class DemoOllamaClient:
    """Demo Ollama client that simulates LLM responses"""
    
    def __init__(self):
        self.model = "mistral"
        self.api_url = "http://localhost:11434/api/generate"
    
    def generate(self, prompt, **kwargs):
        """Simulate LLM response with realistic delays"""
        # Simulate processing time based on prompt complexity
        delay = min(2 + len(prompt) / 1000, 5)  # 2-5 seconds
        time.sleep(delay)
        
        # Generate contextual responses based on prompt content
        if "categorize" in prompt.lower():
            return self._generate_categorization_response(prompt)
        elif "phishing" in prompt.lower():
            return self._generate_phishing_response(prompt)
        elif "reply" in prompt.lower():
            return self._generate_reply_response(prompt)
        else:
            return {"response": "Demo response generated successfully."}
    
    def _generate_categorization_response(self, prompt):
        """Generate demo categorization response"""
        categories = [
            "Work & Business",
            "Security & Alerts", 
            "Personal",
            "Promotional",
            "Events & Invitations",
            "Financial",
            "Team Communication"
        ]
        
        return {
            "response": f"Category: {random.choice(categories)}\nConfidence: {random.randint(75, 95)}%\nReason: Based on email content analysis."
        }
    
    def _generate_phishing_response(self, prompt):
        """Generate demo phishing detection response"""
        if "suspicious" in prompt or "verify" in prompt or "urgent" in prompt:
            risk_score = random.randint(60, 90)
            risk_level = "high" if risk_score > 80 else "medium"
        else:
            risk_score = random.randint(5, 25)
            risk_level = "safe" if risk_score < 20 else "low"
        
        return {
            "response": f'{{"risk_score": {risk_score}, "explanation": "Automated analysis detected potential phishing indicators based on urgency language and suspicious links."}}'
        }
    
    def _generate_reply_response(self, prompt):
        """Generate demo auto-reply response"""
        replies = [
            "Thank you for your email. I have received your message and will respond within 24 hours.",
            "Hi there,\n\nThank you for reaching out. I'll review your request and get back to you soon.\n\nBest regards,",
            "Hello,\n\nI appreciate you contacting me. I'll look into this matter and provide you with an update shortly.\n\nThanks,",
        ]
        
        return {
            "response": f'{{"reply_text": "{random.choice(replies)}", "tone": "professional", "confidence": {random.randint(80, 95)}, "key_points": ["acknowledgment", "timeline", "professional closing"]}}'
        }


class DemoEmailProcessor:
    """Demo email processor that simulates processing"""
    
    def __init__(self, gmail_client=None, ollama_client=None):
        self.gmail_client = gmail_client or DemoGmailClient()
        self.ollama_client = ollama_client or DemoOllamaClient()
    
    def process_unread_emails(self, query, options):
        """Simulate email processing with realistic results"""
        print(f"[DEMO] Processing emails with options: {options}")
        
        # Simulate processing time
        time.sleep(2)
        
        # Generate demo results
        demo_summaries = [
            {
                'email_id': 'demo_001',
                'subject': 'Meeting request for project review',
                'sender': 'sarah.wilson@company.com',
                'category': 'Work & Business',
                'priority': 'Medium',
                'requires_response': True,
                'summary': 'Sarah Wilson is requesting a meeting to review Q4 project deliverables for next Tuesday at 2 PM.',
                'action_items': ['Schedule meeting for Tuesday 2 PM', 'Prepare Q4 project deliverables'],
                'confidence_score': 88
            },
            {
                'email_id': 'demo_002',
                'subject': 'Urgent: Account verification required',
                'sender': 'noreply@suspicious-bank.tk',
                'category': 'Security & Alerts',
                'priority': 'High',
                'requires_response': False,
                'summary': 'Suspicious email claiming account suspension and requesting immediate verification.',
                'action_items': ['Do not click any links', 'Report as phishing'],
                'confidence_score': 92
            },
            {
                'email_id': 'demo_003',
                'subject': 'Weekly team standup notes',
                'sender': 'team-lead@company.com',
                'category': 'Team Communication',
                'priority': 'Low',
                'requires_response': False,
                'summary': 'Team standup notes showing 80% sprint progress with no current blockers.',
                'action_items': ['Review sprint progress', 'Prepare frontend updates'],
                'confidence_score': 85
            },
            {
                'email_id': 'demo_004',
                'subject': 'Invoice #INV-2024-001 - Payment due',
                'sender': 'billing@vendor-corp.com',
                'category': 'Financial',
                'priority': 'Medium',
                'requires_response': False,
                'summary': 'Invoice for $2,500.00 due January 30, 2024 for services rendered.',
                'action_items': ['Process payment by due date', 'File invoice in accounting system'],
                'confidence_score': 90
            },
            {
                'email_id': 'demo_005',
                'subject': 'RE: Proposal feedback needed',
                'sender': 'client@partner-org.com',
                'category': 'Work & Business',
                'priority': 'High',
                'requires_response': True,
                'summary': 'Client has questions about proposal timeline and budget flexibility.',
                'action_items': ['Address timeline questions', 'Discuss budget flexibility', 'Send revised proposal'],
                'confidence_score': 87
            }
        ]
        
        return {
            'total_emails': len(demo_summaries),
            'categorization_enabled': True,
            'categorization_method': options.get('categorization_method', 'enhanced'),
            'email_summaries': demo_summaries,
            'processing_time': '45 seconds',
            'high_priority_count': len([e for e in demo_summaries if e['priority'] == 'High'])
        }


class DemoPhishingDetector:
    """Demo phishing detector"""
    
    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client or DemoOllamaClient()
    
    def analyze_email(self, email):
        """Simulate phishing analysis"""
        time.sleep(0.5)  # Simulate analysis time
        
        subject = email.get('subject', '').lower()
        sender = email.get('sender', '').lower()
        body = email.get('body', '').lower()
        
        # Simulate risk assessment
        risk_indicators = []
        risk_score = 10
        
        if any(word in subject for word in ['urgent', 'verify', 'suspended', 'winner']):
            risk_score += 30
            risk_indicators.append("Urgent language in subject")
        
        if any(domain in sender for domain in ['.tk', '.ml', 'suspicious']):
            risk_score += 40
            risk_indicators.append("Suspicious sender domain")
        
        if any(phrase in body for phrase in ['click here', 'verify immediately', 'account suspended']):
            risk_score += 20
            risk_indicators.append("Suspicious content patterns")
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'high'
        elif risk_score >= 50:
            risk_level = 'medium'
        elif risk_score >= 20:
            risk_level = 'low'
        else:
            risk_level = 'safe'
        
        return {
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'indicators': risk_indicators,
            'explanation': f"Analysis detected {len(risk_indicators)} risk indicators. Risk level: {risk_level}."
        }


class DemoAutoReplyGenerator:
    """Demo auto-reply generator"""
    
    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client or DemoOllamaClient()
    
    def generate_reply(self, email):
        """Simulate reply generation"""
        time.sleep(1)  # Simulate generation time
        
        subject = email.get('subject', '')
        sender = email.get('sender', '')
        sender_name = sender.split('@')[0] if '@' in sender else 'there'
        
        # Generate contextual replies
        if 'meeting' in subject.lower():
            reply_text = f"Hi {sender_name.title()},\n\nThank you for the meeting request. I'll check my calendar and get back to you with my availability shortly.\n\nBest regards,"
            tone = 'professional'
            confidence = 85
            key_points = ['acknowledged request', 'checking availability', 'will respond soon']
        
        elif 'proposal' in subject.lower() or 'RE:' in subject:
            reply_text = f"Hi {sender_name.title()},\n\nThank you for your feedback on the proposal. I'll review your questions and provide detailed responses within 24 hours.\n\nBest regards,"
            tone = 'professional'
            confidence = 88
            key_points = ['acknowledged feedback', 'reviewing questions', 'provided timeline']
        
        else:
            reply_text = f"Hi {sender_name.title()},\n\nThank you for your email. I have received your message and will respond appropriately soon.\n\nBest regards,"
            tone = 'neutral'
            confidence = 75
            key_points = ['acknowledged email', 'will respond']
        
        return {
            'reply_text': reply_text,
            'tone': tone,
            'confidence': confidence,
            'key_points': key_points
        }