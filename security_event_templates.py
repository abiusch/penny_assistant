#!/usr/bin/env python3
"""
Security Event Classification Templates
Optimized LLM context templates for efficient security analysis
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import re

class EventCategory(Enum):
    """Security event categories for template classification"""
    ACCESS_CONTROL = "access_control"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_PROTECTION = "data_protection"
    NETWORK_SECURITY = "network_security"
    SYSTEM_INTEGRITY = "system_integrity"
    EMERGENCY_RESPONSE = "emergency_response"
    COMPLIANCE = "compliance"
    ANOMALY_DETECTION = "anomaly_detection"
    THREAT_DETECTION = "threat_detection"

class AnalysisComplexity(Enum):
    """Analysis complexity levels"""
    SIMPLE = "simple"           # Template-based analysis only
    MODERATE = "moderate"       # Template + limited reasoning
    COMPLEX = "complex"         # Full LLM analysis required
    CRITICAL = "critical"       # Comprehensive analysis with escalation

class TokenOptimization(Enum):
    """Token optimization strategies"""
    MINIMAL = "minimal"         # Absolute minimum context
    COMPACT = "compact"         # Essential context only
    STANDARD = "standard"       # Normal context
    DETAILED = "detailed"       # Full context for complex cases

@dataclass
class SecurityEventTemplate:
    """Template for security event classification and analysis"""
    template_id: str
    name: str
    category: EventCategory
    patterns: List[str]
    keywords: List[str]

    # Context optimization
    analysis_complexity: AnalysisComplexity
    token_optimization: TokenOptimization
    max_context_tokens: int

    # Template structure
    context_template: str
    reasoning_template: str
    decision_template: str

    # Cached patterns
    risk_indicators: List[str]
    common_decisions: Dict[str, str]
    typical_mitigations: List[str]

    # Performance metrics
    accuracy_rate: float
    avg_processing_time_ms: float
    cache_hit_rate: float

@dataclass
class CompressedContext:
    """Compressed context for LLM analysis"""
    template_id: str
    event_summary: str
    key_parameters: Dict[str, Any]
    risk_indicators: List[str]
    context_hash: str
    token_count: int
    compression_ratio: float

class SecurityEventClassifier:
    """Classifies security events and selects optimal templates"""

    def __init__(self):
        self.templates: Dict[str, SecurityEventTemplate] = {}
        self.classification_cache: Dict[str, str] = {}
        self.logger = logging.getLogger("security_classifier")

        # Load default templates
        self._load_default_templates()

        # Pattern compilation cache
        self._compiled_patterns: Dict[str, re.Pattern] = {}

    def _load_default_templates(self):
        """Load default security event templates"""

        # File Access Template
        file_access_template = SecurityEventTemplate(
            template_id="file_access_001",
            name="File Access Control",
            category=EventCategory.ACCESS_CONTROL,
            patterns=[
                r"file_(read|write|access|open)",
                r"(read|write|access)\s+.*\.(txt|json|log|config)",
                r"permission.*file",
            ],
            keywords=["file", "read", "write", "access", "permission", "path"],
            analysis_complexity=AnalysisComplexity.SIMPLE,
            token_optimization=TokenOptimization.MINIMAL,
            max_context_tokens=150,
            context_template="""
Event: {event_type}
Operation: {operation}
Resource: {resource}
User: {user_id}
Decision: {decision}
Risk: {risk_score:.2f}
""".strip(),
            reasoning_template="""
File access request analyzed:
- Operation: {operation} on {resource}
- User permission level: {user_permission}
- Risk assessment: {risk_level}
- Security concerns: {concerns}
""".strip(),
            decision_template="""
