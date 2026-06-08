import os
from dotenv import load_dotenv
import requests
from utils.logger import logger

load_dotenv()

class WhatsAppClient:
    def __init__(self):
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
        self.token = os.getenv("WHATSAPP_TOKEN", "")
        self.verify_token = os.getenv("VERIFY_TOKEN", "")
        api_ver = os.getenv("GRAPH_API_VERSION", "v17.0")
        self.api_url = f"https://graph.facebook.com/{api_ver}/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, phone_number: str = None, message_text: str = None, **kwargs):
        """
        Send a text message. Accepts positional arguments or keyword aliases `to` and `text`.
        """
        # support keyword aliases for backward compatibility
        if not phone_number and kwargs.get("to"):
            phone_number = kwargs.get("to")
        if not message_text and kwargs.get("text"):
            message_text = kwargs.get("text")

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message_text}
        }

        logger.info(f"Sending message to {phone_number}: {str(message_text)[:50]}...")

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            try:
                body = response.json()
            except Exception:
                body = response.text
            if response.status_code in (200, 201):
                logger.info(f"Message sent successfully to {phone_number}")
                message_id = None
                if isinstance(body, dict):
                    message_id = body.get("messages", [{}])[0].get("id")
                return {"success": True, "message_id": message_id, "response": body}
            else:
                logger.error(f"Failed to send message: {body}")
                return {"success": False, "error": body}
        except Exception as e:
            logger.error(f"Exception sending message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_template_message(self, phone_number: str, template_name: str, parameters: list = None):
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"}
            }
        }
        
        if parameters:
            payload["template"]["parameters"] = {"body": {"parameters": parameters}}
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            if response.status_code == 200:
                return {"success": True, "message_id": response.json().get("messages", [{}])[0].get("id")}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

wa_client = WhatsAppClient()