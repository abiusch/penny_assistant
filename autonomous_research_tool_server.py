"""
Autonomous Research Tool Server
Enables Penny to identify knowledge gaps, conduct independent research,
synthesize findings, and generate actionable insights
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# MCP and security imports with fallbacks
try:
    from mcp_client import MCPToolServer, MCPOperation, MCPResult
    from tool_server_foundation import ToolServerType, SecurityLevel
    from command_whitelist_system import CommandWhitelistSystem
    from multi_channel_emergency_stop import MultiChannelEmergencyStop
    from enhanced_security_logging import EnhancedSecurityLogging
    from rollback_recovery_system import RollbackRecoverySystem
    from rate_limiting_resource_control import RateLimitingResourceControl
    MCP_AVAILABLE = True
except ImportError:
    # Fallback definitions for standalone operation
    from enum import Enum
    from dataclasses import dataclass

    class ToolServerType(Enum):
        AUTONOMOUS_RESEARCH = "autonomous_research"

    class SecurityLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    @dataclass
    class MCPOperation:
        name: str
        parameters: Dict[str, Any]
        security_level: SecurityLevel = SecurityLevel.MEDIUM

    @dataclass
    class MCPResult:
        success: bool
        data: Any = None
        error: Optional[str] = None
        metadata: Optional[Dict[str, Any]] = None

    class MCPToolServer:
        def __init__(self, name, operations): pass
        async def start(self): return True
        async def stop(self): return True

    # Mock security classes
    class CommandWhitelistSystem:
        async def is_command_allowed(self, command): return True

    class MultiChannelEmergencyStop:
        def is_emergency_active(self): return False

    class EnhancedSecurityLogging:
        async def log_security_event(self, event_type, details): pass

    class RollbackRecoverySystem:
        async def create_checkpoint(self, checkpoint_id): return f"checkpoint_{checkpoint_id}"

    class RateLimitingResourceControl:
        async def check_rate_limit(self, user_id, operation): return True

    MCP_AVAILABLE = False


class ResearchScope(Enum):
    """Research scope types"""
    QUICK = "quick"          # 1-3 sources, 30 seconds
    COMPREHENSIVE = "comprehensive"  # 5-10 sources, 2-5 minutes
    DEEP = "deep"            # 10+ sources, 5-10 minutes


class KnowledgeGapType(Enum):
    """Types of knowledge gaps that can be detected"""
    FACTUAL = "factual"           # Missing specific facts or data
    PROCEDURAL = "procedural"     # Missing knowledge of how to do something
    CONTEXTUAL = "contextual"     # Missing understanding of context or background
    COMPARATIVE = "comparative"   # Missing knowledge for comparisons
    TEMPORAL = "temporal"         # Missing current/recent information
    DOMAIN_SPECIFIC = "domain_specific"  # Missing specialized knowledge


class ResearchStatus(Enum):
    """Research execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class KnowledgeGap:
    """Represents an identified knowledge gap"""
    gap_id: str
    gap_type: KnowledgeGapType
    description: str
    context: str
    confidence: float
    priority: int  # 1-10, 10 being highest priority
    detected_at: datetime
    conversation_context: Dict[str, Any]


@dataclass
class ResearchQuestion:
    """Represents a research question generated from a knowledge gap"""
    question_id: str
    question: str
    question_type: str  # "factual", "analytical", "practical", etc.
    knowledge_gap_id: str
    priority: int
    expected_sources: List[str]
    time_estimate: int  # seconds
    created_at: datetime


@dataclass
class ResearchSource:
    """Represents a research source and its content"""
    source_id: str
    url: str
    title: str
    content: str
    credibility_score: float
    relevance_score: float
    timestamp: datetime
    source_type: str  # "web", "document", "academic", etc.


@dataclass
class ResearchFinding:
    """Represents a synthesized research finding"""
    finding_id: str
    research_question_id: str
    summary: str
    key_insights: List[str]
    supporting_sources: List[str]
    confidence_level: float
    actionable_recommendations: List[str]
    related_topics: List[str]
    created_at: datetime


@dataclass
class ResearchPlan:
    """Represents a research execution plan"""
    plan_id: str
    knowledge_gap_id: str
    research_questions: List[ResearchQuestion]
    research_scope: ResearchScope
    time_limit: int
    source_types: List[str]
    priority_order: List[str]  # Question IDs in priority order
    created_at: datetime
    status: ResearchStatus


