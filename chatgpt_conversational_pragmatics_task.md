**Task for ChatGPT: Conversational Pragmatics Research & Implementation Guide**

You are tasked with conducting comprehensive research using web search and repository analysis to create an implementation guide for conversational pragmatics in AI systems. This will be integrated into an advanced AI companion named Penny to improve her conversational understanding beyond surface-level pattern matching.

**MANDATORY RESEARCH ACTIVITIES:**

**Phase 1: Literature Search & Repository Analysis**
1. **Search for recent academic papers (2020-2025) on:**
   - "conversational pragmatics computational linguistics"
   - "dialogue state tracking neural networks"
   - "intent recognition multi-turn conversation"
   - "theory of mind artificial intelligence"
   - "speech act classification deep learning"

2. **Find and analyze GitHub repositories related to:**
   - Conversational AI frameworks (Rasa, Botpress, DeepPavlov)
   - Dialogue systems with pragmatic understanding
   - Multi-turn conversation management
   - Intent classification beyond simple Q&A

3. **Search for industry implementations:**
   - Google's LaMDA conversation abilities
   - Anthropic's Constitutional AI conversational training
   - OpenAI's ChatGPT conversation management
   - Meta's BlenderBot dialogue research

**Phase 2: Specific Technical Research**
1. **Search for papers on the exact problem:**
   - "ask me anything" vs "I'll ask you anything" disambiguation
   - Conversational role reversal detection
   - User intention inference in dialogue systems

2. **Find existing codebases that solve similar problems:**
   - Intent classification libraries
   - Conversation state management frameworks
   - Dialogue act recognition systems

3. **Research training datasets:**
   - MultiWOZ for dialogue state tracking
   - PersonaChat for personality-consistent conversation
   - DailyDialog for natural conversation patterns
   - Any datasets specifically for pragmatic understanding

**RESEARCH DELIVERABLES:**

**Section 1: Literature Review with Citations**
- Cite at least 5 recent papers (2020+) on conversational pragmatics
- Include DOI links and key findings from each paper
- Identify the most promising approaches with empirical results

**Section 2: Existing Solution Analysis**
- Document at least 3 GitHub repositories that address similar problems
- Include repository URLs, star counts, and last update dates
- Analyze code quality, documentation, and integration feasibility

**Section 3: Dataset Requirements**
- Identify specific datasets available for training pragmatic understanding
- Include download links, licensing information, and data format details
- Recommend the best datasets for the specific "ask me" problem

**Section 4: Technical Implementation Plan**
Based on your research findings, create:
- Architecture recommendations using proven approaches from literature
- Code examples adapted from existing repositories
- Training procedures based on successful academic implementations
- Performance benchmarks from published results

**SEARCH STRATEGIES TO USE:**

1. **Academic Search:**
   - Use Google Scholar, arXiv, ACL Anthology
   - Search terms: "pragmatics + dialogue systems", "intent + conversation + AI"
   - Focus on ACL, EMNLP, NAACL conference papers

2. **Repository Search:**
   - GitHub search with keywords: "conversation pragmatics", "dialogue state tracking", "intent classification"
   - Look for repos with >100 stars and recent commits
   - Check "awesome lists" for conversational AI

3. **Industry Research:**
   - Search for technical blogs from AI companies
   - Look for open-sourced models and training procedures
   - Find case studies of successful conversational AI implementations

**VALIDATION REQUIREMENTS:**

- Every claim must be backed by a specific citation or repository link
- Include actual code snippets from found repositories where relevant
- Provide empirical performance numbers where available
- Note any limitations or gaps in current research

**OUTPUT FORMAT:**

Create a research report with:
1. **Executive Summary** - Key research findings and recommended approach
2. **Literature Analysis** - Detailed review of found papers with citations
3. **Repository Evaluation** - Analysis of relevant codebases with links
4. **Dataset Assessment** - Available training data with access information
5. **Implementation Roadmap** - Step-by-step plan based on research findings
6. **Resource Links** - Complete bibliography with URLs and access information

**SUCCESS CRITERIA:**
The research must identify concrete, proven approaches that can be implemented, not theoretical frameworks. Focus on finding existing solutions to similar problems that can be adapted for Penny's specific conversational understanding challenges.

**Section 1: Conversational Context Framework**
- Data structures for tracking conversational state across multiple turns
- Algorithms for detecting conversational role reversals (when user wants AI to ask questions)
- Methods for maintaining conversation goals and participant intentions
- Implementation of conversational memory that goes beyond simple history

**Section 2: Intent Classification System**
- Taxonomy of conversational intents beyond information-seeking
- Classification framework for distinguishing:
  * Information requests vs invitation for questions
  * Validation-seeking vs genuine curiosity
  * Social bonding vs task completion
- Training data requirements and labeling guidelines

**Section 3: Dynamic Response Strategy Selection**
- Decision trees for choosing between answering vs asking
- Algorithms for detecting when users want to share vs receive information
- Methods for recognizing implicit invitations and social cues
- Framework for adapting response style based on conversational context

**Section 4: Integration with Existing Personality Systems**
- How conversational pragmatics interact with dynamic personality states
- Methods for maintaining personality consistency while adapting conversational role
- Integration points with ML learning systems for improving conversational understanding
- Fallback mechanisms when pragmatic understanding fails

**TECHNICAL SPECIFICATIONS:**

**Input Requirements:**
- Current conversation history (last N turns)
- User utterance with linguistic analysis
- Conversation metadata (duration, topic, participant roles)
- Personality state information

**Output Requirements:**
- Conversational intent classification
- Recommended response strategy
- Confidence scores for pragmatic interpretations
- Context updates for next turn

**Performance Criteria:**
- Accuracy in detecting role reversal situations (user wanting AI to ask questions)
- Consistency with personality while adapting conversational behavior
- Graceful degradation when pragmatic understanding is uncertain
- Integration feasibility with existing ML personality learning

**DELIVERABLE FORMAT:**

Create a structured document with:
1. **Executive Summary** - Key findings and implementation approach
2. **Literature Review** - Academic foundations and current research
3. **Technical Architecture** - Detailed system design and algorithms
4. **Implementation Guide** - Step-by-step integration instructions
5. **Training Data Requirements** - Specifications for conversation datasets
6. **Evaluation Metrics** - Methods for measuring conversational pragmatics performance
7. **Integration Roadmap** - Phased approach for adding to existing Penny system

**CONSTRAINTS:**
- Must integrate with existing ML personality core and dynamic states system
- Should maintain computational efficiency for real-time conversation
- Must include fallback mechanisms for uncertain pragmatic interpretation
- Should preserve Penny's existing personality while improving conversational intelligence

**SUCCESS CRITERIA:**
The final implementation should enable Penny to:
- Correctly identify when "ask me anything" means the user wants to be questioned
- Recognize social cues for conversation role transitions
- Maintain appropriate conversational initiative based on context
- Ask engaging, contextually appropriate questions about user experiences
- Adapt questioning style to match current personality state

Focus on practical, implementable solutions rather than purely theoretical frameworks. The goal is actionable technical guidance that can be coded into Penny's existing architecture.