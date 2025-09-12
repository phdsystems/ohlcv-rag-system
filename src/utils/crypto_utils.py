"""
Cryptographic utilities for handling encrypted API keys.
Uses ADE-Crypt for secure key management with fallback to Python cryptography.
"""

import os
import subprocess
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from functools import lru_cache

# Try to import simple_crypto as fallback
try:
    from .simple_crypto import get_encrypted_api_key as simple_get_key, SecureConfig
    SIMPLE_CRYPTO_AVAILABLE = True
except ImportError:
    SIMPLE_CRYPTO_AVAILABLE = False
    simple_get_key = None
    SecureConfig = None

logger = logging.getLogger(__name__)


class CryptoManager:
    """Manages encryption and decryption of API keys using ADE-Crypt."""
    
    def __init__(self, encrypted_dir: str = "./config/encrypted"):
        """
        Initialize the CryptoManager.
        
        Args:
            encrypted_dir: Directory containing encrypted key files
        """
        self.encrypted_dir = Path(encrypted_dir)
        self._decrypted_cache: Dict[str, str] = {}
        
    def _check_ade_crypt(self) -> bool:
        """Check if ADE-Crypt is installed."""
        try:
            result = subprocess.run(
                ["which", "ade-crypt-lib"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @lru_cache(maxsize=32)
    def decrypt_key(self, key_name: str) -> Optional[str]:
        """
        Decrypt an API key using ADE-Crypt.
        
        Args:
            key_name: Name of the key to decrypt (e.g., 'CLAUDE_API_KEY')
            
        Returns:
            Decrypted key value or None if decryption fails
        """
        # Check cache first
        if key_name in self._decrypted_cache:
            return self._decrypted_cache[key_name]
        
        # Check if ADE-Crypt is available
        if not self._check_ade_crypt():
            logger.warning("ADE-Crypt not installed, falling back to environment variables")
            return os.getenv(key_name)
        
        encrypted_file = self.encrypted_dir / f"{key_name}.enc"
        
        # If encrypted file doesn't exist, try environment variable
        if not encrypted_file.exists():
            logger.debug(f"Encrypted file not found for {key_name}, checking environment")
            return os.getenv(key_name)
        
        try:
            # Decrypt the key using ADE-Crypt to temp file
            temp_file = self.encrypted_dir / f"{key_name}.tmp.dec"
            result = subprocess.run(
                ["ade-crypt-lib", "decrypt-file", str(encrypted_file), str(temp_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Read decrypted value from temp file
            with open(temp_file, 'r') as f:
                decrypted_value = f.read().strip()
            
            # Clean up temp file
            temp_file.unlink(missing_ok=True)
            
            # Cache the decrypted value
            self._decrypted_cache[key_name] = decrypted_value
            
            logger.info(f"Successfully decrypted {key_name}")
            return decrypted_value
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to decrypt {key_name}: {e.stderr}")
            # Fall back to environment variable
            return os.getenv(key_name)
        except Exception as e:
            logger.error(f"Unexpected error decrypting {key_name}: {str(e)}")
            return os.getenv(key_name)
    
    def encrypt_key(self, key_name: str, key_value: str) -> bool:
        """
        Encrypt an API key using ADE-Crypt.
        
        Args:
            key_name: Name of the key to encrypt
            key_value: Value to encrypt
            
        Returns:
            True if encryption successful, False otherwise
        """
        if not self._check_ade_crypt():
            logger.error("ADE-Crypt not installed")
            return False
        
        # Create encrypted directory if it doesn't exist
        self.encrypted_dir.mkdir(parents=True, exist_ok=True)
        
        encrypted_file = self.encrypted_dir / f"{key_name}.enc"
        temp_file = self.encrypted_dir / f"{key_name}.tmp"
        
        try:
            # Write value to temp file (ADE-Crypt doesn't support stdin)
            with open(temp_file, 'w') as f:
                f.write(key_value)
            os.chmod(temp_file, 0o600)
            
            # Encrypt the key using ADE-Crypt
            result = subprocess.run(
                ["ade-crypt-lib", "encrypt-file", str(temp_file), str(encrypted_file)],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Clean up temp file
            temp_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully encrypted {key_name}")
                return True
            else:
                logger.error(f"Failed to encrypt {key_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error encrypting {key_name}: {str(e)}")
            temp_file.unlink(missing_ok=True)
            return False
    
    def get_api_key(self, key_name: str, fallback_env: Optional[str] = None) -> Optional[str]:
        """
        Get an API key, attempting decryption first, then falling back to environment.
        
        Args:
            key_name: Name of the key to retrieve
            fallback_env: Alternative environment variable name to check
            
        Returns:
            The API key value or None if not found
        """
        # Try to decrypt first
        key_value = self.decrypt_key(key_name)
        
        # If not found and fallback provided, try fallback
        if not key_value and fallback_env:
            key_value = os.getenv(fallback_env)
        
        # If still not found and simple_crypto is available, try that
        if not key_value and SIMPLE_CRYPTO_AVAILABLE and simple_get_key:
            logger.debug(f"Trying simple_crypto fallback for {key_name}")
            key_value = simple_get_key(key_name, fallback_env)
        
        # Handle placeholder values
        if key_value and key_value.startswith("your_") and key_value.endswith("_here"):
            logger.warning(f"{key_name} contains placeholder value")
            return None
            
        return key_value
    
    def clear_cache(self):
        """Clear the decrypted key cache."""
        self._decrypted_cache.clear()
        self.decrypt_key.cache_clear()


# Global instance for convenience
_crypto_manager: Optional[CryptoManager] = None


def get_crypto_manager() -> CryptoManager:
    """Get or create the global CryptoManager instance."""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager


def get_api_key(key_name: str, fallback_env: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get an API key using the global CryptoManager.
    
    Args:
        key_name: Name of the key to retrieve
        fallback_env: Alternative environment variable name to check
        
    Returns:
        The API key value or None if not found
    """
    return get_crypto_manager().get_api_key(key_name, fallback_env)