Decision: {decision}
Reason: {primary_reason}
Alternatives: {alternatives}
""".strip(),
            risk_indicators=["../", "system", "etc", "passwd", "shadow", "admin"],
            common_decisions={
                "safe_read": "allow",
                "config_read": "allow_with_monitoring",
                "system_read": "block",
                "traversal_attempt": "block",
                "admin_access": "require_authentication"
            },
            typical_mitigations=[
                "Use absolute paths only",
                "Implement proper access controls",
                "Log all file operations",
                "Regular permission audits"
            ],
            accuracy_rate=0.95,
            avg_processing_time_ms=25.0,
            cache_hit_rate=0.85
        )

        # Network Security Template
        network_security_template = SecurityEventTemplate(
            template_id="network_sec_001",
            name="Network Security Operations",
            category=EventCategory.NETWORK_SECURITY,
            patterns=[
                r"network_(request|access|connection)",
                r"(http|https|ftp|ssh)://",
                r"(curl|wget|connect|download|upload)",
            ],
            keywords=["network", "http", "url", "download", "upload", "connection"],
            analysis_complexity=AnalysisComplexity.MODERATE,
            token_optimization=TokenOptimization.COMPACT,
            max_context_tokens=250,
            context_template="""
Event: {event_type}
Network Operation: {operation}
Target: {target_url}
Method: {method}
User: {user_id}
Risk Level: {risk_score:.2f}
Threat Indicators: {threat_indicators}
""".strip(),
            reasoning_template="""
Network security analysis:
- Target URL: {target_url}
- Request method: {method}
- Reputation check: {url_reputation}
- Protocol security: {protocol_security}
- Data sensitivity: {data_classification}
""".strip(),
            decision_template="""
Decision: {decision}
Basis: {security_analysis}
Monitoring: {monitoring_required}
Restrictions: {restrictions}
""".strip(),
            risk_indicators=["malware", "phishing", "suspicious", "blacklist", "tor", "proxy"],
            common_decisions={
                "trusted_domain": "allow",
                "unknown_domain": "allow_with_monitoring",
                "suspicious_domain": "block",
                "malicious_domain": "block",
                "internal_network": "allow"
            },
            typical_mitigations=[
                "URL reputation checking",
                "Content filtering",
                "Network monitoring",
                "Proxy configuration",
                "DNS filtering"
            ],
            accuracy_rate=0.88,
            avg_processing_time_ms=45.0,
            cache_hit_rate=0.72
        )

        # Authentication Template
        auth_template = SecurityEventTemplate(
            template_id="auth_001",
            name="Authentication Events",
            category=EventCategory.AUTHENTICATION,
            patterns=[
                r"(login|logout|authenticate|credential)",
                r"(password|token|session).*validation",
                r"user.*authentication",
            ],
            keywords=["login", "authentication", "password", "token", "session", "credential"],
            analysis_complexity=AnalysisComplexity.SIMPLE,
            token_optimization=TokenOptimization.MINIMAL,
            max_context_tokens=120,
            context_template="""
Event: {event_type}
Auth Method: {auth_method}
User: {user_id}
Result: {auth_result}
Risk: {risk_score:.2f}
""".strip(),
            reasoning_template="""
Authentication event:
- Method: {auth_method}
- Result: {auth_result}
- Risk factors: {risk_factors}
""".strip(),
            decision_template="""
Decision: {decision}
Security Level: {security_level}
""".strip(),
            risk_indicators=["failed", "bruteforce", "suspicious", "multiple", "rapid"],
            common_decisions={
                "successful_auth": "allow",
                "failed_auth": "log_and_continue",
                "multiple_failures": "rate_limit",
                "bruteforce_attempt": "block"
            },
            typical_mitigations=[
                "Account lockout policies",
                "Multi-factor authentication",
                "Rate limiting",
                "Monitoring failed attempts"
            ],
            accuracy_rate=0.92,
            avg_processing_time_ms=20.0,
            cache_hit_rate=0.90
        )

        # Privilege Escalation Template
        privilege_template = SecurityEventTemplate(
            template_id="privilege_001",
            name="Privilege Escalation",
            category=EventCategory.AUTHORIZATION,
            patterns=[
                r"privilege.*escalation",
                r"sudo|admin|root",
                r"permission.*elevation",
            ],
            keywords=["privilege", "escalation", "sudo", "admin", "root", "elevation"],
            analysis_complexity=AnalysisComplexity.COMPLEX,
            token_optimization=TokenOptimization.STANDARD,
            max_context_tokens=400,
            context_template="""
Event: {event_type}
Escalation Type: {escalation_type}
Current Permission: {current_permission}
Requested Permission: {requested_permission}
User: {user_id}
Justification: {justification}
Risk Assessment: {risk_score:.2f}
Context: {context_summary}
""".strip(),
            reasoning_template="""
