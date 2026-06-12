import datetime
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

class MicrosoftGraphService:
    """
    Service layer integrating with Microsoft Graph API to extract
    communications (emails) and calendar appointments (meetings).
    """
    
    def __init__(self):
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token" if self.tenant_id else ""
        self.api_url = settings.MICROSOFT_GRAPH_ENDPOINT
        self.access_token = None
        
    async def _get_access_token(self) -> Optional[str]:
        """Obtains OAuth2 token client_credentials flow from Azure AD."""
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            # Return None to signify we should use mock fallback data
            return None
            
        if self.access_token:
            return self.access_token
            
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                if response.status_code == 200:
                    res_json = response.json()
                    self.access_token = res_json.get("access_token")
                    return self.access_token
            except Exception as e:
                print(f"Error fetching Microsoft Graph token: {e}")
        return None

    async def fetch_emails(self, customer_email: str) -> List[Dict[str, Any]]:
        """Queries /users/{id}/messages for communication analysis."""
        token = await self._get_access_token()
        if not token:
            # Mock email retrieval based on customer domain
            return self._generate_mock_emails(customer_email)
            
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.api_url}/users/{customer_email}/messages"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    messages = response.json().get("value", [])
                    return [
                        {
                            "sender": msg.get("from", {}).get("emailAddress", {}).get("address"),
                            "recipient": customer_email,
                            "subject": msg.get("subject"),
                            "body": msg.get("bodyPreview"),
                            "date": msg.get("receivedDateTime"),
                            "id": msg.get("id")
                        }
                        for msg in messages
                    ]
            except Exception as e:
                print(f"Error querying Graph emails: {e}")
        return self._generate_mock_emails(customer_email)

    async def fetch_meetings(self, customer_email: str) -> List[Dict[str, Any]]:
        """Queries /users/{id}/calendar/events for customer meetings logs."""
        token = await self._get_access_token()
        if not token:
            return self._generate_mock_meetings(customer_email)
            
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.api_url}/users/{customer_email}/calendar/events"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    events = response.json().get("value", [])
                    return [
                        {
                            "title": evt.get("subject"),
                            "summary": evt.get("bodyPreview", "No agenda summary provided."),
                            "attendees": [att.get("emailAddress", {}).get("address") for att in evt.get("attendees", [])],
                            "date": evt.get("start", {}).get("dateTime"),
                            "id": evt.get("id")
                        }
                        for evt in events
                    ]
            except Exception as e:
                print(f"Error querying Graph meetings: {e}")
        return self._generate_mock_meetings(customer_email)

    def _generate_mock_emails(self, customer_email: str) -> List[Dict[str, Any]]:
        domain = customer_email.split("@")[-1] if "@" in customer_email else "enterprise.com"
        company = domain.split(".")[0].capitalize()
        
        # Returns a structured sample email timeline
        return [
            {
                "sender": f"accounts@{domain}",
                "recipient": "billing@reviveiq.com",
                "subject": f"Inquiry regarding Invoice for {company}",
                "body": "Hi team, we received our recent invoice. We noticed a discrepancy in the user count license billing. Can we hold payment until this is resolved? Thanks.",
                "date": (datetime.datetime.utcnow() - datetime.timedelta(days=15)).isoformat()
            },
            {
                "sender": f"exec@{domain}",
                "recipient": "csm@reviveiq.com",
                "subject": "Platform Adoption and Renewal discussion",
                "body": "Hi, we are heading into our annual budgeting cycle. Given the unresolved performance issues we reported last month, we are evaluating alternatives. I'd like to set up a chat to see what renewal options are available.",
                "date": (datetime.datetime.utcnow() - datetime.timedelta(days=5)).isoformat()
            }
        ]

    def _generate_mock_meetings(self, customer_email: str) -> List[Dict[str, Any]]:
        domain = customer_email.split("@")[-1] if "@" in customer_email else "enterprise.com"
        return [
            {
                "title": "Quarterly Business Review - Tech Alignment",
                "summary": "Discussed adoption metrics and product feedback. Client highlighted dissatisfaction with API latency spikes. Renewal depends on resolution of latency and discount negotiation.",
                "attendees": ["csm@reviveiq.com", f"exec@{domain}", f"cto@{domain}"],
                "date": (datetime.datetime.utcnow() - datetime.timedelta(days=10)).isoformat()
            }
        ]

graph_service = MicrosoftGraphService()
