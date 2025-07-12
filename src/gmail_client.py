import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import email
from typing import List, Dict, Any
import logging

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        print("🔐 Starting Gmail authentication process...")
        logging.info(f"Looking for credentials at: {self.credentials_path}")
        logging.info(f"Looking for token at: {self.token_path}")
        
        creds = None
        if os.path.exists(self.token_path):
            print("🎫 Found existing authentication token, loading...")
            logging.info("Loading existing authentication token")
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        else:
            print("🆕 No existing token found, will need fresh authentication")
            logging.info("No existing token found")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Token expired, refreshing...")
                logging.info("Refreshing expired token")
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            else:
                print("🌐 Starting OAuth2 flow - browser will open...")
                logging.info("Starting OAuth2 flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ OAuth2 authentication completed")
            
            print("💾 Saving authentication token for future use...")
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            logging.info("Authentication token saved")
        else:
            print("✅ Using valid existing authentication token")
        
        print("🔗 Establishing Gmail API connection...")
        self.service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile to show which account is connected
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress', 'Unknown')
            total_messages = profile.get('messagesTotal', 'Unknown')
            print(f"✅ Successfully connected to Gmail account: {email_address}")
            print(f"📊 Account has {total_messages} total messages")
            logging.info(f"Gmail API authenticated successfully for {email_address}")
        except Exception as e:
            print("✅ Gmail API connection established (profile info unavailable)")
            logging.info("Gmail API authenticated successfully")
    
    def get_unread_messages(self, query: str = 'is:unread') -> List[Dict[str, Any]]:
        try:
            print("📧 Connecting to Gmail...")
            logging.info(f"Fetching messages with query: {query}")
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📬 Found {len(messages)} unread messages")
            logging.info(f"Found {len(messages)} unread messages to process")
            unread_emails = []
            
            if len(messages) > 0:
                print("📥 Downloading email content...")
                from tqdm import tqdm
                
                # Progress bar for email downloading
                progress_bar = tqdm(
                    messages, 
                    desc="📥 Downloading", 
                    unit="email",
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} emails [{elapsed}<{remaining}]'
                )
                
                for message in progress_bar:
                    msg = self.service.users().messages().get(
                        userId='me', id=message['id'], format='full'
                    ).execute()
                    
                    email_data = self._parse_message(msg)
                    sender_short = email_data['sender'].split('@')[0][:20]
                    subject_short = email_data['subject'][:30] + "..." if len(email_data['subject']) > 30 else email_data['subject']
                    
                    progress_bar.set_description(f"📥 Downloaded: {sender_short}")
                    progress_bar.set_postfix_str(f"'{subject_short}'")
                    
                    # Log detailed info about each email
                    logging.info(f"Downloaded email: '{email_data['subject']}' from {email_data['sender']} ({email_data['date']})")
                    
                    unread_emails.append(email_data)
                
                progress_bar.close()
                print("✅ All emails downloaded successfully")
            
            logging.info(f"Successfully retrieved {len(unread_emails)} unread messages")
            return unread_emails
            
        except Exception as e:
            logging.error(f"Error retrieving unread messages: {e}")
            return []
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        headers = message['payload'].get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        body = self._extract_body(message['payload'])
        
        return {
            'id': message['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body
        }
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body[:1000]  # Reduced body length for faster processing
    
    def mark_as_read(self, message_id: str):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logging.info(f"Marked message {message_id} as read")
        except Exception as e:
            logging.error(f"Error marking message as read: {e}")