Privilege escalation analysis:
- Current level: {current_permission}
- Requested level: {requested_permission}
- Business justification: {justification}
- Risk assessment: {risk_analysis}
- Historical behavior: {user_history}
- System impact: {impact_assessment}
""".strip(),
            decision_template="""
Decision: {decision}
Rationale: {detailed_reasoning}
Conditions: {approval_conditions}
Monitoring: {enhanced_monitoring}
Escalation: {human_review_required}
""".strip(),
            risk_indicators=["unauthorized", "suspicious", "anomalous", "excessive", "unnecessary"],
            common_decisions={
                "legitimate_escalation": "approve_with_conditions",
                "business_justified": "approve_with_monitoring",
                "suspicious_request": "deny_and_investigate",
                "unauthorized_attempt": "block_and_alert"
            },
            typical_mitigations=[
                "Just-in-time access",
                "Approval workflows",
                "Time-limited permissions",
                "Enhanced monitoring",
                "Regular access reviews"
            ],
            accuracy_rate=0.85,
            avg_processing_time_ms=120.0,
            cache_hit_rate=0.65
        )

        # Data Exfiltration Template
        data_exfil_template = SecurityEventTemplate(
            template_id="data_exfil_001",
            name="Data Exfiltration Detection",
            category=EventCategory.DATA_PROTECTION,
            patterns=[
                r"data.*(export|download|copy|transfer)",
                r"large.*file.*(download|transfer)",
                r"bulk.*(access|download)",
            ],
            keywords=["data", "export", "download", "transfer", "bulk", "large", "copy"],
            analysis_complexity=AnalysisComplexity.COMPLEX,
            token_optimization=TokenOptimization.DETAILED,
            max_context_tokens=500,
            context_template="""
Event: {event_type}
Data Operation: {operation}
Data Classification: {data_classification}
Volume: {data_volume}
User: {user_id}
Destination: {destination}
Business Context: {business_context}
Risk Level: {risk_score:.2f}
Anomaly Score: {anomaly_score:.2f}
""".strip(),
            reasoning_template="""
Data protection analysis:
- Data classification: {data_classification}
- Volume assessment: {volume_analysis}
- User behavior pattern: {behavior_analysis}
- Destination assessment: {destination_analysis}
- Business justification: {business_justification}
- Regulatory compliance: {compliance_check}
- Risk indicators: {risk_indicators}
""".strip(),
            decision_template="""
Decision: {decision}
Data Protection Rationale: {protection_reasoning}
Compliance Requirements: {compliance_actions}
Monitoring Requirements: {monitoring_plan}
Incident Response: {response_actions}
""".strip(),
            risk_indicators=["personal", "confidential", "proprietary", "large_volume", "unusual_time"],
            common_decisions={
                "routine_export": "allow_with_logging",
                "business_transfer": "allow_with_approval",
                "suspicious_volume": "block_and_investigate",
                "unauthorized_access": "block_and_alert"
            },
            typical_mitigations=[
                "Data loss prevention",
                "Classification-based controls",
                "User behavior analytics",
                "Destination validation",
                "Encryption in transit"
            ],
            accuracy_rate=0.78,
            avg_processing_time_ms=180.0,
            cache_hit_rate=0.45
        )

        # System Command Template
        system_command_template = SecurityEventTemplate(
            template_id="system_cmd_001",
            name="System Commands",
            category=EventCategory.SYSTEM_INTEGRITY,
            patterns=[
                r"system.*command",
                r"(rm|delete|format|shutdown)",
                r"command.*execution",
            ],
            keywords=["system", "command", "execute", "rm", "delete", "shutdown"],
            analysis_complexity=AnalysisComplexity.MODERATE,
            token_optimization=TokenOptimization.COMPACT,
            max_context_tokens=300,
            context_template="""
Event: {event_type}
Command: {command}
Parameters: {parameters}
User: {user_id}
System Impact: {impact_level}
Risk: {risk_score:.2f}
""".strip(),
            reasoning_template="""
System command analysis:
- Command: {command}
- Impact assessment: {impact_assessment}
- Safety check: {safety_analysis}
- Authorization level: {auth_check}
""".strip(),
            decision_template="""
