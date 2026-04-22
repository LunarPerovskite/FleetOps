"""Email Service Adapters for FleetOps

SendGrid, Resend, Mailgun, AWS SES, SMTP
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

class BaseEmailAdapter(ABC):
    """Abstract email adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.default_from = config.get("from_email", "fleetops@example.com")
    
    @abstractmethod
    async def send_email(self, to: str, subject: str, 
                        body: str, html: str = None) -> Dict:
        """Send email"""
        pass
    
    @abstractmethod
    async def send_bulk(self, recipients: List[str], subject: str,
                       body: str, html: str = None) -> Dict:
        """Send bulk email"""
        pass
    
    @abstractmethod
    async def get_status(self, message_id: str) -> Dict:
        """Get email status"""
        pass

class SendGridAdapter(BaseEmailAdapter):
    """SendGrid email adapter"""
    
    PROVIDER_NAME = "sendgrid"
    
    def __init__(self, api_key: str = None, from_email: str = None):
        super().__init__({"api_key": api_key, "from_email": from_email})
        self.api_key = api_key
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send_email(self, to: str, subject: str,
                        body: str, html: str = None) -> Dict:
        """Send email via SendGrid"""
        import requests
        
        try:
            payload = {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": self.default_from},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body}
                ]
            }
            
            if html:
                payload["content"].append(
                    {"type": "text/html", "value": html}
                )
            
            response = requests.post(
                f"{self.base_url}/mail/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 202:
                return {
                    "status": "sent",
                    "provider": "sendgrid",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "status": "error",
                "message": response.text
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def send_bulk(self, recipients: List[str], subject: str,
                       body: str, html: str = None) -> Dict:
        """Send bulk email"""
        results = []
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body, html)
            results.append(result)
        
        return {
            "status": "completed",
            "total": len(recipients),
            "sent": sum(1 for r in results if r["status"] == "sent"),
            "failed": sum(1 for r in results if r["status"] == "error")
        }
    
    async def get_status(self, message_id: str) -> Dict:
        """Get email status from SendGrid"""
        return {"status": "unknown", "provider": "sendgrid"}

class ResendAdapter(BaseEmailAdapter):
    """Resend.com email adapter"""
    
    PROVIDER_NAME = "resend"
    
    def __init__(self, api_key: str = None, from_email: str = None):
        super().__init__({"api_key": api_key, "from_email": from_email})
        self.api_key = api_key
        self.base_url = "https://api.resend.com"
    
    async def send_email(self, to: str, subject: str,
                        body: str, html: str = None) -> Dict:
        """Send email via Resend"""
        import requests
        
        try:
            payload = {
                "from": self.default_from,
                "to": [to],
                "subject": subject,
                "text": body
            }
            
            if html:
                payload["html"] = html
            
            response = requests.post(
                f"{self.base_url}/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "sent",
                    "provider": "resend",
                    "message_id": data.get("id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "status": "error",
                "message": response.text
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def send_bulk(self, recipients: List[str], subject: str,
                       body: str, html: str = None) -> Dict:
        """Send bulk via Resend batch API"""
        import requests
        
        try:
            batch = []
            for recipient in recipients:
                email = {
                    "from": self.default_from,
                    "to": [recipient],
                    "subject": subject,
                    "text": body
                }
                if html:
                    email["html"] = html
                batch.append(email)
            
            response = requests.post(
                f"{self.base_url}/emails/batch",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=batch
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "sent",
                    "provider": "resend",
                    "total": len(data.get("data", [])),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_status(self, message_id: str) -> Dict:
        """Get email status from Resend"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/emails/{message_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": data.get("status", "unknown"),
                    "provider": "resend"
                }
            
            return {"status": "error"}
        except Exception:
            return {"status": "error"}

class SMTPAdapter(BaseEmailAdapter):
    """SMTP email adapter (for self-hosted)"""
    
    PROVIDER_NAME = "smtp"
    
    def __init__(self, host: str = "localhost", port: int = 587,
                 username: str = None, password: str = None,
                 from_email: str = None, use_tls: bool = True):
        super().__init__({
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "use_tls": use_tls
        })
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send_email(self, to: str, subject: str,
                        body: str, html: str = None) -> Dict:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.default_from
            msg["To"] = to
            
            # Add plain text
            msg.attach(MIMEText(body, "plain"))
            
            # Add HTML if provided
            if html:
                msg.attach(MIMEText(html, "html"))
            
            # Send
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return {
                "status": "sent",
                "provider": "smtp",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def send_bulk(self, recipients: List[str], subject: str,
                       body: str, html: str = None) -> Dict:
        """Send bulk via SMTP"""
        results = []
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body, html)
            results.append(result)
        
        return {
            "status": "completed",
            "total": len(recipients),
            "sent": sum(1 for r in results if r["status"] == "sent"),
            "failed": sum(1 for r in results if r["status"] == "error")
        }
    
    async def get_status(self, message_id: str) -> Dict:
        """SMTP doesn't support status tracking"""
        return {"status": "unknown", "provider": "smtp"}

# Registry
EMAIL_ADAPTERS = {
    "sendgrid": SendGridAdapter,
    "resend": ResendAdapter,
    "smtp": SMTPAdapter,
    "mailgun": SendGridAdapter,  # TODO: Implement Mailgun
    "aws_ses": SendGridAdapter  # TODO: Implement SES
}

def get_email_adapter(provider: str, config: Dict = None):
    """Get email adapter"""
    adapter_class = EMAIL_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown email provider: {provider}")
    
    return adapter_class(**(config or {}))
