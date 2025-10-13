# llm_engine.py
import os
from openai import OpenAI
from personality_prompt_builder import get_personality_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt_response(user_input, agent_mode=False, context=None, use_personality=True):
    """
    Generate GPT response with optional personality awareness

    Args:
        user_input: User's message
        agent_mode: Enable agent mode for task breakdown
        context: Optional context dict (time_of_day, mood, etc.)
        use_personality: Use learned personality preferences (default: True)

    Returns:
        Response string or None on error
    """
    try:
        # Build system prompt with personality if enabled
        if use_personality:
            try:
                base = "You are Penny, an AI assistant"
                if agent_mode:
                    base += " in AGENT MODE - break down multi-step tasks and narrate each step clearly"

                system_prompt = get_personality_prompt(base, context)
                print(f"🎭 Personality applied: Using learned preferences (confidence check passed)")

            except Exception as e:
                # Fallback to basic prompt if personality system fails
                print(f"⚠️ Personality system unavailable: {e}")
                system_prompt = "You are Penny, a sassy AI assistant with charm, sarcasm, and helpfulness."
                if agent_mode:
                    system_prompt += " You are now in [AGENT_MODE], so break down multi-step tasks and narrate each one clearly before performing it."
        else:
            # Use basic prompt without personality
            system_prompt = "You are Penny, a sassy AI assistant with charm, sarcasm, and helpfulness."
            if agent_mode:
                system_prompt += " You are now in [AGENT_MODE], so break down multi-step tasks and narrate each one clearly before performing it."

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.6,  # Lower for constraint adherence (was 0.8)
            presence_penalty=0.5,  # Reduce repetitive enthusiasm
            frequency_penalty=0.3,  # Encourage varied phrasing
            max_tokens=400,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[ERROR_MODE] GPT call failed: {e}")
        return None

