"""
Test Suite for Autonomous Research Tool Server
Tests knowledge gap detection, research planning, execution, and synthesis
"""

import asyncio
import time
from datetime import datetime

from autonomous_research_tool_server import (
    create_autonomous_research_server, KnowledgeGap, KnowledgeGapType, ResearchScope
)


class MockSecurityComponent:
    """Mock security component for testing"""

    def __init__(self, allow_all=True):
        self.allow_all = allow_all
        self.events = []

    async def is_command_allowed(self, command):
        return self.allow_all

    def is_emergency_active(self):
        return False

    async def log_security_event(self, event_type, details):
        self.events.append({"type": event_type, "details": details})

    async def create_checkpoint(self, checkpoint_id):
        return f"checkpoint_{checkpoint_id}"

    async def check_rate_limit(self, user_id, operation):
        return self.allow_all


async def test_knowledge_gap_detection():
    """Test knowledge gap detection functionality"""
    print("🔍 Testing Knowledge Gap Detection")

    server = await create_autonomous_research_server()

    try:
        # Test conversation with clear uncertainty
        conversation = "I've been working on machine learning projects, but I'm not sure about the latest frameworks."
        user_query = "I don't know which deep learning library to choose. Can you help me understand the options?"

        result = await server.identify_knowledge_gaps(
            conversation_context=conversation,
            user_query=user_query,
            user_id="test_user"
        )

        print(f"   Gap detection: {'SUCCESS' if result.success else 'FAILED'}")
        if result.success:
            gaps = result.data["knowledge_gaps"]
            print(f"   Gaps found: {len(gaps)}")
            if gaps:
                print(f"   First gap type: {gaps[0]['gap_type']}")
                print(f"   First gap confidence: {gaps[0]['confidence']}")

        # Test conversation analysis
        conversation_history = """
        User: I want to learn about quantum computing
        Assistant: I'd need to research quantum computing to give you current information
        User: What about quantum algorithms?
        Assistant: I'm not familiar with the latest quantum algorithm developments
        User: How do quantum computers compare to classical computers?
        """

        analysis_result = await server.analyze_conversation_for_learning_opportunities(
            conversation_history=conversation_history,
            user_id="test_user"
        )

        print(f"   Conversation analysis: {'SUCCESS' if analysis_result.success else 'FAILED'}")
        if analysis_result.success:
            opportunities = analysis_result.data["learning_opportunities"]
            print(f"   Learning opportunities found: {len(opportunities)}")

        return result.success and analysis_result.success

    finally:
        await server.stop()


async def test_research_question_generation():
    """Test research question generation"""
    print("❓ Testing Research Question Generation")

    server = await create_autonomous_research_server()

    try:
        # Create a test knowledge gap
        test_gap = {
            "gap_id": "test_gap_001",
            "gap_type": "temporal",
            "description": "Need current information about AI frameworks",
            "context": "user asking about latest deep learning frameworks for image classification",
            "confidence": 0.8,
            "priority": 8,
            "detected_at": datetime.now().isoformat(),
            "conversation_context": {"test": "context"}
        }

        result = await server.generate_research_questions(
            knowledge_gap=test_gap,
            max_questions=3,
            user_id="test_user"
        )

        print(f"   Question generation: {'SUCCESS' if result.success else 'FAILED'}")
        if result.success:
            questions = result.data["research_questions"]
            print(f"   Questions generated: {len(questions)}")
            for i, q in enumerate(questions, 1):
                print(f"   Q{i}: {q['question'][:60]}...")

        return result.success

    finally:
        await server.stop()


async def test_research_planning():
    """Test research plan creation"""
    print("📋 Testing Research Planning")

    server = await create_autonomous_research_server()

    try:
        # Test knowledge gap
        test_gap = {
            "gap_id": "test_gap_002",
            "gap_type": "procedural",
            "description": "How to implement neural networks",
            "context": "user wants to understand how to build neural networks from scratch",
            "confidence": 0.9,
            "priority": 9,
            "detected_at": datetime.now().isoformat(),
            "conversation_context": {"test": "context"}
        }

        # Test different research scopes
        scopes = ["quick", "comprehensive", "deep"]
        results = []

        for scope in scopes:
            result = await server.create_research_plan(
                knowledge_gap=test_gap,
                research_scope=scope,
                time_limit=180,
                user_id="test_user"
            )

            success = result.success
            results.append(success)

            print(f"   {scope.capitalize()} plan: {'SUCCESS' if success else 'FAILED'}")
            if success:
                plan = result.data["research_plan"]
                print(f"   Questions: {result.data['question_count']}")
                print(f"   Estimated time: {result.data['estimated_time']}s")

        return all(results)

    finally:
        await server.stop()


