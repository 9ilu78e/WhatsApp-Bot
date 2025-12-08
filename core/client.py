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
        self.api_url = f"https://graph.facebook.com/v22.0/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, phone_number: str, message_text: str):
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message_text}
        }
        
        logger.info(f"Sending message to {phone_number}: {message_text[:50]}...")
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return {"success": True, "message_id": response.json().get("messages", [{}])[0].get("id")}
            else:
                logger.error(f"Failed to send message: {response.text}")
                return {"success": False, "error": response.text}
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