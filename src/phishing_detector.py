import re
import logging
from typing import Dict, List, Any
from urllib.parse import urlparse
import json

class PhishingDetector:
    """
    AI-powered phishing detection system using LLM analysis
    and rule-based indicators to assess email safety.
    """
    
    def __init__(self, ollama_client):
        """
        Initialize phishing detector
        
        Args:
            ollama_client: Instance of OllamaClient for LLM analysis
        """
        self.ollama_client = ollama_client
        
        # Common phishing indicators
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'shortener.com', 'goo.gl', 't.co',
            'ow.ly', 'is.gd', 'buff.ly', 'ift.tt'
        ]
        
        self.phishing_keywords = [
            'urgent action required', 'verify account', 'suspended account',
            'click here immediately', 'limited time offer', 'act now',
            'confirm identity', 'update payment', 'security alert',
            'account will be closed', 'verify now', 'immediate action'
        ]
        
        self.suspicious_phrases = [
            'dear customer', 'dear user', 'dear valued customer',
            'congratulations you have won', 'you are a winner',
            'claim your prize', 'free gift', 'no strings attached'
        ]
    
    def analyze_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive phishing analysis of an email
        
        Returns:
            Dict with risk_score (0-100), risk_level, indicators, and explanation
        """
        try:
            # Extract email components
            sender = email.get('sender', '')
            subject = email.get('subject', '')
            body = email.get('body', '')
            
            # Rule-based analysis
            rule_based_score, rule_indicators = self._rule_based_analysis(sender, subject, body)
            
            # LLM-based analysis
            llm_score, llm_explanation = self._llm_based_analysis(sender, subject, body)
            
            # Combine scores (60% LLM, 40% rules)
            final_score = int((llm_score * 0.6) + (rule_based_score * 0.4))
            
            # Determine risk level
            if final_score >= 80:
                risk_level = 'high'
            elif final_score >= 50:
                risk_level = 'medium'
            elif final_score >= 20:
                risk_level = 'low'
            else:
                risk_level = 'safe'
            
            return {
                'risk_score': final_score,
                'risk_level': risk_level,
                'indicators': rule_indicators,
                'explanation': llm_explanation,
                'rule_based_score': rule_based_score,
                'llm_score': llm_score
            }
            
        except Exception as e:
            logging.error(f"Phishing analysis failed: {e}")
            return {
                'risk_score': 0,
                'risk_level': 'unknown',
                'indicators': ['Analysis failed'],
                'explanation': f'Failed to analyze: {str(e)}'
            }
    
    def _rule_based_analysis(self, sender: str, subject: str, body: str) -> tuple:
        """Rule-based phishing detection"""
        score = 0
        indicators = []
        
        # Check sender domain
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            
            # Suspicious domains
            if any(susp_domain in domain for susp_domain in self.suspicious_domains):
                score += 30
                indicators.append(f"Suspicious sender domain: {domain}")
            
            # Domain spoofing (common techniques)
            spoofing_patterns = [
                r'[0-9]', r'[.-]{2,}', r'[a-z][A-Z]', r'[_-]'
            ]
            for pattern in spoofing_patterns:
                if re.search(pattern, domain.replace('.com', '').replace('.org', '')):
                    score += 10
                    indicators.append("Potentially spoofed domain")
                    break
        
        # Check for phishing keywords in subject
        subject_lower = subject.lower()
        for keyword in self.phishing_keywords:
            if keyword in subject_lower:
                score += 15
                indicators.append(f"Suspicious subject: '{keyword}'")
        
        # Check for suspicious phrases in body
        body_lower = body.lower()
        for phrase in self.suspicious_phrases:
            if phrase in body_lower:
                score += 10
                indicators.append(f"Suspicious phrase: '{phrase}'")
        
        # Check for urgency indicators
        urgency_words = ['urgent', 'immediate', 'asap', 'expires', 'deadline']
        urgency_count = sum(1 for word in urgency_words if word in body_lower)
        if urgency_count >= 2:
            score += 20
            indicators.append("Multiple urgency indicators")
        
        # Check for suspicious URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', body)
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Short URLs
                if any(short_domain in domain for short_domain in self.suspicious_domains):
                    score += 25
                    indicators.append(f"Suspicious shortened URL: {domain}")
                
                # IP addresses instead of domains
                if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
                    score += 30
                    indicators.append("URL uses IP address instead of domain")
                
                # Suspicious TLDs
                suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.click', '.download']
                if any(domain.endswith(tld) for tld in suspicious_tlds):
                    score += 20
                    indicators.append(f"Suspicious domain extension: {domain}")
                    
            except Exception:
                pass
        
        # Check for credential harvesting patterns
        credential_patterns = [
            r'password', r'login', r'username', r'pin\s*code',
            r'social\s*security', r'credit\s*card', r'bank\s*account'
        ]
        for pattern in credential_patterns:
            if re.search(pattern, body_lower):
                score += 15
                indicators.append("Requests sensitive information")
                break
        
        # Grammar and spelling issues (simplified check)
        if self._has_poor_grammar(subject + ' ' + body):
            score += 10
            indicators.append("Poor grammar/spelling")
        
        return min(score, 100), indicators
    
    def _has_poor_grammar(self, text: str) -> bool:
        """Simple check for poor grammar/spelling"""
        # Count consecutive uppercase words
        words = text.split()
        consecutive_upper = 0
        max_consecutive = 0
        
        for word in words:
            if word.isupper() and len(word) > 2:
                consecutive_upper += 1
                max_consecutive = max(max_consecutive, consecutive_upper)
            else:
                consecutive_upper = 0
        
        # Multiple words in all caps suggest poor formatting
        return max_consecutive >= 3
    
    def _llm_based_analysis(self, sender: str, subject: str, body: str) -> tuple:
        """LLM-based phishing analysis"""
        try:
            # Create analysis prompt
            prompt = f"""Analyze this email for phishing indicators. Rate the phishing risk from 0-100.

