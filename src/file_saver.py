import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

class FileSaver:
    def __init__(self, output_dir: str = "summaries"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"Created output directory: {self.output_dir}")
    
    def save_summary(self, processing_result: Dict[str, Any], text_summary: str, html_summary: str, voice_file_path: Optional[str] = None) -> Dict[str, str]:
        """Save email summary to local files with categorization support"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check if categorization was enabled
        categorization_enabled = processing_result.get('categorization_enabled', False)
        
        if categorization_enabled:
            # Save separate files for commercial and personal emails
            return self._save_categorized_summary(processing_result, text_summary, html_summary, voice_file_path, timestamp)
        else:
            # Save unified summary
            return self._save_unified_summary(processing_result, text_summary, html_summary, voice_file_path, timestamp)
    
    def _save_unified_summary(self, processing_result: Dict[str, Any], text_summary: str, html_summary: str, voice_file_path: Optional[str], timestamp: str) -> Dict[str, str]:
        """Save unified email summary files"""
        base_filename = f"email_summary_{timestamp}"
        saved_files = {}
        
        try:
            # Save JSON data
            json_path = os.path.join(self.output_dir, f"{base_filename}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(processing_result, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_path
            logging.info(f"Saved JSON summary: {json_path}")
            
            # Save text summary
            text_path = os.path.join(self.output_dir, f"{base_filename}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_summary)
            saved_files['text'] = text_path
            logging.info(f"Saved text summary: {text_path}")
            
            # Save HTML summary
            html_path = os.path.join(self.output_dir, f"{base_filename}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_summary)
            saved_files['html'] = html_path
            logging.info(f"Saved HTML summary: {html_path}")
            
            # Copy voice file if provided
            if voice_file_path and os.path.exists(voice_file_path):
                voice_dest = os.path.join(self.output_dir, f"{base_filename}_voice.mp3")
                import shutil
                shutil.copy2(voice_file_path, voice_dest)
                saved_files['voice'] = voice_dest
                logging.info(f"Saved voice summary: {voice_dest}")
            
            # Create summary index file
            self._update_index(base_filename, processing_result, saved_files)
            
            logging.info(f"Email summary saved successfully with {len(saved_files)} files")
            return saved_files
            
        except Exception as e:
            logging.error(f"Failed to save summary files: {e}")
            return {}
    
    def _save_categorized_summary(self, processing_result: Dict[str, Any], text_summary: str, html_summary: str, voice_file_path: Optional[str], timestamp: str) -> Dict[str, str]:
        """Save categorized email summary files"""
        base_filename = f"email_summary_categorized_{timestamp}"
        saved_files = {}
        
        try:
            # Save main JSON data
            json_path = os.path.join(self.output_dir, f"{base_filename}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(processing_result, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_path
            logging.info(f"Saved categorized JSON summary: {json_path}")
            
            # Save unified text and HTML summaries (contains both categories)
            text_path = os.path.join(self.output_dir, f"{base_filename}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_summary)
            saved_files['text'] = text_path
            
            html_path = os.path.join(self.output_dir, f"{base_filename}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_summary)
            saved_files['html'] = html_path
            
            # Create separate commercial and personal reports
            commercial_emails = processing_result.get('commercial_emails', [])
            personal_emails = processing_result.get('personal_emails', [])
            
            if commercial_emails:
                commercial_result = self._create_category_result(processing_result, commercial_emails, 'commercial')
                commercial_text = self._create_category_text_summary(commercial_result, 'Commercial')
                commercial_html = self._create_category_html_summary(commercial_result, 'Commercial')
                
                # Save commercial files
                comm_text_path = os.path.join(self.output_dir, f"{base_filename}_commercial.txt")
                with open(comm_text_path, 'w', encoding='utf-8') as f:
                    f.write(commercial_text)
                saved_files['commercial_text'] = comm_text_path
                
                comm_html_path = os.path.join(self.output_dir, f"{base_filename}_commercial.html")
                with open(comm_html_path, 'w', encoding='utf-8') as f:
                    f.write(commercial_html)
                saved_files['commercial_html'] = comm_html_path
                
                logging.info(f"Saved commercial email reports: {len(commercial_emails)} emails")
            
            if personal_emails:
                personal_result = self._create_category_result(processing_result, personal_emails, 'personal')
                personal_text = self._create_category_text_summary(personal_result, 'Personal')
                personal_html = self._create_category_html_summary(personal_result, 'Personal')
                
                # Save personal files
                pers_text_path = os.path.join(self.output_dir, f"{base_filename}_personal.txt")
                with open(pers_text_path, 'w', encoding='utf-8') as f:
                    f.write(personal_text)
                saved_files['personal_text'] = pers_text_path
                
                pers_html_path = os.path.join(self.output_dir, f"{base_filename}_personal.html")
                with open(pers_html_path, 'w', encoding='utf-8') as f:
                    f.write(personal_html)
                saved_files['personal_html'] = pers_html_path
                
                logging.info(f"Saved personal email reports: {len(personal_emails)} emails")
            
            # Copy voice file if provided
            if voice_file_path and os.path.exists(voice_file_path):
                voice_dest = os.path.join(self.output_dir, f"{base_filename}_voice.mp3")
                import shutil
                shutil.copy2(voice_file_path, voice_dest)
                saved_files['voice'] = voice_dest
                logging.info(f"Saved voice summary: {voice_dest}")
            
            # Create summary index file
            self._update_categorized_index(base_filename, processing_result, saved_files)
            
            logging.info(f"Categorized email summary saved successfully with {len(saved_files)} files")
            return saved_files
            
        except Exception as e:
            logging.error(f"Failed to save categorized summary files: {e}")
            return {}
    
    def _create_category_result(self, original_result: Dict[str, Any], category_emails: list, category: str) -> Dict[str, Any]:
        """Create a result dict for a specific category"""
        # Filter email summaries for this category
        category_summaries = [email for email in original_result.get('email_summaries', []) if email.get('category', '').lower() == category]
        
        # Calculate stats for this category
        high_priority_count = len([e for e in category_summaries if e['priority'] == 'High'])
        action_items_total = sum(len(e['action_items']) for e in category_summaries)
        
        return {
            'total_emails': len(category_emails),
            'email_summaries': category_summaries,
            'high_priority_count': high_priority_count,
            'action_items_total': action_items_total,
            'processed_at': original_result.get('processed_at'),
            'category': category.title()
        }
    
    def _create_category_text_summary(self, category_result: Dict[str, Any], category_name: str) -> str:
        """Create text summary for a specific category"""
        email_summaries = category_result['email_summaries']
        
        text = f"""
{category_name.upper()} EMAIL SUMMARY REPORT
Generated: {category_result['processed_at']}
Total {category_name} Emails: {category_result['total_emails']}
High Priority: {category_result['high_priority_count']}
Total Action Items: {category_result['action_items_total']}

