"""
Data Encryption Module
Encrypts sensitive data at rest using Fernet (symmetric encryption)

WEEK 7: SECURITY FOUNDATION
- Encrypts emotional states (GDPR Article 9 - special category data)
- Encrypts learned phrases (culture learning Week 8-9)
- Secure key storage with file permissions
- Automatic key generation on first run
"""

from cryptography.fernet import Fernet
from pathlib import Path
import json
import logging
import os

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    Encrypt sensitive data at rest using Fernet (AES-128-CBC).

    This protects:
    - Emotional states (joy, sadness, anger, fear, etc.)
    - Sentiment scores
    - Learned user phrases (future: Week 8-9)
    - Personal preferences

    Key is stored locally in data/.encryption_key with 0o600 permissions.
    """

    def __init__(self, key_file: Path = None):
        """
        Initialize encryption with secure key storage.

        Args:
            key_file: Path to encryption key file (default: data/.encryption_key)
        """
        if key_file is None:
            key_file = Path(__file__).parent.parent.parent / "data" / ".encryption_key"

        self.key_file = Path(key_file)
        self._load_or_create_key()

    def _load_or_create_key(self):
        """Load existing key or create new one with secure permissions"""
        if self.key_file.exists() and self.key_file.stat().st_size > 0:
            # Load existing key (only if file has content)
            try:
                with open(self.key_file, 'rb') as f:
                    self.key = f.read()

                # Validate key format
                Fernet(self.key)  # Will raise ValueError if invalid
                logger.info(f"🔐 Loaded encryption key from {self.key_file}")
            except (ValueError, Exception) as e:
                # Invalid or corrupted key file, regenerate
                logger.warning(f"Invalid key file, regenerating: {e}")
                self._generate_new_key()
        else:
            # Generate new key (file doesn't exist or is empty)
            self._generate_new_key()

        # Initialize cipher
        self.cipher = Fernet(self.key)

    def _generate_new_key(self):
        """Generate and save a new encryption key"""
        self.key = Fernet.generate_key()

        # Create parent directory if needed
        self.key_file.parent.mkdir(parents=True, exist_ok=True)

        # Write key with secure permissions
        with open(self.key_file, 'wb') as f:
            f.write(self.key)

        # Set restrictive permissions (owner read/write only)
        try:
            self.key_file.chmod(0o600)
            logger.info(f"🔐 Created new encryption key at {self.key_file} (permissions: 0600)")
        except Exception as e:
            logger.warning(f"Could not set key file permissions: {e}")

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.

        Args:
            data: Plaintext string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not data:
            return ""

        encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Plaintext string
        """
        if not encrypted_data:
            return ""

        decrypted_bytes = self.cipher.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')

    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt dictionary as JSON.

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted JSON string
        """
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt and parse JSON dictionary.

        Args:
            encrypted_data: Base64-encoded encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

    def encrypt_selective(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt only specified fields in a dictionary.

        Useful for encrypting sensitive fields while leaving others plaintext
        for querying/indexing.

        Args:
            data: Dictionary with mixed sensitive/non-sensitive fields
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with specified fields encrypted

        Example:
            >>> encryptor = DataEncryption()
            >>> data = {'emotion': 'joy', 'timestamp': '2025-12-08', 'user_id': '123'}
            >>> encrypted = encryptor.encrypt_selective(data, ['emotion'])
            >>> # Result: {'emotion': 'gAA...encrypted...', 'timestamp': '2025-12-08', 'user_id': '123'}
        """
        result = data.copy()

        for field in fields_to_encrypt:
            if field in result and result[field] is not None:
                # Convert to string if not already
                value_str = str(result[field])
                result[field] = self.encrypt(value_str)

        return result

    def decrypt_selective(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt only specified fields in a dictionary.

        Args:
            data: Dictionary with encrypted fields
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with specified fields decrypted

        Example:
            >>> encryptor = DataEncryption()
            >>> data = {'emotion': 'gAA...encrypted...', 'timestamp': '2025-12-08'}
            >>> decrypted = encryptor.decrypt_selective(data, ['emotion'])
            >>> # Result: {'emotion': 'joy', 'timestamp': '2025-12-08'}
        """
        result = data.copy()

        for field in fields_to_decrypt:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except Exception as e:
                    logger.warning(f"Failed to decrypt field '{field}': {e}")
                    # Keep encrypted value if decryption fails
                    pass

        return result


# Singleton instance for module-level access
_encryption_instance = None


def get_encryption() -> DataEncryption:
    """
    Get singleton encryption instance.

    Returns:
        DataEncryption instance
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = DataEncryption()
    return _encryption_instance


__all__ = ['DataEncryption', 'get_encryption']
