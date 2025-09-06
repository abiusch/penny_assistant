Voice Quality Upgrade: ElevenLabs Integration with Personality Awareness

MAJOR MILESTONE: Transformed Penny from robotic Google TTS to natural human-sounding voice

## What's New:
- ✅ ElevenLabs TTS integration with Rachel voice (rated 4/5 in testing)
- ✅ Personality-aware voice modulation (sassy, tech enthusiast, supportive, playful modes)
- ✅ Intelligent text chunking system prevents API timeouts
- ✅ Markdown/symbol cleaning for natural speech (no more "asterisk" pronunciation)
- ✅ TTS factory pattern for easy switching between voice engines
- ✅ Configuration-driven voice selection in penny_config.json

## Files Added/Modified:
- src/adapters/tts/elevenlabs_tts_adapter.py (NEW) - Main ElevenLabs integration
- src/adapters/tts/streaming_elevenlabs_tts.py (NEW) - Parallel chunk synthesis
- src/adapters/tts/tts_factory.py (NEW) - Voice engine selection
- penny_with_elevenlabs.py (NEW) - Demo script with ElevenLabs
- penny_config.json (MODIFIED) - Added ElevenLabs configuration
- scripts/penny_voice_optimizer.py (NEW) - Voice testing framework
- scripts/test_streaming_speed.py (NEW) - Performance comparison tools

## Technical Achievements:
- Personality detection from text content triggers appropriate voice settings
- Intelligent chunking splits long responses for better flow
- Comprehensive error handling with graceful fallbacks
- Caching system maintains performance while adding quality
- Drop-in replacement preserves existing pipeline compatibility

## User Experience Impact:
- Dramatic improvement in naturalness (robotic → human-sounding)
- Context-aware personality expression through voice
- Maintained conversation flow with optimized chunk timing
- Clean speech without markdown artifacts

## Next: Ready for real-world conversation testing with natural voice AI companion

This represents the completion of the voice quality upgrade roadmap priority.