Decision: {decision}
Safety Rationale: {safety_reasoning}
Safeguards: {required_safeguards}
""".strip(),
            risk_indicators=["destructive", "irreversible", "system", "critical", "admin"],
            common_decisions={
                "safe_command": "allow",
                "maintenance_command": "allow_with_confirmation",
                "destructive_command": "block",
                "system_critical": "require_approval"
            },
            typical_mitigations=[
                "Command whitelisting",
                "Parameter validation",
                "Impact assessment",
                "Confirmation prompts",
                "Backup verification"
            ],
            accuracy_rate=0.91,
            avg_processing_time_ms=35.0,
            cache_hit_rate=0.80
        )

        # Store templates
        for template in [file_access_template, network_security_template, auth_template,
                        privilege_template, data_exfil_template, system_command_template]:
            self.templates[template.template_id] = template

            # Compile patterns for performance
            for pattern in template.patterns:
                try:
                    self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern {pattern}: {e}")

    def classify_event(self, event_data: Dict[str, Any]) -> Optional[SecurityEventTemplate]:
        """Classify security event and return optimal template"""

        # Create event signature for caching
        event_signature = self._create_event_signature(event_data)

        if event_signature in self.classification_cache:
            template_id = self.classification_cache[event_signature]
            return self.templates.get(template_id)

        # Extract text for pattern matching
        event_text = self._extract_event_text(event_data)

        # Score templates against event
        template_scores = {}

        for template_id, template in self.templates.items():
            score = self._calculate_template_score(template, event_text, event_data)
            if score > 0.3:  # Minimum threshold
                template_scores[template_id] = score

        # Select best matching template
        if template_scores:
            best_template_id = max(template_scores, key=template_scores.get)
            best_template = self.templates[best_template_id]

            # Cache result
            self.classification_cache[event_signature] = best_template_id

            return best_template

        return None

    def _create_event_signature(self, event_data: Dict[str, Any]) -> str:
        """Create unique signature for event classification caching"""
        key_fields = ['event_type', 'operation', 'resource', 'parameters']
        signature_data = {}

        for field in key_fields:
            if field in event_data:
                signature_data[field] = event_data[field]

        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]

    def _extract_event_text(self, event_data: Dict[str, Any]) -> str:
        """Extract searchable text from event data"""
        text_parts = []

        # Key text fields
        for field in ['event_type', 'operation', 'resource', 'description', 'reason']:
            if field in event_data and event_data[field]:
                text_parts.append(str(event_data[field]))

        # Parameters as text
        if 'parameters' in event_data:
            params = event_data['parameters']
            if isinstance(params, dict):
                text_parts.extend(str(v) for v in params.values() if v)
            elif params:
                text_parts.append(str(params))

        return ' '.join(text_parts).lower()

    def _calculate_template_score(self, template: SecurityEventTemplate,
                                 event_text: str, event_data: Dict[str, Any]) -> float:
        """Calculate how well a template matches an event"""
        score = 0.0

        # Pattern matching (40% weight)
        pattern_score = 0.0
        for pattern in template.patterns:
            if pattern in self._compiled_patterns:
                if self._compiled_patterns[pattern].search(event_text):
                    pattern_score += 1.0
            elif pattern.lower() in event_text:
                pattern_score += 0.5

        if template.patterns:
            pattern_score = pattern_score / len(template.patterns)
        score += pattern_score * 0.4

        # Keyword matching (30% weight)
        keyword_score = 0.0
        for keyword in template.keywords:
            if keyword.lower() in event_text:
                keyword_score += 1.0

        if template.keywords:
            keyword_score = keyword_score / len(template.keywords)
        score += keyword_score * 0.3

        # Risk indicator matching (20% weight)
        risk_score = 0.0
        for indicator in template.risk_indicators:
            if indicator.lower() in event_text:
                risk_score += 1.0

        if template.risk_indicators:
            risk_score = min(risk_score / len(template.risk_indicators), 1.0)
        score += risk_score * 0.2

        # Category alignment (10% weight)
        event_type = event_data.get('event_type', '').lower()
        category_keywords = {
            EventCategory.ACCESS_CONTROL: ['access', 'permission', 'file', 'resource'],
            EventCategory.AUTHENTICATION: ['login', 'auth', 'credential', 'session'],
            EventCategory.AUTHORIZATION: ['privilege', 'escalation', 'role', 'permission'],
            EventCategory.NETWORK_SECURITY: ['network', 'http', 'url', 'connection'],
            EventCategory.DATA_PROTECTION: ['data', 'export', 'download', 'privacy'],
            EventCategory.SYSTEM_INTEGRITY: ['system', 'command', 'execute', 'admin']
        }

        category_words = category_keywords.get(template.category, [])
        category_match = any(word in event_text for word in category_words)
        score += 0.1 if category_match else 0.0

        return min(score, 1.0)

    def get_template_by_id(self, template_id: str) -> Optional[SecurityEventTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: EventCategory) -> List[SecurityEventTemplate]:
        """Get all templates for a category"""
        return [t for t in self.templates.values() if t.category == category]

    def add_custom_template(self, template: SecurityEventTemplate) -> bool:
        """Add custom security event template"""
        try:
            # Validate template
            if not template.template_id or not template.name:
                return False

            # Compile and validate patterns
            for pattern in template.patterns:
                re.compile(pattern, re.IGNORECASE)

            # Store template
            self.templates[template.template_id] = template

            # Update compiled patterns
            for pattern in template.patterns:
                self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)

            self.logger.info(f"Added custom template: {template.template_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add custom template: {e}")
            return False

    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification performance statistics"""
        return {
            "total_templates": len(self.templates),
            "cache_size": len(self.classification_cache),
            "templates_by_category": {
                category.value: len(self.get_templates_by_category(category))
                for category in EventCategory
            },
            "avg_accuracy": sum(t.accuracy_rate for t in self.templates.values()) / len(self.templates),
            "avg_processing_time": sum(t.avg_processing_time_ms for t in self.templates.values()) / len(self.templates)
        }

