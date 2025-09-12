"""
Simple encryption/decryption utilities for API keys using Python's cryptography library.
This provides a fallback when ADE-Crypt is not available or has issues.
"""

import os
import base64
import json
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class SimpleCrypto:
    """Simple encryption/decryption for API keys using Fernet."""
    
    def __init__(self, key_file: str = "./config/.encryption_key"):
        """
        Initialize SimpleCrypto with a key file.
        
        Args:
            key_file: Path to store the encryption key
        """
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = self._get_or_create_fernet()
    
    def _get_or_create_fernet(self) -> Fernet:
        """Get existing Fernet instance or create new one."""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            logger.info(f"Generated new encryption key at {self.key_file}")
        
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.
        
        Args:
            ciphertext: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_file(self, plaintext: str, output_file: Path):
        """
        Encrypt string and save to file.
        
        Args:
            plaintext: String to encrypt
            output_file: Path to save encrypted data
        """
        encrypted = self.encrypt(plaintext)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(encrypted)
        os.chmod(output_file, 0o600)
    
    def decrypt_file(self, input_file: Path) -> str:
        """
        Decrypt data from file.
        
        Args:
            input_file: Path to encrypted file
            
        Returns:
            Decrypted string
        """
        with open(input_file, 'r') as f:
            ciphertext = f.read()
        return self.decrypt(ciphertext)


class SecureConfig:
    """Manage encrypted configuration for API keys."""
    
    def __init__(self, config_dir: str = "./config/encrypted"):
        """
        Initialize SecureConfig.
        
        Args:
            config_dir: Directory to store encrypted configs
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.crypto = SimpleCrypto()
        self._cache: Dict[str, str] = {}
    
    def set_key(self, key_name: str, key_value: str):
        """
        Encrypt and store an API key.
        
        Args:
            key_name: Name of the key (e.g., 'CLAUDE_API_KEY')
            key_value: The actual API key value
        """
        encrypted_file = self.config_dir / f"{key_name}.enc"
        self.crypto.encrypt_file(key_value, encrypted_file)
        self._cache[key_name] = key_value
        logger.info(f"Encrypted and stored {key_name}")
    
    def get_key(self, key_name: str, fallback_env: Optional[str] = None) -> Optional[str]:
        """
        Get a decrypted API key.
        
        Args:
            key_name: Name of the key to retrieve
            fallback_env: Fallback environment variable name
            
        Returns:
            The decrypted API key or None
        """
        # Check cache
        if key_name in self._cache:
            return self._cache[key_name]
        
        # Try to decrypt from file
        encrypted_file = self.config_dir / f"{key_name}.enc"
        if encrypted_file.exists():
            try:
                value = self.crypto.decrypt_file(encrypted_file)
                self._cache[key_name] = value
                return value
            except Exception as e:
                logger.error(f"Failed to decrypt {key_name}: {e}")
        
        # Fall back to environment variable
        value = os.getenv(key_name)
        if not value and fallback_env:
            value = os.getenv(fallback_env)
        
        # Filter out placeholder values
        if value and value.startswith("your_") and value.endswith("_here"):
            return None
        
        return value
    
    def encrypt_from_env(self):
        """Encrypt all API keys from environment variables."""
        keys_to_encrypt = [
            "CLAUDE_API_KEY",
            "OPENAI_API_KEY", 
            "ANTHROPIC_API_KEY",
            "ALPHA_VANTAGE_API_KEY",
            "POLYGON_API_KEY",
            "WEAVIATE_API_KEY",
            "QDRANT_API_KEY"
        ]
        
        encrypted_count = 0
        for key_name in keys_to_encrypt:
            value = os.getenv(key_name)
            if value and not value.startswith("your_"):
                self.set_key(key_name, value)
                encrypted_count += 1
        
        logger.info(f"Encrypted {encrypted_count} API keys from environment")
        return encrypted_count


# Global instance
_secure_config: Optional[SecureConfig] = None


def get_secure_config() -> SecureConfig:
    """Get or create the global SecureConfig instance."""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfig()
    return _secure_config


def get_encrypted_api_key(key_name: str, fallback_env: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get an encrypted API key.
    
    Args:
        key_name: Name of the key to retrieve
        fallback_env: Fallback environment variable name
        
    Returns:
        The decrypted API key or None
    """
    return get_secure_config().get_key(key_name, fallback_env)