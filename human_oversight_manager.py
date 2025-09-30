#!/usr/bin/env python3
"""
Human-in-the-Loop Governance System
Manages human approval workflows for risky AI operations and maintains
transparent decision-making processes with proper audit trails
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time
import logging

# Configure logging for human oversight
logging.basicConfig(level=logging.INFO)
oversight_logger = logging.getLogger('PennyHumanOversight')

class ApprovalStatus(Enum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class UrgencyLevel(Enum):
    """Urgency levels for approval requests"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class ApprovalRequest:
    """Represents a request for human approval"""
    id: str
    operation: str
    details: Dict[str, Any]
    urgency: UrgencyLevel
    timestamp: datetime
    timeout_seconds: int
    status: ApprovalStatus
    requested_by: str
    risk_assessment: Dict[str, Any]
    context: Dict[str, Any]
    approval_criteria: List[str]

@dataclass
class ApprovalResponse:
    """Response to an approval request"""
    request_id: str
    status: ApprovalStatus
    response_time: datetime
    reviewer: str
    decision_reason: str
    additional_constraints: List[str]
    follow_up_required: bool

@dataclass
class ApprovalPolicy:
    """Policy defining when approval is required"""
    operation_pattern: str
    required: bool
    timeout_seconds: int
    required_reviewer_level: str
    escalation_path: List[str]
    auto_approve_conditions: List[str]
    auto_deny_conditions: List[str]

