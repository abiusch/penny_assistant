# Security Guide: PennyGPT

**Week 7**: Architecture Refactor + Security Foundation

This document describes the security features implemented in Week 7, including data encryption and PII detection.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Encryption](#data-encryption)
3. [PII Detection](#pii-detection)
4. [GDPR Compliance](#gdpr-compliance)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

PennyGPT implements multiple layers of security to protect user data:

- **Data Encryption**: AES-128 encryption for sensitive emotional data (Fernet)
- **PII Detection**: Automatic filtering of personally identifiable information
- **Secure Key Storage**: Encryption keys stored with restricted file permissions (0o600)
- **GDPR Compliance**: Meets Article 9 requirements for special category data

---

## Data Encryption

### What is Encrypted

**Sensitive Fields** (encrypted at rest):
- `emotion` - Emotional states (joy, sadness, anger, fear, surprise, neutral)
- `sentiment` - Sentiment classification (positive, negative, neutral)
- `sentiment_score` - Numerical sentiment score (-1.0 to +1.0)

**Non-Sensitive Fields** (plaintext for queryability):
- `user_input`, `assistant_response` - Needed for semantic search
- `timestamp`, `turn_id` - Needed for indexing
- `research_used`, `financial_topic` - Analytics metadata
- `tools_used`, `ab_test_group` - Experiment tracking

### Encryption Algorithm

**Algorithm**: Fernet (symmetric encryption)
- Based on AES-128-CBC
- HMAC for authentication
- URL-safe base64 encoding

**Key Generation**: Automatic on first run
- Location: `data/.encryption_key`
- Permissions: `0o600` (owner read/write only)
- 32-byte key (256 bits)

### Usage Examples

#### Basic Encryption

```python
from src.security import get_encryption

# Get singleton encryptor
encryptor = get_encryption()

# Encrypt a value
plaintext = "joy"
encrypted = encryptor.encrypt(plaintext)
# Result: "gAAAABj5K..."

# Decrypt
decrypted = encryptor.decrypt(encrypted)
# Result: "joy"
```

#### Selective Field Encryption

```python
from src.security import get_encryption

encryptor = get_encryption()

# Data with mix of sensitive and non-sensitive fields
data = {
    'emotion': 'joy',
    'sentiment': 'positive',
    'sentiment_score': 0.85,
    'timestamp': '2025-12-14T10:30:00',
    'user_input': 'I love this feature!'
}

# Encrypt only sensitive fields
sensitive_fields = ['emotion', 'sentiment', 'sentiment_score']
encrypted_data = encryptor.encrypt_selective(data, sensitive_fields)

# Result:
# {
#     'emotion': 'gAAAABj5K...',  # Encrypted
#     'sentiment': 'gAAAABj7L...',  # Encrypted
#     'sentiment_score': 'gAAAABj9M...',  # Encrypted
#     'timestamp': '2025-12-14T10:30:00',  # Plaintext
#     'user_input': 'I love this feature!'  # Plaintext
# }

# Decrypt selective fields
decrypted_data = encryptor.decrypt_selective(encrypted_data, sensitive_fields)
# Restores original values
```

#### Full Dictionary Encryption

```python
from src.security import get_encryption

encryptor = get_encryption()

# Encrypt all fields
data = {'user_id': '123', 'preferences': 'dark_mode'}
encrypted = encryptor.encrypt_dict(data)

# Decrypt all fields
decrypted = encryptor.decrypt_dict(encrypted)
```

### Automatic Integration

**Semantic Memory** automatically encrypts/decrypts sensitive fields:

```python
from src.memory import SemanticMemory

# Initialize with encryption enabled (default)
semantic_memory = SemanticMemory(encrypt_sensitive=True)

# Add conversation - emotions are encrypted automatically
semantic_memory.add_conversation_turn(
    user_input="I'm feeling great today!",
    assistant_response="That's wonderful!",
    context={
        'emotion': 'joy',  # Automatically encrypted before storage
        'sentiment': 'positive',  # Automatically encrypted
        'sentiment_score': 0.95,  # Automatically encrypted
        'research_used': False  # Not encrypted (queryable metadata)
    }
)

# Search - results are automatically decrypted
results = semantic_memory.semantic_search("feeling great", k=3)
# Emotions in results are decrypted for use
```

### Key Management

#### Location and Permissions

```bash
# Key file location
data/.encryption_key

# Permissions (automatically set)
-rw------- (0600)  # Owner read/write only
```

#### Key Rotation (Future)

Currently, keys are generated once and reused. For production deployments:

1. Implement periodic key rotation (e.g., every 90 days)
2. Re-encrypt existing data with new keys
3. Maintain key history for data recovery

**TODO**: Implement key rotation in future week

---

## PII Detection

### What is Detected

**Regex-Based Detection**:
- Email addresses: `user@example.com`
- Phone numbers: `555-123-4567`, `(555) 123-4567`, `5551234567`
- SSNs: `123-45-6789`, `123 45 6789`
- Credit cards: `1234 5678 9012 3456`
- Street addresses: `123 Main Street`, `456 Oak Avenue`

**Known Entity Lists**:
- Company names: 100+ tech companies, banks, consulting firms
  - Examples: Google, Microsoft, Apple, Amazon, Anthropic, OpenAI
- Personal names: 100+ common first names from census data
  - Examples: John, Sarah, Michael, Jennifer, David, Emily
- Company indicators: Inc, LLC, Corp, Corporation, Ltd, etc.

### Why PII Detection Matters

**Culture Learning Risk** (Week 8-9):
Without PII detection, culture learning could accidentally adopt phrases like:

❌ **Bad**: "I work at Google" → Penny later says "Yeah, like when you worked at Google..."
❌ **Bad**: "My friend Sarah said..." → Leaks personal name in examples
❌ **Bad**: "Contact me at john@example.com" → Could leak in conversations

✅ **Good**: PII detection blocks these phrases from being learned

### Usage Examples

#### Basic PII Detection

```python
from src.security import get_pii_detector

detector = get_pii_detector()

# Check if text contains PII
if detector.contains_pii("I work at Google"):
    print("🚫 Contains PII - blocked")
# Output: 🚫 Contains PII - blocked

if detector.contains_pii("that's fire"):
    print("🚫 Contains PII - blocked")
else:
    print("✅ Safe to use")
# Output: ✅ Safe to use
```

#### Filtering Phrases for Culture Learning

```python
from src.security import get_pii_detector

detector = get_pii_detector()

# Candidate phrases for culture learning
phrases = [
    "that's fire",  # Safe
    "I work at Google",  # PII - company name
    "no cap",  # Safe
    "My friend Sarah said",  # PII - personal name
    "let's gooo",  # Safe
    "Email me at test@example.com",  # PII - email
]

# Filter out PII
safe, blocked = detector.filter_pii_phrases(phrases)

print(f"✅ Safe phrases: {safe}")
# Output: ["that's fire", "no cap", "let's gooo"]

print(f"🚫 Blocked phrases: {blocked}")
# Output: ["I work at Google", "My friend Sarah said", "Email me at test@example.com"]
```

#### Identifying Specific PII Types

```python
from src.security import get_pii_detector

detector = get_pii_detector()

text = "Email john@example.com, phone 555-123-4567, I work at Google"
pii_types = detector.get_pii_types(text)

print(f"PII types found: {pii_types}")
# Output: ['email', 'phone', 'company_name']
```

#### Redacting PII from Logs

```python
from src.security import get_pii_detector

detector = get_pii_detector()

# Original text
text = "Contact me at john@example.com or call 555-123-4567"

# Redact PII
redacted = detector.redact_pii(text)
print(redacted)
# Output: "Contact me at [EMAIL] or call [PHONE]"
```

### Extending PII Detection

#### Adding Custom Company Names

```python
from src.security import get_pii_detector

detector = get_pii_detector()

# Add custom companies
detector.known_companies.update({
    'MyStartup',
    'Secret Project',
    'Stealth Inc'
})

# Now detects custom companies
assert detector.contains_pii("I work at MyStartup") == True
```

#### Adding Custom Personal Names

```python
from src.security import get_pii_detector

detector = get_pii_detector()

# Add custom names
detector.common_first_names.update({
    'Aaliyah',
    'Zephyr',
    'Custom'
})

# Now detects custom names
assert detector.contains_pii("My friend Aaliyah") == True
```

---

## GDPR Compliance

### Article 9: Special Category Data

**Requirement**: Special categories of personal data (including data concerning health, biometric data, genetic data) must be encrypted at rest.

**Emotional Data Classification**:
- Emotional states (joy, sadness, anger, fear) are considered **health-related data**
- Falls under GDPR Article 9 (special category data)
- **Must be encrypted at rest**

**PennyGPT Compliance**:
- ✅ Emotional states encrypted with AES-128 (Fernet)
- ✅ Sentiment data encrypted
- ✅ Automatic encryption on storage
- ✅ Automatic decryption on retrieval

### Article 32: Security of Processing

**Requirement**: Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.

**PennyGPT Implementation**:
- ✅ Encryption of sensitive data at rest (AES-128)
- ✅ Secure key storage with restricted permissions (0o600)
- ✅ PII detection to prevent data leakage
- ✅ Automatic redaction capabilities for logs

### Article 25: Data Protection by Design

**Requirement**: Implement data protection by design and by default.

**PennyGPT Implementation**:
- ✅ Encryption enabled by default (`encrypt_sensitive=True`)
- ✅ PII detection integrated into culture learning pipeline
- ✅ Minimal data collection (only what's needed)
- ✅ Clear separation of sensitive vs. non-sensitive data

### Article 17: Right to Erasure

**Requirement**: Users have the right to request deletion of their personal data.

**PennyGPT Implementation**:
- ✅ `delete_conversation()` method in semantic memory
- ✅ Complete removal from vector store and metadata
- ✅ No residual encrypted data after deletion

---

## Best Practices

### For Developers

1. **Always Enable Encryption for Production**:
   ```python
   # ✅ Good
   semantic_memory = SemanticMemory(encrypt_sensitive=True)

   # ❌ Bad (only for testing)
   semantic_memory = SemanticMemory(encrypt_sensitive=False)
   ```

2. **Use Selective Encryption for Performance**:
   ```python
   # Only encrypt what needs encryption
   sensitive_fields = ['emotion', 'sentiment', 'sentiment_score']
   encrypted = encryptor.encrypt_selective(data, sensitive_fields)
   ```

3. **Filter PII Before Culture Learning**:
   ```python
   # Always filter phrases before learning
   safe, blocked = detector.filter_pii_phrases(candidate_phrases)
   learn_from_phrases(safe)  # Only learn from safe phrases
   ```

4. **Redact PII in Logs**:
   ```python
   # Before logging user input
   logged_input = detector.redact_pii(user_input)
   logger.info(f"User input: {logged_input}")
   ```

5. **Protect Encryption Keys**:
   ```bash
   # Never commit encryption keys to git
   echo "data/.encryption_key" >> .gitignore

   # Verify key permissions
   chmod 600 data/.encryption_key
   ```

### For Security Audits

1. **Verify Encryption is Enabled**:
   ```python
   semantic_memory = SemanticMemory()
   assert semantic_memory.encrypt_sensitive == True
   ```

2. **Check Key File Permissions**:
   ```bash
   ls -l data/.encryption_key
   # Should show: -rw------- (0600)
   ```

3. **Test PII Detection Coverage**:
   ```python
   detector = get_pii_detector()

   # Test cases
   assert detector.contains_pii("Email: test@example.com")
   assert detector.contains_pii("Phone: 555-123-4567")
   assert detector.contains_pii("I work at Google")
   ```

4. **Verify Encrypted Storage**:
   ```python
   # Check that sensitive data is actually encrypted in FAISS
   # (Manually inspect vector_store.id_to_metadata)
   ```

---

## Troubleshooting

### Encryption Key Issues

#### Problem: "ValueError: Fernet key must be 32 url-safe base64-encoded bytes"

**Cause**: Corrupted or invalid encryption key file

**Solution**:
```bash
# Delete corrupted key file (will auto-regenerate)
rm data/.encryption_key

# Restart application
python3 research_first_pipeline.py
```

⚠️ **Warning**: Deleting the key will make existing encrypted data unreadable. Only do this if the key is corrupted OR if you don't need existing data.

#### Problem: Permission denied when accessing encryption key

**Cause**: Incorrect file permissions

**Solution**:
```bash
# Fix permissions
chmod 600 data/.encryption_key

# Verify
ls -l data/.encryption_key
# Should show: -rw------- (0600)
```

### PII Detection Issues

#### Problem: False positives (blocking safe phrases)

**Cause**: Overly aggressive pattern matching

**Solution 1**: Adjust detection thresholds
```python
detector = get_pii_detector()

# Remove specific false positive from company list
detector.known_companies.discard('Amazon')  # If "Amazon" is too generic
```

**Solution 2**: Use `get_pii_types()` to diagnose
```python
phrase = "that's fire"  # Being incorrectly blocked
pii_types = detector.get_pii_types(phrase)
print(f"Detected PII types: {pii_types}")
# Investigate why it's being flagged
```

#### Problem: False negatives (not detecting PII)

**Cause**: Missing patterns or entities

**Solution**: Add custom patterns
```python
detector = get_pii_detector()

# Add missing company
detector.known_companies.add('NewCompany')

# Add missing name
detector.common_first_names.add('Unique')
```

### Performance Issues

#### Problem: Encryption is slow

**Cause**: Encrypting too many fields

**Solution**: Use selective encryption
```python
# Only encrypt what's necessary
sensitive_fields = ['emotion', 'sentiment', 'sentiment_score']
encrypted = encryptor.encrypt_selective(data, sensitive_fields)
```

#### Problem: PII detection is slow

**Cause**: Complex regex patterns on large text

**Solution**: Pre-filter text
```python
# Only check PII for phrases under 200 characters
if len(phrase) < 200:
    if detector.contains_pii(phrase):
        blocked.append(phrase)
```

---

## Security Checklist

### Deployment Checklist

- [ ] Encryption enabled in production (`encrypt_sensitive=True`)
- [ ] Encryption key has correct permissions (0o600)
- [ ] Encryption key is NOT committed to git
- [ ] PII detection is active for culture learning
- [ ] Logs are redacted using `redact_pii()`
- [ ] Regular security audits scheduled
- [ ] Backup encryption key securely stored off-site
- [ ] GDPR compliance verified (Articles 9, 17, 25, 32)

### Development Checklist

- [ ] Tests pass (`pytest tests/test_week7_security.py`)
- [ ] Encryption roundtrip works (encrypt → decrypt = original)
- [ ] PII detection has >90% accuracy on test cases
- [ ] Key regeneration works if key file is deleted
- [ ] Semantic memory integration tests pass
- [ ] Migration script tested on sample data

---

## Future Enhancements

### Planned (Future Weeks)

1. **Key Rotation** - Periodic encryption key rotation
2. **Multi-User Encryption** - Per-user encryption keys
3. **ML-Based PII Detection** - More accurate named entity recognition
4. **Audit Logging** - Track access to encrypted data
5. **Hardware Security Modules** - Store keys in HSM for production

### Under Consideration

1. **Homomorphic Encryption** - Compute on encrypted data
2. **Differential Privacy** - Add noise to sensitive aggregates
3. **Zero-Knowledge Proofs** - Verify without revealing data

---

## References

- [Cryptography Library Documentation](https://cryptography.io/en/latest/fernet/)
- [GDPR Official Text](https://gdpr-info.eu/)
- [NIST Encryption Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175Br1.pdf)

---

**Last Updated**: December 14, 2025
**Maintained By**: PennyGPT Security Team
