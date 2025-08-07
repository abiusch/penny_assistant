# llm_engine.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt_response(user_input, agent_mode=False):
    try:
        system_prompt = "You are PennyGPT, a sassy AI assistant with charm, sarcasm, and helpfulness."

        if agent_mode:
            system_prompt += " You are now in [AGENT_MODE], so break down multi-step tasks and narrate each one clearly before performing it."

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
        print(f"[ERROR_MODE] GPT call failed: {e}")
        return None

