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
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def summarize_email(self, email_data: Dict[str, Any]) -> Dict[str, str]:
        prompt = f"""
        Please analyze this email and provide:
        1. A concise summary (2-3 sentences)
        2. Any action items or tasks mentioned
        3. Priority level (High/Medium/Low)
        
        Email Details:
        From: {email_data['sender']}
        Subject: {email_data['subject']}
        Date: {email_data['date']}
        
        Content:
        {email_data['body']}
        
        Format your response as JSON:
        {{
            "summary": "Brief summary here",
            "action_items": ["action 1", "action 2"],
            "priority": "High/Medium/Low",
            "requires_response": true/false
        }}
        """
        
        try:
            response = self._generate(prompt)
            return self._parse_summary_response(response)
        except Exception as e:
            logging.error(f"Error summarizing email: {e}")
            return {
                "summary": f"Error processing email from {email_data['sender']}",
                "action_items": [],
                "priority": "Medium",
                "requires_response": False
            }
    
    def generate_overall_summary(self, email_summaries: List[Dict[str, Any]]) -> str:
        high_priority = [e for e in email_summaries if e.get('priority') == 'High']
        medium_priority = [e for e in email_summaries if e.get('priority') == 'Medium']
        low_priority = [e for e in email_summaries if e.get('priority') == 'Low']
        
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
            return self._generate(prompt)
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
            timeout=60
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