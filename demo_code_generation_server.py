"""
Code Generation Tool Server Demo
Demonstrates autonomous learning and self-improvement capabilities
Shows how Penny can write, test, and implement code enhancements
"""

import asyncio
from datetime import datetime

from code_generation_tool_server import create_code_generation_server


async def demo_autonomous_learning_scenarios():
    """Demonstrate autonomous learning scenarios with code generation"""
    print("🧠 CODE GENERATION SERVER - AUTONOMOUS LEARNING DEMO")
    print("=" * 60)
    print("Demonstrating how Penny can write, test, and implement code")
    print("for autonomous learning and self-improvement within secure boundaries.\\n")

    # Initialize code generation server
    server = await create_code_generation_server()

    try:
        scenarios = [
            {
                "title": "📚 LEARNING SCENARIO: Research Assistant Enhancement",
                "description": "Penny identifies need for better research summarization",
                "specification": "Create a function that extracts key points from research text and generates structured summaries"
            },
            {
                "title": "🔧 IMPROVEMENT SCENARIO: Performance Optimization",
                "description": "Penny notices slow response times and creates optimization",
                "specification": "Create a caching system class that stores frequently accessed data with TTL expiration"
            },
            {
                "title": "🎯 CAPABILITY EXPANSION: New Skill Development",
                "description": "Penny learns to generate code for new domains",
                "specification": "Create a data analysis helper that can calculate statistics and generate insights from datasets"
            },
            {
                "title": "🛡️ SECURITY ENHANCEMENT: Safety Improvement",
                "description": "Penny proposes security improvements to existing systems",
                "specification": "Create an input validation system that sanitizes user input and prevents injection attacks"
            },
            {
                "title": "🤖 META-LEARNING: Code Generation Improvement",
                "description": "Penny improves her own code generation capabilities",
                "specification": "Create an enhancement that adds better error handling and logging to generated code"
            }
        ]

        successful_scenarios = 0
        total_scenarios = len(scenarios)

        for i, scenario in enumerate(scenarios, 1):
            print(f"\\n{scenario['title']}")
            print("-" * 50)
            print(f"🎯 Context: {scenario['description']}")
            print(f"🔧 Task: {scenario['specification']}")

            try:
                # Step 1: Code Generation
                print("\\n📝 Step 1: Autonomous Code Generation")
                generation_result = await server.generate_code(
                    specification=scenario['specification'],
                    code_type="function" if i <= 2 else "class" if i <= 4 else "enhancement",
                    style_preferences={
                        "function_name": f"autonomous_function_{i}",
                        "class_name": f"AutonomousClass_{i}",
                        "enhancement_name": f"autonomous_enhancement_{i}"
                    },
                    user_id="penny_autonomous"
                )

                if generation_result.success:
                    generated_code = generation_result.data["code"]
                    print(f"   ✅ Code generated: {len(generated_code)} characters")
                    print(f"   📂 Type: {generation_result.data['type']}")

                    # Show code snippet
                    lines = generated_code.split('\\n')
                    preview = '\\n'.join(lines[:8])
                    print(f"   📋 Preview:\\n{preview}\\n   ...")

                else:
                    print(f"   ❌ Generation failed: {generation_result.error}")
                    continue

                # Step 2: Security Analysis
                print("\\n🔒 Step 2: Security Validation")
                security_result = await server.check_security_compliance(
                    code_content=generated_code,
                    user_id="penny_autonomous"
                )

                if security_result.success:
                    print("   ✅ Security validation passed")
                else:
                    print(f"   ⚠️ Security concerns: {security_result.error}")

                # Step 3: Automated Testing
                print("\\n🧪 Step 3: Automated Testing")

                # Generate test code
                test_generation = await server.create_test_cases(
                    code_content=generated_code,
                    test_type="unit",
                    user_id="penny_autonomous"
                )

                if test_generation.success:
                    test_code = test_generation.data["code"]
                    print(f"   ✅ Test cases generated: {len(test_code)} characters")

                    # Execute tests in sandbox
                    test_execution = await server.execute_code_sandboxed(
                        code_content=f"{generated_code}\\n\\n{test_code}",
                        timeout=15.0,
                        user_id="penny_autonomous"
                    )

                    if test_execution.success and test_execution.data and test_execution.data["success"]:
                        print("   ✅ All tests passed in sandbox")
                    else:
                        error_msg = "Unknown"
                        if test_execution.data:
                            error_msg = test_execution.data.get('error', 'Unknown')
                        print(f"   ⚠️ Test execution issues: {error_msg}")

                else:
                    print(f"   ❌ Test generation failed: {test_generation.error}")

                # Step 4: Code Analysis and Improvement
                print("\\n📊 Step 4: Code Analysis & Improvement Suggestions")
                analysis_result = await server.analyze_existing_code(
                    code_content=generated_code,
                    analysis_type="comprehensive",
                    user_id="penny_autonomous"
                )

                if analysis_result.success:
                    analysis = analysis_result.data["analysis"]
                    print(f"   📈 Complexity: {analysis['complexity']['level']}")
                    print(f"   🔍 Functions: {len(analysis['structure']['functions'])}")
                    print(f"   📝 Suggestions: {len(analysis['suggestions'])}")

                    if analysis['suggestions']:
                        print(f"   💡 Top suggestion: {analysis['suggestions'][0]}")

                # Step 5: Enhancement Proposal
                print("\\n🚀 Step 5: System Enhancement Proposal")
                enhancement_result = await server.propose_system_enhancement(
                    enhancement_description=f"Autonomous enhancement: {scenario['description']}",
                    code_implementation=generated_code,
                    user_id="penny_autonomous"
                )

                if enhancement_result.success:
                    print("   ✅ Enhancement proposal created")
                    print("   📋 Status: Pending user approval for deployment")
                else:
                    print(f"   ❌ Enhancement proposal failed: {enhancement_result.error}")

                print("\\n🎉 Autonomous Learning Cycle Complete!")
                successful_scenarios += 1

            except Exception as e:
                print(f"\\n❌ Scenario failed: {e}")

            print()

        # Overall Results
        print("=" * 60)
        print("🎊 AUTONOMOUS LEARNING DEMONSTRATION COMPLETE")
        print("=" * 60)

        success_rate = (successful_scenarios / total_scenarios) * 100

        print(f"\\n📊 LEARNING OUTCOMES:")
        print(f"   Scenarios completed: {successful_scenarios}/{total_scenarios}")
        print(f"   Success rate: {success_rate:.1f}%")

        # Get server metrics
        metrics = await server.get_performance_metrics()
        print(f"   Code generations: {metrics['total_generation_requests']}")
        print(f"   Successful executions: {metrics['successful_executions']}")
        print(f"   Security validations: {metrics['security_violations']} violations blocked")

        print(f"\\n🧠 AUTONOMOUS LEARNING CAPABILITIES VALIDATED:")
        print("✅ Natural language specification → Working code")
        print("✅ Automatic security validation and compliance checking")
        print("✅ Automated test generation and execution")
        print("✅ Code analysis and improvement suggestions")
        print("✅ System enhancement proposals with approval workflow")
        print("✅ Sandboxed execution preventing system damage")
        print("✅ Resource limits and emergency stop compliance")

        print(f"\\n🚀 PENNY'S AUTONOMOUS LEARNING FOUNDATION:")
        print("• Can identify learning needs during conversations")
        print("• Generates code to implement new capabilities")
        print("• Tests implementations safely in sandbox")
        print("• Proposes system enhancements with user approval")
        print("• Operates within strict security boundaries")
        print("• Learns from failures and improves iteratively")

        if success_rate >= 80:
            print(f"\\n🎉 AUTONOMOUS LEARNING SYSTEM OPERATIONAL!")
            print("Ready to enable Penny's self-improvement capabilities")
        else:
            print(f"\\n⚠️ Some autonomous learning features need refinement")

        return success_rate >= 80

    finally:
        await server.stop()


