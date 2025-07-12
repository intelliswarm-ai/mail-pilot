import requests
import json
import logging
from typing import List, Dict, Any

class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_url = f"{self.base_url}/api/generate"
    
    def test_connection(self) -> bool:
        try:
            logging.info(f"Testing connection to Ollama at {self.base_url}")
            
            # Test basic connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                logging.error(f"Ollama server returned status {response.status_code}")
                return False
            
            # Check if the model is available
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            logging.info(f"Available models: {', '.join(model_names)}")
            
            if not any(self.model in name for name in model_names):
                logging.error(f"Model '{self.model}' not found. Available models: {', '.join(model_names)}")
                logging.error(f"Please run: ollama pull {self.model}")
                return False
            
            # Test actual generation with a simple prompt
            logging.info(f"Testing model '{self.model}' with simple prompt...")
            test_response = self._test_generate()
            
            if test_response:
                logging.info("✅ Ollama connection and model test successful")
                return True
            else:
                logging.error("❌ Ollama model test failed")
                return False
                
        except requests.exceptions.ConnectionError:
            logging.error("❌ Cannot connect to Ollama server. Is Ollama running?")
            logging.error("Try: ollama serve (if not already running)")
            return False
        except requests.exceptions.Timeout:
            logging.error("❌ Connection to Ollama timed out")
            return False
        except Exception as e:
            logging.error(f"❌ Failed to connect to Ollama: {e}")
            return False
    
    def _test_generate(self) -> bool:
        """Test the model with a simple generation"""
        try:
            test_prompt = "Reply with just 'OK' to confirm you are working."
            
            payload = {
                "model": self.model,
                "prompt": test_prompt,
                "stream": False
            }
            
            # Show progress for the test
            print(f"⏳ Testing {self.model} model response...")
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                logging.debug(f"Test response: {result}")
                print(f"✅ Model test successful: {result[:50]}...")
                return len(result) > 0
            else:
                logging.error(f"Test generation failed with status {response.status_code}")
                print(f"❌ Model test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Test generation error: {e}")
            print(f"❌ Model test error: {e}")
            return False
    
    def summarize_email(self, email_data: Dict[str, Any]) -> Dict[str, str]:
        logging.info(f"Generating AI summary for email from {email_data['sender']}")
        
        # Truncate email body for faster processing
        body_preview = email_data['body'][:500] + "..." if len(email_data['body']) > 500 else email_data['body']
        
        prompt = f"""Analyze this email and respond with JSON only:

From: {email_data['sender']}
Subject: {email_data['subject']}

Content: {body_preview}

Return JSON format:
{{
    "summary": "Brief 1-2 sentence summary",
    "action_items": ["list any action items"],
    "priority": "High/Medium/Low",
    "requires_response": true/false
}}"""
        
        try:
            logging.debug(f"Sending email to Ollama for analysis (model: {self.model})")
            response = self._generate(prompt)
            logging.debug(f"Received response from Ollama: {response[:100]}...")
            parsed = self._parse_summary_response(response)
            logging.info(f"Email summary completed - Priority: {parsed.get('priority', 'Unknown')}")
            return parsed
        except Exception as e:
            logging.error(f"Error summarizing email from {email_data['sender']}: {e}")
            return {
                "summary": f"Error processing email from {email_data['sender']}",
                "action_items": [],
                "priority": "Medium",
                "requires_response": False
            }
    
    def generate_overall_summary(self, email_summaries: List[Dict[str, Any]]) -> str:
        logging.info(f"Generating overall summary for {len(email_summaries)} emails")
        
        high_priority = [e for e in email_summaries if e.get('priority') == 'High']
        medium_priority = [e for e in email_summaries if e.get('priority') == 'Medium']
        low_priority = [e for e in email_summaries if e.get('priority') == 'Low']
        
        logging.debug(f"Priority breakdown - High: {len(high_priority)}, Medium: {len(medium_priority)}, Low: {len(low_priority)}")
        
        prompt = f"""
        Create an executive summary of {len(email_summaries)} unread emails.
        
        High Priority Emails ({len(high_priority)}):
        {self._format_emails_for_prompt(high_priority)}
        
        Medium Priority Emails ({len(medium_priority)}):
        {self._format_emails_for_prompt(medium_priority)}
        
        Low Priority Emails ({len(low_priority)}):
        {self._format_emails_for_prompt(low_priority)}
        
        Provide a comprehensive summary including:
        - Overall assessment
        - Urgent items requiring immediate attention
        - Total action items across all emails
        - Recommended next steps
        
        Keep the summary professional and actionable.
        """
        
        try:
            logging.debug("Generating executive summary with Ollama")
            summary = self._generate(prompt)
            logging.info("Overall summary generation completed")
            return summary
        except Exception as e:
            logging.error(f"Error generating overall summary: {e}")
            return f"Summary of {len(email_summaries)} emails processed with some errors."
    
    def _generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(
            self.api_url,
            json=payload,
            timeout=120  # Increased timeout to 2 minutes
        )
        
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        try:
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    "summary": response[:200] + "..." if len(response) > 200 else response,
                    "action_items": [],
                    "priority": "Medium",
                    "requires_response": False
                }
        except json.JSONDecodeError:
            return {
                "summary": response[:200] + "..." if len(response) > 200 else response,
                "action_items": [],
                "priority": "Medium",
                "requires_response": False
            }
    
    def _format_emails_for_prompt(self, emails: List[Dict[str, Any]]) -> str:
        formatted = []
        for email in emails:
            formatted.append(f"- {email.get('summary', 'No summary')} (Actions: {', '.join(email.get('action_items', []))})")
        return '\n'.join(formatted) if formatted else "None"