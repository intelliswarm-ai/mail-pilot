import logging
import json
import re
from typing import Dict, List, Any
from datetime import datetime

class AutoReplyGenerator:
    """
    AI-powered auto-reply generator that creates contextual,
    professional email responses using LLM analysis.
    """
    
    def __init__(self, ollama_client):
        """
        Initialize auto-reply generator
        
        Args:
            ollama_client: Instance of OllamaClient for LLM analysis
        """
        self.ollama_client = ollama_client
        
        # Reply templates for different categories
        self.reply_templates = {
            'meeting_request': {
                'tone': 'professional',
                'key_elements': ['availability', 'agenda', 'location/platform']
            },
            'information_request': {
                'tone': 'helpful',
                'key_elements': ['acknowledgment', 'timeline', 'next_steps']
            },
            'job_application': {
                'tone': 'professional',
                'key_elements': ['gratitude', 'timeline', 'next_steps']
            },
            'customer_support': {
                'tone': 'helpful',
                'key_elements': ['acknowledgment', 'understanding', 'solution_timeline']
            },
            'collaboration': {
                'tone': 'collaborative',
                'key_elements': ['enthusiasm', 'availability', 'contribution']
            },
            'follow_up': {
                'tone': 'polite',
                'key_elements': ['acknowledgment', 'status_update', 'next_steps']
            }
        }
    
    def generate_reply(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an appropriate reply for the given email
        
        Returns:
            Dict with reply_text, tone, confidence, and key_points
        """
        try:
            sender = email.get('sender', '')
            subject = email.get('subject', '')
            body = email.get('body', '')
            
            # Analyze email context and intent
            context_analysis = self._analyze_email_context(sender, subject, body)
            
            # Generate reply using LLM
            reply_data = self._generate_llm_reply(sender, subject, body, context_analysis)
            
            # Enhance with template-based improvements
            enhanced_reply = self._enhance_with_templates(reply_data, context_analysis)
            
            return enhanced_reply
            
        except Exception as e:
            logging.error(f"Auto-reply generation failed: {e}")
            return {
                'reply_text': self._generate_fallback_reply(email),
                'tone': 'neutral',
                'confidence': 0.3,
                'key_points': ['Auto-generation failed'],
                'error': str(e)
            }
    
    def _analyze_email_context(self, sender: str, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email to understand context and required response type"""
        try:
            prompt = f"""Analyze this email to understand the context and determine the appropriate response type.

From: {sender}
Subject: {subject}
Body: {body[:400]}{'...' if len(body) > 400 else ''}

Determine:
1. Email category (meeting_request, information_request, job_application, customer_support, collaboration, follow_up, other)
2. Urgency level (low, medium, high)
3. Sender relationship (colleague, client, vendor, recruiter, unknown)
4. Key topics mentioned
5. Questions or requests that need addressing

Respond with JSON:
{{
    "category": "meeting_request",
    "urgency": "medium", 
    "relationship": "colleague",
    "key_topics": ["project timeline", "budget discussion"],
    "questions_to_address": ["When are you available?", "What's the budget?"],
    "response_type": "detailed"
}}
"""
            
            response = self._call_llm_with_timeout(prompt, 45)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_context_fallback(response, subject, body)
                
        except Exception as e:
            logging.error(f"Context analysis failed: {e}")
            return self._basic_context_analysis(subject, body)
    
    def _generate_llm_reply(self, sender: str, subject: str, body: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reply using LLM"""
        try:
            sender_name = sender.split('@')[0] if '@' in sender else 'there'
            
            prompt = f"""Generate a professional email reply based on this context:

Original Email:
From: {sender}
Subject: {subject}
Body: {body[:300]}{'...' if len(body) > 300 else ''}

Context Analysis:
- Category: {context.get('category', 'general')}
- Urgency: {context.get('urgency', 'medium')}
- Relationship: {context.get('relationship', 'professional')}
- Key Topics: {', '.join(context.get('key_topics', []))}

Generate a reply that:
1. Acknowledges their email appropriately
2. Addresses their main questions/requests
3. Maintains a {context.get('relationship', 'professional')} tone
4. Provides helpful next steps
5. Is concise but complete

Reply Guidelines:
- Start with appropriate greeting
- Reference their email/request
- Provide clear, actionable response
- End with professional closing
- Keep it under 200 words

Respond with JSON:
{{
    "reply_text": "Hi [Name],\\n\\nThank you for your email...",
    "tone": "professional",
    "confidence": 85,
    "key_points": ["acknowledged request", "provided timeline", "suggested next steps"]
}}
"""
            
            response = self._call_llm_with_timeout(prompt, 60)
            
            try:
                result = json.loads(response)
                
                # Clean and validate the reply
                reply_text = result.get('reply_text', '').strip()
                
                # Replace placeholder with actual name
                if '[Name]' in reply_text:
                    reply_text = reply_text.replace('[Name]', sender_name.title())
                
                return {
                    'reply_text': reply_text,
                    'tone': result.get('tone', 'professional'),
                    'confidence': int(result.get('confidence', 70)),
                    'key_points': result.get('key_points', [])
                }
                
            except json.JSONDecodeError:
                # Extract reply from unstructured response
                return self._parse_reply_fallback(response, sender_name, context)
                
        except Exception as e:
            logging.error(f"LLM reply generation failed: {e}")
            return self._generate_template_reply(sender, context)
    
    def _enhance_with_templates(self, reply_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance reply using template-based improvements"""
        category = context.get('category', 'general')
        template = self.reply_templates.get(category)
        
        if template:
            # Adjust tone if needed
            if reply_data['tone'] == 'neutral' and template['tone']:
                reply_data['tone'] = template['tone']
            
            # Add template-specific enhancements
            reply_text = reply_data['reply_text']
            
            # Add signature if missing
            if not reply_text.endswith(('Best regards,', 'Sincerely,', 'Thanks,')):
                reply_text += "\n\nBest regards,"
            
            reply_data['reply_text'] = reply_text
            reply_data['template_category'] = category
        
        return reply_data
    
    def _call_llm_with_timeout(self, prompt: str, timeout: int) -> str:
        """Call LLM with timeout handling"""
        import requests
        import time
        
        max_attempts = 2
        
        for attempt in range(max_attempts):
            try:
                current_timeout = timeout * (attempt + 1)
                
                payload = {
                    "model": self.ollama_client.model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(
                    self.ollama_client.api_url,
                    json=payload,
                    timeout=current_timeout
                )
                
                if response.status_code == 200:
                    return response.json().get('response', '')
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt == max_attempts - 1:
                    raise Exception("LLM timeout after retries")
                time.sleep(2)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(1)
        
        return ""
    
    def _parse_context_fallback(self, response: str, subject: str, body: str) -> Dict[str, Any]:
        """Fallback context parsing when JSON fails"""
        context = {
            'category': 'general',
            'urgency': 'medium',
            'relationship': 'professional',
            'key_topics': [],
            'questions_to_address': []
        }
        
        # Simple keyword-based categorization
        subject_body = (subject + ' ' + body).lower()
        
        if any(word in subject_body for word in ['meeting', 'call', 'schedule', 'availability']):
            context['category'] = 'meeting_request'
        elif any(word in subject_body for word in ['job', 'position', 'application', 'interview']):
            context['category'] = 'job_application'
        elif any(word in subject_body for word in ['help', 'support', 'issue', 'problem']):
            context['category'] = 'customer_support'
        elif any(word in subject_body for word in ['follow up', 'status', 'update']):
            context['category'] = 'follow_up'
        elif any(word in subject_body for word in ['collaborate', 'project', 'work together']):
            context['category'] = 'collaboration'
        
        # Urgency detection
        if any(word in subject_body for word in ['urgent', 'asap', 'immediate', 'emergency']):
            context['urgency'] = 'high'
        elif any(word in subject_body for word in ['when convenient', 'no rush', 'whenever']):
            context['urgency'] = 'low'
        
        return context
    
    def _basic_context_analysis(self, subject: str, body: str) -> Dict[str, Any]:
        """Basic context analysis when LLM fails"""
        return {
            'category': 'general',
            'urgency': 'medium',
            'relationship': 'professional',
            'key_topics': [],
            'questions_to_address': []
        }
    
    def _parse_reply_fallback(self, response: str, sender_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse reply from unstructured LLM response"""
        # Try to extract the main reply text
        lines = response.split('\n')
        reply_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('confidence:', 'tone:', 'key_points:')):
                reply_lines.append(line)
        
        reply_text = '\n'.join(reply_lines[:10])  # Limit to reasonable length
        
        if not reply_text:
            reply_text = self._generate_simple_reply(sender_name, context)
        
        return {
            'reply_text': reply_text,
            'tone': context.get('relationship', 'professional'),
            'confidence': 60,
            'key_points': ['Generated from LLM response']
        }
    
    def _generate_template_reply(self, sender: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reply using templates when LLM fails"""
        sender_name = sender.split('@')[0] if '@' in sender else 'there'
        category = context.get('category', 'general')
        
        templates = {
            'meeting_request': f"Hi {sender_name.title()},\n\nThank you for reaching out about scheduling a meeting. I'll review my calendar and get back to you with my availability within 24 hours.\n\nBest regards,",
            'information_request': f"Hi {sender_name.title()},\n\nThank you for your inquiry. I've received your request and will gather the information you need. I'll respond with details within 2 business days.\n\nBest regards,",
            'job_application': f"Dear {sender_name.title()},\n\nThank you for your interest in our position. We have received your application and will review it carefully. We'll be in touch within the next week regarding next steps.\n\nBest regards,",
            'customer_support': f"Hi {sender_name.title()},\n\nThank you for contacting support. I've received your request and understand your concern. I'll investigate this issue and provide you with an update within 24 hours.\n\nBest regards,",
            'collaboration': f"Hi {sender_name.title()},\n\nThank you for reaching out about this collaboration opportunity. I'm interested in learning more and would be happy to discuss how we can work together.\n\nBest regards,",
            'follow_up': f"Hi {sender_name.title()},\n\nThank you for following up. I appreciate your patience and will provide you with an update on the status shortly.\n\nBest regards,"
        }
        
        reply_text = templates.get(category, templates['information_request'])
        
        return {
            'reply_text': reply_text,
            'tone': 'professional',
            'confidence': 70,
            'key_points': ['Template-based response', f'Category: {category}']
        }
    
    def _generate_simple_reply(self, sender_name: str, context: Dict[str, Any]) -> str:
        """Generate simple acknowledgment reply"""
        return f"Hi {sender_name.title()},\n\nThank you for your email. I've received your message and will respond appropriately soon.\n\nBest regards,"
    
    def _generate_fallback_reply(self, email: Dict[str, Any]) -> str:
        """Generate basic fallback reply when all else fails"""
        sender = email.get('sender', '')
        sender_name = sender.split('@')[0] if '@' in sender else 'there'
        
        return f"Hi {sender_name.title()},\n\nThank you for your email. I've received your message and will get back to you soon.\n\nBest regards,"
    
    def get_reply_suggestions(self, tone: str) -> List[str]:
        """Get tone-specific reply suggestions"""
        suggestions = {
            'professional': [
                "Consider adding specific timelines",
                "Include relevant contact information", 
                "Mention next steps clearly"
            ],
            'friendly': [
                "Add a personal touch if appropriate",
                "Use warmer language",
                "Include enthusiasm where suitable"
            ],
            'formal': [
                "Use formal language and structure",
                "Include proper salutations",
                "Be precise and concise"
            ],
            'helpful': [
                "Offer additional assistance",
                "Provide useful resources",
                "Be proactive in addressing needs"
            ]
        }
        
        return suggestions.get(tone, suggestions['professional'])
    
    def validate_reply(self, reply_text: str) -> Dict[str, Any]:
        """Validate generated reply for common issues"""
        issues = []
        score = 100
        
        # Check length
        if len(reply_text) < 20:
            issues.append("Reply is too short")
            score -= 20
        elif len(reply_text) > 1000:
            issues.append("Reply is too long")
            score -= 10
        
        # Check for greeting
        if not any(greeting in reply_text.lower() for greeting in ['hi', 'hello', 'dear', 'greetings']):
            issues.append("Missing greeting")
            score -= 15
        
        # Check for closing
        if not any(closing in reply_text.lower() for closing in ['regards', 'sincerely', 'thanks', 'best']):
            issues.append("Missing professional closing")
            score -= 15
        
        # Check for placeholder text
        if '[' in reply_text or '{' in reply_text:
            issues.append("Contains placeholder text")
            score -= 25
        
        return {
            'is_valid': len(issues) == 0,
            'score': max(score, 0),
            'issues': issues
        }