from dataclasses import dataclass
import logging
from typing import Dict, Optional
import keyring
import json
from pathlib import Path
import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class CloudCredentials:
    """Cloud service credentials"""
    service: str
    api_key: str
    region: Optional[str] = None
    org_id: Optional[str] = None


class CredentialsManager:
    """Secure credentials management"""
    
    def __init__(self):
        self.keyring_service = "mac_computer_use"
        self.required_services = {
            "aws": ["api_key", "secret_key", "region"],
            "openai": ["api_key", "org_id"],
            "huggingface": ["api_key"],
            "anthropic": ["api_key"]
        }
        
    def save_credentials(self, service: str, credentials: Dict):
        """Securely save credentials"""
        try:
            # Validate required fields
            required_fields = self.required_services.get(service, [])
            for field in required_fields:
                if field not in credentials:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Save to keyring
            keyring.set_password(
                self.keyring_service,
                service,
                json.dumps(credentials)
            )
            
            logger.info(f"Saved credentials for {service}")
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
            
    def get_credentials(self, service: str) -> Optional[Dict]:
        """Retrieve credentials"""
        try:
            creds_json = keyring.get_password(self.keyring_service, service)
            if not creds_json:
                return None
                
            return json.loads(creds_json)
            
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None 