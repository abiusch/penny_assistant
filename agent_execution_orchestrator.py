"""
Agent Execution Orchestrator
Executes multi-step plans from the goal decomposer through existing MCP infrastructure
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import traceback

# Import existing infrastructure
from agent_goal_decomposer import ExecutionPlan, PlanStep, SecurityError

# Import existing MCP and security infrastructure with fallbacks
try:
    from mcp_client import MCPClient
    from tool_server_foundation import ToolServerType, SecurityLevel
    from command_whitelist_system import CommandWhitelistSystem
    from multi_channel_emergency_stop import MultiChannelEmergencyStop
    from enhanced_security_logging import EnhancedSecurityLogging
    from rollback_recovery_system import RollbackRecoverySystem
    MCP_AVAILABLE = True
except ImportError:
    # Fallback definitions for testing
    from enum import Enum

    class ToolServerType(Enum):
        FILE_SYSTEM = "file_system"
        WEB_SEARCH = "web_search"
        CALENDAR = "calendar"
        TASK_MANAGEMENT = "task_management"

    class SecurityLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    # Mock infrastructure classes
    class MCPClient:
        async def call_tool(self, server_type, operation, parameters):
            return {"status": "success", "result": "mock_result"}
        async def initialize(self): return True
        async def close(self): pass

    class CommandWhitelistSystem:
        async def is_command_allowed(self, command): return True

    class MultiChannelEmergencyStop:
        def is_emergency_active(self): return False

    class EnhancedSecurityLogging:
        async def log_security_event(self, event_type, details): pass

    class RollbackRecoverySystem:
        async def create_checkpoint(self, execution_id): return "checkpoint_id"
        async def rollback_to_checkpoint(self, checkpoint_id): return True

    MCP_AVAILABLE = False


class ExecutionStatus(Enum):
    """Execution status states"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EMERGENCY_STOPPED = "emergency_stopped"


class StepStatus(Enum):
    """Individual step status states"""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class StepExecution:
    """Execution state for individual step"""
    step: PlanStep
    status: StepStatus = StepStatus.WAITING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    checkpoint_id: Optional[str] = None


@dataclass
class ExecutionResult:
    """Complete execution result"""
    execution_id: str
    plan_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    completed_steps: int
    total_steps: int
    step_results: List[StepExecution]
    final_result: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionContext:
    """Runtime context for plan execution"""
    execution_id: str
    plan: ExecutionPlan
    user_id: str
    status: ExecutionStatus
    step_executions: Dict[str, StepExecution]
    start_time: datetime
    progress_callback: Optional[callable] = None
    emergency_stop_callback: Optional[callable] = None
    checkpoint_ids: List[str] = None

    def __post_init__(self):
        if self.checkpoint_ids is None:
            self.checkpoint_ids = []