class ContextCompressor:
    """Compresses security event context for optimal LLM usage"""

    def __init__(self):
        self.compression_cache: Dict[str, CompressedContext] = {}
        self.logger = logging.getLogger("context_compressor")

        # Token estimation rules (approximate)
        self.token_estimator = {
            'char_to_token_ratio': 4.0,  # ~4 characters per token
            'json_overhead': 1.2,        # JSON adds ~20% tokens
            'template_overhead': 1.1     # Templates add ~10% tokens
        }

    def compress_event_context(self, event_data: Dict[str, Any],
                             template: SecurityEventTemplate) -> CompressedContext:
        """Compress event context using template optimization"""

        # Create context hash for caching
        context_str = json.dumps(event_data, sort_keys=True)
        context_hash = hashlib.md5(f"{template.template_id}_{context_str}".encode()).hexdigest()[:16]

        if context_hash in self.compression_cache:
            return self.compression_cache[context_hash]

        # Extract key information based on template
        compressed = self._apply_template_compression(event_data, template)

        # Estimate token count
        token_count = self._estimate_token_count(compressed)

        # Calculate compression ratio
        original_size = len(context_str)
        compressed_size = len(json.dumps(compressed))
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

        # Create compressed context
        result = CompressedContext(
            template_id=template.template_id,
            event_summary=self._create_event_summary(event_data, template),
            key_parameters=compressed,
            risk_indicators=self._extract_risk_indicators(event_data, template),
            context_hash=context_hash,
            token_count=token_count,
            compression_ratio=compression_ratio
        )

        # Cache result
        self.compression_cache[context_hash] = result

        return result

    def _apply_template_compression(self, event_data: Dict[str, Any],
                                  template: SecurityEventTemplate) -> Dict[str, Any]:
        """Apply template-specific compression rules"""

        compressed = {}

        # Always include essential fields
        essential_fields = ['event_type', 'operation', 'user_id', 'session_id', 'risk_score']
        for field in essential_fields:
            if field in event_data:
                compressed[field] = event_data[field]

        # Template-specific compression
        if template.token_optimization == TokenOptimization.MINIMAL:
            # Only absolute essentials
            minimal_fields = ['event_type', 'operation', 'decision']
            compressed = {k: v for k, v in compressed.items() if k in minimal_fields}

        elif template.token_optimization == TokenOptimization.COMPACT:
            # Essential + context
            if 'resource' in event_data:
                compressed['resource'] = event_data['resource']
            if 'reason' in event_data:
                compressed['reason'] = event_data['reason']

            # Compress parameters
            if 'parameters' in event_data:
                compressed['parameters'] = self._compress_parameters(
                    event_data['parameters'], template
                )

        elif template.token_optimization == TokenOptimization.STANDARD:
            # Standard compression - most fields
            for field in ['resource', 'reason', 'parameters', 'context', 'alternatives_suggested']:
                if field in event_data:
                    if field == 'parameters':
                        compressed[field] = self._compress_parameters(event_data[field], template)
                    elif field == 'context':
                        compressed[field] = self._compress_context(event_data[field], template)
                    else:
                        compressed[field] = event_data[field]

        else:  # DETAILED
            # Full context with minimal compression
            compressed = event_data.copy()
            if 'parameters' in compressed:
                compressed['parameters'] = self._compress_parameters(compressed['parameters'], template)

        return compressed

    def _compress_parameters(self, parameters: Any, template: SecurityEventTemplate) -> Any:
        """Compress parameters based on template relevance"""
        if not isinstance(parameters, dict):
            return parameters

        compressed_params = {}

        # Include parameters mentioned in template keywords
        for key, value in parameters.items():
            # Always include if key matches template keywords
            if any(keyword.lower() in key.lower() for keyword in template.keywords):
                compressed_params[key] = value
            # Include if value contains risk indicators
            elif any(indicator.lower() in str(value).lower() for indicator in template.risk_indicators):
                compressed_params[key] = value
            # Include critical security parameters
            elif key.lower() in ['path', 'url', 'command', 'file', 'user', 'permission']:
                compressed_params[key] = value

        # If nothing important found, include first few parameters
        if not compressed_params and parameters:
            compressed_params = dict(list(parameters.items())[:3])

        return compressed_params

    def _compress_context(self, context: Any, template: SecurityEventTemplate) -> Any:
        """Compress context information"""
        if not isinstance(context, dict):
            return context

        # Keep only relevant context based on template category
        relevant_keys = {
            EventCategory.ACCESS_CONTROL: ['permission_level', 'resource_type', 'access_method'],
            EventCategory.AUTHENTICATION: ['auth_method', 'session_info', 'failure_count'],
            EventCategory.NETWORK_SECURITY: ['url_reputation', 'protocol', 'destination'],
            EventCategory.DATA_PROTECTION: ['data_classification', 'volume', 'destination'],
            EventCategory.SYSTEM_INTEGRITY: ['command_type', 'impact_level', 'safeguards']
        }

        template_keys = relevant_keys.get(template.category, [])

        compressed_context = {}
        for key, value in context.items():
            if (key.lower() in [k.lower() for k in template_keys] or
                any(keyword.lower() in key.lower() for keyword in template.keywords)):
                compressed_context[key] = value

        return compressed_context

    def _create_event_summary(self, event_data: Dict[str, Any],
                            template: SecurityEventTemplate) -> str:
        """Create concise event summary"""

        # Extract key information
        event_type = event_data.get('event_type', 'unknown')
        operation = event_data.get('operation', 'unknown')
        resource = event_data.get('resource', '')
        user_id = event_data.get('user_id', 'unknown')

        # Template-specific summary format
        if template.category == EventCategory.ACCESS_CONTROL:
            return f"{event_type}: {user_id} attempted {operation} on {resource}"
        elif template.category == EventCategory.AUTHENTICATION:
            return f"{event_type}: {user_id} authentication {operation}"
        elif template.category == EventCategory.NETWORK_SECURITY:
            return f"{event_type}: {operation} to {resource}"
        else:
            return f"{event_type}: {operation} by {user_id}"

    def _extract_risk_indicators(self, event_data: Dict[str, Any],
                                template: SecurityEventTemplate) -> List[str]:
        """Extract risk indicators present in event"""
        event_text = ' '.join(str(v) for v in event_data.values() if v).lower()

        found_indicators = []
        for indicator in template.risk_indicators:
            if indicator.lower() in event_text:
                found_indicators.append(indicator)

        return found_indicators

    def _estimate_token_count(self, data: Any) -> int:
        """Estimate token count for data"""
        if isinstance(data, str):
            char_count = len(data)
        else:
            char_count = len(json.dumps(data))

        # Apply estimation rules
        base_tokens = char_count / self.token_estimator['char_to_token_ratio']

        if isinstance(data, dict):
            base_tokens *= self.token_estimator['json_overhead']

        return int(base_tokens)

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics"""
        if not self.compression_cache:
            return {"cache_size": 0, "avg_compression_ratio": 0.0, "avg_token_count": 0}

        ratios = [c.compression_ratio for c in self.compression_cache.values()]
        tokens = [c.token_count for c in self.compression_cache.values()]

        return {
            "cache_size": len(self.compression_cache),
            "avg_compression_ratio": sum(ratios) / len(ratios),
            "avg_token_count": sum(tokens) / len(tokens),
            "min_compression": min(ratios),
            "max_compression": max(ratios),
            "token_savings": f"{(1 - sum(ratios) / len(ratios)) * 100:.1f}%"
        }

def demo_template_system():
    """Demonstrate the security event template system"""

    print("🔖 Security Event Template System Demo")
    print("=" * 60)

    # Initialize components
    classifier = SecurityEventClassifier()
    compressor = ContextCompressor()

    # Test events
    test_events = [
        {
            "event_type": "permission_check",
            "operation": "file_read",
            "resource": "/home/user/config.json",
            "user_id": "user123",
            "parameters": {"file_path": "/home/user/config.json", "mode": "read"},
            "risk_score": 0.2,
            "decision": "allow"
        },
        {
            "event_type": "security_violation",
            "operation": "file_access",
            "resource": "../../../etc/passwd",
            "user_id": "user456",
            "parameters": {"file_path": "../../../etc/passwd", "attempted_access": "read"},
            "risk_score": 0.9,
            "decision": "block"
        },
        {
            "event_type": "privilege_escalation",
            "operation": "sudo_request",
            "resource": "system_admin",
            "user_id": "user789",
            "parameters": {"requested_privilege": "root", "justification": "system maintenance"},
            "risk_score": 0.7,
            "context": {"time": "outside_hours", "frequency": "unusual"}
        },
        {
            "event_type": "data_export",
            "operation": "bulk_download",
            "resource": "customer_database",
            "user_id": "user101",
            "parameters": {"record_count": 50000, "destination": "external_drive"},
            "risk_score": 0.8
        }
    ]

    print(f"Processing {len(test_events)} test events...\n")

    for i, event in enumerate(test_events, 1):
        print(f"{i}. Event: {event['event_type']}")
        print(f"   Operation: {event['operation']}")
        print(f"   Resource: {event['resource']}")

        # Classify event
        template = classifier.classify_event(event)
        if template:
            print(f"   Template: {template.name} ({template.template_id})")
            print(f"   Category: {template.category.value}")
            print(f"   Complexity: {template.analysis_complexity.value}")
            print(f"   Optimization: {template.token_optimization.value}")
            print(f"   Max Tokens: {template.max_context_tokens}")

            # Compress context
            compressed = compressor.compress_event_context(event, template)
            print(f"   Compressed Tokens: {compressed.token_count}")
            print(f"   Compression Ratio: {compressed.compression_ratio:.2f}")
            print(f"   Risk Indicators: {compressed.risk_indicators}")

        else:
            print(f"   Template: No matching template found")

        print()

    # Show statistics
    print("📊 System Statistics")
    print("=" * 30)

    classification_stats = classifier.get_classification_stats()
    print(f"Total Templates: {classification_stats['total_templates']}")
    print(f"Avg Accuracy: {classification_stats['avg_accuracy']:.2%}")
    print(f"Avg Processing Time: {classification_stats['avg_processing_time']:.1f}ms")

    compression_stats = compressor.get_compression_stats()
    print(f"Avg Token Count: {compression_stats['avg_token_count']:.0f}")
    print(f"Token Savings: {compression_stats['token_savings']}")

    print("\n✅ Security Event Template System Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    demo_template_system()