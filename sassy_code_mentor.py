#!/usr/bin/env python3
"""
Sassy Code Mentor - Penny's Personality + Jedi-Level Code Analysis
Combines technical expertise with Penny's characteristic sass and humor
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_code_analyzer import JediCodeAnalyzer, CodebaseAnalysis
from interactive_debugger import InteractiveDebugger, DebugPlan
from code_review_mentor import CodeReviewMentor, CodeReview

class SassyCodeMentor:
    """
    Combine technical analysis with Penny's personality
    - Technical depth like Claude
    - Personality and sass like Penny
    - Educational approach that's actually engaging
    """

    def __init__(self):
        self.analyzer = JediCodeAnalyzer()
        self.debugger = InteractiveDebugger(self.analyzer)
        self.reviewer = CodeReviewMentor()

        # Penny's sass levels for different scenarios
        self.sass_responses = {
            "excellent_code": [
                "Damn, this is some clean code! 🔥",
                "Someone's been reading their programming books! *chef's kiss*",
                "This code is so good it makes me want to frame it",
                "Look at you, writing code like a senior dev! I'm genuinely impressed"
            ],
            "good_code": [
                "Not bad, not bad at all! You're getting the hang of this",
                "Solid work! A few tweaks and this'll be *chef's kiss*",
                "I can see the potential here - nice foundation!"
            ],
            "needs_work": [
                "Okay, we need to have a little chat about this code...",
                "I mean, it works, but let's make it work *well*, yeah?",
                "This has potential, but right now it's giving me 'first draft' vibes"
            ],
            "hot_mess": [
                "Oh honey, no. Just... no. Let's fix this together 😅",
                "I've seen some code in my day, but this... this is special",
                "Okay, deep breath. We can absolutely make this better!"
            ],
            "security_issues": [
                "WHOA there! We've got some security red flags 🚨",
                "This code is more open than a 24/7 diner. Let's lock it down!",
                "Someone could drive a truck through these security holes!"
            ],
            "performance_issues": [
                "This code is moving slower than a Windows 95 startup",
                "I've seen molasses with better performance than this",
                "Your users are gonna be waiting longer than a DMV line"
            ]
        }

    async def analyze_with_personality(self, user_request: str, code_files: List[str] = None,
                                     project_path: str = None) -> str:
        """
        Combine technical analysis with Penny's personality
        """
        request_lower = user_request.lower()

        try:
            if "debug" in request_lower and code_files:
                return await self.debug_with_sass(user_request, code_files)
            elif "review" in request_lower and code_files:
                return await self.review_with_attitude(code_files[0] if code_files else None)
            elif "analyze" in request_lower or "architecture" in request_lower:
                if project_path:
                    return await self.analyze_architecture_with_humor(project_path)
                elif code_files:
                    return await self.analyze_architecture_with_humor(os.path.dirname(code_files[0]))
            elif "explain" in request_lower and code_files:
                return await self.explain_code_with_personality(code_files[0])
            else:
                return await self.general_code_help_with_sass(user_request)

        except Exception as e:
            return f"Oof, something went sideways while analyzing your code: {e}\n\nBut hey, that's what debugging is for! Want me to help figure out what happened? 🔍"

    async def debug_with_sass(self, issue: str, files: List[str]) -> str:
        """
        Debugging help with Penny's characteristic style
        """
        debug_info = await self.debugger.debug_issue(issue, files)

        # Determine sass level based on issue complexity
        if debug_info.root_cause_analysis['confidence'] > 0.8:
            sass_level = "confident"
        elif len(debug_info.proposed_solutions) > 2:
            sass_level = "helpful"
        else:
            sass_level = "detective"

        response = f"Alright, let's debug this mess together! 🔍\n\n"

        # Problem understanding with sass
        error_type = debug_info.problem_understanding['error_type']
        if error_type == "runtime_error":
            response += f"**What's happening:** Your code is throwing a tantrum (aka {error_type})\n"
        elif error_type == "performance_issue":
            response += f"**What's happening:** Your code is moving like it's stuck in molasses\n"
        else:
            response += f"**What's happening:** We've got a {error_type} situation on our hands\n"

        # Root cause with personality
        primary_cause = debug_info.root_cause_analysis['primary_cause']
        confidence = debug_info.root_cause_analysis['confidence']

        if confidence > 0.7:
            response += f"**My best guess:** I'm {confidence:.0%} sure this is a '{primary_cause}' situation\n\n"
        else:
            response += f"**My best guess:** This looks like '{primary_cause}', but I'm not 100% sure (detective work needed!)\n\n"

        # Step-by-step investigation with sass
        response += f"**Let's trace this step by step:**\n"
        for i, step in enumerate(debug_info.reproduction_steps[:4], 1):
            response += f"{i}. {step}\n"

        # Solution with attitude
        if debug_info.proposed_solutions:
            best_solution = debug_info.proposed_solutions[0]
            response += f"\n**My fix recommendation:**\n"
            response += f"**Approach:** {best_solution['approach']}\n"
            response += f"**Complexity:** {best_solution['complexity']} (because I believe in honest estimates)\n"
            response += f"**Time estimate:** {best_solution['estimated_effort']}\n\n"

            response += f"**Implementation game plan:**\n"
            for i, step in enumerate(best_solution['implementation_steps'][:3], 1):
                response += f"{i}. {step}\n"

            # Risks with honesty
            if best_solution['risks']:
                response += f"\n**Heads up on risks:** {', '.join(best_solution['risks'][:2])}\n"

        # Encouraging close
        if confidence > 0.7:
            response += f"\nI'm pretty confident this'll fix it. Want me to walk through any of these steps in detail? 🛠️"
        else:
            response += f"\nThis should get us started, but we might need to iterate. That's just how debugging works sometimes! 🤷‍♀️"

        return response

    async def review_with_attitude(self, file_path: str) -> str:
        """
        Code review with Penny's sass and educational value
        """
        if not file_path or not os.path.exists(file_path):
            return "Can't review code that doesn't exist! Send me a real file path, yeah? 😏"

        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        review = await self.reviewer.review_code(code_content, file_path)

        # Determine overall sass tone
        quality_score = review.code_quality_score
        if quality_score >= 8:
            sass_tone = "excellent_code"
        elif quality_score >= 6:
            sass_tone = "good_code"
        elif quality_score >= 4:
            sass_tone = "needs_work"
        else:
            sass_tone = "hot_mess"

        # Special handling for security issues
        critical_issues = [issue for issue in review.issues_found if issue.severity == "critical"]
        if critical_issues:
            sass_tone = "security_issues"

        response = f"Let me take a look at your code... *cracks knuckles* 💻\n\n"
        response += f"**{self._get_sass_response(sass_tone)}**\n\n"

        # Overall assessment with personality
        response += f"**Overall Quality:** {quality_score:.1f}/10\n"
        if quality_score >= 7:
            response += f"**Translation:** You know what you're doing! 👏\n\n"
        elif quality_score >= 5:
            response += f"**Translation:** Solid foundation, room to grow 📈\n\n"
        else:
            response += f"**Translation:** We've got some work to do, but that's what I'm here for! 💪\n\n"

        # Positive aspects first (because encouragement matters)
        if review.positive_aspects:
            response += f"**What I Love:**\n"
            for positive in review.positive_aspects[:3]:
                response += f"• ✨ {positive}\n"
            response += "\n"

        # Issues with educational context
        if review.issues_found:
            critical = [i for i in review.issues_found if i.severity == "critical"]
            major = [i for i in review.issues_found if i.severity == "major"]

            if critical:
                response += f"**🚨 Critical Issues (fix these ASAP!):**\n"
                for issue in critical[:2]:
                    response += f"• **{issue.description}**\n"
                    response += f"  *Why this matters:* {issue.explanation}\n"
                    response += f"  *Quick fix:* {issue.suggested_fix}\n\n"

            if major:
                response += f"**🔧 Major Improvements:**\n"
                for issue in major[:2]:
                    response += f"• **{issue.description}**\n"
                    response += f"  *Educational note:* {issue.learning_note}\n\n"

        # Design patterns with teaching moments
        if review.pattern_analysis:
            response += f"**🎨 Design Pattern Spotted:**\n"
            for pattern in review.pattern_analysis[:2]:
                if pattern.implementation_quality in ["excellent", "good"]:
                    response += f"• **{pattern.pattern_name}** - {pattern.implementation_quality} implementation! 🎯\n"
                    response += f"  *Teaching moment:* {pattern.explanation}\n"
                else:
                    response += f"• **{pattern.pattern_name}** - room for improvement\n"
                    if pattern.improvement_suggestions:
                        response += f"  *Suggestion:* {pattern.improvement_suggestions[0]}\n"
            response += "\n"

        # Learning recommendations with sass
        if review.learning_recommendations:
            response += f"**📚 Level Up Your Skills:**\n"
            for rec in review.learning_recommendations[:3]:
                response += f"• {rec}\n"
            response += "\n"

        # Encouraging close
        if quality_score >= 7:
            response += f"Seriously though, this is solid work. Keep doing what you're doing! 🚀"
        elif quality_score >= 5:
            response += f"You're on the right track! A few tweaks and this'll be *chef's kiss* 💋"
        else:
            response += f"Hey, we all start somewhere. Let's make this code something you can be proud of! 💪"

        return response

    async def analyze_architecture_with_humor(self, project_path: str) -> str:
        """
        Architecture analysis with Penny's humor and insights
        """
        if not os.path.exists(project_path):
            return "That path doesn't exist! Are you trying to analyze imaginary code? 😏"

        analysis = await self.analyzer.analyze_codebase(project_path)

        response = f"Alright, let me put on my architecture detective hat and see what you've built here... 🔍\n\n"

        # Architecture overview with sass
        arch_pattern = analysis.architecture_overview['pattern']
        confidence = analysis.architecture_overview['confidence']

        if confidence > 0.7:
            response += f"**Architecture Pattern:** You've got yourself a {arch_pattern} architecture (and I'm {confidence:.0%} confident about that)\n"
        else:
            response += f"**Architecture Pattern:** Looks like {arch_pattern}, but it's giving me mixed signals (only {confidence:.0%} sure)\n"

        complexity = analysis.architecture_overview['complexity_score']
        if complexity < 5:
            response += f"**Complexity:** Refreshingly simple! ({complexity:.1f}/10) 🌱\n"
        elif complexity < 7:
            response += f"**Complexity:** Getting sophisticated ({complexity:.1f}/10) 🏗️\n"
        else:
            response += f"**Complexity:** This is some next-level architecture ({complexity:.1f}/10) 🏰\n"

        response += "\n"

        # Main components with personality
        if analysis.architecture_overview.get('core_components'):
            response += f"**Main Components I Found:**\n"
            for component in analysis.architecture_overview['core_components'][:5]:
                component_name = os.path.basename(component)
                if 'main' in component_name.lower():
                    response += f"• 🚪 **{component_name}** - The front door of your app\n"
                elif 'core' in component_name.lower() or 'engine' in component_name.lower():
                    response += f"• ⚙️ **{component_name}** - The beating heart\n"
                elif 'security' in component_name.lower():
                    response += f"• 🛡️ **{component_name}** - Keeping the bad guys out\n"
                elif 'memory' in component_name.lower():
                    response += f"• 🧠 **{component_name}** - The brain of the operation\n"
                else:
                    response += f"• 📦 **{component_name}** - Essential functionality\n"
            response += "\n"

        # Design patterns with educational sass
        if analysis.design_patterns:
            response += f"**Design Patterns Detected:**\n"
            for pattern in analysis.design_patterns[:3]:
                if pattern.confidence > 0.7:
                    response += f"• 🎨 **{pattern.pattern_name}** ({pattern.confidence:.0%} confidence) - Nice!\n"
                    if pattern.educational_notes:
                        response += f"  *Why it's good:* {pattern.educational_notes[0]}\n"
                else:
                    response += f"• 🤔 **{pattern.pattern_name}** (only {pattern.confidence:.0%} sure) - might need cleanup\n"
            response += "\n"

        # Security overview with appropriate sass
        security_score = analysis.security_analysis['overall_score']
        if security_score >= 8:
            response += f"**Security:** Locked down tight! ({security_score}/10) 🔒\n"
        elif security_score >= 6:
            response += f"**Security:** Pretty solid, few small gaps ({security_score}/10) 🛡️\n"
        elif security_score >= 4:
            response += f"**Security:** Some holes need patching ({security_score}/10) ⚠️\n"
        else:
            response += f"**Security:** Houston, we have a problem ({security_score}/10) 🚨\n"

        # Performance insights
        bottlenecks = analysis.performance_insights.get('bottlenecks', [])
        if bottlenecks:
            response += f"**Performance Red Flags:** {len(bottlenecks)} potential issues spotted\n"
            if len(bottlenecks) > 3:
                response += f"*Note:* Quite a few performance concerns - might want to prioritize these!\n"
        else:
            response += f"**Performance:** No obvious bottlenecks detected 🚀\n"

        response += "\n"

        # Top recommendations with personality
        if analysis.recommendations:
            response += f"**My Top Recommendations:**\n"
            for i, rec in enumerate(analysis.recommendations[:4], 1):
                if "security" in rec.lower():
                    response += f"{i}. 🛡️ {rec}\n"
                elif "performance" in rec.lower():
                    response += f"{i}. ⚡ {rec}\n"
                elif "test" in rec.lower():
                    response += f"{i}. 🧪 {rec}\n"
                else:
                    response += f"{i}. 💡 {rec}\n"
            response += "\n"

        # Encouraging close based on overall quality
        if security_score >= 7 and complexity < 6:
            response += f"Overall? You've built something solid here. I'm genuinely impressed! 👏"
        elif security_score >= 5:
            response += f"This is a good foundation! A few improvements and you'll have something really solid 🏗️"
        else:
            response += f"There's potential here! Let's work together to make this architecture shine ✨"

        return response

    async def explain_code_with_personality(self, file_path: str) -> str:
        """
        Explain code functionality with Penny's engaging style
        """
        if not os.path.exists(file_path):
            return "Can't explain code that's not there! Check that file path 😉"

        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        file_name = os.path.basename(file_path)

        response = f"Let me break down what's happening in **{file_name}**... 🤓\n\n"

        # Quick analysis for context
        review = await self.reviewer.review_code(code_content, file_path)

        # Explain based on file patterns
        if 'class' in code_content and 'def' in code_content:
            response += f"**What this file does:**\n"
            response += f"This is a class-based module (object-oriented programming for the win!)\n\n"

            # Find main classes
            import ast
            try:
                tree = ast.parse(code_content)
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

                if classes:
                    response += f"**Main Classes:**\n"
                    for class_name in classes[:3]:
                        response += f"• `{class_name}` - Handles the heavy lifting for {class_name.lower().replace('_', ' ')}\n"

                if functions:
                    response += f"\n**Key Functions:**\n"
                    for func_name in functions[:3]:
                        if not func_name.startswith('_'):  # Skip private methods
                            response += f"• `{func_name}()` - Does the {func_name.lower().replace('_', ' ')} magic\n"

            except SyntaxError:
                response += f"*Note: File has syntax issues that prevent detailed analysis*\n"

        elif 'def' in code_content:
            response += f"**What this file does:**\n"
            response += f"Function-based module (keeping it simple and functional!)\n\n"

        # Design patterns explanation
        if review.pattern_analysis:
            response += f"\n**Design Patterns at Work:**\n"
            for pattern in review.pattern_analysis[:2]:
                response += f"• **{pattern.pattern_name} Pattern** - {pattern.explanation}\n"
                if pattern.educational_notes:
                    response += f"  *Why it's useful:* {pattern.educational_notes[0]}\n"

        # Educational highlights
        if review.educational_highlights:
            response += f"\n**Cool Things I Notice:**\n"
            for highlight in review.educational_highlights[:3]:
                response += f"• {highlight}\n"

        response += f"\n**The Bottom Line:**\n"
        if review.code_quality_score >= 7:
            response += f"This is well-structured code that knows what it's doing! 👌"
        elif review.code_quality_score >= 5:
            response += f"Solid code with good fundamentals. Easy to follow and understand 👍"
        else:
            response += f"The logic is there, but could use some cleanup for better readability 🧹"

        return response

    async def general_code_help_with_sass(self, request: str) -> str:
        """
        General code help with Penny's personality
        """
        request_lower = request.lower()

        if any(word in request_lower for word in ['help', 'how', 'what', 'explain']):
            response = f"I'm your sassy code mentor! Here's what I can help you with:\n\n"
            response += f"🔍 **Code Analysis** - \"analyze my project\" or \"explain this architecture\"\n"
            response += f"🐛 **Debugging** - \"debug this error\" or \"help me fix this issue\"\n"
            response += f"📝 **Code Review** - \"review my code\" or \"check this file\"\n"
            response += f"🎓 **Learning** - \"explain this pattern\" or \"how does this work\"\n\n"
            response += f"Just send me your code files or project path and tell me what you need! 💪"

        elif any(word in request_lower for word in ['best', 'practice', 'improve', 'better']):
            response = f"Want to level up your code? Here are my top tips:\n\n"
            response += f"1. 📖 **Document your code** - Future you will thank present you\n"
            response += f"2. 🧪 **Write tests** - They're like insurance for your code\n"
            response += f"3. 🛡️ **Handle errors gracefully** - Don't let your app crash and burn\n"
            response += f"4. 🎨 **Use design patterns** - Stand on the shoulders of giants\n"
            response += f"5. 🔒 **Security first** - Keep the bad guys out\n\n"
            response += f"Want me to review your code and give specific feedback? Just share it! 🚀"

        elif any(word in request_lower for word in ['pattern', 'design', 'architecture']):
            response = f"Ah, a fellow architecture enthusiast! 🏗️\n\n"
            response += f"Design patterns are like recipes for solving common coding problems:\n\n"
            response += f"• **Singleton** - When you need exactly one instance (like a database connection)\n"
            response += f"• **Factory** - When object creation is complex (like making different types of users)\n"
            response += f"• **Observer** - When objects need to react to events (like UI updates)\n"
            response += f"• **Strategy** - When you have multiple ways to do something (like different sorting algorithms)\n\n"
            response += f"Want me to analyze your code and see what patterns you're using? 🎯"

        else:
            response = f"I'm here to help with all things code! 💻\n\n"
            response += f"Whether you need debugging help, code reviews, architecture analysis, or just want to understand how something works - I've got you covered.\n\n"
            response += f"Share your code files or describe what you're working on, and let's make some magic happen! ✨"

        return response

    def _get_sass_response(self, tone: str) -> str:
        """Get a random sass response for the given tone"""
        import random
        responses = self.sass_responses.get(tone, ["Let's take a look at this code..."])
        return random.choice(responses)

    async def quick_code_check(self, file_path: str) -> str:
        """Quick code quality check with personality"""
        if not os.path.exists(file_path):
            return "File not found! Did you check the path? 🤔"

        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        # Quick assessment
        lines = code_content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        response = f"**Quick Code Health Check for {os.path.basename(file_path)}** 🏥\n\n"

        # Basic stats
        response += f"📊 **Stats:** {len(non_empty_lines)} lines of actual code\n"

        # Quick checks
        has_classes = 'class ' in code_content
        has_functions = 'def ' in code_content
        has_docstrings = '"""' in code_content or "'''" in code_content
        has_error_handling = 'try:' in code_content and 'except' in code_content
        has_comments = any(line.strip().startswith('#') for line in lines)

        health_score = 0
        issues = []
        good_things = []

        if has_classes or has_functions:
            health_score += 2
            good_things.append("Well-structured with classes/functions")
        else:
            issues.append("No clear structure (consider organizing into functions)")

        if has_docstrings:
            health_score += 1
            good_things.append("Has documentation")
        else:
            issues.append("Missing documentation")

        if has_error_handling:
            health_score += 1
            good_things.append("Handles errors properly")
        else:
            issues.append("No error handling found")

        if has_comments:
            health_score += 1
            good_things.append("Has helpful comments")

        # Security red flags
        if 'eval(' in code_content or 'exec(' in code_content:
            issues.append("🚨 SECURITY RISK: Uses eval() or exec()")
            health_score -= 2

        # Normalize score
        health_score = max(0, min(5, health_score))

        if health_score >= 4:
            response += f"💚 **Health:** Excellent ({health_score}/5)\n"
        elif health_score >= 3:
            response += f"💛 **Health:** Good ({health_score}/5)\n"
        elif health_score >= 2:
            response += f"🧡 **Health:** Needs improvement ({health_score}/5)\n"
        else:
            response += f"❤️ **Health:** Needs attention ({health_score}/5)\n"

        if good_things:
            response += f"\n✅ **Good things:** {', '.join(good_things)}\n"

        if issues:
            response += f"\n⚠️ **Issues:** {', '.join(issues[:3])}\n"

        response += f"\nWant a detailed review? Just ask! 😊"

        return response


if __name__ == "__main__":
    async def main():
        mentor = SassyCodeMentor()

        # Test scenarios
        test_scenarios = [
            ("analyze my project architecture", None, "/Users/CJ/Desktop/penny_assistant"),
            ("review this code file", ["/Users/CJ/Desktop/penny_assistant/jedi_code_analyzer.py"], None),
            ("debug this research pipeline error", ["research_first_pipeline.py"], None),
            ("explain what this code does", ["/Users/CJ/Desktop/penny_assistant/sassy_code_mentor.py"], None),
            ("how can I improve my code?", None, None)
        ]

        for request, files, project_path in test_scenarios:
            print(f"\n{'='*60}")
            print(f"USER: {request}")
            print(f"{'='*60}")

            response = await mentor.analyze_with_personality(request, files, project_path)
            print(response)

            print(f"\n{'='*60}")

    asyncio.run(main())