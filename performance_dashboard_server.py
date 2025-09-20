#!/usr/bin/env python3
"""
Real-time Performance Dashboard Server for LM Studio Monitoring
Task A1.5.4: Performance Monitoring Integration (Day 4)

Provides web-based dashboard for real-time performance monitoring with:
- Live metrics visualization
- Alert notifications
- Health status indicators
- Historical trend analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
from aiohttp import web, WSMsgType
import aiohttp_cors
import weakref

from lm_studio_performance_monitor import (
    LMStudioPerformanceMonitor,
    PerformanceDashboard,
    PerformanceAlert,
    AlertSeverity,
    ConnectionStatus
)


class PerformanceDashboardServer:
    """
    Web server for real-time performance monitoring dashboard
    """

    def __init__(self,
                 monitor: LMStudioPerformanceMonitor,
                 dashboard: PerformanceDashboard,
                 port: int = 8080,
                 host: str = "localhost"):
        self.monitor = monitor
        self.dashboard = dashboard
        self.port = port
        self.host = host

        # WebSocket connections for real-time updates
        self.websocket_connections = weakref.WeakSet()

        # Dashboard update interval (seconds)
        self.update_interval = 5

        # Server state
        self.app = None
        self.server_task = None
        self.update_task = None

        # Add alert callback to monitor
        self.monitor.add_alert_callback(self._handle_new_alert)

    async def start_server(self):
        """Start the dashboard web server"""
        # Create aiohttp application
        self.app = web.Application()

        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # Add routes
        self.app.router.add_get('/', self._handle_dashboard)
        self.app.router.add_get('/api/metrics', self._handle_api_metrics)
        self.app.router.add_get('/api/alerts', self._handle_api_alerts)
        self.app.router.add_get('/api/health', self._handle_api_health)
        self.app.router.add_get('/api/historical/{metric_type}', self._handle_api_historical)
        self.app.router.add_get('/api/report', self._handle_api_report)
        self.app.router.add_get('/ws', self._handle_websocket)
        self.app.router.add_static('/static', str(Path(__file__).parent / 'static'), name='static')

        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

        # Start server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        # Start update task
        self.update_task = asyncio.create_task(self._update_loop())

        logging.info(f"Performance dashboard server started at http://{self.host}:{self.port}")

    async def stop_server(self):
        """Stop the dashboard web server"""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        if self.app:
            await self.app.shutdown()
            await self.app.cleanup()

    async def _handle_dashboard(self, request):
        """Serve the main dashboard HTML page"""
        html_content = self._generate_dashboard_html()
        return web.Response(text=html_content, content_type='text/html')

    async def _handle_api_metrics(self, request):
        """API endpoint for current metrics"""
        try:
            metrics = await self.dashboard.get_dashboard_data()
            return web.json_response(metrics)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_api_alerts(self, request):
        """API endpoint for active alerts"""
        try:
            alerts = [
                {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity.name,
                    'metric_type': alert.metric_type.value,
                    'description': alert.description,
                    'timestamp': alert.timestamp.isoformat(),
                    'current_value': alert.current_value,
                    'threshold_value': alert.threshold_value,
                    'recommended_action': alert.recommended_action
                }
                for alert in self.monitor.active_alerts.values()
            ]
            return web.json_response({'alerts': alerts})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_api_health(self, request):
        """API endpoint for connection health"""
        try:
            health_data = {
                'status': self.monitor.connection_health.status.value,
                'uptime_percentage': self.monitor.connection_health.uptime_percentage,
                'average_response_time': self.monitor.connection_health.average_response_time,
                'consecutive_failures': self.monitor.connection_health.consecutive_failures,
                'last_successful_request': (
                    self.monitor.connection_health.last_successful_request.isoformat()
                    if self.monitor.connection_health.last_successful_request else None
                ),
                'last_error': self.monitor.connection_health.last_error
            }
            return web.json_response(health_data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_api_historical(self, request):
        """API endpoint for historical metrics"""
        try:
            metric_type_str = request.match_info['metric_type']
            hours = int(request.query.get('hours', 24))

            from lm_studio_performance_monitor import PerformanceMetricType
            metric_type = PerformanceMetricType(metric_type_str)

            historical_data = await self.monitor.get_historical_metrics(metric_type, hours)
            return web.json_response({'data': historical_data})
        except ValueError as e:
            return web.json_response({'error': f'Invalid metric type: {e}'}, status=400)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_api_report(self, request):
        """API endpoint for performance reports"""
        try:
            hours = int(request.query.get('hours', 24))
            report = await self.monitor.generate_performance_report(hours)
            return web.json_response(report)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_websocket(self, request):
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Add to active connections
        self.websocket_connections.add(ws)

        try:
            # Send initial data
            dashboard_data = await self.dashboard.get_dashboard_data()
            await ws.send_str(json.dumps({
                'type': 'dashboard_update',
                'data': dashboard_data
            }))

            # Handle incoming messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'subscribe':
                            # Client subscription (already handled by adding to connections)
                            pass
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    logging.error(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            logging.error(f'WebSocket handler error: {e}')
        finally:
            # Connection cleanup is handled by WeakSet
            pass

        return ws

    async def _update_loop(self):
        """Background task to send real-time updates"""
        while True:
            try:
                await asyncio.sleep(self.update_interval)

                if not self.websocket_connections:
                    continue

                # Get current dashboard data
                dashboard_data = await self.dashboard.get_dashboard_data()

                # Send to all connected clients
                update_message = json.dumps({
                    'type': 'dashboard_update',
                    'data': dashboard_data,
                    'timestamp': datetime.now().isoformat()
                })

                # Send to all active WebSocket connections
                disconnected = []
                for ws in self.websocket_connections:
                    try:
                        await ws.send_str(update_message)
                    except Exception:
                        disconnected.append(ws)

                # Remove disconnected websockets (WeakSet handles this automatically)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f'Update loop error: {e}')

    async def _handle_new_alert(self, alert: PerformanceAlert):
        """Handle new performance alerts by broadcasting to clients"""
        if not self.websocket_connections:
            return

        alert_message = json.dumps({
            'type': 'new_alert',
            'alert': {
                'alert_id': alert.alert_id,
                'severity': alert.severity.name,
                'metric_type': alert.metric_type.value,
                'description': alert.description,
                'timestamp': alert.timestamp.isoformat(),
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'recommended_action': alert.recommended_action
            }
        })

        # Send to all active WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.send_str(alert_message)
            except Exception:
                pass

    def _generate_dashboard_html(self) -> str:
        """Generate the main dashboard HTML page"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LM Studio Performance Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }

        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .dashboard {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border: 1px solid #e1e8ed;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        .card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }

        .metric.warning {
            border-left-color: #f39c12;
            background: #fef9e7;
        }

        .metric.critical {
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }

        .metric-label {
            font-weight: 600;
            color: #555;
        }

        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }

        .health-score {
            text-align: center;
            padding: 20px;
        }

        .health-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            font-weight: bold;
            color: white;
            background: conic-gradient(from 0deg, #e74c3c 0deg, #f39c12 60deg, #27ae60 85deg);
        }

        .health-circle.excellent {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
        }

        .health-circle.good {
            background: linear-gradient(135deg, #f39c12, #e67e22);
        }

        .health-circle.poor {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-healthy { background-color: #27ae60; }
        .status-degraded { background-color: #f39c12; }
        .status-unstable { background-color: #e67e22; }
        .status-disconnected { background-color: #e74c3c; }

        .alert {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }

        .alert.info {
            background-color: #e3f2fd;
            border-left-color: #2196f3;
            color: #1565c0;
        }

        .alert.warning {
            background-color: #fff3e0;
            border-left-color: #ff9800;
            color: #ef6c00;
        }

        .alert.critical {
            background-color: #ffebee;
            border-left-color: #f44336;
            color: #c62828;
        }

        .alert.emergency {
            background-color: #fce4ec;
            border-left-color: #e91e63;
            color: #ad1457;
        }

        .recommendations {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }

        .recommendations h4 {
            color: #2c3e50;
            margin-bottom: 15px;
        }

        .recommendations ul {
            list-style: none;
        }

        .recommendations li {
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }

        .recommendations li:before {
            content: "💡 ";
            margin-right: 8px;
        }

        .chart-container {
            height: 200px;
            background: #f8f9fa;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-style: italic;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 25px;
            background: #27ae60;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transition: all 0.3s ease;
        }

        .connection-status.disconnected {
            background: #e74c3c;
        }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
                padding: 20px;
            }

            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">
        🔗 Connected
    </div>

    <div class="container">
        <div class="header">
            <h1>🚀 LM Studio Performance Monitor</h1>
            <p class="subtitle">Real-time monitoring and analytics for your AI infrastructure</p>
        </div>

        <div class="dashboard" id="dashboard">
            <div class="loading">
                Loading dashboard data...
            </div>
        </div>
    </div>

    <script>
        class PerformanceDashboard {
            constructor() {
                this.ws = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.reconnectDelay = 1000;
                this.dashboard = document.getElementById('dashboard');
                this.connectionStatus = document.getElementById('connectionStatus');

                this.connect();
            }

            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus(true);
                    this.ws.send(JSON.stringify({ type: 'subscribe' }));
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.updateConnectionStatus(false);
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
            }

            attemptReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

                    setTimeout(() => {
                        this.connect();
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            }

            updateConnectionStatus(connected) {
                if (connected) {
                    this.connectionStatus.textContent = '🔗 Connected';
                    this.connectionStatus.className = 'connection-status';
                } else {
                    this.connectionStatus.textContent = '❌ Disconnected';
                    this.connectionStatus.className = 'connection-status disconnected';
                }
            }

            handleMessage(message) {
                switch (message.type) {
                    case 'dashboard_update':
                        this.updateDashboard(message.data);
                        break;
                    case 'new_alert':
                        this.showNewAlert(message.alert);
                        break;
                    default:
                        console.log('Unknown message type:', message.type);
                }
            }

            updateDashboard(data) {
                this.dashboard.innerHTML = this.generateDashboardHTML(data);
            }

            generateDashboardHTML(data) {
                const healthScore = data.health_score || 0;
                const healthClass = healthScore >= 80 ? 'excellent' : healthScore >= 60 ? 'good' : 'poor';

                return `
                    <div class="card">
                        <h3>🎯 Overall Health Score</h3>
                        <div class="health-score">
                            <div class="health-circle ${healthClass}">
                                ${Math.round(healthScore)}%
                            </div>
                            <p><strong>System Status:</strong> ${this.getHealthStatus(healthScore)}</p>
                        </div>
                    </div>

                    <div class="card">
                        <h3>🔗 Connection Health</h3>
                        ${this.generateConnectionMetrics(data.connection_health)}
                    </div>

                    <div class="card">
                        <h3>⚡ Performance Metrics</h3>
                        ${this.generatePerformanceMetrics(data.current_metrics)}
                    </div>

                    <div class="card">
                        <h3>📊 Statistics</h3>
                        ${this.generateStatistics(data.statistics)}
                    </div>

                    <div class="card">
                        <h3>🚨 Active Alerts</h3>
                        ${this.generateAlerts(data.active_alerts)}
                    </div>

                    <div class="card">
                        <h3>📈 Trends</h3>
                        ${this.generateTrends(data.trends)}
                    </div>

                    <div class="recommendations">
                        <h4>💡 Recommendations</h4>
                        <ul>
                            ${(data.recommendations || []).map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            generateConnectionMetrics(health) {
                const statusClass = `status-${health.status}`;
                return `
                    <div class="metric">
                        <span class="metric-label">
                            <span class="status-indicator ${statusClass}"></span>
                            Status
                        </span>
                        <span class="metric-value">${health.status.toUpperCase()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime</span>
                        <span class="metric-value">${health.uptime_percentage.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Response Time</span>
                        <span class="metric-value">${health.average_response_time.toFixed(0)}ms</span>
                    </div>
                    <div class="metric ${health.consecutive_failures > 0 ? 'warning' : ''}">
                        <span class="metric-label">Failures</span>
                        <span class="metric-value">${health.consecutive_failures}</span>
                    </div>
                `;
            }

            generatePerformanceMetrics(metrics) {
                return `
                    <div class="metric ${metrics.average_response_time_ms > 3000 ? 'warning' : ''}">
                        <span class="metric-label">Avg Response Time</span>
                        <span class="metric-value">${metrics.average_response_time_ms.toFixed(0)}ms</span>
                    </div>
                    <div class="metric ${metrics.recent_error_rate > 5 ? 'critical' : ''}">
                        <span class="metric-label">Error Rate</span>
                        <span class="metric-value">${metrics.recent_error_rate.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Tokens/Min</span>
                        <span class="metric-value">${metrics.tokens_per_minute.toFixed(0)}</span>
                    </div>
                    <div class="metric ${metrics.queue_depth > 10 ? 'warning' : ''}">
                        <span class="metric-label">Queue Depth</span>
                        <span class="metric-value">${metrics.queue_depth}</span>
                    </div>
                `;
            }

            generateStatistics(stats) {
                const uptime = stats.monitoring_start_time ?
                    Math.round((Date.now() - new Date(stats.monitoring_start_time).getTime()) / 1000 / 60) : 0;

                return `
                    <div class="metric">
                        <span class="metric-label">Total Requests</span>
                        <span class="metric-value">${stats.total_requests || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Success Rate</span>
                        <span class="metric-value">${stats.total_requests ?
                            ((stats.successful_requests / stats.total_requests) * 100).toFixed(1) : 0}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Tokens Processed</span>
                        <span class="metric-value">${(stats.total_tokens_processed || 0).toLocaleString()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Monitoring Uptime</span>
                        <span class="metric-value">${uptime} min</span>
                    </div>
                `;
            }

            generateAlerts(alerts) {
                if (!alerts || alerts.length === 0) {
                    return '<p style="color: #27ae60; text-align: center; padding: 20px;">✅ No active alerts</p>';
                }

                return alerts.map(alert => `
                    <div class="alert ${alert.severity.toLowerCase()}">
                        <strong>${alert.metric_type.toUpperCase()}</strong><br>
                        ${alert.description}<br>
                        <small><em>Recommended: ${alert.recommended_action}</em></small>
                    </div>
                `).join('');
            }

            generateTrends(trends) {
                if (!trends) return '<p>No trend data available</p>';

                const getTrendIcon = (trend) => {
                    switch (trend) {
                        case 'improving': return '📈';
                        case 'degrading': return '📉';
                        case 'stable': return '➡️';
                        default: return '❓';
                    }
                };

                return `
                    <div class="metric">
                        <span class="metric-label">Response Time</span>
                        <span class="metric-value">${getTrendIcon(trends.response_time)} ${trends.response_time}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Error Rate</span>
                        <span class="metric-value">${getTrendIcon(trends.error_rate)} ${trends.error_rate}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Connection</span>
                        <span class="metric-value">${getTrendIcon(trends.connection_stability)} ${trends.connection_stability}</span>
                    </div>
                `;
            }

            getHealthStatus(score) {
                if (score >= 80) return 'Excellent';
                if (score >= 60) return 'Good';
                if (score >= 40) return 'Fair';
                return 'Poor';
            }

            showNewAlert(alert) {
                // Show browser notification if permitted
                if (Notification.permission === 'granted') {
                    new Notification(`LM Studio Alert: ${alert.severity}`, {
                        body: alert.description,
                        icon: '/favicon.ico'
                    });
                }

                // Log to console for debugging
                console.log('New alert:', alert);
            }
        }

        // Request notification permission
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new PerformanceDashboard();
        });
    </script>
</body>
</html>
        """


async def start_dashboard_server(
    monitor: LMStudioPerformanceMonitor,
    dashboard: PerformanceDashboard,
    port: int = 8080,
    host: str = "localhost"
) -> PerformanceDashboardServer:
    """
    Start the performance dashboard web server

    Args:
        monitor: Performance monitor instance
        dashboard: Dashboard instance
        port: Server port
        host: Server host

    Returns:
        Started dashboard server instance
    """
    server = PerformanceDashboardServer(monitor, dashboard, port, host)
    await server.start_server()
    return server


if __name__ == "__main__":
    # Example usage
    async def main():
        from lm_studio_performance_monitor import create_integrated_performance_monitor

        # Create performance monitoring system
        monitor, dashboard = await create_integrated_performance_monitor()

        # Start dashboard server
        server = await start_dashboard_server(monitor, dashboard, port=8080)

        print("Dashboard server running at http://localhost:8080")
        print("Press Ctrl+C to stop...")

        try:
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping server...")
            await server.stop_server()
            monitor.stop_monitoring()

    asyncio.run(main())