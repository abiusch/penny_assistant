#!/usr/bin/env python3
"""
Penny Web Interface - Flask Backend
Simple HTTP server that exposes Penny via REST API

SECURITY NOTE:
- Default: localhost-only (127.0.0.1) - Most secure
- To enable network access: Set ALLOW_NETWORK=True
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import asyncio
from pathlib import Path

# Set HuggingFace cache to local project directory BEFORE any imports
os.environ['HF_HOME'] = str(Path(__file__).parent.parent / '.cache' / 'huggingface')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_first_pipeline import ResearchFirstPipeline
from personality_tracker import PersonalityTracker

# Phase 3A Week 2: Milestone & Achievement System
try:
    from src.personality.personality_milestone_tracker import PersonalityMilestoneTracker
    milestone_tracker = PersonalityMilestoneTracker()
    MILESTONES_AVAILABLE = True
except ImportError:
    milestone_tracker = None
    MILESTONES_AVAILABLE = False

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for local development

# SECURITY CONFIGURATION
# Set to True to allow access from other devices on your network
# WARNING: Anyone on your WiFi can access Penny if enabled
ALLOW_NETWORK = os.environ.get('PENNY_ALLOW_NETWORK', 'False').lower() == 'true'

# Initialize Penny
print("Initializing Penny's pipeline...")
pipeline = ResearchFirstPipeline()
personality_tracker = PersonalityTracker()
print("✅ Penny initialized successfully!")
if MILESTONES_AVAILABLE:
    print("🏆 Milestone & Achievement System enabled")

@app.route('/')
def index():
    """Serve the main HTML interface"""
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the web interface"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        print(f"\n📝 User: {user_message}")
        print("=" * 60)

        # Process message through Penny's pipeline using state machine
        from core.pipeline import State
        pipeline.state = State.THINKING

        # Call think() which should print debug info from research_first_pipeline.py
        response_text = pipeline.think(user_message)

        print("=" * 60)
        print(f"🤖 Penny: {response_text[:100]}...")

        # Extract actual research status from pipeline
        research_triggered = getattr(pipeline, 'last_research_triggered', False)
        research_success = getattr(pipeline, 'last_research_success', False)

        print(f"🔍 Research triggered: {research_triggered}")
        print(f"✅ Research successful: {research_success}")

        # Extract metadata for display
        metadata = {
            'research': research_success,  # Only show as "researched" if actually successful
            'research_attempted': research_triggered,
            'adjustments': [],  # TODO: Extract from personality post-processor
        }

        # Get personality info
        personality = get_personality_info()

        return jsonify({
            'response': response_text,
            'metadata': metadata,
            'personality': personality
        })
    
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/personality', methods=['GET'])
def personality():
    """Get current personality state"""
    try:
        info = get_personality_info()
        return jsonify(info)
    except Exception as e:
        print(f"Error getting personality info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/achievements', methods=['GET'])
def achievements():
    """Get user achievements (Phase 3A Week 2)"""
    try:
        if not MILESTONES_AVAILABLE or not milestone_tracker:
            return jsonify({'achievements': [], 'available': False})

        user_achievements = milestone_tracker.get_achievements(user_id="default")
        return jsonify({
            'achievements': user_achievements,
            'available': True,
            'total_count': len(user_achievements)
        })
    except Exception as e:
        print(f"Error getting achievements: {e}")
        return jsonify({'error': str(e), 'available': False}), 500

def get_personality_info():
    """Helper to get personality information"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state = loop.run_until_complete(
            personality_tracker.get_current_personality_state()
        )
        loop.close()

        # Extract key metrics - state is dict of PersonalityDimension objects
        formality = state.get('communication_formality')
        tech = state.get('technical_depth_preference')

        # Get vocabulary count
        vocab_count = len(state) if state else 0

        # Get cache statistics (Phase 3A)
        cache_stats = personality_tracker.get_cache_stats()

        result = {
            'formality': f"{formality.current_value:.2f}" if formality else "0.50",
            'technical_depth': f"{tech.current_value:.2f}" if tech else "0.50",
            'vocabulary_count': vocab_count,
            'confidence': f"{formality.confidence:.2f}" if formality else "0.00"
        }

        # Add cache stats if available
        if cache_stats:
            result['cache'] = {
                'hit_rate': f"{cache_stats.get('hit_rate', 0) * 100:.1f}%",
                'hits': cache_stats.get('hits', 0),
                'misses': cache_stats.get('misses', 0)
            }

        return result
    except Exception as e:
        print(f"Error in get_personality_info: {e}")
        return {
            'formality': '--',
            'technical_depth': '--',
            'vocabulary_count': '--',
            'confidence': '--'
        }

if __name__ == '__main__':
    # Determine host based on security setting
    host = '0.0.0.0' if ALLOW_NETWORK else '127.0.0.1'
    security_mode = "Network Accessible" if ALLOW_NETWORK else "Localhost Only (Secure)"
    
    print("=" * 60)
    print("🤖 Penny Web Interface Starting...")
    print("=" * 60)
    print()
    print(f"🔒 Security Mode: {security_mode}")
    print()
    print("📱 Open your browser to: http://localhost:5001")
    print()
    if ALLOW_NETWORK:
        print("⚠️  WARNING: Network access enabled!")
        print("   Anyone on your WiFi can access Penny.")
        print()
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"   Other devices: http://{local_ip}:5001")
        print()
    else:
        print("✅ Secure: Only accessible on this computer")
        print("   To enable network access: export PENNY_ALLOW_NETWORK=true")
        print()
    
    print("Features:")
    print("  • Beautiful chat interface")
    print("  • Real-time personality tracking")
    print("  • Debug panel for development")
    print("  • Code syntax highlighting")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    app.run(host=host, port=5001, debug=False)
