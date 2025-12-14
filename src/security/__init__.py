"""
Security Module for PennyGPT

WEEK 7: Architecture Refactor + Security Foundation

Components:
- DataEncryption: Encrypt sensitive data at rest (Fernet/AES-128)
- PIIDetector: Detect and filter personally identifiable information
- UserAuth: User authentication (future: multi-user support)
"""

from src.security.encryption import DataEncryption, get_encryption
from src.security.pii_detector import PIIDetector, get_pii_detector

__all__ = ['DataEncryption', 'get_encryption', 'PIIDetector', 'get_pii_detector']