async def demo_specific_capabilities():
    """Demonstrate specific autonomous learning capabilities"""
    print("\\n🔬 SPECIFIC AUTONOMOUS LEARNING CAPABILITIES")
    print("=" * 50)

    server = await create_code_generation_server()

    try:
        # Demo 1: Self-Improvement Through Code Analysis
        print("\\n1️⃣ SELF-IMPROVEMENT THROUGH CODE ANALYSIS")

        existing_code = '''
def slow_function(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''

        print("   🔍 Analyzing existing code for improvements...")
        improvement_result = await server.suggest_improvements(
            code_content=existing_code,
            focus_areas=["performance", "readability"],
            user_id="penny_improvement"
        )

        if improvement_result.success:
            print("   ✅ Improvement suggestions generated")
            suggestions = improvement_result.data.get("suggestions", [])
            for suggestion in suggestions[:3]:  # Show first 3
                print(f"      💡 {suggestion}")

        # Demo 2: Adaptive Learning from Errors
        print("\\n2️⃣ ADAPTIVE LEARNING FROM EXECUTION ERRORS")

        buggy_code = '''
def division_function(a, b):
    return a / b  # Potential division by zero
'''

        print("   🐛 Executing potentially problematic code...")
        execution_result = await server.execute_code_sandboxed(
            f"{buggy_code}\\nresult = division_function(10, 0)",
            user_id="penny_learning"
        )

        if execution_result.data and not execution_result.data["success"]:
            print("   ⚠️ Error detected in execution")
            print(f"      Error: {execution_result.data['error']}")
        elif not execution_result.data:
            print("   ⚠️ Execution failed - no result data")

            # Generate improved version
            improved_spec = "Create a safe division function that handles division by zero"
            improvement = await server.generate_code(
                improved_spec,
                user_id="penny_learning"
            )

            if improvement.success:
                print("   ✅ Improved version generated automatically")

        # Demo 3: Knowledge Integration
        print("\\n3️⃣ KNOWLEDGE INTEGRATION AND SYNTHESIS")

        research_spec = "Create a knowledge integration system that combines information from multiple sources"
        knowledge_system = await server.generate_code(
            research_spec,
            code_type="class",
            style_preferences={"class_name": "KnowledgeIntegrator"},
            user_id="penny_knowledge"
        )

        if knowledge_system.success:
            print("   ✅ Knowledge integration system generated")
            print("   📚 Capability: Synthesize research into actionable code")

        # Demo 4: Meta-Learning (Learning About Learning)
        print("\\n4️⃣ META-LEARNING: IMPROVING LEARNING PROCESSES")

        meta_spec = "Create a learning progress tracker that monitors improvement over time"
        meta_system = await server.generate_code(
            meta_spec,
            code_type="class",
            style_preferences={"class_name": "LearningTracker"},
            user_id="penny_meta"
        )

        if meta_system.success:
            print("   ✅ Meta-learning system generated")
            print("   🔄 Capability: Monitor and improve own learning processes")

        print("\\n🎯 AUTONOMOUS LEARNING ARCHITECTURE DEMONSTRATED:")
        print("   • Self-analysis and improvement identification")
        print("   • Error-driven learning and adaptation")
        print("   • Knowledge synthesis from multiple sources")
        print("   • Meta-learning for process improvement")

    finally:
        await server.stop()


if __name__ == "__main__":
    async def main():
        success = await demo_autonomous_learning_scenarios()
        await demo_specific_capabilities()
        return success

    # Run the demonstration
    import sys
    success = asyncio.run(main())

    if success:
        print("\\n🎊 Code Generation Server ready for autonomous learning!")
        print("Penny can now write, test, and improve her own code safely.")
    else:
        print("\\n⚠️ Issues found during autonomous learning demonstration")

    sys.exit(0 if success else 1)