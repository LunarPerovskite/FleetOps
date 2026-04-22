"""Email Support Connector for FleetOps

Handles customer support via email with human escalation.
"""

import asyncio
import imaplib
import email
from typing import Optional
from datetime import datetime
from connectors.base import FleetOpsConnector, AgentConfig, AgentMode, AgentType

class EmailSupportConnector(FleetOpsConnector):
    """Email customer support agent with human escalation"""
    
    PROVIDER = "email"
    DEFAULT_MODEL = "gpt-4.1"
    
    def __init__(self, api_key: str, fleetops_url: str,
                 email_address: str, imap_server: str, imap_password: str,
                 name: str = "Email Support", level: str = "senior",
                 parent_agent_id: Optional[str] = None):
        config = AgentConfig(
            name=name, provider=self.PROVIDER, model=self.DEFAULT_MODEL,
            mode=AgentMode.CLOUD, agent_type=AgentType.EMAIL,
            capabilities=["email", "escalate", "ticket", "faq", "support"],
            level=level, parent_agent_id=parent_agent_id,
            metadata={
                "email_address": email_address,
                "imap_server": imap_server,
                "channels": ["email"]
            }
        )
        super().__init__(api_key, fleetops_url, config)
        self.email_address = email_address
        self.imap_server = imap_server
        self.imap_password = imap_password
        self.tickets: dict = {}
    
    async def handle_email(self, message_id: str, from_address: str,
                          subject: str, body: str):
        """Handle incoming email"""
        # Create ticket ID from message_id
        ticket_id = f"email_{message_id}"
        
        # Check for escalation keywords
        if await self._needs_escalation(subject + " " + body):
            await self.request_approval(
                task_id=ticket_id, stage="email_support",
                required_role="operator", sla_minutes=60,
                context={
                    "from": from_address,
                    "subject": subject,
                    "body_preview": body[:500],
                    "channel": "email"
                }
            )
            return {"status": "escalated", "ticket_id": ticket_id}
        
        # Auto-respond
        response = await self._generate_response(subject, body)
        
        await self.report_task_event(
            task_id=ticket_id, status="completed", stage="auto_response",
            data={
                "from": from_address,
                "subject": subject,
                "response": response,
                "channel": "email"
            }
        )
        
        return {"status": "responded", "response": response}
    
    async def _needs_escalation(self, text: str) -> bool:
        keywords = ["urgent", "asap", "emergency", "complaint", "refund",
                   "chargeback", "fraud", "legal", "lawyer", "sue", "escalate",
                   "manager", "supervisor", "human", "angry", "frustrated"]
        return any(kw in text.lower() for kw in keywords)
    
    async def _generate_response(self, subject: str, body: str) -> str:
        return f"Thank you for contacting us regarding: {subject}\n\nWe have received your inquiry and will respond within 24 hours."
    
    async def poll_emails(self):
        """Poll IMAP for new emails"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.imap_password)
            mail.select('inbox')
            
            _, data = mail.search(None, 'UNSEEN')
            email_ids = data[0].split()
            
            for e_id in email_ids:
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                from_addr = msg['from']
                subject = msg['subject']
                
                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                await self.handle_email(str(e_id), from_addr, subject, body)
            
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"Email polling error: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="https://api.fleetops.io")
    parser.add_argument("--email", required=True)
    parser.add_argument("--imap-server", required=True)
    parser.add_argument("--imap-password", required=True)
    args = parser.parse_args()
    
    connector = EmailSupportConnector(
        api_key=args.api_key, fleetops_url=args.url,
        email_address=args.email, imap_server=args.imap_server,
        imap_password=args.imap_password
    )
    
    asyncio.run(connector.connect())
    print(f"Email Support connector running for {args.email}")
    
    # Poll loop
    async def poll_loop():
        while True:
            await connector.poll_emails()
            await asyncio.sleep(60)  # Poll every minute
    
    try:
        asyncio.get_event_loop().run_until_complete(poll_loop())
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
