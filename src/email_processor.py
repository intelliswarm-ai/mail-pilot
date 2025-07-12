import logging
from typing import List, Dict, Any
from datetime import datetime
from .gmail_client import GmailClient
from .ollama_client import OllamaClient

class EmailProcessor:
    def __init__(self, gmail_client: GmailClient, ollama_client: OllamaClient):
        self.gmail_client = gmail_client
        self.ollama_client = ollama_client
    
    def process_unread_emails(self) -> Dict[str, Any]:
        logging.info("Starting email processing...")
        
        # Get unread emails
        unread_emails = self.gmail_client.get_unread_messages()
        
        if not unread_emails:
            logging.info("No unread emails found")
            return {
                'total_emails': 0,
                'email_summaries': [],
                'overall_summary': 'No unread emails at this time.',
                'high_priority_count': 0,
                'action_items_total': 0
            }
        
        logging.info(f"Processing {len(unread_emails)} unread emails")
        
        # Process each email through Ollama
        email_summaries = []
        for email_data in unread_emails:
            try:
                summary = self.ollama_client.summarize_email(email_data)
                email_summaries.append({
                    'email_id': email_data['id'],
                    'sender': email_data['sender'],
                    'subject': email_data['subject'],
                    'date': email_data['date'],
                    'summary': summary['summary'],
                    'action_items': summary['action_items'],
                    'priority': summary['priority'],
                    'requires_response': summary['requires_response']
                })
                logging.info(f"Processed email from {email_data['sender']}")
            except Exception as e:
                logging.error(f"Error processing email from {email_data['sender']}: {e}")
                email_summaries.append({
                    'email_id': email_data['id'],
                    'sender': email_data['sender'],
                    'subject': email_data['subject'],
                    'date': email_data['date'],
                    'summary': 'Error processing this email',
                    'action_items': [],
                    'priority': 'Medium',
                    'requires_response': False
                })
        
        # Generate overall summary
        overall_summary = self.ollama_client.generate_overall_summary(email_summaries)
        
        # Calculate statistics
        high_priority_count = len([e for e in email_summaries if e['priority'] == 'High'])
        action_items_total = sum(len(e['action_items']) for e in email_summaries)
        
        result = {
            'total_emails': len(unread_emails),
            'email_summaries': email_summaries,
            'overall_summary': overall_summary,
            'high_priority_count': high_priority_count,
            'action_items_total': action_items_total,
            'processed_at': datetime.now().isoformat()
        }
        
        logging.info(f"Email processing completed. {len(email_summaries)} emails processed")
        return result
    
    def format_email_summary_text(self, processing_result: Dict[str, Any]) -> str:
        email_summaries = processing_result['email_summaries']
        
        text = f"""
EMAIL SUMMARY REPORT
Generated: {processing_result['processed_at']}
Total Emails: {processing_result['total_emails']}
High Priority: {processing_result['high_priority_count']}
Total Action Items: {processing_result['action_items_total']}

OVERALL SUMMARY:
{processing_result['overall_summary']}

INDIVIDUAL EMAIL SUMMARIES:
"""
        
        # Group by priority
        high_priority = [e for e in email_summaries if e['priority'] == 'High']
        medium_priority = [e for e in email_summaries if e['priority'] == 'Medium']
        low_priority = [e for e in email_summaries if e['priority'] == 'Low']
        
        for priority_group, title in [(high_priority, "HIGH PRIORITY"), 
                                     (medium_priority, "MEDIUM PRIORITY"), 
                                     (low_priority, "LOW PRIORITY")]:
            if priority_group:
                text += f"\n{title} EMAILS:\n"
                text += "-" * (len(title) + 8) + "\n"
                
                for email in priority_group:
                    text += f"\nFrom: {email['sender']}\n"
                    text += f"Subject: {email['subject']}\n"
                    text += f"Summary: {email['summary']}\n"
                    
                    if email['action_items']:
                        text += f"Action Items:\n"
                        for item in email['action_items']:
                            text += f"  • {item}\n"
                    
                    if email['requires_response']:
                        text += "⚠️ REQUIRES RESPONSE\n"
                    
                    text += "\n"
        
        return text
    
    def format_email_summary_html(self, processing_result: Dict[str, Any]) -> str:
        email_summaries = processing_result['email_summaries']
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .stat {{ background-color: #e9e9e9; padding: 10px; border-radius: 5px; text-align: center; }}
                .priority-high {{ border-left: 5px solid #d32f2f; }}
                .priority-medium {{ border-left: 5px solid #f57c00; }}
                .priority-low {{ border-left: 5px solid #388e3c; }}
                .email-item {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .action-items {{ margin-top: 10px; }}
                .action-items ul {{ margin: 5px 0; }}
                .requires-response {{ color: #d32f2f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Email Summary Report</h1>
                <p><strong>Generated:</strong> {processing_result['processed_at']}</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h3>{processing_result['total_emails']}</h3>
                    <p>Total Emails</p>
                </div>
                <div class="stat">
                    <h3>{processing_result['high_priority_count']}</h3>
                    <p>High Priority</p>
                </div>
                <div class="stat">
                    <h3>{processing_result['action_items_total']}</h3>
                    <p>Action Items</p>
                </div>
            </div>
            
            <div class="overall-summary">
                <h2>📋 Overall Summary</h2>
                <p>{processing_result['overall_summary']}</p>
            </div>
            
            <h2>📬 Individual Email Summaries</h2>
        """
        
        # Group by priority
        priority_groups = [
            ([e for e in email_summaries if e['priority'] == 'High'], "🔴 High Priority", "priority-high"),
            ([e for e in email_summaries if e['priority'] == 'Medium'], "🟡 Medium Priority", "priority-medium"),
            ([e for e in email_summaries if e['priority'] == 'Low'], "🟢 Low Priority", "priority-low")
        ]
        
        for emails, title, css_class in priority_groups:
            if emails:
                html += f"<h3>{title}</h3>"
                
                for email in emails:
                    response_indicator = "⚠️ REQUIRES RESPONSE" if email['requires_response'] else ""
                    
                    html += f"""
                    <div class="email-item {css_class}">
                        <h4>{email['subject']}</h4>
                        <p><strong>From:</strong> {email['sender']}</p>
                        <p><strong>Summary:</strong> {email['summary']}</p>
                    """
                    
                    if email['action_items']:
                        html += "<div class='action-items'><strong>Action Items:</strong><ul>"
                        for item in email['action_items']:
                            html += f"<li>{item}</li>"
                        html += "</ul></div>"
                    
                    if email['requires_response']:
                        html += f"<p class='requires-response'>{response_indicator}</p>"
                    
                    html += "</div>"
        
        html += "</body></html>"
        return html