INDIVIDUAL {category_name.upper()} EMAIL SUMMARIES:
"""
        
        # Group by priority
        high_priority = [e for e in email_summaries if e['priority'] == 'High']
        medium_priority = [e for e in email_summaries if e['priority'] == 'Medium']
        low_priority = [e for e in email_summaries if e['priority'] == 'Low']
        
        for priority_group, title in [(high_priority, "HIGH PRIORITY"), 
                                     (medium_priority, "MEDIUM PRIORITY"), 
                                     (low_priority, "LOW PRIORITY")]:
            if priority_group:
                text += f"\n{title} {category_name.upper()} EMAILS:\n"
                text += "-" * (len(title) + len(category_name) + 8) + "\n"
                
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
    
    def _create_category_html_summary(self, category_result: Dict[str, Any], category_name: str) -> str:
        """Create HTML summary for a specific category"""
        email_summaries = category_result['email_summaries']
        category_icon = "🏢" if category_name.lower() == "commercial" else "👤"
        
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
                <h1>{category_icon} {category_name} Email Summary Report</h1>
                <p><strong>Generated:</strong> {category_result['processed_at']}</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h3>{category_result['total_emails']}</h3>
                    <p>Total {category_name} Emails</p>
                </div>
                <div class="stat">
                    <h3>{category_result['high_priority_count']}</h3>
                    <p>High Priority</p>
                </div>
                <div class="stat">
                    <h3>{category_result['action_items_total']}</h3>
                    <p>Action Items</p>
                </div>
            </div>
            
            <h2>📬 Individual {category_name} Email Summaries</h2>
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
    
    def _update_index(self, base_filename: str, processing_result: Dict[str, Any], saved_files: Dict[str, str]):
        """Update index file with summary information"""
        index_path = os.path.join(self.output_dir, "index.json")
        
        # Load existing index or create new one
        index_data = []
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load existing index: {e}")
                index_data = []
        
        # Add new entry
        new_entry = {
            'timestamp': processing_result.get('processed_at'),
            'base_filename': base_filename,
            'total_emails': processing_result.get('total_emails', 0),
            'high_priority_count': processing_result.get('high_priority_count', 0),
            'action_items_total': processing_result.get('action_items_total', 0),
            'files': saved_files,
            'categorized': False
        }
        
        index_data.append(new_entry)
        
        # Keep only last 100 entries
        if len(index_data) > 100:
            index_data = index_data[-100:]
        
        # Save updated index
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Updated summary index: {index_path}")
        except Exception as e:
            logging.error(f"Failed to update index: {e}")
    
    def _update_categorized_index(self, base_filename: str, processing_result: Dict[str, Any], saved_files: Dict[str, str]):
        """Update index file with categorized summary information"""
        index_path = os.path.join(self.output_dir, "index.json")
        
        # Load existing index or create new one
        index_data = []
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load existing index: {e}")
                index_data = []
        
        # Add new entry with categorization info
        new_entry = {
            'timestamp': processing_result.get('processed_at'),
            'base_filename': base_filename,
            'total_emails': processing_result.get('total_emails', 0),
            'commercial_emails': len(processing_result.get('commercial_emails', [])),
            'personal_emails': len(processing_result.get('personal_emails', [])),
            'high_priority_count': processing_result.get('high_priority_count', 0),
            'action_items_total': processing_result.get('action_items_total', 0),
            'files': saved_files,
            'categorized': True
        }
        
        index_data.append(new_entry)
        
        # Keep only last 100 entries
        if len(index_data) > 100:
            index_data = index_data[-100:]
        
        # Save updated index
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Updated categorized summary index: {index_path}")
        except Exception as e:
            logging.error(f"Failed to update index: {e}")
    
    def get_recent_summaries(self, limit: int = 10) -> list:
        """Get list of recent summaries"""
        index_path = os.path.join(self.output_dir, "index.json")
        
        if not os.path.exists(index_path):
            return []
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Return most recent summaries
            return index_data[-limit:][::-1]  # Reverse to get newest first
            
        except Exception as e:
            logging.error(f"Failed to load recent summaries: {e}")
            return []
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up summary files older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for filename in os.listdir(self.output_dir):
                if filename == "index.json":
                    continue
                
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logging.info(f"Cleaned up old file: {filename}")
                        
        except Exception as e:
            logging.error(f"Failed to cleanup old files: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get statistics about saved summaries"""
        try:
            if not os.path.exists(self.output_dir):
                return {'total_summaries': 0, 'total_files': 0, 'disk_usage': 0}
            
            files = os.listdir(self.output_dir)
            total_files = len(files)
            
            # Count summary sets (each summary creates multiple files)
            json_files = len([f for f in files if f.endswith('.json') and f != 'index.json'])
            
            # Calculate disk usage
            total_size = 0
            for filename in files:
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_summaries': json_files,
                'total_files': total_files,
                'disk_usage': total_size,
                'disk_usage_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logging.error(f"Failed to get summary stats: {e}")
            return {'error': str(e)}