async def test_research_execution():
    """Test research plan execution"""
    print("🔬 Testing Research Execution")

    server = await create_autonomous_research_server()

    try:
        # Create a simple research plan
        test_gap = {
            "gap_id": "test_gap_003",
            "gap_type": "factual",
            "description": "Information about Python libraries",
            "context": "user needs to know about Python data science libraries",
            "confidence": 0.7,
            "priority": 7,
            "detected_at": datetime.now().isoformat(),
            "conversation_context": {"test": "context"}
        }

        # Create plan
        plan_result = await server.create_research_plan(
            knowledge_gap=test_gap,
            research_scope="quick",
            time_limit=60,
            user_id="test_user"
        )

        if not plan_result.success:
            print(f"   Plan creation failed: {plan_result.error}")
            return False

        # Execute research
        execution_result = await server.execute_research_plan(
            research_plan=plan_result.data["research_plan"],
            user_id="test_user"
        )

        print(f"   Research execution: {'SUCCESS' if execution_result.success else 'FAILED'}")
        if execution_result.success:
            findings = execution_result.data["research_findings"]
            print(f"   Findings generated: {len(findings)}")
            print(f"   Execution time: {execution_result.data['execution_time']:.2f}s")

            # Test synthesis of findings
            if findings:
                synthesis_result = await server.synthesize_research_findings(
                    research_findings=findings,
                    synthesis_style="comprehensive",
                    user_id="test_user"
                )

                print(f"   Synthesis: {'SUCCESS' if synthesis_result.success else 'FAILED'}")
                if synthesis_result.success:
                    synthesis = synthesis_result.data
                    print(f"   Key insights: {len(synthesis['key_insights'])}")
                    print(f"   Recommendations: {len(synthesis['recommendations'])}")

                return synthesis_result.success

        return execution_result.success

    finally:
        await server.stop()


async def test_information_processing():
    """Test information processing capabilities"""
    print("🧠 Testing Information Processing")

    server = await create_autonomous_research_server()

    try:
        # Test insight extraction
        test_data = {
            "content": "Machine learning is becoming increasingly important in software development. Deep learning frameworks like TensorFlow and PyTorch are the most popular choices. Recent studies show that transformer models are revolutionizing natural language processing.",
            "findings": [
                {
                    "key_insights": [
                        "TensorFlow and PyTorch are leading frameworks",
                        "Transformer models are game-changing for NLP",
                        "ML adoption is accelerating in software development"
                    ]
                }
            ]
        }

        insight_result = await server.extract_key_insights(
            research_data=test_data,
            focus_areas=["frameworks", "models"],
            user_id="test_user"
        )

        print(f"   Insight extraction: {'SUCCESS' if insight_result.success else 'FAILED'}")
        if insight_result.success:
            insights = insight_result.data["key_insights"]
            print(f"   Insights extracted: {len(insights)}")

        # Test information quality validation
        source_data = {
            "sources": [
                {"credibility_score": 0.9, "content_length": 1000},
                {"credibility_score": 0.6, "content_length": 500},
                {"credibility_score": 0.8, "content_length": 800}
            ]
        }

        validation_result = await server.validate_information_quality(
            source_data=source_data,
            credibility_threshold=0.7,
            user_id="test_user"
        )

        print(f"   Quality validation: {'SUCCESS' if validation_result.success else 'FAILED'}")

        return insight_result.success and validation_result.success

    finally:
        await server.stop()


async def test_learning_integration():
    """Test learning integration and knowledge storage"""
    print("💾 Testing Learning Integration")

    server = await create_autonomous_research_server()

    try:
        # Test knowledge storage
        test_insights = {
            "topic": "machine learning frameworks",
            "key_points": [
                "TensorFlow is Google's framework",
                "PyTorch is Facebook's framework",
                "Both support GPU acceleration"
            ],
            "recommendations": [
                "Choose TensorFlow for production",
                "Choose PyTorch for research"
            ]
        }

        storage_result = await server.store_research_findings(
            insights=test_insights,
            knowledge_category="ml_frameworks",
            confidence_level=0.85,
            user_id="test_user"
        )

        print(f"   Knowledge storage: {'SUCCESS' if storage_result.success else 'FAILED'}")
        if storage_result.success:
            print(f"   Knowledge base size: {storage_result.data['knowledge_base_size']}")

        # Test learning summary generation
        summary_result = await server.generate_learning_summary(
            research_session_id="test_session_001",
            include_sources=True,
            user_id="test_user"
        )

        # This should fail since the session doesn't exist, which is expected
        print(f"   Learning summary: {'SUCCESS' if summary_result.success else 'EXPECTED FAILURE'}")

        return storage_result.success

    finally:
        await server.stop()


async def test_security_integration():
    """Test security component integration"""
    print("🔒 Testing Security Integration")

    # Test with blocking security components
    blocking_security = {
        'whitelist': MockSecurityComponent(allow_all=False),
        'emergency': MockSecurityComponent(allow_all=False),
        'logger': MockSecurityComponent(allow_all=True),
        'rollback': MockSecurityComponent(allow_all=True),
        'rate_limiter': MockSecurityComponent(allow_all=False)
    }

    server = await create_autonomous_research_server(blocking_security)

    try:
        # Test blocked operation
        result = await server.identify_knowledge_gaps(
            conversation_context="test",
            user_query="test",
            user_id="test_user"
        )

        print(f"   Blocked operation handling: {'SUCCESS' if not result.success else 'FAILED'}")
        print(f"   Security events logged: {len(blocking_security['logger'].events)}")

        return not result.success  # Should be blocked

    finally:
        await server.stop()


