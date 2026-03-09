import os
import pickle
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64

class GoogleService:
    """Manages Google API integrations (Gmail, Calendar, Drive)"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, credentials_path: str = "data/credentials.json"):
        self.creds = None
        self.creds_path = credentials_path
        self.token_path = "data/token.pickle"
        self.service = None
        
        # Ensure data dir exists
        os.makedirs(os.path.dirname(self.creds_path), exist_ok=True)
        
        # Load existing token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            except Exception:
                pass

    def authenticate(self, interactive: bool = False):
        """Handle OAuth2 flow. Requires credentials.json from Google Cloud Console."""
        if self.creds and self.creds.valid:
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
                self.service = build('gmail', 'v1', credentials=self.creds)
                return True
            except Exception:
                pass

        if not interactive:
            return False

        # Start interactive flow if we have credentials.json
        if not os.path.exists(self.creds_path):
            print(f"[Google] ERROR: Missing {self.creds_path}. Please download it from Google Cloud Console.")
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, self.SCOPES)
            self.creds = flow.run_local_server(port=0)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        except Exception as e:
            print(f"[Google] Auth Error: {e}")
            return False

    def get_unread_emails_summary(self, max_count: int = 3) -> Dict:
        """Fetch and briefly summarize unread emails"""
        if not self.authenticate():
            return {
                "success": False,
                "message": "Gmail integration is not set up. Please place 'credentials.json' in the data folder and authenticate."
            }
        
        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
            messages = results.get('messages', [])
            
            if not messages:
                return {"success": True, "message": "You have no unread emails.", "emails": []}
            
            emails = []
            for msg in messages[:max_count]:
                m = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = m['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From')
                
                # Simple summary of snippet
                snippet = m.get('snippet', '')
                emails.append({
                    "from": sender,
                    "subject": subject,
                    "snippet": snippet
                })
            
            # Formatting the response
            summary_msg = f"You have {len(messages)} unread emails. Here are the top {len(emails)}:\n"
            for i, email in enumerate(emails):
                summary_msg += f"{i+1}. From {email['from']}: {email['subject']}\n"
            
            return {
                "success": True, 
                "message": summary_msg, 
                "emails": emails, 
                "total_unread": len(messages)
            }
        except Exception as e:
            return {"success": False, "message": f"Could not fetch emails: {e}"}