class ConversationAnalyzer:
    """Analyzes conversations to detect knowledge gaps and learning opportunities"""

    def __init__(self):
        self.uncertainty_patterns = [
            r"i'?m not sure",
            r"i don'?t know",
            r"i'?m not familiar",
            r"that'?s outside my knowledge",
            r"i'?d need to research",
            r"i don'?t have information",
            r"i'?m uncertain",
            r"i lack knowledge",
            r"i'?m not aware",
            r"beyond my current understanding"
        ]

        self.learning_trigger_patterns = [
            r"tell me more about",
            r"i'?d like to learn",
            r"how does .* work",
            r"what'?s the latest",
            r"can you explain",
            r"i'?m curious about",
            r"what are the best practices",
            r"how do i .*",
            r"what should i know about"
        ]

    async def identify_knowledge_gaps(self, conversation_context: str, user_query: str,
                                    confidence_threshold: float = 0.7) -> List[KnowledgeGap]:
        """Identify knowledge gaps from conversation context"""
        gaps = []

        # Analyze for uncertainty expressions
        uncertainty_gaps = await self._detect_uncertainty_gaps(conversation_context, user_query)
        gaps.extend(uncertainty_gaps)

        # Analyze for learning opportunities
        learning_gaps = await self._detect_learning_opportunities(conversation_context, user_query)
        gaps.extend(learning_gaps)

        # Analyze for domain-specific knowledge needs
        domain_gaps = await self._detect_domain_knowledge_gaps(conversation_context, user_query)
        gaps.extend(domain_gaps)

        # Filter by confidence threshold
        filtered_gaps = [gap for gap in gaps if gap.confidence >= confidence_threshold]

        # Prioritize gaps
        prioritized_gaps = await self._prioritize_knowledge_gaps(filtered_gaps)

        return prioritized_gaps

    async def _detect_uncertainty_gaps(self, context: str, query: str) -> List[KnowledgeGap]:
        """Detect gaps based on uncertainty expressions"""
        gaps = []
        combined_text = f"{context} {query}".lower()

        for pattern in self.uncertainty_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                # Extract context around the uncertainty
                start = max(0, match.start() - 100)
                end = min(len(combined_text), match.end() + 100)
                gap_context = combined_text[start:end].strip()

                # Determine gap type and create knowledge gap
                gap_type = await self._classify_gap_type(gap_context)

                gap = KnowledgeGap(
                    gap_id=self._generate_gap_id(gap_context),
                    gap_type=KnowledgeGapType(gap_type),
                    description=f"Uncertainty about: {gap_context[:100]}...",
                    context=gap_context,
                    confidence=0.8,
                    priority=7,
                    detected_at=datetime.now(),
                    conversation_context={"full_context": context, "user_query": query}
                )
                gaps.append(gap)

        return gaps

    async def _detect_learning_opportunities(self, context: str, query: str) -> List[KnowledgeGap]:
        """Detect gaps based on learning triggers in user queries"""
        gaps = []
        combined_text = f"{context} {query}".lower()

        for pattern in self.learning_trigger_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                # Extract the topic being asked about
                start = max(0, match.start() - 50)
                end = min(len(combined_text), match.end() + 150)
                topic_context = combined_text[start:end].strip()

                gap_type = await self._classify_gap_type(topic_context)

                gap = KnowledgeGap(
                    gap_id=self._generate_gap_id(topic_context),
                    gap_type=KnowledgeGapType(gap_type),
                    description=f"Learning opportunity: {topic_context[:100]}...",
                    context=topic_context,
                    confidence=0.9,
                    priority=8,
                    detected_at=datetime.now(),
                    conversation_context={"full_context": context, "user_query": query}
                )
                gaps.append(gap)

        return gaps

    async def _detect_domain_knowledge_gaps(self, context: str, query: str) -> List[KnowledgeGap]:
        """Detect gaps in domain-specific knowledge"""
        gaps = []

        # Technical terms that might indicate specialized knowledge needs
        technical_indicators = [
            r"\b[A-Z]{2,}\b",  # Acronyms
            r"\b\w+\.\w+\b",   # Technical notation (e.g., "node.js", "v1.0")
            r"\b\d+\.\d+\b",   # Version numbers
            r"\bAPI\b", r"\bSDK\b", r"\bframework\b", r"\blibrary\b",
            r"\btool\b", r"\bplatform\b", r"\bservice\b"
        ]

        combined_text = f"{context} {query}"

        for pattern in technical_indicators:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                # Check if this technical term needs research
                term_context = self._extract_term_context(combined_text, match)

                if await self._needs_domain_research(term_context):
                    gap = KnowledgeGap(
                        gap_id=self._generate_gap_id(term_context),
                        gap_type=KnowledgeGapType.DOMAIN_SPECIFIC,
                        description=f"Domain knowledge needed: {term_context[:100]}...",
                        context=term_context,
                        confidence=0.6,
                        priority=6,
                        detected_at=datetime.now(),
                        conversation_context={"full_context": context, "user_query": query}
                    )
                    gaps.append(gap)

        return gaps

    async def _classify_gap_type(self, context: str) -> str:
        """Classify the type of knowledge gap based on context"""
        context_lower = context.lower()

        if any(word in context_lower for word in ["how to", "steps", "process", "procedure"]):
            return "procedural"
        elif any(word in context_lower for word in ["latest", "recent", "current", "new", "updates"]):
            return "temporal"
        elif any(word in context_lower for word in ["compare", "versus", "vs", "difference", "better"]):
            return "comparative"
        elif any(word in context_lower for word in ["background", "context", "why", "reason"]):
            return "contextual"
        else:
            return "factual"

    def _extract_term_context(self, text: str, match) -> str:
        """Extract context around a technical term"""
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        return text[start:end].strip()

    async def _needs_domain_research(self, context: str) -> bool:
        """Determine if a technical term/context needs research"""
        # Simple heuristic - could be enhanced with ML
        uncertainty_indicators = ["unfamiliar", "new to", "don't know", "not sure", "learn about"]
        return any(indicator in context.lower() for indicator in uncertainty_indicators)

    async def _prioritize_knowledge_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Prioritize knowledge gaps based on various factors"""
        # Sort by priority score (higher is more important)
        return sorted(gaps, key=lambda g: (g.priority, g.confidence), reverse=True)

    def _generate_gap_id(self, context: str) -> str:
        """Generate unique ID for knowledge gap"""
        hash_input = f"{context}_{datetime.now().isoformat()}"
        return f"gap_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"


class ResearchQuestionGenerator:
    """Generates specific research questions from identified knowledge gaps"""

    def __init__(self):
        self.question_templates = {
            KnowledgeGapType.FACTUAL: [
                "What is {topic}?",
                "What are the key facts about {topic}?",
                "What is the current status of {topic}?",
                "What are the latest developments in {topic}?"
            ],
            KnowledgeGapType.PROCEDURAL: [
                "How do you {action}?",
                "What are the steps to {action}?",
                "What is the best way to {action}?",
                "What are the best practices for {action}?"
            ],
            KnowledgeGapType.CONTEXTUAL: [
                "What is the background of {topic}?",
                "Why is {topic} important?",
                "What is the context surrounding {topic}?",
                "How did {topic} develop historically?"
            ],
            KnowledgeGapType.COMPARATIVE: [
                "How does {topic1} compare to {topic2}?",
                "What are the differences between {topic1} and {topic2}?",
                "Which is better: {topic1} or {topic2}?",
                "What are the pros and cons of {topic1} vs {topic2}?"
            ],
            KnowledgeGapType.TEMPORAL: [
                "What are the latest updates on {topic}?",
                "What has changed recently with {topic}?",
                "What is the current state of {topic}?",
                "What are the recent trends in {topic}?"
            ],
            KnowledgeGapType.DOMAIN_SPECIFIC: [
                "What are the technical details of {topic}?",
                "How does {topic} work in practice?",
                "What are the specifications for {topic}?",
                "What do experts say about {topic}?"
            ]
        }

    async def generate_research_questions(self, knowledge_gap: KnowledgeGap,
                                        max_questions: int = 3) -> List[ResearchQuestion]:
        """Generate research questions from a knowledge gap"""
        questions = []

        # Extract topics from the gap context
        topics = await self._extract_topics(knowledge_gap.context)

        # Generate questions based on gap type
        templates = self.question_templates.get(knowledge_gap.gap_type,
                                               self.question_templates[KnowledgeGapType.FACTUAL])

        for i, template in enumerate(templates[:max_questions]):
            question_text = await self._fill_template(template, topics, knowledge_gap.context)

            question = ResearchQuestion(
                question_id=f"q_{knowledge_gap.gap_id}_{i}",
                question=question_text,
                question_type=knowledge_gap.gap_type.value,
                knowledge_gap_id=knowledge_gap.gap_id,
                priority=knowledge_gap.priority,
                expected_sources=await self._suggest_source_types(knowledge_gap.gap_type),
                time_estimate=await self._estimate_research_time(knowledge_gap.gap_type),
                created_at=datetime.now()
            )
            questions.append(question)

        return questions

    async def _extract_topics(self, context: str) -> Dict[str, str]:
        """Extract key topics from context"""
        # Simple topic extraction - could be enhanced with NLP
        words = context.split()
        topics = {}

        # Look for nouns and technical terms
        for word in words:
            if len(word) > 3 and word.isalnum():
                if word.lower() not in ['that', 'this', 'what', 'how', 'when', 'where', 'why']:
                    topics['topic'] = word
                    break

        # Default fallback
        if not topics:
            topics['topic'] = "the subject"

        return topics

    async def _fill_template(self, template: str, topics: Dict[str, str], context: str) -> str:
        """Fill in question template with extracted topics"""
        question = template

        for placeholder, value in topics.items():
            question = question.replace(f"{{{placeholder}}}", value)

        # Handle action placeholders for procedural questions
        if "{action}" in question:
            action = await self._extract_action(context)
            question = question.replace("{action}", action)

        return question

    async def _extract_action(self, context: str) -> str:
        """Extract action/verb from context for procedural questions"""
        # Look for verbs that indicate actions
        action_words = ["implement", "create", "build", "setup", "configure", "install", "use", "do"]
        words = context.lower().split()

        for word in words:
            if word in action_words:
                return word

        return "accomplish this"

    async def _suggest_source_types(self, gap_type: KnowledgeGapType) -> List[str]:
        """Suggest appropriate source types for different gap types"""
        source_mapping = {
            KnowledgeGapType.FACTUAL: ["web", "encyclopedia", "official"],
            KnowledgeGapType.PROCEDURAL: ["documentation", "tutorials", "guides"],
            KnowledgeGapType.CONTEXTUAL: ["articles", "background", "historical"],
            KnowledgeGapType.COMPARATIVE: ["reviews", "comparisons", "expert_analysis"],
            KnowledgeGapType.TEMPORAL: ["news", "recent_articles", "updates"],
            KnowledgeGapType.DOMAIN_SPECIFIC: ["technical_docs", "expert_sources", "specifications"]
        }
        return source_mapping.get(gap_type, ["web", "general"])

    async def _estimate_research_time(self, gap_type: KnowledgeGapType) -> int:
        """Estimate research time in seconds based on gap type"""
        time_estimates = {
            KnowledgeGapType.FACTUAL: 60,
            KnowledgeGapType.PROCEDURAL: 120,
            KnowledgeGapType.CONTEXTUAL: 180,
            KnowledgeGapType.COMPARATIVE: 240,
            KnowledgeGapType.TEMPORAL: 90,
            KnowledgeGapType.DOMAIN_SPECIFIC: 300
        }
        return time_estimates.get(gap_type, 120)


class ResearchExecutor:
    """Executes research plans using available tools and sources"""

    def __init__(self, web_search_available: bool = True, file_system_available: bool = True):
        self.web_search_available = web_search_available
        self.file_system_available = file_system_available
        self.active_research_sessions = {}

    async def create_research_plan(self, knowledge_gap: KnowledgeGap,
                                 research_questions: List[ResearchQuestion],
                                 research_scope: ResearchScope = ResearchScope.COMPREHENSIVE,
                                 time_limit: int = 300) -> ResearchPlan:
        """Create a research execution plan"""

        # Determine source types based on availability and scope
        source_types = []
        if self.web_search_available:
            source_types.append("web")
        if self.file_system_available:
            source_types.append("documents")

        # Prioritize questions by importance and research time
        priority_order = sorted(research_questions,
                              key=lambda q: (q.priority, -q.time_estimate),
                              reverse=True)

        plan = ResearchPlan(
            plan_id=f"plan_{knowledge_gap.gap_id}",
            knowledge_gap_id=knowledge_gap.gap_id,
            research_questions=[q for q in priority_order],
            research_scope=research_scope,
            time_limit=time_limit,
            source_types=source_types,
            priority_order=[q.question_id for q in priority_order],
            created_at=datetime.now(),
            status=ResearchStatus.PENDING
        )

        return plan

    async def execute_research_plan(self, research_plan: ResearchPlan,
                                  user_id: str,
                                  progress_callback=None) -> List[ResearchFinding]:
        """Execute a research plan and return findings"""
        findings = []
        start_time = time.time()

        # Update plan status
        research_plan.status = ResearchStatus.IN_PROGRESS
        self.active_research_sessions[research_plan.plan_id] = research_plan

        try:
            for i, question in enumerate(research_plan.research_questions):
                # Check time limit
                elapsed_time = time.time() - start_time
                if elapsed_time > research_plan.time_limit:
                    break

                # Report progress
                if progress_callback:
                    await progress_callback({
                        "plan_id": research_plan.plan_id,
                        "progress": (i / len(research_plan.research_questions)) * 100,
                        "current_question": question.question,
                        "elapsed_time": elapsed_time
                    })

                # Research the question
                question_findings = await self._research_question(question, research_plan, user_id)
                findings.extend(question_findings)

            research_plan.status = ResearchStatus.COMPLETED

        except Exception as e:
            research_plan.status = ResearchStatus.FAILED
            raise

        finally:
            if research_plan.plan_id in self.active_research_sessions:
                del self.active_research_sessions[research_plan.plan_id]

        return findings

    async def _research_question(self, question: ResearchQuestion,
                               plan: ResearchPlan, user_id: str) -> List[ResearchFinding]:
        """Research a specific question"""
        findings = []
        sources = []

        # Perform web search if available
        if "web" in plan.source_types and self.web_search_available:
            web_sources = await self._web_search(question.question, user_id)
            sources.extend(web_sources)

        # Search documents if available
        if "documents" in plan.source_types and self.file_system_available:
            doc_sources = await self._document_search(question.question, user_id)
            sources.extend(doc_sources)

        # Synthesize findings from sources
        if sources:
            finding = await self._synthesize_finding(question, sources)
            findings.append(finding)

        return findings

    async def _web_search(self, query: str, user_id: str) -> List[ResearchSource]:
        """Perform web search using Brave Search API with fallback chain"""
        sources = []

        try:
            # Use Brave Search as primary (best performance from real-world experience)
            from brave_search_api import brave_search

            # Try Brave Search first
            search_results = await brave_search(query, max_results=5)

            # Convert search results to research sources
            for result in search_results:
                if result.get("url") and result.get("title"):
                    source = ResearchSource(
                        source_id=f"brave_{hashlib.md5(result['url'].encode()).hexdigest()[:8]}",
                        url=result["url"],
                        title=result["title"],
                        content=result.get("snippet", ""),
                        credibility_score=0.9,  # High credibility for Brave results
                        relevance_score=0.9,
                        timestamp=datetime.now(),
                        source_type="web"
                    )
                    sources.append(source)

        except Exception as e:
            # Try fallback chain: Google CSE -> DuckDuckGo
            print(f"⚠️ Brave Search failed ({e}), trying fallbacks...")
            sources = await self._web_search_fallback_chain(query)

        print(f"🔍 Web search for '{query}' found {len(sources)} sources")
        return sources

    async def _web_search_fallback_chain(self, query: str) -> List[ResearchSource]:
        """Fallback chain: Google CSE -> DuckDuckGo when Brave fails"""
        sources = []

        # Try Google CSE first
        try:
            from google_cse_search import google_cse_search
            search_results = await google_cse_search(query, max_results=3)

            for result in search_results:
                if result.get("url") and result.get("title"):
                    source = ResearchSource(
                        source_id=f"gcs_{hashlib.md5(result['url'].encode()).hexdigest()[:8]}",
                        url=result["url"],
                        title=result["title"],
                        content=result.get("snippet", ""),
                        credibility_score=0.8,  # Slightly lower for fallback
                        relevance_score=0.8,
                        timestamp=datetime.now(),
                        source_type="web_fallback"
                    )
                    sources.append(source)

            if sources:
                print(f"✅ Google CSE fallback found {len(sources)} sources")
                return sources

        except Exception as e:
            print(f"⚠️ Google CSE fallback also failed: {e}")

        # Final fallback to DuckDuckGo
        try:
            sources = await self._web_search_duckduckgo_fallback(query)
            if sources:
                print(f"✅ DuckDuckGo fallback found {len(sources)} sources")
        except Exception as e:
            print(f"⚠️ All search fallbacks failed: {e}")

        return sources

    async def _web_search_duckduckgo_fallback(self, query: str) -> List[ResearchSource]:
        """Fallback DuckDuckGo search when Google CSE fails"""
        sources = []

        try:
            import aiohttp

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Process abstract if available
                        if data.get("Abstract") and data.get("AbstractURL"):
                            source = ResearchSource(
                                source_id=f"ddg_{hashlib.md5(data['AbstractURL'].encode()).hexdigest()[:8]}",
                                url=data["AbstractURL"],
                                title=data.get("Heading", "DuckDuckGo Abstract"),
                                content=data["Abstract"],
                                credibility_score=0.7,  # Slightly lower for fallback
                                relevance_score=0.8,
                                timestamp=datetime.now(),
                                source_type="web_fallback"
                            )
                            sources.append(source)

                        # Process related topics
                        for topic in data.get("RelatedTopics", [])[:2]:
                            if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                                source = ResearchSource(
                                    source_id=f"ddg_{hashlib.md5(topic['FirstURL'].encode()).hexdigest()[:8]}",
                                    url=topic["FirstURL"],
                                    title=topic.get("Text", "").split(" - ")[0],
                                    content=topic["Text"],
                                    credibility_score=0.6,
                                    relevance_score=0.7,
                                    timestamp=datetime.now(),
                                    source_type="web_fallback"
                                )
                                sources.append(source)

        except Exception as e:
            print(f"⚠️ DuckDuckGo fallback also failed: {e}")

        return sources

    async def _document_search(self, query: str, user_id: str) -> List[ResearchSource]:
        """Search local documents (mock implementation)"""
        # This would integrate with file system server to search documents
        return []  # No local documents for now

    async def _synthesize_finding(self, question: ResearchQuestion,
                                sources: List[ResearchSource]) -> ResearchFinding:
        """Synthesize research sources into a coherent finding"""

        # Extract key insights from sources
        key_insights = []
        supporting_sources = []

        for source in sources:
            # Simple insight extraction (would be enhanced with NLP)
            insights = self._extract_insights_from_content(source.content)
            key_insights.extend(insights)
            supporting_sources.append(source.source_id)

        # Generate summary
        summary = await self._generate_summary(question.question, key_insights)

        # Generate recommendations
        recommendations = await self._generate_recommendations(question, key_insights)

        # Calculate confidence level
        confidence = await self._calculate_confidence(sources, key_insights)

        # Extract related topics
        related_topics = await self._extract_related_topics(key_insights)

        finding = ResearchFinding(
            finding_id=f"finding_{question.question_id}",
            research_question_id=question.question_id,
            summary=summary,
            key_insights=key_insights[:5],  # Top 5 insights
            supporting_sources=supporting_sources,
            confidence_level=confidence,
            actionable_recommendations=recommendations,
            related_topics=related_topics,
            created_at=datetime.now()
        )

        return finding

    def _extract_insights_from_content(self, content: str) -> List[str]:
        """Extract key insights from source content"""
        # Simple sentence extraction - would be enhanced with NLP
        sentences = content.split('.')
        insights = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                insights.append(sentence)

        return insights[:3]  # Return top 3 insights per source

    async def _generate_summary(self, question: str, insights: List[str]) -> str:
        """Generate a summary from research insights"""
        if not insights:
            return f"No substantial information found for: {question}"

        # Simple summary generation
        return f"Research on '{question}' reveals: {'. '.join(insights[:3])}"

    async def _generate_recommendations(self, question: ResearchQuestion,
                                      insights: List[str]) -> List[str]:
        """Generate actionable recommendations from insights"""
        recommendations = []

        # Generate basic recommendations based on question type
        if question.question_type == "procedural":
            recommendations.append("Follow the documented best practices")
            recommendations.append("Start with a simple implementation")
        elif question.question_type == "factual":
            recommendations.append("Verify information with primary sources")
            recommendations.append("Consider multiple perspectives")
        elif question.question_type == "temporal":
            recommendations.append("Monitor for ongoing updates")
            recommendations.append("Set up alerts for new developments")

        return recommendations[:3]

    async def _calculate_confidence(self, sources: List[ResearchSource],
                                  insights: List[str]) -> float:
        """Calculate confidence level for research findings"""
        if not sources:
            return 0.0

        # Calculate average source credibility
        avg_credibility = sum(s.credibility_score for s in sources) / len(sources)

        # Factor in number of sources
        source_factor = min(1.0, len(sources) / 3)  # Optimal at 3+ sources

        # Factor in insight quality (simple length-based heuristic)
        insight_factor = min(1.0, len([i for i in insights if len(i) > 50]) / 3)

        confidence = (avg_credibility * 0.5) + (source_factor * 0.3) + (insight_factor * 0.2)
        return round(confidence, 2)

    async def _extract_related_topics(self, insights: List[str]) -> List[str]:
        """Extract related topics from insights"""
        # Simple topic extraction based on common words
        all_text = " ".join(insights).lower()
        words = all_text.split()

        # Filter for potential topics (longer words, not common words)
        common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        potential_topics = [word for word in words if len(word) > 4 and word not in common_words]

        # Return most frequent topics
        from collections import Counter
        topic_counts = Counter(potential_topics)
        return [topic for topic, count in topic_counts.most_common(5)]


class InformationSynthesizer:
    """Synthesizes research findings into actionable insights"""

    async def synthesize_research_findings(self, findings: List[ResearchFinding],
                                         synthesis_style: str = "comprehensive") -> Dict[str, Any]:
        """Synthesize multiple research findings into comprehensive insights"""

        if not findings:
            return {
                "summary": "No research findings to synthesize",
                "key_insights": [],
                "recommendations": [],
                "confidence": 0.0
            }

        # Combine all insights
        all_insights = []
        all_recommendations = []
        all_topics = []

        for finding in findings:
            all_insights.extend(finding.key_insights)
            all_recommendations.extend(finding.actionable_recommendations)
            all_topics.extend(finding.related_topics)

        # Remove duplicates and prioritize
        unique_insights = await self._deduplicate_insights(all_insights)
        unique_recommendations = await self._deduplicate_recommendations(all_recommendations)
        unique_topics = list(set(all_topics))

        # Generate overall summary
        overall_summary = await self._generate_overall_summary(findings, synthesis_style)

        # Calculate overall confidence
        overall_confidence = await self._calculate_overall_confidence(findings)

        # Identify knowledge gaps and next steps
        next_steps = await self._identify_next_steps(findings)

        synthesis = {
            "summary": overall_summary,
            "key_insights": unique_insights[:10],  # Top 10 insights
            "recommendations": unique_recommendations[:8],  # Top 8 recommendations
            "related_topics": unique_topics[:15],  # Top 15 related topics
            "confidence": overall_confidence,
            "next_steps": next_steps,
            "source_count": len(set(source for finding in findings for source in finding.supporting_sources)),
            "research_completeness": await self._assess_research_completeness(findings)
        }

        return synthesis

    async def _deduplicate_insights(self, insights: List[str]) -> List[str]:
        """Remove duplicate or very similar insights"""
        unique_insights = []
        seen_keywords = set()

        for insight in insights:
            # Simple deduplication based on key words
            words = set(insight.lower().split())
            if not any(word in seen_keywords for word in words if len(word) > 4):
                unique_insights.append(insight)
                seen_keywords.update(words)

        return unique_insights

    async def _deduplicate_recommendations(self, recommendations: List[str]) -> List[str]:
        """Remove duplicate recommendations"""
        seen = set()
        unique_recs = []

        for rec in recommendations:
            if rec.lower() not in seen:
                unique_recs.append(rec)
                seen.add(rec.lower())

        return unique_recs

    async def _generate_overall_summary(self, findings: List[ResearchFinding],
                                      style: str) -> str:
        """Generate an overall summary of research findings"""

        if style == "comprehensive":
            return f"Comprehensive research across {len(findings)} areas reveals multiple key insights and actionable recommendations. The research covered various aspects of the topic with varying confidence levels."
        elif style == "concise":
            return f"Research summary: {len(findings)} main findings with actionable insights identified."
        else:
            return f"Research completed with {len(findings)} findings synthesized."

    async def _calculate_overall_confidence(self, findings: List[ResearchFinding]) -> float:
        """Calculate overall confidence across all findings"""
        if not findings:
            return 0.0

        confidence_scores = [f.confidence_level for f in findings]
        return round(sum(confidence_scores) / len(confidence_scores), 2)

    async def _identify_next_steps(self, findings: List[ResearchFinding]) -> List[str]:
        """Identify potential next steps based on research findings"""
        next_steps = []

        # Analyze findings for gaps and opportunities
        low_confidence_areas = [f for f in findings if f.confidence_level < 0.7]

        if low_confidence_areas:
            next_steps.append("Conduct additional research in areas with low confidence")

        # Look for procedural next steps
        procedural_findings = [f for f in findings if "how to" in f.summary.lower()]
        if procedural_findings:
            next_steps.append("Begin implementation based on procedural guidance found")

        # Default next steps
        next_steps.extend([
            "Monitor for new developments in researched areas",
            "Apply insights to current situation",
            "Share findings with relevant stakeholders"
        ])

        return next_steps[:5]

    async def _assess_research_completeness(self, findings: List[ResearchFinding]) -> float:
        """Assess how complete the research appears to be"""
        # Simple heuristic based on number of findings and confidence
        base_score = min(1.0, len(findings) / 5)  # Diminishing returns after 5 findings

        # Factor in average confidence
        avg_confidence = sum(f.confidence_level for f in findings) / len(findings) if findings else 0

        completeness = (base_score * 0.6) + (avg_confidence * 0.4)
        return round(completeness, 2)


class AutonomousResearchToolServer(MCPToolServer):
    """Main autonomous research tool server"""

    def __init__(self, security_components: Optional[Dict[str, Any]] = None):
        # Define research operations
        operations = {
            # Knowledge Gap Detection
            "identify_knowledge_gaps": MCPOperation(
                name="identify_knowledge_gaps",
                parameters={
                    "conversation_context": {"type": "string", "description": "Current conversation context"},
                    "user_query": {"type": "string", "description": "User's current query"},
                    "confidence_threshold": {"type": "number", "default": 0.7}
                },
                security_level=SecurityLevel.LOW
            ),

            "analyze_conversation_for_learning_opportunities": MCPOperation(
                name="analyze_conversation_for_learning_opportunities",
                parameters={
                    "conversation_history": {"type": "string", "description": "Full conversation history"},
                    "max_gaps": {"type": "integer", "default": 5}
                },
                security_level=SecurityLevel.LOW
            ),

            # Research Planning & Execution
            "generate_research_questions": MCPOperation(
                name="generate_research_questions",
                parameters={
                    "knowledge_gap": {"type": "object", "description": "Knowledge gap to research"},
                    "max_questions": {"type": "integer", "default": 3}
                },
                security_level=SecurityLevel.LOW
            ),

            "create_research_plan": MCPOperation(
                name="create_research_plan",
                parameters={
                    "knowledge_gap": {"type": "object", "description": "Knowledge gap to research"},
                    "research_scope": {"type": "string", "enum": ["quick", "comprehensive", "deep"], "default": "comprehensive"},
                    "time_limit": {"type": "integer", "default": 300}
                },
                security_level=SecurityLevel.MEDIUM
            ),

            "execute_research_plan": MCPOperation(
                name="execute_research_plan",
                parameters={
                    "research_plan": {"type": "object", "description": "Research plan to execute"},
                    "progress_callback": {"type": "boolean", "default": False}
                },
                security_level=SecurityLevel.MEDIUM
            ),

            # Information Processing
            "synthesize_research_findings": MCPOperation(
                name="synthesize_research_findings",
                parameters={
                    "research_findings": {"type": "array", "description": "List of research findings"},
                    "synthesis_style": {"type": "string", "enum": ["comprehensive", "concise", "summary"], "default": "comprehensive"}
                },
                security_level=SecurityLevel.LOW
            ),

            "extract_key_insights": MCPOperation(
                name="extract_key_insights",
                parameters={
                    "research_data": {"type": "object", "description": "Research data to analyze"},
                    "focus_areas": {"type": "array", "default": None}
                },
                security_level=SecurityLevel.LOW
            ),

            "validate_information_quality": MCPOperation(
                name="validate_information_quality",
                parameters={
                    "source_data": {"type": "object", "description": "Source data to validate"},
                    "credibility_threshold": {"type": "number", "default": 0.8}
                },
                security_level=SecurityLevel.MEDIUM
            ),

            # Learning Integration
            "store_research_findings": MCPOperation(
                name="store_research_findings",
                parameters={
                    "insights": {"type": "object", "description": "Insights to store"},
                    "knowledge_category": {"type": "string", "description": "Category for organization"},
                    "confidence_level": {"type": "number", "description": "Confidence in findings"}
                },
                security_level=SecurityLevel.HIGH
            ),

            "update_knowledge_base": MCPOperation(
                name="update_knowledge_base",
                parameters={
                    "new_information": {"type": "object", "description": "New information to add"},
                    "related_topics": {"type": "array", "default": None}
                },
                security_level=SecurityLevel.HIGH
            ),

            "generate_learning_summary": MCPOperation(
                name="generate_learning_summary",
                parameters={
                    "research_session_id": {"type": "string", "description": "Research session to summarize"},
                    "include_sources": {"type": "boolean", "default": True}
                },
                security_level=SecurityLevel.LOW
            ),

            # Utility Operations
            "get_research_status": MCPOperation(
                name="get_research_status",
                parameters={
                    "session_id": {"type": "string", "description": "Research session ID"}
                },
                security_level=SecurityLevel.LOW
            )
        }

        super().__init__(
            name="autonomous_research_server",
            operations=operations
        )

        # Initialize security components
        self.command_whitelist = security_components.get('whitelist') if security_components else CommandWhitelistSystem()
        self.emergency_stop = security_components.get('emergency') if security_components else MultiChannelEmergencyStop()
        self.security_logger = security_components.get('logger') if security_components else EnhancedSecurityLogging()
        self.rollback_system = security_components.get('rollback') if security_components else RollbackRecoverySystem()
        self.rate_limiter = security_components.get('rate_limiter') if security_components else RateLimitingResourceControl()

        # Initialize research components
        self.conversation_analyzer = ConversationAnalyzer()
        self.question_generator = ResearchQuestionGenerator()
        self.research_executor = ResearchExecutor()
        self.information_synthesizer = InformationSynthesizer()

        # Research state
        self.research_sessions = {}
        self.knowledge_base = {}

        # Performance metrics
        self.research_metrics = {
            "total_research_sessions": 0,
            "successful_research_sessions": 0,
            "total_knowledge_gaps_identified": 0,
            "total_research_questions_generated": 0,
            "total_findings_synthesized": 0,
            "average_research_time": 0.0,
            "knowledge_base_size": 0
        }

    async def _validate_operation_security(self, operation: str, user_id: str) -> bool:
        """Validate operation against security systems"""
        # Check emergency stop
        if self.emergency_stop.is_emergency_active():
            return False

        # Check command whitelist
        if not await self.command_whitelist.is_command_allowed(f"research:{operation}"):
            return False

        # Check rate limiting
        if not await self.rate_limiter.check_rate_limit(user_id, operation):
            return False

        return True

    # Knowledge Gap Detection Operations

    async def identify_knowledge_gaps(self, conversation_context: str,
                                    user_query: str,
                                    confidence_threshold: float = 0.7,
                                    user_id: str = "anonymous") -> MCPResult:
        """Identify knowledge gaps from conversation context"""

        if not await self._validate_operation_security("identify_knowledge_gaps", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            gaps = await self.conversation_analyzer.identify_knowledge_gaps(
                conversation_context, user_query, confidence_threshold
            )

            self.research_metrics["total_knowledge_gaps_identified"] += len(gaps)

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "knowledge_gaps_identified",
                    {
                        "user_id": user_id,
                        "gaps_found": len(gaps),
                        "context_length": len(conversation_context)
                    }
                )

            # Convert knowledge gaps to serializable format
            serializable_gaps = []
            for gap in gaps:
                gap_dict = asdict(gap)
                gap_dict['detected_at'] = gap_dict['detected_at'].isoformat()
                gap_dict['gap_type'] = gap_dict['gap_type'].value
                serializable_gaps.append(gap_dict)

            return MCPResult(
                success=True,
                data={
                    "knowledge_gaps": serializable_gaps,
                    "total_gaps": len(gaps),
                    "confidence_threshold": confidence_threshold
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Knowledge gap identification failed: {str(e)}")

    async def analyze_conversation_for_learning_opportunities(self, conversation_history: str,
                                                            max_gaps: int = 5,
                                                            user_id: str = "anonymous") -> MCPResult:
        """Analyze full conversation history for learning opportunities"""

        if not await self._validate_operation_security("analyze_conversation", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Split conversation into segments for analysis
            segments = conversation_history.split('\n')
            all_gaps = []

            for segment in segments:
                if len(segment.strip()) > 20:  # Skip very short segments
                    gaps = await self.conversation_analyzer.identify_knowledge_gaps(
                        conversation_history, segment, 0.6
                    )
                    all_gaps.extend(gaps)

            # Remove duplicates and prioritize
            unique_gaps = await self._deduplicate_knowledge_gaps(all_gaps)
            top_gaps = sorted(unique_gaps, key=lambda g: g.priority, reverse=True)[:max_gaps]

            # Convert to serializable format
            serializable_opportunities = []
            for gap in top_gaps:
                gap_dict = asdict(gap)
                gap_dict['detected_at'] = gap_dict['detected_at'].isoformat()
                gap_dict['gap_type'] = gap_dict['gap_type'].value
                serializable_opportunities.append(gap_dict)

            return MCPResult(
                success=True,
                data={
                    "learning_opportunities": serializable_opportunities,
                    "total_opportunities": len(top_gaps),
                    "analysis_coverage": len(segments)
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Conversation analysis failed: {str(e)}")

    # Research Planning & Execution Operations

    async def generate_research_questions(self, knowledge_gap: Dict[str, Any],
                                        max_questions: int = 3,
                                        user_id: str = "anonymous") -> MCPResult:
        """Generate research questions from a knowledge gap"""

        if not await self._validate_operation_security("generate_questions", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Convert dict back to KnowledgeGap object
            gap_data = knowledge_gap.copy()
            # Handle gap_type conversion
            if isinstance(gap_data.get('gap_type'), str):
                gap_data['gap_type'] = KnowledgeGapType(gap_data['gap_type'])
            # Handle datetime conversion
            if isinstance(gap_data.get('detected_at'), str):
                gap_data['detected_at'] = datetime.fromisoformat(gap_data['detected_at'])

            gap = KnowledgeGap(**gap_data)

            questions = await self.question_generator.generate_research_questions(gap, max_questions)

            self.research_metrics["total_research_questions_generated"] += len(questions)

            # Convert to serializable format
            serializable_questions = []
            for q in questions:
                q_dict = asdict(q)
                q_dict['created_at'] = q_dict['created_at'].isoformat()
                serializable_questions.append(q_dict)

            return MCPResult(
                success=True,
                data={
                    "research_questions": serializable_questions,
                    "total_questions": len(questions),
                    "knowledge_gap_id": gap.gap_id
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Research question generation failed: {str(e)}")

    async def create_research_plan(self, knowledge_gap: Dict[str, Any],
                                 research_scope: str = "comprehensive",
                                 time_limit: int = 300,
                                 user_id: str = "anonymous") -> MCPResult:
        """Create a research execution plan"""

        if not await self._validate_operation_security("create_plan", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Convert dict to KnowledgeGap object
            gap_data = knowledge_gap.copy()
            # Handle gap_type conversion
            if isinstance(gap_data.get('gap_type'), str):
                gap_data['gap_type'] = KnowledgeGapType(gap_data['gap_type'])
            # Handle datetime conversion
            if isinstance(gap_data.get('detected_at'), str):
                gap_data['detected_at'] = datetime.fromisoformat(gap_data['detected_at'])

            gap = KnowledgeGap(**gap_data)

            # Generate research questions first
            questions = await self.question_generator.generate_research_questions(gap)

            # Create research plan
            scope = ResearchScope(research_scope)
            plan = await self.research_executor.create_research_plan(gap, questions, scope, time_limit)

            # Store the plan
            self.research_sessions[plan.plan_id] = plan

            # Convert to serializable format
            plan_dict = asdict(plan)
            plan_dict['created_at'] = plan_dict['created_at'].isoformat()
            plan_dict['research_scope'] = plan_dict['research_scope'].value
            plan_dict['status'] = plan_dict['status'].value

            # Convert nested research questions
            serializable_questions = []
            for q in plan_dict['research_questions']:
                q['created_at'] = q['created_at'].isoformat()
                serializable_questions.append(q)
            plan_dict['research_questions'] = serializable_questions

            return MCPResult(
                success=True,
                data={
                    "research_plan": plan_dict,
                    "estimated_time": sum(q.time_estimate for q in questions),
                    "question_count": len(questions)
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Research plan creation failed: {str(e)}")

    async def execute_research_plan(self, research_plan: Dict[str, Any],
                                  progress_callback: bool = False,
                                  user_id: str = "anonymous") -> MCPResult:
        """Execute a research plan"""

        if not await self._validate_operation_security("execute_research", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Convert dict to ResearchPlan object
            plan_data = research_plan.copy()

            # Convert nested objects
            plan_data['research_questions'] = [
                ResearchQuestion(**q) for q in plan_data['research_questions']
            ]
            plan_data['research_scope'] = ResearchScope(plan_data['research_scope'])
            plan_data['status'] = ResearchStatus(plan_data['status'])
            plan_data['created_at'] = datetime.fromisoformat(plan_data['created_at'])

            plan = ResearchPlan(**plan_data)

            self.research_metrics["total_research_sessions"] += 1
            start_time = time.time()

            # Execute research
            findings = await self.research_executor.execute_research_plan(plan, user_id)

            execution_time = time.time() - start_time
            self.research_metrics["average_research_time"] = (
                (self.research_metrics["average_research_time"] * (self.research_metrics["total_research_sessions"] - 1) + execution_time) /
                self.research_metrics["total_research_sessions"]
            )

            if findings:
                self.research_metrics["successful_research_sessions"] += 1
                self.research_metrics["total_findings_synthesized"] += len(findings)

            # Convert findings to serializable format
            serializable_findings = []
            for f in findings:
                f_dict = asdict(f)
                f_dict['created_at'] = f_dict['created_at'].isoformat()
                serializable_findings.append(f_dict)

            return MCPResult(
                success=True,
                data={
                    "research_findings": serializable_findings,
                    "execution_time": execution_time,
                    "plan_status": plan.status.value,
                    "findings_count": len(findings)
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Research execution failed: {str(e)}")

    # Information Processing Operations

    async def synthesize_research_findings(self, research_findings: List[Dict[str, Any]],
                                         synthesis_style: str = "comprehensive",
                                         user_id: str = "anonymous") -> MCPResult:
        """Synthesize research findings into coherent insights"""

        if not await self._validate_operation_security("synthesize_findings", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Convert dicts to ResearchFinding objects
            findings = []
            for finding_data in research_findings:
                finding_data['created_at'] = datetime.fromisoformat(finding_data['created_at'])
                findings.append(ResearchFinding(**finding_data))

            synthesis = await self.information_synthesizer.synthesize_research_findings(
                findings, synthesis_style
            )

            return MCPResult(
                success=True,
                data=synthesis
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Research synthesis failed: {str(e)}")

    async def extract_key_insights(self, research_data: Dict[str, Any],
                                 focus_areas: Optional[List[str]] = None,
                                 user_id: str = "anonymous") -> MCPResult:
        """Extract key insights from research data"""

        if not await self._validate_operation_security("extract_insights", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Simple insight extraction
            insights = []

            if "findings" in research_data:
                for finding in research_data["findings"]:
                    insights.extend(finding.get("key_insights", []))

            if "content" in research_data:
                # Extract insights from raw content
                content_insights = self._extract_insights_from_text(research_data["content"])
                insights.extend(content_insights)

            # Filter by focus areas if provided
            if focus_areas:
                filtered_insights = []
                for insight in insights:
                    if any(area.lower() in insight.lower() for area in focus_areas):
                        filtered_insights.append(insight)
                insights = filtered_insights

            return MCPResult(
                success=True,
                data={
                    "key_insights": insights[:10],  # Top 10 insights
                    "total_insights": len(insights),
                    "focus_areas": focus_areas
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Insight extraction failed: {str(e)}")

    async def validate_information_quality(self, source_data: Dict[str, Any],
                                         credibility_threshold: float = 0.8,
                                         user_id: str = "anonymous") -> MCPResult:
        """Validate information quality and credibility"""

        if not await self._validate_operation_security("validate_quality", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            if "sources" in source_data:
                sources = source_data["sources"]
                high_quality_sources = [s for s in sources if s.get("credibility_score", 0) >= credibility_threshold]

                validation_result = {
                    "total_sources": len(sources),
                    "high_quality_sources": len(high_quality_sources),
                    "quality_percentage": (len(high_quality_sources) / len(sources)) * 100 if sources else 0,
                    "meets_threshold": len(high_quality_sources) > 0
                }
            else:
                validation_result = {
                    "total_sources": 0,
                    "high_quality_sources": 0,
                    "quality_percentage": 0,
                    "meets_threshold": False
                }

            return MCPResult(
                success=True,
                data=validation_result
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Information quality validation failed: {str(e)}")

    def _extract_insights_from_text(self, text: str) -> List[str]:
        """Extract insights from raw text"""
        sentences = text.split('.')
        insights = []

        for sentence in sentences:
            sentence = sentence.strip()
            # Look for informative sentences
            if (len(sentence) > 30 and
                any(word in sentence.lower() for word in
                    ['important', 'key', 'significant', 'shows', 'indicates', 'reveals'])):
                insights.append(sentence)

        return insights

    # Learning Integration Operations

    async def store_research_findings(self, insights: Dict[str, Any],
                                    knowledge_category: str,
                                    confidence_level: float,
                                    user_id: str = "anonymous") -> MCPResult:
        """Store research findings in knowledge base"""

        if not await self._validate_operation_security("store_findings", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Store in knowledge base
            if knowledge_category not in self.knowledge_base:
                self.knowledge_base[knowledge_category] = []

            knowledge_entry = {
                "insights": insights,
                "confidence_level": confidence_level,
                "stored_at": datetime.now().isoformat(),
                "user_id": user_id
            }

            self.knowledge_base[knowledge_category].append(knowledge_entry)
            self.research_metrics["knowledge_base_size"] += 1

            return MCPResult(
                success=True,
                data={
                    "stored": True,
                    "category": knowledge_category,
                    "knowledge_base_size": self.research_metrics["knowledge_base_size"]
                }
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Knowledge storage failed: {str(e)}")

    async def generate_learning_summary(self, research_session_id: str,
                                      include_sources: bool = True,
                                      user_id: str = "anonymous") -> MCPResult:
        """Generate a summary of learning from research session"""

        if not await self._validate_operation_security("generate_summary", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            if research_session_id not in self.research_sessions:
                return MCPResult(success=False, error="Research session not found")

            session = self.research_sessions[research_session_id]

            summary = {
                "session_id": research_session_id,
                "research_scope": session.research_scope.value,
                "questions_researched": len(session.research_questions),
                "status": session.status.value,
                "learning_summary": f"Research session explored {len(session.research_questions)} questions about knowledge gaps.",
                "key_topics": [q.question for q in session.research_questions[:3]]
            }

            if include_sources:
                summary["source_types"] = session.source_types

            return MCPResult(
                success=True,
                data=summary
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Learning summary generation failed: {str(e)}")

    # Utility Operations

    async def get_research_status(self, session_id: str,
                                user_id: str = "anonymous") -> MCPResult:
        """Get status of a research session"""

        try:
            if session_id in self.research_sessions:
                session = self.research_sessions[session_id]
                return MCPResult(
                    success=True,
                    data={
                        "session_id": session_id,
                        "status": session.status.value,
                        "progress": "completed" if session.status == ResearchStatus.COMPLETED else "in_progress"
                    }
                )
            else:
                return MCPResult(success=False, error="Research session not found")

        except Exception as e:
            return MCPResult(success=False, error=f"Status check failed: {str(e)}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get research performance metrics"""
        return self.research_metrics.copy()

    async def _deduplicate_knowledge_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Remove duplicate knowledge gaps"""
        seen_contexts = set()
        unique_gaps = []

        for gap in gaps:
            # Simple deduplication based on context similarity
            context_key = gap.context.lower()[:100]  # First 100 chars
            if context_key not in seen_contexts:
                unique_gaps.append(gap)
                seen_contexts.add(context_key)

        return unique_gaps


async def create_autonomous_research_server(security_components: Optional[Dict[str, Any]] = None) -> AutonomousResearchToolServer:
    """Create and initialize autonomous research server"""
    server = AutonomousResearchToolServer(security_components)
    await server.start()
    return server


if __name__ == "__main__":
    # Example usage and testing
    async def demo_autonomous_research():
        """Demonstrate autonomous research capabilities"""
        print("🔬 AUTONOMOUS RESEARCH TOOL SERVER DEMO")
        print("=" * 60)

        server = await create_autonomous_research_server()

        try:
            # Demo conversation context
            conversation = "User mentioned they're working on a machine learning project but aren't sure about the latest deep learning frameworks. They want to build an image classifier but don't know which approach to use."
            user_query = "What's the best way to build an image classifier these days? I'm not familiar with the latest frameworks."

            # Step 1: Identify knowledge gaps
            print("🔍 Step 1: Identifying Knowledge Gaps")
            gap_result = await server.identify_knowledge_gaps(
                conversation_context=conversation,
                user_query=user_query,
                user_id="demo_user"
            )

            if gap_result.success:
                gaps = gap_result.data["knowledge_gaps"]
                print(f"   Found {len(gaps)} knowledge gaps")
                for i, gap in enumerate(gaps[:2], 1):
                    print(f"   Gap {i}: {gap['description'][:80]}...")

            # Step 2: Generate research questions
            if gaps:
                print("\n❓ Step 2: Generating Research Questions")
                question_result = await server.generate_research_questions(
                    knowledge_gap=gaps[0],
                    user_id="demo_user"
                )

                if question_result.success:
                    questions = question_result.data["research_questions"]
                    print(f"   Generated {len(questions)} research questions")
                    for i, q in enumerate(questions, 1):
                        print(f"   Q{i}: {q['question']}")

            # Step 3: Create research plan
            if gaps:
                print("\n📋 Step 3: Creating Research Plan")
                plan_result = await server.create_research_plan(
                    knowledge_gap=gaps[0],
                    research_scope="comprehensive",
                    user_id="demo_user"
                )

                if plan_result.success:
                    plan = plan_result.data["research_plan"]
                    print(f"   Research plan created: {plan['plan_id']}")
                    print(f"   Questions: {plan_result.data['question_count']}")
                    print(f"   Estimated time: {plan_result.data['estimated_time']} seconds")

            # Step 4: Execute research (mock)
            if gaps and plan_result.success:
                print("\n🔬 Step 4: Executing Research Plan")
                execution_result = await server.execute_research_plan(
                    research_plan=plan_result.data["research_plan"],
                    user_id="demo_user"
                )

                if execution_result.success:
                    findings = execution_result.data["research_findings"]
                    print(f"   Research completed in {execution_result.data['execution_time']:.2f}s")
                    print(f"   Generated {len(findings)} findings")

                    # Step 5: Synthesize findings
                    if findings:
                        print("\n🧠 Step 5: Synthesizing Research Findings")
                        synthesis_result = await server.synthesize_research_findings(
                            research_findings=findings,
                            user_id="demo_user"
                        )

                        if synthesis_result.success:
                            synthesis = synthesis_result.data
                            print(f"   Synthesis complete")
                            print(f"   Key insights: {len(synthesis['key_insights'])}")
                            print(f"   Recommendations: {len(synthesis['recommendations'])}")
                            print(f"   Overall confidence: {synthesis['confidence']}")

            # Get performance metrics
            print("\n📊 Performance Metrics")
            metrics = await server.get_performance_metrics()
            print(f"   Research sessions: {metrics['total_research_sessions']}")
            print(f"   Knowledge gaps identified: {metrics['total_knowledge_gaps_identified']}")
            print(f"   Research questions generated: {metrics['total_research_questions_generated']}")

        finally:
            await server.stop()

    # Run demo
    asyncio.run(demo_autonomous_research())