async def test_performance_under_load():
    """Test performance under multiple concurrent operations"""
    print("⚡ Testing Performance Under Load")

    server = await create_autonomous_research_server()

    try:
        # Create multiple concurrent gap detection tasks
        tasks = []
        for i in range(5):
            task = server.identify_knowledge_gaps(
                conversation_context=f"Test context {i} with uncertainty about topics",
                user_query=f"I don't know about topic {i}",
                user_id=f"user_{i}"
            )
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time

        successful = sum(1 for r in results if hasattr(r, 'success') and r.success)
        print(f"   Concurrent operations: {successful}/5 successful")
        print(f"   Total execution time: {execution_time:.2f}s")

        # Test metrics collection
        metrics = await server.get_performance_metrics()
        print(f"   Knowledge gaps identified: {metrics['total_knowledge_gaps_identified']}")

        return successful >= 4 and execution_time < 10.0

    finally:
        await server.stop()


async def test_end_to_end_research_workflow():
    """Test complete end-to-end research workflow"""
    print("🎯 Testing End-to-End Research Workflow")

    server = await create_autonomous_research_server()

    try:
        # Complete workflow: Gap detection → Question generation → Plan creation → Execution
        conversation = "I'm building a chatbot but I'm not sure about the latest NLP techniques. I don't know which language models to use or how to implement them effectively."

        # Step 1: Detect gaps
        gap_result = await server.identify_knowledge_gaps(
            conversation_context=conversation,
            user_query="What are the best practices for building chatbots with modern NLP?",
            user_id="workflow_test"
        )

        if not gap_result.success or not gap_result.data["knowledge_gaps"]:
            print("   Gap detection failed")
            return False

        gap = gap_result.data["knowledge_gaps"][0]
        print(f"   ✅ Gap detected: {gap['gap_type']}")

        # Step 2: Generate questions
        question_result = await server.generate_research_questions(
            knowledge_gap=gap,
            user_id="workflow_test"
        )

        if not question_result.success:
            print("   Question generation failed")
            return False

        print(f"   ✅ Questions generated: {question_result.data['total_questions']}")

        # Step 3: Create plan
        plan_result = await server.create_research_plan(
            knowledge_gap=gap,
            research_scope="comprehensive",
            user_id="workflow_test"
        )

        if not plan_result.success:
            print("   Plan creation failed")
            return False

        print(f"   ✅ Research plan created")

        # Step 4: Execute research
        execution_result = await server.execute_research_plan(
            research_plan=plan_result.data["research_plan"],
            user_id="workflow_test"
        )

        if not execution_result.success:
            print("   Research execution failed")
            return False

        print(f"   ✅ Research executed: {execution_result.data['findings_count']} findings")

        # Step 5: Store findings
        if execution_result.data["research_findings"]:
            storage_result = await server.store_research_findings(
                insights={"workflow_test": "completed"},
                knowledge_category="chatbot_nlp",
                confidence_level=0.8,
                user_id="workflow_test"
            )

            if storage_result.success:
                print(f"   ✅ Findings stored")

        print("   🎉 End-to-end workflow completed successfully")
        return True

    finally:
        await server.stop()


async def run_autonomous_research_tests():
    """Run comprehensive autonomous research tests"""
    print("🧪 AUTONOMOUS RESEARCH TOOL SERVER TESTS")
    print("=" * 60)

    tests = [
        ("Knowledge Gap Detection", test_knowledge_gap_detection),
        ("Research Question Generation", test_research_question_generation),
        ("Research Planning", test_research_planning),
        ("Research Execution", test_research_execution),
        ("Information Processing", test_information_processing),
        ("Learning Integration", test_learning_integration),
        ("Security Integration", test_security_integration),
        ("Performance Under Load", test_performance_under_load),
        ("End-to-End Research Workflow", test_end_to_end_research_workflow)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"   ✅ {test_name}: {'PASS' if result else 'FAIL'}\n")
        except Exception as e:
            print(f"   ❌ {test_name}: ERROR - {e}\n")
            results.append((test_name, False))

    # Summary
    print("=" * 60)
    print("📊 AUTONOMOUS RESEARCH TEST RESULTS")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    success_rate = (passed / total) * 100
    print(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 AUTONOMOUS RESEARCH CAPABILITIES READY!")
        print("   Knowledge gap detection operational")
        print("   Research planning and execution validated")
        print("   Information synthesis working correctly")
        print("   Learning integration functional")
        print("   Security controls effective")
    elif success_rate >= 70:
        print("⚠️  Some research features need improvement")
    else:
        print("❌ Critical issues found in research capabilities")

    return success_rate >= 90


if __name__ == "__main__":
    success = asyncio.run(run_autonomous_research_tests())
    exit(0 if success else 1)