class HumanOversightManager:
    """
    Manages human approval workflows for AI operations that require oversight:
    - Code execution and file system operations
    - Significant personality changes beyond safe thresholds
    - Sensitive research topics or data access
    - System configuration modifications
    - Emergency interventions and safety overrides
    """

    def __init__(self, db_path: str = "data/human_oversight.db"):
        self.db_path = db_path
        self.oversight_logger = oversight_logger

        # Approval policies - define what operations require human approval
        self.approval_policies = {
            'code_execution': ApprovalPolicy(
                operation_pattern='code_execution',
                required=True,
                timeout_seconds=300,  # 5 minutes
                required_reviewer_level='developer',
                escalation_path=['senior_developer', 'security_officer'],
                auto_approve_conditions=[],  # Never auto-approve code execution
                auto_deny_conditions=['contains_system_calls', 'network_access_requested']
            ),
            'significant_personality_change': ApprovalPolicy(
                operation_pattern='personality_change',
                required=True,
                timeout_seconds=600,  # 10 minutes
                required_reviewer_level='user',
                escalation_path=['administrator'],
                auto_approve_conditions=['magnitude_below_0.1', 'user_explicitly_requested'],
                auto_deny_conditions=['magnitude_above_0.5', 'rapid_succession_changes']
            ),
            'sensitive_research': ApprovalPolicy(
                operation_pattern='research',
                required=True,
                timeout_seconds=180,  # 3 minutes
                required_reviewer_level='user',
                escalation_path=['content_moderator', 'administrator'],
                auto_approve_conditions=['general_knowledge_only'],
                auto_deny_conditions=['medical_advice', 'financial_advice', 'legal_advice', 'personal_information']
            ),
            'system_modification': ApprovalPolicy(
                operation_pattern='system_config',
                required=True,
                timeout_seconds=900,  # 15 minutes
                required_reviewer_level='administrator',
                escalation_path=['security_officer', 'system_owner'],
                auto_approve_conditions=[],  # Never auto-approve system changes
                auto_deny_conditions=['security_weakening', 'data_exposure_risk']
            ),
            'emergency_override': ApprovalPolicy(
                operation_pattern='emergency',
                required=True,
                timeout_seconds=60,   # 1 minute for emergencies
                required_reviewer_level='any_human',
                escalation_path=['emergency_contact'],
                auto_approve_conditions=[],
                auto_deny_conditions=[]
            ),
            'file_system_access': ApprovalPolicy(
                operation_pattern='file_system',
                required=True,
                timeout_seconds=240,  # 4 minutes
                required_reviewer_level='user',
                escalation_path=['administrator'],
                auto_approve_conditions=['read_only_access', 'user_documents_only'],
                auto_deny_conditions=['system_files', 'credential_files', 'write_access_to_critical']
            )
        }

        # Active approval requests
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalResponse] = []

        # Human reviewers and their capabilities
        self.available_reviewers = {
            'user': {'level': 'user', 'available': True, 'response_time_avg': 120},
            'administrator': {'level': 'administrator', 'available': True, 'response_time_avg': 300},
            'developer': {'level': 'developer', 'available': True, 'response_time_avg': 180},
            'security_officer': {'level': 'security_officer', 'available': True, 'response_time_avg': 240}
        }

        # Statistics and monitoring
        self.approval_stats = {
            'total_requests': 0,
            'approved': 0,
            'denied': 0,
            'timeouts': 0,
            'average_response_time': 0
        }

        # User interface callbacks for different approval types
        self.approval_interfaces: Dict[str, Callable] = {
            'console': self._console_approval_interface,
            'gui': self._gui_approval_interface,  # Placeholder
            'web': self._web_approval_interface   # Placeholder
        }

        # Default to console interface
        self.current_interface = 'console'

        # Initialize database
        self._init_oversight_database()

        # Load historical data
        self._load_approval_history()

        # Background task for handling timeouts
        self._start_timeout_monitor()

    def _init_oversight_database(self):
        """Initialize human oversight database"""
        with sqlite3.connect(self.db_path) as conn:
            # Approval requests table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS approval_requests (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation TEXT NOT NULL,
                    details TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    timeout_seconds INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    requested_by TEXT,
                    risk_assessment TEXT,
                    context TEXT,
                    approval_criteria TEXT
                )
            ''')

            # Approval responses table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS approval_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    response_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    reviewer TEXT,
                    decision_reason TEXT,
                    additional_constraints TEXT,
                    follow_up_required BOOLEAN DEFAULT FALSE,
                    response_time_seconds INTEGER,
                    FOREIGN KEY (request_id) REFERENCES approval_requests (id)
                )
            ''')

            # Reviewer activity log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reviewer_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviewer TEXT NOT NULL,
                    action TEXT NOT NULL,
                    request_id TEXT,
                    notes TEXT
                )
            ''')

            # Approval policy overrides
            conn.execute('''
                CREATE TABLE IF NOT EXISTS policy_overrides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_pattern TEXT NOT NULL,
                    override_type TEXT NOT NULL,
                    conditions TEXT,
                    authorized_by TEXT,
                    expires_at DATETIME,
                    active BOOLEAN DEFAULT TRUE
                )
            ''')

            conn.commit()

    def _load_approval_history(self):
        """Load recent approval history for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT ar.id, ar.operation, ar.urgency, ar.status, ar.timestamp,
                           ares.status, ares.reviewer, ares.decision_reason, ares.response_time_seconds
                    FROM approval_requests ar
                    LEFT JOIN approval_responses ares ON ar.id = ares.request_id
                    WHERE ar.timestamp > datetime('now', '-30 days')
                    ORDER BY ar.timestamp DESC
                    LIMIT 100
                ''')

                for row in cursor.fetchall():
                    if row[5]:  # Has response
                        response = ApprovalResponse(
                            request_id=row[0],
                            status=ApprovalStatus(row[5]),
                            response_time=datetime.now(),  # Placeholder
                            reviewer=row[6] or 'unknown',
                            decision_reason=row[7] or '',
                            additional_constraints=[],
                            follow_up_required=False
                        )
                        self.approval_history.append(response)

                # Update statistics
                self._update_approval_statistics()

        except Exception as e:
            self.oversight_logger.error(f"Failed to load approval history: {e}")

    def _update_approval_statistics(self):
        """Update approval statistics from history"""
        if not self.approval_history:
            return

        total = len(self.approval_history)
        approved = len([r for r in self.approval_history if r.status == ApprovalStatus.APPROVED])
        denied = len([r for r in self.approval_history if r.status == ApprovalStatus.DENIED])
        timeouts = len([r for r in self.approval_history if r.status == ApprovalStatus.TIMEOUT])

        self.approval_stats.update({
            'total_requests': total,
            'approved': approved,
            'denied': denied,
            'timeouts': timeouts,
            'approval_rate': approved / total if total > 0 else 0,
            'timeout_rate': timeouts / total if total > 0 else 0
        })

    def _start_timeout_monitor(self):
        """Start background thread to monitor request timeouts"""
        def timeout_monitor():
            while True:
                try:
                    current_time = datetime.now()
                    expired_requests = []

                    for request_id, request in self.pending_approvals.items():
                        if request.status == ApprovalStatus.PENDING:
                            elapsed = (current_time - request.timestamp).total_seconds()
                            if elapsed > request.timeout_seconds:
                                expired_requests.append(request_id)

                    # Process expired requests
                    for request_id in expired_requests:
                        asyncio.create_task(self._handle_timeout(request_id))

                    time.sleep(10)  # Check every 10 seconds

                except Exception as e:
                    self.oversight_logger.error(f"Timeout monitor error: {e}")
                    time.sleep(30)  # Wait longer after error

        thread = threading.Thread(target=timeout_monitor, daemon=True)
        thread.start()

    async def request_human_approval(self, operation: str, details: Dict[str, Any],
                                   urgency: UrgencyLevel = UrgencyLevel.NORMAL,
                                   requested_by: str = "system",
                                   context: Dict[str, Any] = None,
                                   test_mode: bool = False,
                                   test_timeout: float = 1.0) -> ApprovalResponse:
        """
        Request human approval for a potentially risky operation
        """
        context = context or {}

        # Check if approval is required based on policies
        policy = self._get_applicable_policy(operation, details)
        if not policy or not policy.required:
            # Auto-approve if no policy requires approval
            return ApprovalResponse(
                request_id="auto_approved",
                status=ApprovalStatus.APPROVED,
                response_time=datetime.now(),
                reviewer="system",
                decision_reason="No approval required by policy",
                additional_constraints=[],
                follow_up_required=False
            )

        # Check auto-deny conditions
        if self._check_auto_deny_conditions(policy, details, context):
            return ApprovalResponse(
                request_id="auto_denied",
                status=ApprovalStatus.DENIED,
                response_time=datetime.now(),
                reviewer="system",
                decision_reason="Automatically denied by policy",
                additional_constraints=[],
                follow_up_required=True
            )

        # Check auto-approve conditions
        if self._check_auto_approve_conditions(policy, details, context):
            return ApprovalResponse(
                request_id="auto_approved_conditional",
                status=ApprovalStatus.APPROVED,
                response_time=datetime.now(),
                reviewer="system",
                decision_reason="Automatically approved by policy conditions",
                additional_constraints=[],
                follow_up_required=False
            )

        # Handle test mode with mock responses
        if test_mode:
            return await self._handle_test_mode_approval(operation, details, test_timeout)

        # Generate approval request
        approval_id = str(uuid.uuid4())
        risk_assessment = await self._assess_operation_risk(operation, details, context)

        # Use test timeout if in test mode
        timeout_seconds = test_timeout if test_mode else policy.timeout_seconds

        approval_request = ApprovalRequest(
            id=approval_id,
            operation=operation,
            details=details,
            urgency=urgency,
            timestamp=datetime.now(),
            timeout_seconds=int(timeout_seconds),
            status=ApprovalStatus.PENDING,
            requested_by=requested_by,
            risk_assessment=risk_assessment,
            context=context,
            approval_criteria=self._generate_approval_criteria(operation, details, risk_assessment)
        )

        self.pending_approvals[approval_id] = approval_request

        # Store in database
        await self._store_approval_request(approval_request)

        # Display approval request to user
        await self._display_approval_request(approval_request)

        # Wait for response or timeout
        response = await self._wait_for_approval_response(approval_id, policy.timeout_seconds)

        return response

    def _get_applicable_policy(self, operation: str, details: Dict[str, Any]) -> Optional[ApprovalPolicy]:
        """Get the applicable approval policy for an operation"""
        for policy_name, policy in self.approval_policies.items():
            if operation.lower() in policy.operation_pattern.lower():
                return policy

        # Check for pattern matches in operation details
        for policy_name, policy in self.approval_policies.items():
            if any(policy.operation_pattern.lower() in str(value).lower() for value in details.values()):
                return policy

        return None

    def _check_auto_deny_conditions(self, policy: ApprovalPolicy, details: Dict[str, Any],
                                   context: Dict[str, Any]) -> bool:
        """Check if auto-deny conditions are met"""
        for condition in policy.auto_deny_conditions:
            if self._evaluate_condition(condition, details, context):
                self.oversight_logger.warning(f"Auto-deny condition triggered: {condition}")
                return True
        return False

    def _check_auto_approve_conditions(self, policy: ApprovalPolicy, details: Dict[str, Any],
                                     context: Dict[str, Any]) -> bool:
        """Check if auto-approve conditions are met"""
        if not policy.auto_approve_conditions:
            return False

        # All conditions must be met for auto-approval
        for condition in policy.auto_approve_conditions:
            if not self._evaluate_condition(condition, details, context):
                return False

        return True

    def _evaluate_condition(self, condition: str, details: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a policy condition"""
        # Simple condition evaluation - in production, this would be more sophisticated
        condition_lower = condition.lower()

        if 'magnitude_below' in condition_lower:
            magnitude = details.get('change_magnitude', 0)
            threshold = float(condition_lower.split('_')[-1])
            return magnitude < threshold

        elif 'magnitude_above' in condition_lower:
            magnitude = details.get('change_magnitude', 0)
            threshold = float(condition_lower.split('_')[-1])
            return magnitude > threshold

        elif 'user_explicitly_requested' in condition_lower:
            return context.get('user_initiated', False)

        elif 'contains_system_calls' in condition_lower:
            code = details.get('code', '')
            dangerous_calls = ['subprocess', 'os.system', 'exec', 'eval']
            return any(call in code for call in dangerous_calls)

        elif 'network_access_requested' in condition_lower:
            return 'network' in str(details).lower() or 'http' in str(details).lower()

        elif 'read_only_access' in condition_lower:
            return details.get('access_type', '').lower() == 'read'

        elif 'medical_advice' in condition_lower:
            content = str(details) + str(context)
            medical_keywords = ['diagnose', 'treatment', 'medication', 'symptoms', 'disease']
            return any(keyword in content.lower() for keyword in medical_keywords)

        # Default to False for unknown conditions
        return False

    async def _assess_operation_risk(self, operation: str, details: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk level of an operation"""
        risk_assessment = {
            'overall_risk': 'medium',
            'risk_factors': [],
            'mitigation_suggestions': [],
            'confidence': 0.7
        }

        # Analyze different risk factors
        if operation == 'code_execution':
            if any(keyword in str(details).lower() for keyword in ['subprocess', 'system', 'exec']):
                risk_assessment['risk_factors'].append('System call execution')
                risk_assessment['overall_risk'] = 'high'

            if 'network' in str(details).lower():
                risk_assessment['risk_factors'].append('Network access requested')
                risk_assessment['overall_risk'] = 'high'

        elif operation == 'personality_change':
            magnitude = details.get('change_magnitude', 0)
            if magnitude > 0.3:
                risk_assessment['risk_factors'].append('Large personality change')
                risk_assessment['overall_risk'] = 'high'

        elif operation == 'file_system':
            if details.get('access_type') == 'write':
                risk_assessment['risk_factors'].append('Write access to file system')

            if any(path in str(details).lower() for path in ['/system/', '/etc/', 'password']):
                risk_assessment['risk_factors'].append('Access to sensitive system files')
                risk_assessment['overall_risk'] = 'critical'

        # Generate mitigation suggestions
        if risk_assessment['overall_risk'] in ['high', 'critical']:
            risk_assessment['mitigation_suggestions'].extend([
                'Consider limiting scope of operation',
                'Implement additional monitoring',
                'Require elevated approval authority'
            ])

        return risk_assessment

    def _generate_approval_criteria(self, operation: str, details: Dict[str, Any],
                                  risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate criteria that reviewers should consider"""
        criteria = [
            'Does this operation serve a legitimate user need?',
            'Are the risks acceptable given the benefits?',
            'Have appropriate safeguards been considered?'
        ]

        if operation == 'code_execution':
            criteria.extend([
                'Is the code from a trusted source?',
                'Does the code perform only the intended function?',
                'Are there any obvious security vulnerabilities?'
            ])

        elif operation == 'personality_change':
            criteria.extend([
                'Is this change aligned with user preferences?',
                'Will this change improve the user experience?',
                'Is the magnitude of change reasonable?'
            ])

        elif operation == 'file_system':
            criteria.extend([
                'Is file access necessary for the requested operation?',
                'Are only appropriate files being accessed?',
                'Is the access level (read/write) appropriate?'
            ])

        return criteria

    async def _display_approval_request(self, request: ApprovalRequest):
        """Display approval request to user using configured interface"""
        interface_func = self.approval_interfaces.get(self.current_interface, self._console_approval_interface)
        await interface_func(request)

    async def _console_approval_interface(self, request: ApprovalRequest):
        """Console-based approval interface"""
        print(f"\n{'='*60}")
        print(f"🚨 HUMAN APPROVAL REQUIRED 🚨")
        print(f"{'='*60}")
        print(f"Request ID: {request.id}")
        print(f"Operation: {request.operation}")
        print(f"Urgency: {request.urgency.value}")
        print(f"Requested by: {request.requested_by}")
        print(f"Timeout: {request.timeout_seconds} seconds")
        print(f"Risk Level: {request.risk_assessment.get('overall_risk', 'unknown')}")

        print(f"\nOperation Details:")
        for key, value in request.details.items():
            print(f"  {key}: {value}")

        if request.risk_assessment.get('risk_factors'):
            print(f"\nRisk Factors:")
            for factor in request.risk_assessment['risk_factors']:
                print(f"  ⚠️ {factor}")

        if request.approval_criteria:
            print(f"\nApproval Criteria:")
            for i, criterion in enumerate(request.approval_criteria, 1):
                print(f"  {i}. {criterion}")

        print(f"\nOptions:")
        print(f"  y/yes/approve - Approve this operation")
        print(f"  n/no/deny     - Deny this operation")
        print(f"  d/details     - Show more details")
        print(f"  c/cancel      - Cancel this request")
        print(f"{'='*60}")
        print(f"Please respond within {request.timeout_seconds} seconds...")

    async def _gui_approval_interface(self, request: ApprovalRequest):
        """GUI-based approval interface (placeholder)"""
        # In a real implementation, this would show a GUI dialog
        print(f"[GUI] Approval request displayed for {request.operation}")

    async def _web_approval_interface(self, request: ApprovalRequest):
        """Web-based approval interface (placeholder)"""
        # In a real implementation, this would send a web notification
        print(f"[WEB] Approval request sent via web interface for {request.operation}")

    async def _wait_for_approval_response(self, approval_id: str, timeout_seconds: int) -> ApprovalResponse:
        """Wait for approval response or timeout"""
        start_time = datetime.now()
        check_interval = 1.0  # Check every second

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Check if response has been provided
            if approval_id in self.pending_approvals:
                request = self.pending_approvals[approval_id]
                if request.status != ApprovalStatus.PENDING:
                    # Response received
                    response = await self._get_stored_response(approval_id)
                    if response:
                        return response

            await asyncio.sleep(check_interval)

        # Timeout occurred
        await self._handle_timeout(approval_id)
        return ApprovalResponse(
            request_id=approval_id,
            status=ApprovalStatus.TIMEOUT,
            response_time=datetime.now(),
            reviewer="system",
            decision_reason="Request timed out",
            additional_constraints=[],
            follow_up_required=True
        )

    async def process_approval_response(self, approval_id: str, response: str,
                                      reviewer: str = "user") -> ApprovalResponse:
        """Process human approval response"""
        if approval_id not in self.pending_approvals:
            return ApprovalResponse(
                request_id=approval_id,
                status=ApprovalStatus.DENIED,
                response_time=datetime.now(),
                reviewer=reviewer,
                decision_reason="Invalid approval ID",
                additional_constraints=[],
                follow_up_required=False
            )

        request = self.pending_approvals[approval_id]
        response_lower = response.lower().strip()

        # Parse response
        if response_lower in ['y', 'yes', 'approve', 'approved']:
            status = ApprovalStatus.APPROVED
            reason = "Human reviewer approved the operation"
        elif response_lower in ['n', 'no', 'deny', 'denied']:
            status = ApprovalStatus.DENIED
            reason = "Human reviewer denied the operation"
        elif response_lower in ['c', 'cancel', 'cancelled']:
            status = ApprovalStatus.CANCELLED
            reason = "Request cancelled by reviewer"
        elif response_lower in ['d', 'details']:
            # Show more details (don't change status)
            await self._show_detailed_information(request)
            return ApprovalResponse(
                request_id=approval_id,
                status=ApprovalStatus.PENDING,
                response_time=datetime.now(),
                reviewer=reviewer,
                decision_reason="Details requested - still pending approval",
                additional_constraints=[],
                follow_up_required=False
            )
        else:
            return ApprovalResponse(
                request_id=approval_id,
                status=ApprovalStatus.PENDING,
                response_time=datetime.now(),
                reviewer=reviewer,
                decision_reason="Invalid response - please respond y/n/c/d",
                additional_constraints=[],
                follow_up_required=False
            )

        # Update request status
        request.status = status

        # Create response
        approval_response = ApprovalResponse(
            request_id=approval_id,
            status=status,
            response_time=datetime.now(),
            reviewer=reviewer,
            decision_reason=reason,
            additional_constraints=[],
            follow_up_required=status == ApprovalStatus.DENIED
        )

        # Store response
        await self._store_approval_response(approval_response)

        # Remove from pending
        if approval_id in self.pending_approvals:
            del self.pending_approvals[approval_id]

        # Update statistics
        self.approval_stats['total_requests'] += 1
        if status == ApprovalStatus.APPROVED:
            self.approval_stats['approved'] += 1
        elif status == ApprovalStatus.DENIED:
            self.approval_stats['denied'] += 1

        # Log the decision
        self.oversight_logger.info(f"APPROVAL DECISION: {approval_id} - {status.value} by {reviewer}")

        return approval_response

    async def _handle_timeout(self, approval_id: str):
        """Handle approval request timeout"""
        if approval_id not in self.pending_approvals:
            return

        request = self.pending_approvals[approval_id]
        request.status = ApprovalStatus.TIMEOUT

        # Create timeout response
        timeout_response = ApprovalResponse(
            request_id=approval_id,
            status=ApprovalStatus.TIMEOUT,
            response_time=datetime.now(),
            reviewer="system",
            decision_reason="Request timed out - defaulting to deny for safety",
            additional_constraints=["Manual review required for retry"],
            follow_up_required=True
        )

        # Store response
        await self._store_approval_response(timeout_response)

        # Remove from pending
        del self.pending_approvals[approval_id]

        # Update statistics
        self.approval_stats['timeouts'] += 1

        self.oversight_logger.warning(f"APPROVAL TIMEOUT: {approval_id} - {request.operation}")

    async def _show_detailed_information(self, request: ApprovalRequest):
        """Show detailed information about an approval request"""
        print(f"\n{'='*60}")
        print(f"DETAILED APPROVAL INFORMATION")
        print(f"{'='*60}")
        print(f"Request ID: {request.id}")
        print(f"Timestamp: {request.timestamp}")
        print(f"Operation: {request.operation}")
        print(f"Requested by: {request.requested_by}")

        print(f"\nFull Details:")
        print(json.dumps(request.details, indent=2))

        print(f"\nContext:")
        print(json.dumps(request.context, indent=2))

        print(f"\nRisk Assessment:")
        print(json.dumps(request.risk_assessment, indent=2))

        if request.approval_criteria:
            print(f"\nApproval Criteria:")
            for i, criterion in enumerate(request.approval_criteria, 1):
                print(f"  {i}. {criterion}")

        print(f"{'='*60}")

    async def _store_approval_request(self, request: ApprovalRequest):
        """Store approval request in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO approval_requests
                    (id, operation, details, urgency, timeout_seconds, status, requested_by, risk_assessment, context, approval_criteria)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.id, request.operation, json.dumps(request.details),
                    request.urgency.value, request.timeout_seconds, request.status.value,
                    request.requested_by, json.dumps(request.risk_assessment),
                    json.dumps(request.context), json.dumps(request.approval_criteria)
                ))
                conn.commit()

        except Exception as e:
            self.oversight_logger.error(f"Failed to store approval request: {e}")

    async def _store_approval_response(self, response: ApprovalResponse):
        """Store approval response in database"""
        try:
            # Calculate response time
            request = self.pending_approvals.get(response.request_id)
            response_time_seconds = 0
            if request:
                response_time_seconds = int((response.response_time - request.timestamp).total_seconds())

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO approval_responses
                    (request_id, status, reviewer, decision_reason, additional_constraints, follow_up_required, response_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    response.request_id, response.status.value, response.reviewer,
                    response.decision_reason, json.dumps(response.additional_constraints),
                    response.follow_up_required, response_time_seconds
                ))
                conn.commit()

        except Exception as e:
            self.oversight_logger.error(f"Failed to store approval response: {e}")

    async def _get_stored_response(self, approval_id: str) -> Optional[ApprovalResponse]:
        """Get stored approval response"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT status, reviewer, decision_reason, additional_constraints, follow_up_required, response_timestamp
                    FROM approval_responses
                    WHERE request_id = ?
                    ORDER BY response_timestamp DESC
                    LIMIT 1
                ''', (approval_id,))

                row = cursor.fetchone()
                if row:
                    return ApprovalResponse(
                        request_id=approval_id,
                        status=ApprovalStatus(row[0]),
                        response_time=datetime.fromisoformat(row[5]),
                        reviewer=row[1],
                        decision_reason=row[2],
                        additional_constraints=json.loads(row[3]) if row[3] else [],
                        follow_up_required=bool(row[4])
                    )

        except Exception as e:
            self.oversight_logger.error(f"Failed to get stored response: {e}")

        return None

    async def get_approval_statistics(self) -> Dict[str, Any]:
        """Get approval system statistics"""
        stats = self.approval_stats.copy()

        # Add real-time data
        stats['pending_requests'] = len(self.pending_approvals)
        stats['available_reviewers'] = len([r for r in self.available_reviewers.values() if r['available']])

        # Calculate trends
        if self.approval_history:
            recent_responses = [r for r in self.approval_history if r.response_time > datetime.now() - timedelta(days=7)]
            stats['recent_approval_rate'] = len([r for r in recent_responses if r.status == ApprovalStatus.APPROVED]) / len(recent_responses) if recent_responses else 0

        return stats

    async def _handle_test_mode_approval(self, operation: str, details: Dict[str, Any],
                                       timeout: float) -> ApprovalResponse:
        """Handle approval in test mode with mock responses"""
        # Simulate processing time
        await asyncio.sleep(min(0.1, timeout / 10))

        # Mock decision logic for testing
        if operation == 'code_execution':
            code = details.get('code', '')
            if any(dangerous in code for dangerous in ['rm -rf', 'subprocess', 'exec']):
                return ApprovalResponse(
                    request_id="test_auto_denied",
                    status=ApprovalStatus.DENIED,
                    response_time=datetime.now(),
                    reviewer="test_system",
                    decision_reason="Test mode: Dangerous code auto-denied",
                    additional_constraints=[],
                    follow_up_required=False
                )
            else:
                # Timeout for safe code in test mode to test timeout handling
                await asyncio.sleep(timeout + 0.1)
                return ApprovalResponse(
                    request_id="test_timeout",
                    status=ApprovalStatus.TIMEOUT,
                    response_time=datetime.now(),
                    reviewer="test_system",
                    decision_reason="Test mode timeout",
                    additional_constraints=[],
                    follow_up_required=True
                )

        elif operation == 'personality_change':
            magnitude = details.get('change_magnitude', 0)
            if magnitude > 0.3:
                return ApprovalResponse(
                    request_id="test_denied_large_change",
                    status=ApprovalStatus.DENIED,
                    response_time=datetime.now(),
                    reviewer="test_system",
                    decision_reason="Test mode: Large personality change denied",
                    additional_constraints=[],
                    follow_up_required=False
                )
            else:
                return ApprovalResponse(
                    request_id="test_approved_small_change",
                    status=ApprovalStatus.APPROVED,
                    response_time=datetime.now(),
                    reviewer="test_system",
                    decision_reason="Test mode: Small personality change approved",
                    additional_constraints=[],
                    follow_up_required=False
                )

        # Default test approval for other operations
        return ApprovalResponse(
            request_id="test_approved_default",
            status=ApprovalStatus.APPROVED,
            response_time=datetime.now(),
            reviewer="test_system",
            decision_reason="Test mode: Default approval",
            additional_constraints=[],
            follow_up_required=False
        )

    async def get_pending_approvals_summary(self) -> List[Dict[str, Any]]:
        """Get summary of pending approval requests"""
        summary = []

        for request_id, request in self.pending_approvals.items():
            elapsed_time = (datetime.now() - request.timestamp).total_seconds()
            remaining_time = max(0, request.timeout_seconds - elapsed_time)

            summary.append({
                'id': request_id,
                'operation': request.operation,
                'urgency': request.urgency.value,
                'requested_by': request.requested_by,
                'elapsed_seconds': int(elapsed_time),
                'remaining_seconds': int(remaining_time),
                'risk_level': request.risk_assessment.get('overall_risk', 'unknown')
            })

        # Sort by urgency and remaining time
        urgency_order = {UrgencyLevel.EMERGENCY: 0, UrgencyLevel.CRITICAL: 1, UrgencyLevel.HIGH: 2, UrgencyLevel.NORMAL: 3, UrgencyLevel.LOW: 4}
        summary.sort(key=lambda x: (urgency_order.get(UrgencyLevel(x['urgency']), 5), x['remaining_seconds']))

        return summary


if __name__ == "__main__":
    async def main():
        print("👤 Testing Human Oversight Manager")
        print("=" * 50)

        manager = HumanOversightManager()

        # Test 1: Code execution approval
        print("\n1. Testing code execution approval...")
        response = await manager.request_human_approval(
            'code_execution',
            {
                'code': 'print("Hello, World!")',
                'execution_context': 'user_request'
            },
            UrgencyLevel.NORMAL,
            'test_system',
            {'user_initiated': True}
        )
        print(f"Code execution approval: {response.status.value}")
        print(f"Reason: {response.decision_reason}")

        # Test 2: Dangerous code auto-denial
        print("\n2. Testing dangerous code auto-denial...")
        response = await manager.request_human_approval(
            'code_execution',
            {
                'code': 'import subprocess; subprocess.call("rm -rf /")',
                'execution_context': 'automated'
            },
            UrgencyLevel.HIGH,
            'test_system'
        )
        print(f"Dangerous code approval: {response.status.value}")
        print(f"Reason: {response.decision_reason}")

        # Test 3: Personality change approval
        print("\n3. Testing personality change approval...")
        response = await manager.request_human_approval(
            'personality_change',
            {
                'dimension': 'sass_level',
                'change_magnitude': 0.05,
                'current_value': 0.3,
                'proposed_value': 0.35
            },
            UrgencyLevel.LOW,
            'personality_system',
            {'user_initiated': True}
        )
        print(f"Small personality change: {response.status.value}")
        print(f"Reason: {response.decision_reason}")

        # Test 4: Large personality change requiring approval
        print("\n4. Testing large personality change...")
        print("(This will timeout quickly for testing purposes)")

        # Temporarily reduce timeout for testing
        original_timeout = manager.approval_policies['significant_personality_change'].timeout_seconds
        manager.approval_policies['significant_personality_change'].timeout_seconds = 3

        response = await manager.request_human_approval(
            'personality_change',
            {
                'dimension': 'sass_level',
                'change_magnitude': 0.4,  # Large change
                'current_value': 0.3,
                'proposed_value': 0.7
            },
            UrgencyLevel.HIGH,
            'personality_system'
        )
        print(f"Large personality change: {response.status.value}")
        print(f"Reason: {response.decision_reason}")

        # Restore original timeout
        manager.approval_policies['significant_personality_change'].timeout_seconds = original_timeout

        # Test 5: Get statistics
        print("\n5. Approval system statistics...")
        stats = await manager.get_approval_statistics()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Approved: {stats['approved']}")
        print(f"Denied: {stats['denied']}")
        print(f"Timeouts: {stats['timeouts']}")
        print(f"Pending: {stats['pending_requests']}")

        # Test 6: Pending approvals summary
        print("\n6. Pending approvals summary...")
        pending = await manager.get_pending_approvals_summary()
        print(f"Pending approvals: {len(pending)}")
        for approval in pending:
            print(f"  {approval['operation']}: {approval['urgency']} urgency, {approval['remaining_seconds']}s remaining")

        print("\n✅ Human Oversight Manager test completed!")

    asyncio.run(main())