#!/usr/bin/env python3
"""
PennyGPT Metrics Dashboard Server
Simple web server to serve the metrics dashboard
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

try:
    from aiohttp import web, WSMsgType
    from aiohttp.web import Request, Response, WebSocketResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from metrics_collector import MetricsCollector


class DashboardServer:
    """Web server for PennyGPT metrics dashboard."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.collector = MetricsCollector()
        self.app = None
        self.websockets = []
        
    async def index_handler(self, request: Request) -> Response:
        """Serve the main dashboard HTML."""
        dashboard_file = Path(__file__).parent / "dashboard.html"
        
        # If dashboard.html doesn't exist, create it from our artifact
        if not dashboard_file.exists():
            # Create a basic dashboard file
            dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PennyGPT Metrics Dashboard</title>
    <style>
        body { font-family: system-ui; background: #1a1a2e; color: white; margin: 0; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; }
        .metric-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .status-healthy { color: #00ff00; }
        .status-degraded { color: #ffff00; }
        .status-unhealthy { color: #ff0000; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 PennyGPT Metrics Dashboard</h1>
        <div id="overall-status">Loading...</div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>🔌 LM Studio</h3>
            <div class="metric-value" id="lm-time">--</div>
            <div id="lm-status">--</div>
        </div>
        
        <div class="metric-card">
            <h3>🧠 LLM Completion</h3>
            <div class="metric-value" id="llm-time">--</div>
            <div id="llm-status">--</div>
        </div>
        
        <div class="metric-card">
            <h3>🔊 TTS Engine</h3>
            <div class="metric-value" id="tts-time">--</div>
            <div id="tts-status">--</div>
        </div>
        
        <div class="metric-card">
            <h3>🎙️ STT Engine</h3>
            <div class="metric-value" id="stt-time">--</div>
            <div id="stt-status">--</div>
        </div>
        
        <div class="metric-card">
            <h3>🎵 Audio Devices</h3>
            <div class="metric-value" id="audio-time">--</div>
            <div id="audio-status">--</div>
        </div>
        
        <div class="metric-card">
            <h3>⚡ Performance</h3>
            <div class="metric-value" id="requests">0</div>
            <div>Total Requests</div>
        </div>
    </div>
    
    <script>
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                // Update overall status
                document.getElementById('overall-status').textContent = `System: ${data.system_health}`;
                document.getElementById('overall-status').className = `status-${data.system_health.toLowerCase()}`;
                
                // Update individual metrics
                if (data.response_times) {
                    document.getElementById('lm-time').textContent = `${data.response_times.lm_studio?.toFixed(1) || 0}ms`;
                    document.getElementById('llm-time').textContent = `${data.response_times.llm_completion?.toFixed(0) || 0}ms`;
                    document.getElementById('tts-time').textContent = `${data.response_times.tts?.toFixed(0) || 0}ms`;
                    document.getElementById('stt-time').textContent = `${data.response_times.stt?.toFixed(0) || 0}ms`;
                    document.getElementById('audio-time').textContent = `${data.response_times.audio?.toFixed(0) || 0}ms`;
                }
                
                // Update statuses
                if (data.component_statuses) {
                    Object.entries(data.component_statuses).forEach(([name, status]) => {
                        const element = document.getElementById(`${name.toLowerCase().replace(' ', '-')}-status`);
                        if (element) {
                            element.textContent = status;
                            element.className = `status-${status.toLowerCase()}`;
                        }
                    });
                }
                
                // Update totals
                if (data.totals) {
                    document.getElementById('requests').textContent = data.totals.requests || 0;
                }
                
            } catch (error) {
                console.error('Error updating metrics:', error);
                document.getElementById('overall-status').textContent = 'Error loading metrics';
            }
        }
        
        // Update every 5 seconds
        updateMetrics();
        setInterval(updateMetrics, 5000);
    </script>
</body>
</html>"""
            
            with open(dashboard_file, 'w') as f:
                f.write(dashboard_html)
        
        with open(dashboard_file, 'r') as f:
            html_content = f.read()
        
        return Response(text=html_content, content_type='text/html')
    
    async def metrics_api_handler(self, request: Request) -> Response:
        """API endpoint for current metrics."""
        try:
            metrics = self.collector.get_metrics_summary()
            return Response(
                text=json.dumps(metrics, default=str),
                content_type='application/json'
            )
        except Exception as e:
            return Response(
                text=json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500
            )
    
    async def health_api_handler(self, request: Request) -> Response:
        """API endpoint for health check."""
        try:
            # Run a quick health check
            health_status = await self.collector.health_monitor.check_all_components()
            
            # Convert to JSON-serializable format
            health_data = {}
            for name, health in health_status.items():
                health_data[name] = {
                    'status': health.status.value,
                    'response_time_ms': health.response_time_ms,
                    'error': health.error,
                    'details': health.details
                }
            
            return Response(
                text=json.dumps(health_data, default=str),
                content_type='application/json'
            )
        except Exception as e:
            return Response(
                text=json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500
            )
    
    def create_app(self):
        """Create the web application."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for the dashboard server. Install with: pip install aiohttp")
        
        self.app = web.Application()
        
        # Routes
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/metrics', self.metrics_api_handler)
        self.app.router.add_get('/api/health', self.health_api_handler)
        
        return self.app
    
    async def start_server(self):
        """Start the web server."""
        print(f"🌐 Starting PennyGPT Dashboard Server on http://localhost:{self.port}")
        
        # Start metrics collection
        self.collector.start_collection()
        
        # Create and start web app
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        print(f"🎉 Dashboard available at: http://localhost:{self.port}")
        print(f"📊 API endpoints:")
        print(f"   http://localhost:{self.port}/api/metrics")
        print(f"   http://localhost:{self.port}/api/health")
        print(f"\n🔄 Metrics collection running in background")
        print("Press Ctrl+C to stop")
        
        try:
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping server...")
            self.collector.stop_collection()
            await runner.cleanup()
            print("👋 Server stopped!")


def main():
    """Main entry point."""
    if not AIOHTTP_AVAILABLE:
        print("❌ Missing dependency: aiohttp")
        print("📦 Install with: pip install aiohttp")
        print("💡 Or use the simple metrics collector: python3 metrics_collector.py")
        return 1
    
    # Parse port argument
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default 8080.")
    
    # Start server
    server = DashboardServer(port=port)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
