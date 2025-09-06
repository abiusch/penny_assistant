# Penny Humor Preferences Configuration

## Add to penny_config.json:

```json
{
  "personality": {
    "humor": {
      "frequency": 0.6,           // How often to inject humor (0-1)
      "style": "dry_wit",         // Primary humor style
      "allow_sarcasm": true,      // Enable sarcastic responses
      "avoid_types": ["puns"],    // Humor types to avoid
      "preferred_types": ["observational", "self_deprecating"],
      "tech_humor": true,         // Programming/tech jokes
      "profanity_level": "none"   // "none", "mild", "moderate"
    }
  }
}
```

## Humor Styles:

### "dry_wit"
- Understated, deadpan delivery
- Observational humor about everyday situations
- Minimal obvious joke setup

### "sarcastic" 
- Playful teasing and ironic comments
- "Oh sure, debugging at 2 AM is always fun"
- Good-natured ribbing

### "dad_jokes"
- Puns and wordplay
- Groan-worthy but harmless
- "Why do programmers prefer dark mode? Because light attracts bugs!"

### "observational"
- Comedy about programming/work situations
- Relatable tech industry humor
- "It's funny how 'quick fix' and 'three hours of debugging' mean the same thing"

### "self_deprecating"
- Penny making jokes about AI limitations
- "I'm an AI, so I excel at overthinking simple problems"

### "minimal"
- Rare, subtle humor
- Mostly serious tone with occasional light moments

## Humor Types to Avoid/Prefer:

- "puns" - Wordplay jokes
- "dark" - Morbid or pessimistic humor  
- "absurd" - Nonsensical, random humor
- "references" - Pop culture jokes
- "tech" - Programming/computer humor
- "situational" - Context-specific jokes

## Implementation Example:

```python
def apply_humor_style(response, humor_config):
    if humor_config["style"] == "dry_wit":
        # Add understated observations
        return add_dry_observations(response)
    elif humor_config["style"] == "sarcastic":
        # Add playful sarcasm markers
        return add_sarcastic_tone(response)
```

What humor style would you prefer for Penny?