Email Details:
From: {sender}
Subject: {subject}
Body: {body[:500]}{'...' if len(body) > 500 else ''}

Analyze for:
1. Urgency tactics
2. Request for personal information
3. Suspicious links or attachments
4. Grammar/spelling errors
5. Generic greetings
6. Authority impersonation
7. Fear tactics

Respond with JSON:
{{"risk_score": 0-100, "explanation": "detailed explanation of findings"}}
"""
            
            # Call LLM with timeout
            response = self._call_llm_with_timeout(prompt)
            
            # Parse response
            try:
                result = json.loads(response)
                score = int(result.get('risk_score', 0))
                explanation = result.get('explanation', 'LLM analysis completed')
                return min(max(score, 0), 100), explanation
            except (json.JSONDecodeError, ValueError):
                # Fallback parsing
                score_match = re.search(r'risk[_\s]*score["\s]*:\s*(\d+)', response, re.IGNORECASE)
                if score_match:
                    score = int(score_match.group(1))
                    return min(max(score, 0), 100), response
                else:
                    return 25, "LLM analysis completed but score unclear"
                    
        except Exception as e:
            logging.error(f"LLM phishing analysis failed: {e}")
            return 25, f"LLM analysis failed: {str(e)}"
    
    def _call_llm_with_timeout(self, prompt: str) -> str:
        """Call LLM with timeout handling"""
        import requests
        import time
        
        max_attempts = 2
        timeout_base = 30
        
        for attempt in range(max_attempts):
            try:
                timeout = timeout_base * (attempt + 1)  # 30s, then 60s
                
                payload = {
                    "model": self.ollama_client.model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(
                    self.ollama_client.api_url,
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return response.json().get('response', '')
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt == max_attempts - 1:
                    raise Exception("LLM timeout after retries")
                time.sleep(1)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(1)
        
        return ""
    
    def get_risk_color(self, risk_level: str) -> str:
        """Get color code for risk level display"""
        colors = {
            'safe': '#28a745',      # Green
            'low': '#ffc107',       # Yellow
            'medium': '#fd7e14',    # Orange
            'high': '#dc3545',      # Red
            'unknown': '#6c757d'    # Gray
        }
        return colors.get(risk_level, '#6c757d')
    
    def get_recommendations(self, risk_level: str, indicators: List[str]) -> List[str]:
        """Get safety recommendations based on risk assessment"""
        if risk_level == 'high':
            return [
                "🚨 Do NOT click any links or download attachments",
                "🚨 Do NOT provide any personal information",
                "📧 Report this email as phishing to your IT team",
                "🗑️ Delete this email immediately",
                "🔒 Change passwords if you've already interacted"
            ]
        elif risk_level == 'medium':
            return [
                "⚠️ Exercise extreme caution with this email",
                "🔍 Verify sender through alternative communication",
                "🚫 Avoid clicking links - navigate directly to websites",
                "📞 Contact the sender directly if urgent",
                "👥 Consult IT security if unsure"
            ]
        elif risk_level == 'low':
            return [
                "⚠️ Some suspicious elements detected",
                "🔍 Verify sender if requesting sensitive information",
                "🔗 Hover over links to check destinations before clicking",
                "📧 Be cautious with personal information sharing"
            ]
        else:  # safe
            return [
                "✅ Email appears safe based on analysis",
                "🔍 Still verify unexpected requests for sensitive info",
                "🔗 Standard caution with links and attachments advised"
            ]