class AgentExecutionOrchestrator:
    """
    Core execution orchestrator that executes plans through existing MCP infrastructure
    """

    def __init__(self,
                 mcp_client: Optional[MCPClient] = None,
                 security_components: Optional[Dict[str, Any]] = None):
        """Initialize orchestrator with existing infrastructure"""

        # MCP Infrastructure
        self.mcp_client = mcp_client or MCPClient()

        # Security Components
        if security_components:
            self.whitelist_system = security_components.get('whitelist')
            self.emergency_system = security_components.get('emergency')
            self.security_logger = security_components.get('logger')
            self.rollback_system = security_components.get('rollback')
        else:
            # Initialize with existing components if available
            self.whitelist_system = CommandWhitelistSystem() if MCP_AVAILABLE else None
            self.emergency_system = MultiChannelEmergencyStop() if MCP_AVAILABLE else None
            self.security_logger = EnhancedSecurityLogging() if MCP_AVAILABLE else None
            self.rollback_system = RollbackRecoverySystem() if MCP_AVAILABLE else None

        # Execution tracking
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionResult] = []

        # Configuration
        self.max_parallel_steps = 5
        self.max_retry_attempts = 3
        self.retry_delay_base = 1.0  # seconds
        self.progress_update_interval = 5.0  # seconds
        self.execution_timeout = 300.0  # 5 minutes default

        # Performance tracking
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "emergency_stops": 0,
            "total_steps_executed": 0,
            "average_execution_time": 0.0
        }

        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize orchestrator and dependencies"""
        try:
            # Initialize MCP client
            if self.mcp_client:
                await self.mcp_client.initialize()

            # Initialize security components
            if self.whitelist_system and hasattr(self.whitelist_system, 'initialize'):
                await self.whitelist_system.initialize()

            if self.emergency_system and hasattr(self.emergency_system, 'initialize'):
                await self.emergency_system.initialize()

            if self.security_logger and hasattr(self.security_logger, 'initialize'):
                await self.security_logger.initialize()

            if self.rollback_system and hasattr(self.rollback_system, 'initialize'):
                await self.rollback_system.initialize()

            self.initialized = True

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "orchestrator_initialized",
                    {"timestamp": datetime.now().isoformat()}
                )

            return True

        except Exception as e:
            print(f"Failed to initialize execution orchestrator: {e}")
            return False

    async def execute_plan(self,
                          plan: ExecutionPlan,
                          user_id: str,
                          progress_callback: Optional[callable] = None) -> ExecutionResult:
        """
        Execute a plan generated by the goal decomposer
        """
        if not self.initialized:
            await self.initialize()

        execution_id = f"exec_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Create execution context
        context = ExecutionContext(
            execution_id=execution_id,
            plan=plan,
            user_id=user_id,
            status=ExecutionStatus.PENDING,
            step_executions={
                step.step_id: StepExecution(step=step)
                for step in plan.steps
            },
            start_time=datetime.now(),
            progress_callback=progress_callback
        )

        self.active_executions[execution_id] = context

        try:
            # Step 1: Pre-execution security validation
            await self._validate_plan_execution(plan, user_id)

            # Step 2: Create initial checkpoint
            if self.rollback_system:
                checkpoint_id = await self.rollback_system.create_checkpoint(execution_id)
                context.checkpoint_ids.append(checkpoint_id)

            # Step 3: Execute plan
            context.status = ExecutionStatus.RUNNING
            await self._notify_progress(context)

            result = await self._execute_plan_steps(context)

            # Step 4: Finalize execution
            self.performance_metrics["total_executions"] += 1
            if result.status == ExecutionStatus.COMPLETED:
                self.performance_metrics["successful_executions"] += 1
            else:
                self.performance_metrics["failed_executions"] += 1

            return result

        except SecurityError as e:
            return await self._handle_security_failure(context, str(e))
        except Exception as e:
            return await self._handle_execution_failure(context, str(e))
        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time status of ongoing execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]

            completed_steps = sum(
                1 for step_exec in context.step_executions.values()
                if step_exec.status == StepStatus.COMPLETED
            )

            running_steps = [
                step_exec.step.step_id for step_exec in context.step_executions.values()
                if step_exec.status == StepStatus.RUNNING
            ]

            return {
                "execution_id": execution_id,
                "status": context.status.value,
                "progress": {
                    "completed": completed_steps,
                    "total": len(context.plan.steps),
                    "percentage": (completed_steps / len(context.plan.steps)) * 100
                },
                "running_steps": running_steps,
                "start_time": context.start_time.isoformat(),
                "elapsed_time": (datetime.now() - context.start_time).total_seconds()
            }

        # Check execution history
        for result in self.execution_history:
            if result.execution_id == execution_id:
                return {
                    "execution_id": execution_id,
                    "status": result.status.value,
                    "progress": {
                        "completed": result.completed_steps,
                        "total": result.total_steps,
                        "percentage": (result.completed_steps / result.total_steps) * 100 if result.total_steps > 0 else 0
                    },
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat() if result.end_time else None,
                    "final_result": result.final_result
                }

        return None

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel ongoing execution with proper cleanup"""
        if execution_id not in self.active_executions:
            return False

        context = self.active_executions[execution_id]

        try:
            # Mark as cancelled
            context.status = ExecutionStatus.CANCELLED

            # Cancel running steps
            for step_exec in context.step_executions.values():
                if step_exec.status == StepStatus.RUNNING:
                    step_exec.status = StepStatus.SKIPPED
                    step_exec.end_time = datetime.now()

            # Log cancellation
            if self.security_logger:
                await self.security_logger.log_security_event(
                    "execution_cancelled",
                    {
                        "execution_id": execution_id,
                        "user_id": context.user_id,
                        "plan_id": context.plan.plan_id,
                        "cancelled_at": datetime.now().isoformat()
                    }
                )

            # Create final result
            result = await self._create_execution_result(context)
            self.execution_history.append(result)

            return True

        except Exception as e:
            print(f"Error cancelling execution {execution_id}: {e}")
            return False

    async def _validate_plan_execution(self, plan: ExecutionPlan, user_id: str):
        """Validate plan before execution through security components"""

        # Check emergency stop
        if self.emergency_system and self.emergency_system.is_emergency_active():
            raise SecurityError("Emergency stop active - execution blocked")

        # Validate each step through security components
        for step in plan.steps:
            # Check command whitelist
            if self.whitelist_system:
                command_key = f"{step.tool_server.value}:{step.operation}"
                if not await self.whitelist_system.is_command_allowed(command_key):
                    raise SecurityError(f"Operation {command_key} not allowed for user {user_id}")

            # Additional security validations can be added here

        # Log execution validation
        if self.security_logger:
            await self.security_logger.log_security_event(
                "execution_validated",
                {
                    "plan_id": plan.plan_id,
                    "user_id": user_id,
                    "step_count": len(plan.steps),
                    "complexity": plan.complexity.value
                }
            )

    async def _execute_plan_steps(self, context: ExecutionContext) -> ExecutionResult:
        """Execute plan steps with dependency resolution and parallel execution"""

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(context.plan.steps)

        # Execute steps in dependency order
        executed_steps = set()

        while len(executed_steps) < len(context.plan.steps):
            # Check for emergency stop
            if self.emergency_system and self.emergency_system.is_emergency_active():
                context.status = ExecutionStatus.EMERGENCY_STOPPED
                self.performance_metrics["emergency_stops"] += 1
                break

            # Find steps ready to execute
            ready_steps = []
            for step in context.plan.steps:
                if (step.step_id not in executed_steps and
                    all(dep_id in executed_steps for dep_id in step.depends_on)):
                    ready_steps.append(step)

            if not ready_steps:
                # Check if we have any running steps
                running_count = sum(
                    1 for step_exec in context.step_executions.values()
                    if step_exec.status == StepStatus.RUNNING
                )

                if running_count == 0:
                    # No ready steps and none running - likely dependency issue
                    break

                # Wait for running steps to complete
                await asyncio.sleep(0.5)
                continue

            # Execute ready steps (with parallelism limits)
            tasks = []
            for step in ready_steps[:self.max_parallel_steps]:
                if step.step_id not in executed_steps:
                    task = asyncio.create_task(self._execute_step(context, step))
                    tasks.append(task)

            if tasks:
                # Wait for at least one step to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                # Process completed steps
                for task in done:
                    try:
                        step_id, success = await task
                        executed_steps.add(step_id)

                        if success:
                            self.performance_metrics["total_steps_executed"] += 1

                        await self._notify_progress(context)

                    except Exception as e:
                        print(f"Error in step execution: {e}")

                # Cancel pending tasks if needed (they'll be retried in next iteration)
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        # Determine final status
        completed_count = sum(
            1 for step_exec in context.step_executions.values()
            if step_exec.status == StepStatus.COMPLETED
        )

        if context.status == ExecutionStatus.EMERGENCY_STOPPED:
            pass  # Status already set
        elif completed_count == len(context.plan.steps):
            context.status = ExecutionStatus.COMPLETED
        else:
            context.status = ExecutionStatus.FAILED

        # Create final result
        result = await self._create_execution_result(context)
        self.execution_history.append(result)

        return result

    async def _execute_step(self, context: ExecutionContext, step: PlanStep) -> tuple[str, bool]:
        """Execute individual step with retry logic"""
        step_exec = context.step_executions[step.step_id]
        step_exec.status = StepStatus.RUNNING
        step_exec.start_time = datetime.now()

        try:
            # Create checkpoint before step execution
            if self.rollback_system:
                checkpoint_id = await self.rollback_system.create_checkpoint(
                    f"{context.execution_id}_{step.step_id}"
                )
                step_exec.checkpoint_id = checkpoint_id

            # Execute step through MCP client
            result = await self._call_tool_server(step)

            # Mark as completed
            step_exec.status = StepStatus.COMPLETED
            step_exec.end_time = datetime.now()
            step_exec.result = result

            # Log successful step
            if self.security_logger:
                await self.security_logger.log_security_event(
                    "step_completed",
                    {
                        "execution_id": context.execution_id,
                        "step_id": step.step_id,
                        "operation": f"{step.tool_server.value}:{step.operation}",
                        "duration": (step_exec.end_time - step_exec.start_time).total_seconds()
                    }
                )

            return step.step_id, True

        except Exception as e:
            return await self._handle_step_failure(context, step, e)

    async def _handle_step_failure(self, context: ExecutionContext, step: PlanStep, error: Exception) -> tuple[str, bool]:
        """Handle step failure with retry logic"""
        step_exec = context.step_executions[step.step_id]
        step_exec.retry_count += 1
        step_exec.error = str(error)

        # Check if we should retry
        if step_exec.retry_count <= self.max_retry_attempts:
            step_exec.status = StepStatus.RETRYING

            # Exponential backoff
            delay = self.retry_delay_base * (2 ** (step_exec.retry_count - 1))
            await asyncio.sleep(delay)

            # Rollback if possible
            if self.rollback_system and step_exec.checkpoint_id:
                await self.rollback_system.rollback_to_checkpoint(step_exec.checkpoint_id)

            # Retry execution
            return await self._execute_step(context, step)
        else:
            # Max retries exceeded
            step_exec.status = StepStatus.FAILED
            step_exec.end_time = datetime.now()

            # Log failure
            if self.security_logger:
                await self.security_logger.log_security_event(
                    "step_failed",
                    {
                        "execution_id": context.execution_id,
                        "step_id": step.step_id,
                        "operation": f"{step.tool_server.value}:{step.operation}",
                        "error": str(error),
                        "retry_count": step_exec.retry_count
                    }
                )

            return step.step_id, False

    async def _call_tool_server(self, step: PlanStep) -> Dict[str, Any]:
        """Call appropriate tool server through MCP client"""
        if not self.mcp_client:
            # Mock execution for testing
            await asyncio.sleep(step.estimated_time / 1000.0)  # Convert to seconds
            return {"status": "success", "result": f"Mock result for {step.operation}"}

        # Call actual tool server
        return await self.mcp_client.call_tool(
            step.tool_server,
            step.operation,
            step.parameters
        )

    def _build_dependency_graph(self, steps: List[PlanStep]) -> Dict[str, List[str]]:
        """Build dependency graph for execution planning"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.depends_on.copy()
        return graph

    async def _notify_progress(self, context: ExecutionContext):
        """Notify progress callback if available"""
        if context.progress_callback:
            try:
                status_info = await self.get_execution_status(context.execution_id)
                await context.progress_callback(status_info)
            except Exception as e:
                print(f"Error in progress callback: {e}")

    async def _create_execution_result(self, context: ExecutionContext) -> ExecutionResult:
        """Create final execution result"""
        completed_steps = sum(
            1 for step_exec in context.step_executions.values()
            if step_exec.status == StepStatus.COMPLETED
        )

        # Calculate performance metrics
        execution_time = (datetime.now() - context.start_time).total_seconds()

        # Update average execution time
        total_time = (self.performance_metrics["average_execution_time"] *
                     self.performance_metrics["total_executions"] + execution_time)
        self.performance_metrics["average_execution_time"] = (
            total_time / (self.performance_metrics["total_executions"] + 1)
        )

        return ExecutionResult(
            execution_id=context.execution_id,
            plan_id=context.plan.plan_id,
            status=context.status,
            start_time=context.start_time,
            end_time=datetime.now(),
            completed_steps=completed_steps,
            total_steps=len(context.plan.steps),
            step_results=list(context.step_executions.values()),
            performance_metrics={
                "execution_time_seconds": execution_time,
                "parallel_steps": self.max_parallel_steps,
                "retry_attempts": sum(step_exec.retry_count for step_exec in context.step_executions.values())
            }
        )

    async def _handle_security_failure(self, context: ExecutionContext, error_msg: str) -> ExecutionResult:
        """Handle security validation failure"""
        context.status = ExecutionStatus.FAILED

        if self.security_logger:
            await self.security_logger.log_security_event(
                "execution_security_failure",
                {
                    "execution_id": context.execution_id,
                    "plan_id": context.plan.plan_id,
                    "user_id": context.user_id,
                    "error": error_msg
                }
            )

        result = await self._create_execution_result(context)
        result.error_summary = f"Security validation failed: {error_msg}"
        return result

    async def _handle_execution_failure(self, context: ExecutionContext, error_msg: str) -> ExecutionResult:
        """Handle general execution failure"""
        context.status = ExecutionStatus.FAILED

        if self.security_logger:
            await self.security_logger.log_security_event(
                "execution_failure",
                {
                    "execution_id": context.execution_id,
                    "plan_id": context.plan.plan_id,
                    "user_id": context.user_id,
                    "error": error_msg,
                    "stack_trace": traceback.format_exc()
                }
            )

        result = await self._create_execution_result(context)
        result.error_summary = f"Execution failed: {error_msg}"
        return result

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        return self.performance_metrics.copy()

    async def cleanup(self):
        """Cleanup resources and close connections"""
        try:
            # Cancel all active executions
            for execution_id in list(self.active_executions.keys()):
                await self.cancel_execution(execution_id)

            # Close MCP client
            if self.mcp_client:
                await self.mcp_client.close()

            self.initialized = False

        except Exception as e:
            print(f"Error during cleanup: {e}")


# Convenience function for easy integration
async def execute_plan(plan: ExecutionPlan,
                      user_id: str,
                      progress_callback: Optional[callable] = None) -> ExecutionResult:
    """Convenience function to execute a plan"""
    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    try:
        return await orchestrator.execute_plan(plan, user_id, progress_callback)
    finally:
        await orchestrator.cleanup()