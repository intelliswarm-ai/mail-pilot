import os
import tempfile
from gtts import gTTS
import logging
from typing import Optional

class VoiceGenerator:
    def __init__(self, language: str = 'en', enabled: bool = True):
        self.language = language
        self.enabled = enabled
    
    def generate_voice_summary(self, summary_text: str, output_dir: str = None) -> Optional[str]:
        if not self.enabled:
            logging.info("Voice generation is disabled")
            return None
        
        try:
            # Clean the text for speech
            clean_text = self._clean_text_for_speech(summary_text)
            
            # Create TTS object
            tts = gTTS(text=clean_text, lang=self.language, slow=False)
            
            # Determine output path
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, "email_summary_voice.mp3")
            else:
                # Use temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                output_path = temp_file.name
                temp_file.close()
            
            # Save the audio file
            tts.save(output_path)
            
            logging.info(f"Voice summary generated: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Failed to generate voice summary: {e}")
            return None
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more suitable for text-to-speech"""
        
        # Remove markdown formatting
        cleaned = text.replace('**', '')
        cleaned = cleaned.replace('*', '')
        cleaned = cleaned.replace('#', '')
        cleaned = cleaned.replace('_', '')
        
        # Replace common symbols with words
        cleaned = cleaned.replace('&', ' and ')
        cleaned = cleaned.replace('@', ' at ')
        cleaned = cleaned.replace('%', ' percent')
        cleaned = cleaned.replace('$', ' dollars')
        cleaned = cleaned.replace('€', ' euros')
        
        # Replace HTML entities if any
        cleaned = cleaned.replace('&amp;', ' and ')
        cleaned = cleaned.replace('&lt;', ' less than ')
        cleaned = cleaned.replace('&gt;', ' greater than ')
        
        # Clean up emojis and special characters
        cleaned = cleaned.replace('📧', 'Email ')
        cleaned = cleaned.replace('📋', 'Summary ')
        cleaned = cleaned.replace('📬', '')
        cleaned = cleaned.replace('🔴', 'High Priority ')
        cleaned = cleaned.replace('🟡', 'Medium Priority ')
        cleaned = cleaned.replace('🟢', 'Low Priority ')
        cleaned = cleaned.replace('⚠️', 'Warning ')
        cleaned = cleaned.replace('•', '')
        
        # Remove excessive whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Limit length for voice generation (TTS services often have limits)
        if len(cleaned) > 5000:
            cleaned = cleaned[:4900] + "... Summary truncated for voice generation."
        
        return cleaned
    
    def create_voice_summary_text(self, processing_result: dict) -> str:
        """Create a text specifically formatted for voice narration"""
        
        total_emails = processing_result['total_emails']
        high_priority = processing_result['high_priority_count']
        action_items = processing_result['action_items_total']
        
        # Start with overview
        voice_text = f"""
        Email Summary Report. 
        
        You have {total_emails} unread emails in your inbox. 
        """
        
        if high_priority > 0:
            voice_text += f"{high_priority} of these are high priority and require immediate attention. "
        
        if action_items > 0:
            voice_text += f"There are {action_items} total action items across all emails. "
        
        # Add overall summary
        voice_text += f"Overall summary: {processing_result['overall_summary']} "
        
        # Add high priority details
        email_summaries = processing_result['email_summaries']
        high_priority_emails = [e for e in email_summaries if e['priority'] == 'High']
        
        if high_priority_emails:
            voice_text += "High priority emails include: "
            for i, email in enumerate(high_priority_emails[:3]):  # Limit to top 3
                voice_text += f"Email {i+1}: From {email['sender']}. "
                voice_text += f"Subject: {email['subject']}. "
                voice_text += f"Summary: {email['summary']} "
                
                if email['action_items']:
                    voice_text += f"Action items: {'. '.join(email['action_items'])}. "
                
                if email['requires_response']:
                    voice_text += "This email requires a response. "
        
        # Add medium priority summary if space allows
        medium_priority_emails = [e for e in email_summaries if e['priority'] == 'Medium']
        if medium_priority_emails and len(voice_text) < 3000:
            voice_text += f"You also have {len(medium_priority_emails)} medium priority emails "
            
            # Mention a few senders
            senders = [email['sender'].split('@')[0] for email in medium_priority_emails[:3]]
            voice_text += f"from {', '.join(senders)}. "
        
        voice_text += "End of email summary. Check your email for the detailed report."
        
        return voice_text
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary voice files"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logging.info(f"Cleaned up temporary voice file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to cleanup voice file {file_path}: {e}")