#!/usr/bin/env python3
"""
Personality Response Integrator
Integrates personality-aware prompting into Penny's response generation
"""

import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from personality_prompt_builder import PersonalityPromptBuilder, get_personality_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class PersonalityAwareLLMEngine:
    """LLM engine that uses learned personality preferences"""

    def __init__(self):
        self.prompt_builder = PersonalityPromptBuilder()
        self.client = client

    async def get_personality_response(
        self,
        user_input: str,
        agent_mode: bool = False,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate response with personality-aware prompting

        Args:
            user_input: User's message
            agent_mode: Whether in agent mode (task breakdown)
            context: Contextual information (time, mood, etc.)
            conversation_history: Previous messages for context

        Returns:
            Personality-aware response
        """
        try:
            # Build personality-aware system prompt
            base_identity = "You are Penny, an AI assistant"

            if agent_mode:
                base_identity += " in AGENT MODE - break down tasks and narrate each step"

            system_prompt = await self.prompt_builder.build_personality_prompt(
                base_prompt=base_identity,
                context=context
            )

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    messages.append(msg)

            # Add current user input
            messages.append({"role": "user", "content": user_input})

            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.8,  # Keep creative for personality
                max_tokens=400,
            )

            response_text = response.choices[0].message.content

            # Optional: Post-process to inject learned slang naturally
            # (Could be expanded based on effectiveness tracking)

            return response_text

        except Exception as e:
            print(f"❌ Personality-aware response failed: {e}")
            # Fallback to basic response
            return None

    def get_personality_response_sync(
        self,
        user_input: str,
        agent_mode: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Synchronous wrapper for personality-aware responses"""
        import asyncio
        try:
            return asyncio.run(
                self.get_personality_response(user_input, agent_mode, context)
            )
        except Exception as e:
            print(f"❌ Sync personality response failed: {e}")
            return None


# Drop-in replacement for existing get_gpt_response
def get_gpt_response_with_personality(
    user_input: str,
    agent_mode: bool = False,
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Drop-in replacement for get_gpt_response() with personality awareness

    Usage:
        # In your existing code, replace:
        # response = get_gpt_response(user_input, agent_mode)

        # With:
        from personality_response_integrator import get_gpt_response_with_personality
        response = get_gpt_response_with_personality(user_input, agent_mode, context)
    """
    engine = PersonalityAwareLLMEngine()
    return engine.get_personality_response_sync(user_input, agent_mode, context)


# For direct import compatibility
def get_gpt_response(user_input: str, agent_mode: bool = False) -> Optional[str]:
    """
    Direct replacement - automatically uses personality if available
    Falls back to basic response if personality system fails
    """
    try:
        # Try personality-aware response
        response = get_gpt_response_with_personality(user_input, agent_mode)
        if response:
            return response
    except Exception as e:
        print(f"⚠️ Personality system unavailable, using fallback: {e}")

    # Fallback to basic response
    try:
        system_prompt = "You are Penny, a sassy AI assistant with charm, sarcasm, and helpfulness."
        if agent_mode:
            system_prompt += " You are now in [AGENT_MODE], so break down multi-step tasks clearly."

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.8,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ GPT call failed: {e}")
        return None


def demonstrate_personality_difference():
    """Show the difference personality makes in responses"""
    test_input = "what up mofo, explain async functions"

    print("🧪 PERSONALITY INTEGRATION DEMO")
    print("=" * 70)
    print(f"\n💬 User Input: '{test_input}'")

    # Show what prompts are being used
    from personality_prompt_builder import PersonalityPromptBuilder
    builder = PersonalityPromptBuilder()
    examples = builder.get_example_comparison()

    print("\n📋 WITHOUT PERSONALITY (Current State):")
    print(examples['before'])
    print("\n📝 Response would be: Generic, corporate, no personality")

    print("\n\n✨ WITH PERSONALITY (After Integration):")
    print(examples['after_casual'][:300] + "...")
    print("\n📝 Response would be: Casual, sassy, matches user's energy")

    print("\n" + "=" * 70)
    print("\n🎯 INTEGRATION STEPS:")
    print("1. Replace llm_engine.py's get_gpt_response with personality version")
    print("2. Personality automatically loaded from tracking database")
    print("3. Prompts dynamically adjusted based on learned preferences")
    print("4. Responses actually match user's communication style!")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demonstrate_personality_difference()
