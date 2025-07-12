import re
import logging
from typing import Dict, List, Tuple

class EmailCategorizer:
    def __init__(self):
        # Commercial email indicators
        self.commercial_domains = {
            'noreply', 'no-reply', 'donotreply', 'newsletter', 'marketing', 
            'promo', 'offers', 'deals', 'sales', 'notifications', 'updates',
            'info', 'support', 'service', 'hello', 'team', 'contact'
        }
        
        self.commercial_keywords = {
            # Promotional/Marketing
            'unsubscribe', 'promotion', 'discount', 'sale', 'offer', 'deal',
            'coupon', 'limited time', 'act now', 'don\'t miss', 'special offer',
            'free shipping', 'black friday', 'cyber monday', 'clearance',
            
            # Newsletter/Updates
            'newsletter', 'digest', 'weekly update', 'monthly report',
            'news update', 'announcement', 'press release',
            
            # Automated/System
            'automated', 'automatic', 'system generated', 'no reply',
            'confirmation', 'receipt', 'invoice', 'billing', 'payment',
            'subscription', 'renewal', 'expiring', 'expires',
            
            # Social/Platform notifications
            'notification', 'activity', 'mentioned you', 'tagged you',
            'friend request', 'connection', 'follower', 'like', 'comment',
            
            # E-commerce
            'order', 'shipment', 'tracking', 'delivered', 'return',
            'refund', 'cart', 'wishlist', 'recommendation'
        }
        
        self.commercial_companies = {
            'amazon', 'ebay', 'paypal', 'stripe', 'square', 'shopify',
            'mailchimp', 'constant contact', 'sendgrid', 'mandrill',
            'facebook', 'twitter', 'linkedin', 'instagram', 'youtube',
            'google', 'microsoft', 'apple', 'adobe', 'salesforce',
            'hubspot', 'zendesk', 'intercom', 'slack', 'zoom',
            'dropbox', 'spotify', 'netflix', 'hulu', 'disney'
        }
        
        # Personal email indicators
        self.personal_indicators = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'live.com', 'msn.com'
        }
        
        self.personal_keywords = {
            'personal', 'private', 'family', 'friend', 'birthday',
            'wedding', 'invitation', 'meeting', 'lunch', 'dinner',
            'vacation', 'holiday', 'weekend', 'party', 'gathering'
        }
    
    def categorize_emails(self, emails: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Categorize emails into commercial and personal
        Returns: (commercial_emails, personal_emails)
        """
        commercial_emails = []
        personal_emails = []
        
        print(f"\n🔍 Categorizing {len(emails)} emails...")
        
        for email in emails:
            category = self._categorize_single_email(email)
            
            if category == 'commercial':
                commercial_emails.append(email)
            else:
                personal_emails.append(email)
            
            # Log categorization decision
            sender_short = email['sender'].split('@')[0][:20]
            logging.debug(f"Categorized {sender_short}: {category}")
        
        print(f"📊 Categorization complete:")
        print(f"   🏢 Commercial: {len(commercial_emails)} emails")
        print(f"   👤 Personal: {len(personal_emails)} emails")
        
        return commercial_emails, personal_emails
    
    def _categorize_single_email(self, email: Dict) -> str:
        """Categorize a single email as 'commercial' or 'personal'"""
        sender = email['sender'].lower()
        subject = email['subject'].lower()
        body = email['body'].lower()
        
        commercial_score = 0
        personal_score = 0
        
        # Check sender domain and address
        commercial_score += self._check_sender_commercial(sender)
        personal_score += self._check_sender_personal(sender)
        
        # Check subject line
        commercial_score += self._check_content_commercial(subject)
        personal_score += self._check_content_personal(subject)
        
        # Check email body (limited to avoid processing delay)
        body_sample = body[:500]  # First 500 characters
        commercial_score += self._check_content_commercial(body_sample)
        personal_score += self._check_content_personal(body_sample)
        
        # Check for automated/system patterns
        if self._is_automated_email(sender, subject, body_sample):
            commercial_score += 3
        
        # Check for personal email patterns
        if self._is_personal_email(sender, subject):
            personal_score += 3
        
        # Make decision
        if commercial_score > personal_score:
            return 'commercial'
        else:
            return 'personal'
    
    def _check_sender_commercial(self, sender: str) -> int:
        """Check sender for commercial indicators"""
        score = 0
        
        # Check for noreply/automated domains
        for domain_keyword in self.commercial_domains:
            if domain_keyword in sender:
                score += 2
                break
        
        # Check for known commercial companies
        for company in self.commercial_companies:
            if company in sender:
                score += 2
                break
        
        # Check for organizational domains (not personal email providers)
        if '@' in sender:
            domain = sender.split('@')[1]
            if not any(personal_domain in domain for personal_domain in self.personal_indicators):
                # If it's not a personal email provider, likely commercial
                score += 1
        
        return score
    
    def _check_sender_personal(self, sender: str) -> int:
        """Check sender for personal indicators"""
        score = 0
        
        # Check for personal email providers
        for provider in self.personal_indicators:
            if provider in sender:
                score += 2
                break
        
        return score
    
    def _check_content_commercial(self, content: str) -> int:
        """Check content for commercial keywords"""
        score = 0
        
        for keyword in self.commercial_keywords:
            if keyword in content:
                score += 1
        
        return min(score, 5)  # Cap at 5 points
    
    def _check_content_personal(self, content: str) -> int:
        """Check content for personal keywords"""
        score = 0
        
        for keyword in self.personal_keywords:
            if keyword in content:
                score += 1
        
        return min(score, 3)  # Cap at 3 points
    
    def _is_automated_email(self, sender: str, subject: str, body: str) -> bool:
        """Check if email appears to be automated/system generated"""
        automated_patterns = [
            r'no.?reply', r'do.?not.?reply', r'automated', r'system',
            r'notification', r'confirmation', r'receipt'
        ]
        
        content = f"{sender} {subject} {body}"
        
        for pattern in automated_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _is_personal_email(self, sender: str, subject: str) -> bool:
        """Check if email appears to be personal"""
        # Check for personal name patterns (First Last format)
        sender_name = sender.split('@')[0]
        
        # Simple heuristic: contains both letters and possibly dots/underscores
        # but not obvious commercial patterns
        if re.match(r'^[a-z]+[\._]?[a-z]+$', sender_name):
            return True
        
        # Check for personal subject patterns
        personal_subject_patterns = [
            r'\bre:?\s', r'\bfwd?:?\s', r'\bhello\b', r'\bhi\b',
            r'\bthanks?\b', r'\bmeeting\b', r'\bquestion\b'
        ]
        
        for pattern in personal_subject_patterns:
            if re.search(pattern, subject, re.IGNORECASE):
                return True
        
        return False
    
    def get_category_stats(self, commercial_emails: List[Dict], personal_emails: List[Dict]) -> Dict:
        """Get statistics about email categories"""
        total = len(commercial_emails) + len(personal_emails)
        
        if total == 0:
            return {
                'total': 0,
                'commercial_count': 0,
                'personal_count': 0,
                'commercial_percentage': 0,
                'personal_percentage': 0
            }
        
        return {
            'total': total,
            'commercial_count': len(commercial_emails),
            'personal_count': len(personal_emails),
            'commercial_percentage': round(len(commercial_emails) / total * 100, 1),
            'personal_percentage': round(len(personal_emails) / total * 100, 1)
        }