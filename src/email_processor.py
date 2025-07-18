import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .gmail_client import GmailClient
from .ollama_client import OllamaClient
from .email_categorizer import EmailCategorizer
from .email_nlp_categorizer import EmailNLPCategorizer
from .email_enhanced_categorizer import EmailEnhancedCategorizer
from .email_llm_categorizer import EmailLLMCategorizer
from .email_hybrid_categorizer import EmailHybridCategorizer
from tqdm import tqdm

class EmailProcessor:
    def __init__(self, gmail_client: GmailClient, ollama_client: OllamaClient):
        self.gmail_client = gmail_client
        self.ollama_client = ollama_client
        self.categorizer = EmailCategorizer()  # Keep for fallback
        self.nlp_categorizer = EmailNLPCategorizer()  # Legacy categorizer
        self.enhanced_categorizer = EmailEnhancedCategorizer()  # Enhanced categorizer
        self.llm_categorizer = EmailLLMCategorizer(ollama_client)  # LLM-powered categorizer
        self.hybrid_categorizer = EmailHybridCategorizer(self.enhanced_categorizer, ollama_client)  # Hybrid categorizer
    
    def process_unread_emails(self, query: str = 'is:unread', options: Dict = None) -> Dict[str, Any]:
        logging.info("Starting email processing...")
        
        if options is None:
            options = {'categorize_emails': False, 'detailed_summaries': False}
        
        # Get emails based on query
        unread_emails = self.gmail_client.get_unread_messages(query)
        
        if not unread_emails:
            logging.info("No emails found")
            return {
                'total_emails': 0,
                'email_summaries': [],
                'overall_summary': 'No emails found for the selected timeframe.',
                'high_priority_count': 0,
                'action_items_total': 0,
                'commercial_emails': [],
                'personal_emails': [],
                'categorization_enabled': False
            }
        
        logging.info(f"Processing {len(unread_emails)} emails with AI analysis")
        
        # Categorize emails if requested
        if options.get('categorize_emails', False):
            categorization_method = options.get('categorization_method', 'enhanced')
            
            if categorization_method == 'llm':
                # Use hybrid categorization: fast clustering + LLM naming
                try:
                    clustered_emails = self.hybrid_categorizer.categorize_emails(unread_emails)
                    print("✅ Using Hybrid Categorizer (Enhanced Clustering + LLM Naming)")
                except Exception as e:
                    print(f"⚠️  Hybrid categorizer failed ({e}), falling back to enhanced categorizer")
                    clustered_emails = self.enhanced_categorizer.categorize_emails(unread_emails)
            elif categorization_method == 'enhanced':
                # Use enhanced TF-IDF + adaptive clustering
                try:
                    print(f"\n🚀 Starting Enhanced NLP Categorization for {len(unread_emails)} emails...")
                    print("🔬 Using: TF-IDF vectorization + Adaptive clustering algorithms")
                    print("📊 This will process each email individually for detailed analysis")
                    print("=" * 80)
                    
                    clustered_emails = self.enhanced_categorizer.categorize_emails(unread_emails)
                    print("✅ Using Enhanced Categorizer (TF-IDF + Adaptive Clustering)")
                except Exception as e:
                    print(f"⚠️  Enhanced categorizer failed ({e}), falling back to NLP categorizer")
                    clustered_emails = self.nlp_categorizer.categorize_emails(unread_emails)
            else:
                # Use basic NLP clustering (legacy)
                try:
                    clustered_emails = self.nlp_categorizer.categorize_emails(unread_emails)
                    print("✅ Using Basic NLP Categorizer (TF-IDF + KMeans)")
                except Exception as e:
                    print(f"⚠️  All categorizers failed ({e}), using basic categorization")
                    clustered_emails = self.categorizer.categorize_emails(unread_emails)
            
            # Process each cluster separately
            all_summaries = []
            cluster_summaries = {}
            
            for category_name, category_emails in clustered_emails.items():
                category_summaries = self._process_email_batch(category_emails, category_name, options)
                all_summaries.extend(category_summaries)
                cluster_summaries[category_name] = category_summaries
            
            email_summaries = all_summaries
            
            # Generate overall summary with cluster information
            overall_parts = []
            for category_name, category_summaries in cluster_summaries.items():
                if category_summaries:
                    category_overall = self.ollama_client.generate_overall_summary(category_summaries)
                    overall_parts.append(f"{category_name.upper()}:\n{category_overall}")
            
            overall_summary = "\n\n".join(overall_parts) if overall_parts else "No emails found."
            
            # For backward compatibility, try to identify commercial/personal clusters
            commercial_emails, personal_emails = self._map_clusters_to_legacy_categories(clustered_emails)
            
        else:
            # Process all emails together
            email_summaries = self._process_email_batch(unread_emails, "All", options)
            commercial_emails, personal_emails = [], []
            overall_summary = self.ollama_client.generate_overall_summary(email_summaries)
        
        # Print final processing summary
        print(f"\n📊 Final Email Processing Summary:")
        high_priority = len([e for e in email_summaries if e['priority'] == 'High'])
        medium_priority = len([e for e in email_summaries if e['priority'] == 'Medium'])
        low_priority = len([e for e in email_summaries if e['priority'] == 'Low'])
        total_actions = sum(len(e['action_items']) for e in email_summaries)
        need_response = len([e for e in email_summaries if e['requires_response']])
        
        if options.get('categorize_emails', False):
            if isinstance(commercial_emails, list) and isinstance(personal_emails, list):
                print(f"   🏢 Commercial Emails: {len(commercial_emails)}")
                print(f"   👤 Personal Emails: {len(personal_emails)}")
            else:
                # Show cluster statistics instead
                print(f"   📊 Email Clusters: {len(clustered_emails) if 'clustered_emails' in locals() else 'N/A'}")
                if 'clustered_emails' in locals():
                    for category_name, category_emails in clustered_emails.items():
                        print(f"      📂 {category_name}: {len(category_emails)} emails")
        
        print(f"   📈 High Priority: {high_priority} emails")
        print(f"   📊 Medium Priority: {medium_priority} emails")
        print(f"   📉 Low Priority: {low_priority} emails")
        print(f"   ⚡ Total Action Items: {total_actions}")
        print(f"   ⚠️  Need Response: {need_response} emails")
        
        # Calculate statistics
        high_priority_count = len([e for e in email_summaries if e['priority'] == 'High'])
        action_items_total = sum(len(e['action_items']) for e in email_summaries)
        
        result = {
            'total_emails': len(unread_emails),
            'email_summaries': email_summaries,
            'overall_summary': overall_summary,
            'high_priority_count': high_priority_count,
            'action_items_total': action_items_total,
            'processed_at': datetime.now().isoformat(),
            'commercial_emails': commercial_emails,
            'personal_emails': personal_emails,
            'categorization_enabled': options.get('categorize_emails', False)
        }
        
        logging.info(f"Email processing completed. {len(email_summaries)} emails processed")
        return result
    
    def _process_email_batch(self, emails: List[Dict], category: str, options: Dict) -> List[Dict]:
        """Process a batch of emails (commercial, personal, or all)"""
        if not emails:
            return []
        
        email_summaries = []
        
        print(f"\n🔄 Processing {category} Emails ({len(emails)} emails)")
        
        # Create progress bar
        progress_bar = tqdm(
            emails, 
            desc=f"🤖 AI Processing {category}", 
            unit="email",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} emails [{elapsed}<{remaining}, {rate_fmt}]'
        )
        
        for i, email_data in enumerate(progress_bar, 1):
            try:
                # Detailed email info
                sender_short = email_data['sender'].split('@')[0][:20]
                subject_short = email_data['subject'][:25] + "..." if len(email_data['subject']) > 25 else email_data['subject']
                
                # Update progress bar with current email details
                progress_bar.set_description(f"🤖 {category} ({i}/{len(emails)})")
                progress_bar.set_postfix_str(f"{sender_short}: '{subject_short}'")
                
                # Print detailed processing info
                print(f"\n📧 Processing {category} Email {i}/{len(emails)}:")
                print(f"   📤 From: {email_data['sender']}")
                print(f"   📝 Subject: {email_data['subject']}")
                print(f"   📅 Date: {email_data['date']}")
                print(f"   📏 Content length: {len(email_data['body'])} characters")
                print(f"   🤖 Sending to {self.ollama_client.model} for analysis...")
                
                summary = self.ollama_client.summarize_email(email_data)
                
                # Print AI analysis results
                print(f"   ✅ AI Analysis Complete:")
                print(f"      🏷️  Priority: {summary['priority']}")
                print(f"      📋 Summary: {summary['summary'][:100]}{'...' if len(summary['summary']) > 100 else ''}")
                if summary['action_items']:
                    print(f"      ⚡ Action Items: {len(summary['action_items'])} found")
                    for j, item in enumerate(summary['action_items'][:2], 1):  # Show first 2
                        print(f"         {j}. {item}")
                    if len(summary['action_items']) > 2:
                        print(f"         ... and {len(summary['action_items'])-2} more")
                else:
                    print(f"      ⚡ Action Items: None")
                
                if summary['requires_response']:
                    print(f"      ⚠️  Requires Response: YES")
                
                email_summaries.append({
                    'email_id': email_data['id'],
                    'sender': email_data['sender'],
                    'subject': email_data['subject'],
                    'date': email_data['date'],
                    'summary': summary['summary'],
                    'action_items': summary['action_items'],
                    'priority': summary['priority'],
                    'requires_response': summary['requires_response'],
                    'category': category.lower()  # Add category to each email
                })
                
                # Update progress bar with completion status
                progress_bar.set_postfix(status=f"✅ {summary['priority']}")
                
            except Exception as e:
                print(f"   ❌ Error processing email: {e}")
                logging.error(f"Error processing email from {email_data['sender']}: {e}")
                email_summaries.append({
                    'email_id': email_data['id'],
                    'sender': email_data['sender'],
                    'subject': email_data['subject'],
                    'date': email_data['date'],
                    'summary': 'Error processing this email',
                    'action_items': [],
                    'priority': 'Medium',
                    'requires_response': False,
                    'category': category.lower()
                })
                progress_bar.set_postfix(status="❌ Error")
        
        # Close progress bar
        progress_bar.close()
        
        # Print batch summary
        if emails:
            high_priority = len([e for e in email_summaries if e['priority'] == 'High'])
            medium_priority = len([e for e in email_summaries if e['priority'] == 'Medium'])
            low_priority = len([e for e in email_summaries if e['priority'] == 'Low'])
            total_actions = sum(len(e['action_items']) for e in email_summaries)
            need_response = len([e for e in email_summaries if e['requires_response']])
            
            print(f"\n📊 {category} Email Summary:")
            print(f"   📈 High Priority: {high_priority} emails")
            print(f"   📊 Medium Priority: {medium_priority} emails")
            print(f"   📉 Low Priority: {low_priority} emails")
            print(f"   ⚡ Action Items: {total_actions}")
            print(f"   ⚠️  Need Response: {need_response} emails")
        
        return email_summaries
    
    def _map_clusters_to_legacy_categories(self, clustered_emails: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:
        """Map NLP clusters to legacy commercial/personal categories for backward compatibility"""
        commercial_emails = []
        personal_emails = []
        
        # Keywords that suggest commercial/marketing content
        commercial_keywords = ['marketing', 'notification', 'newsletter', 'transactional', 'support', 'sale', 'offer']
        personal_keywords = ['work', 'meeting', 'social', 'personal', 'friend']
        
        for category_name, category_emails in clustered_emails.items():
            category_lower = category_name.lower()
            
            # Determine if this cluster is more commercial or personal
            is_commercial = any(keyword in category_lower for keyword in commercial_keywords)
            is_personal = any(keyword in category_lower for keyword in personal_keywords)
            
            if is_commercial and not is_personal:
                commercial_emails.extend(category_emails)
            elif is_personal and not is_commercial:
                personal_emails.extend(category_emails)
            else:
                # Default unknown categories to commercial
                commercial_emails.extend(category_emails)
        
        return commercial_emails, personal_emails
    
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