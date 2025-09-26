#!/usr/bin/env python3
"""
Jedi-Enhanced Penny
Integration of Jedi-Level Code Analysis with Penny's personality system
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sassy_code_mentor import SassyCodeMentor
from jedi_code_analyzer import JediCodeAnalyzer
from interactive_debugger import InteractiveDebugger
from code_review_mentor import CodeReviewMentor

# Import existing Penny systems
try:
    from memory_system import MemoryManager
    from emotional_memory_system import create_enhanced_memory_system
    from personality_integration import create_personality_integration
except ImportError:
    print("⚠️ Some Penny systems not available - running in standalone mode")
    MemoryManager = None

class JediEnhancedPenny:
    """
    Penny with Jedi-Level Code Analysis capabilities
    Combines her existing personality with deep code understanding
    """

    def __init__(self):
        # Core Jedi systems
        self.sassy_mentor = SassyCodeMentor()
        self.analyzer = JediCodeAnalyzer()
        self.debugger = InteractiveDebugger()
        self.reviewer = CodeReviewMentor()

        # Penny's existing systems (if available)
        self.memory_system = None
        self.personality_system = None
        self._setup_penny_systems()

        # Code analysis conversation state
        self.current_project_path = None
        self.recent_files_analyzed = []
        self.conversation_context = {
            "analyzing_project": False,
            "debugging_issue": False,
            "reviewing_code": False,
            "learning_mode": False
        }

        print("🤖 Jedi-Enhanced Penny initialized!")
        print("   • Advanced code analysis capabilities")
        print("   • Interactive debugging assistance")
        print("   • Educational code reviews with sass")
        print("   • Architecture pattern recognition")

    def _setup_penny_systems(self):
        """Initialize Penny's existing personality and memory systems"""
        if MemoryManager:
            try:
                self.memory_system = MemoryManager()
                enhanced_memory = create_enhanced_memory_system(self.memory_system)
                self.personality_system = create_personality_integration(enhanced_memory)
                print("✅ Penny's personality and memory systems loaded")
            except Exception as e:
                print(f"⚠️ Could not load Penny systems: {e}")

    async def process_code_request(self, user_input: str, context: Dict = None) -> str:
        """
        Process code-related requests with Penny's personality
        """
        user_input_lower = user_input.lower()

        # Update conversation context
        await self._update_conversation_context(user_input)

        # Route to appropriate analysis
        if any(keyword in user_input_lower for keyword in ['analyze', 'architecture', 'structure']):
            return await self._handle_architecture_analysis(user_input, context)
        elif any(keyword in user_input_lower for keyword in ['debug', 'error', 'issue', 'problem', 'bug']):
            return await self._handle_debugging_request(user_input, context)
        elif any(keyword in user_input_lower for keyword in ['review', 'check', 'feedback']):
            return await self._handle_code_review(user_input, context)
        elif any(keyword in user_input_lower for keyword in ['explain', 'how', 'what', 'why']):
            return await self._handle_code_explanation(user_input, context)
        elif any(keyword in user_input_lower for keyword in ['improve', 'optimize', 'better']):
            return await self._handle_improvement_suggestions(user_input, context)
        else:
            return await self._handle_general_code_chat(user_input)

    async def _update_conversation_context(self, user_input: str):
        """Update conversation context based on user input"""
        user_input_lower = user_input.lower()

        # Reset context
        for key in self.conversation_context:
            self.conversation_context[key] = False

        # Set new context
        if any(keyword in user_input_lower for keyword in ['analyze', 'architecture']):
            self.conversation_context["analyzing_project"] = True
        elif any(keyword in user_input_lower for keyword in ['debug', 'error']):
            self.conversation_context["debugging_issue"] = True
        elif any(keyword in user_input_lower for keyword in ['review', 'check']):
            self.conversation_context["reviewing_code"] = True
        elif any(keyword in user_input_lower for keyword in ['explain', 'learn', 'teach']):
            self.conversation_context["learning_mode"] = True

    async def _handle_architecture_analysis(self, user_input: str, context: Dict) -> str:
        """Handle architecture analysis requests"""
        # Extract project path from context or use current directory
        project_path = self._extract_project_path(user_input, context)

        if not project_path:
            return self._get_sassy_response("need_project_path")

        # Store for future reference
        self.current_project_path = project_path

        # Perform analysis with sass
        response = await self.sassy_mentor.analyze_architecture_with_humor(project_path)

        # Store in memory if available
        await self._store_analysis_in_memory("architecture_analysis", response, project_path)

        return response

    async def _handle_debugging_request(self, user_input: str, context: Dict) -> str:
        """Handle debugging assistance requests"""
        # Extract files and error description
        files = self._extract_file_paths(user_input, context)
        error_description = self._extract_error_description(user_input)

        if not files and not error_description:
            return self._get_sassy_response("need_debug_details")

        # Use current project files if no specific files mentioned
        if not files and self.current_project_path:
            files = self._get_relevant_files_for_debugging(error_description)

        response = await self.sassy_mentor.debug_with_sass(error_description, files)

        # Store debugging session in memory
        await self._store_analysis_in_memory("debugging_session", response, files)

        return response

    async def _handle_code_review(self, user_input: str, context: Dict) -> str:
        """Handle code review requests"""
        file_path = self._extract_single_file_path(user_input, context)

        if not file_path:
            return self._get_sassy_response("need_file_path")

        # Add to recent files
        if file_path not in self.recent_files_analyzed:
            self.recent_files_analyzed.append(file_path)
            if len(self.recent_files_analyzed) > 10:
                self.recent_files_analyzed.pop(0)

        response = await self.sassy_mentor.review_with_attitude(file_path)

        # Store review in memory
        await self._store_analysis_in_memory("code_review", response, file_path)

        return response

    async def _handle_code_explanation(self, user_input: str, context: Dict) -> str:
        """Handle code explanation requests"""
        file_path = self._extract_single_file_path(user_input, context)

        if not file_path:
            # Try to use recently analyzed file
            if self.recent_files_analyzed:
                file_path = self.recent_files_analyzed[-1]
                prefix = f"(Using your recent file: {os.path.basename(file_path)})\n\n"
            else:
                return self._get_sassy_response("need_file_for_explanation")
        else:
            prefix = ""

        response = await self.sassy_mentor.explain_code_with_personality(file_path)
        return prefix + response

    async def _handle_improvement_suggestions(self, user_input: str, context: Dict) -> str:
        """Handle improvement and optimization suggestions"""
        # Can work with specific file or recent analysis
        file_path = self._extract_single_file_path(user_input, context)

        if file_path:
            # Specific file improvement
            response = await self.sassy_mentor.review_with_attitude(file_path)
            return f"Here's how to improve that specific file:\n\n{response}"
        elif self.current_project_path:
            # Project-wide improvements
            response = await self.sassy_mentor.analyze_architecture_with_humor(self.current_project_path)
            return f"Here's how to improve your overall project:\n\n{response}"
        else:
            return self._get_sassy_response("general_improvement_advice")

    async def _handle_general_code_chat(self, user_input: str) -> str:
        """Handle general code-related conversation"""
        return await self.sassy_mentor.general_code_help_with_sass(user_input)

    def _extract_project_path(self, user_input: str, context: Dict) -> Optional[str]:
        """Extract project path from user input or context"""
        if context and "project_path" in context:
            return context["project_path"]

        # Look for path in user input
        words = user_input.split()
        for word in words:
            if "/" in word and os.path.exists(word):
                return word

        # Default to current directory if analyzing current project
        if any(keyword in user_input.lower() for keyword in ['this project', 'my project', 'current']):
            return os.getcwd()

        return None

    def _extract_file_paths(self, user_input: str, context: Dict) -> List[str]:
        """Extract file paths from user input or context"""
        files = []

        if context and "files" in context:
            files.extend(context["files"])

        # Look for .py files in user input
        words = user_input.split()
        for word in words:
            if word.endswith('.py') and os.path.exists(word):
                files.append(word)

        return files

    def _extract_single_file_path(self, user_input: str, context: Dict) -> Optional[str]:
        """Extract a single file path from user input or context"""
        files = self._extract_file_paths(user_input, context)
        return files[0] if files else None

    def _extract_error_description(self, user_input: str) -> str:
        """Extract error description from user input"""
        # Remove common debugging keywords to get core description
        keywords_to_remove = ['debug', 'help', 'fix', 'error', 'issue', 'problem']
        words = user_input.split()
        filtered_words = [word for word in words if word.lower() not in keywords_to_remove]
        return ' '.join(filtered_words).strip()

    def _get_relevant_files_for_debugging(self, error_description: str) -> List[str]:
        """Get relevant files for debugging based on error description"""
        if not self.current_project_path:
            return []

        # Simple heuristic - look for Python files in project
        relevant_files = []
        for root, dirs, files in os.walk(self.current_project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relevant_files.append(file_path)

                    # Limit to avoid overwhelming analysis
                    if len(relevant_files) >= 5:
                        break

        return relevant_files

    def _get_sassy_response(self, response_type: str) -> str:
        """Get appropriate sassy response for different situations"""
        responses = {
            "need_project_path": "I'd love to analyze your project, but I need to know where it is! Share the project path with me 📁",
            "need_debug_details": "Want me to debug something? I'll need either the error message or the files that are causing trouble 🔍",
            "need_file_path": "I need a specific file to work with! Share the file path and I'll take a look 📄",
            "need_file_for_explanation": "I need a file to explain! Either share one or let me analyze a file first 🤓",
            "general_improvement_advice": (
                "Want to improve your code? Here's my general advice:\n\n"
                "1. 📖 Write documentation - your future self will thank you\n"
                "2. 🧪 Add tests - they're like insurance for your code\n"
                "3. 🛡️ Handle errors gracefully - don't let things crash and burn\n"
                "4. 🎨 Use design patterns - stand on the shoulders of giants\n"
                "5. 🔒 Security first - keep the bad guys out\n\n"
                "Want specific feedback? Share your code and I'll give you targeted suggestions! 🎯"
            )
        }
        return responses.get(response_type, "I'm here to help with your code! What do you need? 💻")

    async def _store_analysis_in_memory(self, analysis_type: str, content: str, target: Any):
        """Store analysis results in Penny's memory system if available"""
        if not self.memory_system:
            return

        try:
            # Create a memory entry for the code analysis
            context = {
                "analysis_type": analysis_type,
                "target": str(target),
                "timestamp": "now"
            }

            # Store in Penny's memory
            self.memory_system.add_conversation_turn(
                user_input=f"Code analysis: {analysis_type}",
                assistant_response=content[:500] + "..." if len(content) > 500 else content,
                context=context,
                response_time_ms=100
            )

        except Exception as e:
            print(f"⚠️ Could not store analysis in memory: {e}")

    async def quick_file_check(self, file_path: str) -> str:
        """Quick file health check with personality"""
        return await self.sassy_mentor.quick_code_check(file_path)

    async def get_conversation_summary(self) -> str:
        """Get summary of recent code analysis conversations"""
        summary = "📊 **Recent Code Analysis Activity:**\n\n"

        if self.current_project_path:
            summary += f"🏗️ **Current Project:** {os.path.basename(self.current_project_path)}\n"

        if self.recent_files_analyzed:
            summary += f"📁 **Recent Files Reviewed:** {len(self.recent_files_analyzed)}\n"
            for file_path in self.recent_files_analyzed[-3:]:
                summary += f"   • {os.path.basename(file_path)}\n"

        # Current context
        active_contexts = [k for k, v in self.conversation_context.items() if v]
        if active_contexts:
            summary += f"🎯 **Current Focus:** {', '.join(active_contexts)}\n"

        summary += "\n💡 **What I can help with next:**\n"
        summary += "• Architecture analysis and pattern recognition\n"
        summary += "• Interactive debugging with step-by-step guidance\n"
        summary += "• Educational code reviews with improvement suggestions\n"
        summary += "• Code explanation and learning opportunities\n"

        return summary


async def main():
    """Test the Jedi-Enhanced Penny system"""
    penny = JediEnhancedPenny()

    # Test scenarios
    test_requests = [
        "analyze the architecture of this project",
        "review the jedi_code_analyzer.py file",
        "debug an issue with the research pipeline not returning results",
        "explain what the sassy_code_mentor.py file does",
        "how can I improve my code quality?",
        "what design patterns am I using?"
    ]

    print("\n🧪 Testing Jedi-Enhanced Penny")
    print("=" * 50)

    for request in test_requests:
        print(f"\n👤 User: {request}")
        print("-" * 30)

        # Simulate context for testing
        context = {
            "project_path": "/Users/CJ/Desktop/penny_assistant",
            "files": ["/Users/CJ/Desktop/penny_assistant/jedi_code_analyzer.py"]
        }

        response = await penny.process_code_request(request, context)
        print(f"🤖 Penny: {response[:200]}...")

    # Show conversation summary
    print(f"\n{await penny.get_conversation_summary()}")


if __name__ == "__main__":
    asyncio.run(main())