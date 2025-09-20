#!/usr/bin/env python3
"""
Security Analytics Dashboard
Part of Phase A3: Enhanced Security Logging

Real-time security analytics dashboard providing:
- Live security metrics visualization
- Threat detection alerts
- Risk trend analysis
- Compliance monitoring
- Interactive security controls
- Export capabilities
"""

import json
import sqlite3
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import html

try:
    from enhanced_security_logging import EnhancedSecurityLogger, SecurityEventType, SecuritySeverity
    from security_log_analyzer import SecurityLogAnalyzer
except ImportError as e:
    print(f"Warning: Could not import security modules: {e}")


class SecurityDashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for security dashboard web interface"""

    def __init__(self, *args, analyzer=None, **kwargs):
        self.analyzer = analyzer
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        if path == "/" or path == "/dashboard":
            self._serve_dashboard()
        elif path == "/api/metrics":
            self._serve_metrics_api(params)
        elif path == "/api/events":
            self._serve_events_api(params)
        elif path == "/api/report":
            self._serve_report_api(params)
        elif path == "/static/style.css":
            self._serve_css()
        elif path == "/static/app.js":
            self._serve_javascript()
        else:
            self._serve_404()

    def _serve_dashboard(self):
        """Serve main dashboard HTML"""
        html_content = self._generate_dashboard_html()
        self._send_response(200, "text/html", html_content)

    def _serve_metrics_api(self, params):
        """Serve metrics API endpoint"""
        try:
            time_window = params.get('window', ['24h'])[0]

            if hasattr(self.server, 'analyzer'):
                # Get analytics from security logger
                conn = sqlite3.connect(self.server.analyzer.database_path)
                cursor = conn.cursor()

                # Calculate time range
                if time_window == "1h":
                    start_time = (datetime.now() - timedelta(hours=1)).isoformat()
                elif time_window == "7d":
                    start_time = (datetime.now() - timedelta(days=7)).isoformat()
                else:  # 24h default
                    start_time = (datetime.now() - timedelta(days=1)).isoformat()

                # Get metrics
                metrics = self._calculate_dashboard_metrics(cursor, start_time)
                conn.close()

                self._send_response(200, "application/json", json.dumps(metrics))
            else:
                self._send_response(500, "application/json", json.dumps({"error": "Analyzer not available"}))

        except Exception as e:
            self._send_response(500, "application/json", json.dumps({"error": str(e)}))

    def _serve_events_api(self, params):
        """Serve events API endpoint"""
        try:
            limit = int(params.get('limit', ['50'])[0])
            event_type = params.get('type', [None])[0]

            if hasattr(self.server, 'analyzer'):
                events = self._get_recent_events(limit, event_type)
                self._send_response(200, "application/json", json.dumps(events))
            else:
                self._send_response(500, "application/json", json.dumps({"error": "Analyzer not available"}))

        except Exception as e:
            self._send_response(500, "application/json", json.dumps({"error": str(e)}))

    def _serve_report_api(self, params):
        """Serve report generation API"""
        try:
            time_period = params.get('period', ['24h'])[0]

            if hasattr(self.server, 'analyzer'):
                report = self.server.analyzer.generate_comprehensive_report(time_period)
                report_dict = report.__dict__.copy()

                # Convert datetime objects to strings for JSON serialization
                for key, value in report_dict.items():
                    if isinstance(value, datetime):
                        report_dict[key] = value.isoformat()

                self._send_response(200, "application/json", json.dumps(report_dict, default=str))
            else:
                self._send_response(500, "application/json", json.dumps({"error": "Analyzer not available"}))

        except Exception as e:
            self._send_response(500, "application/json", json.dumps({"error": str(e)}))

    def _serve_css(self):
        """Serve CSS styles"""
        css_content = self._generate_css()
        self._send_response(200, "text/css", css_content)

    def _serve_javascript(self):
        """Serve JavaScript application"""
        js_content = self._generate_javascript()
        self._send_response(200, "application/javascript", js_content)

    def _serve_404(self):
        """Serve 404 error page"""
        self._send_response(404, "text/html", "<h1>404 - Not Found</h1>")

    def _send_response(self, status_code, content_type, content):
        """Send HTTP response"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _calculate_dashboard_metrics(self, cursor, start_time):
        """Calculate metrics for dashboard"""
        # Total events
        cursor.execute("SELECT COUNT(*) FROM security_events WHERE timestamp >= ?", (start_time,))
        total_events = cursor.fetchone()[0]

        # Events by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ?
            GROUP BY severity
        """, (start_time,))
        severity_data = cursor.fetchall()

        # Events by type
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ?
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
        """, (start_time,))
        event_type_data = cursor.fetchall()

        # Risk metrics
        cursor.execute("""
            SELECT AVG(risk_score) as avg_risk, MAX(risk_score) as max_risk,
                   COUNT(CASE WHEN risk_score >= 0.8 THEN 1 END) as high_risk_count
            FROM security_events
            WHERE timestamp >= ? AND risk_score IS NOT NULL
        """, (start_time,))
        risk_data = cursor.fetchone()

        # Hourly event distribution
        cursor.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
        """, (start_time,))
        hourly_data = cursor.fetchall()

        return {
            "total_events": total_events,
            "severity_distribution": dict(severity_data),
            "event_types": dict(event_type_data),
            "risk_metrics": {
                "average_risk": risk_data[0] if risk_data[0] else 0.0,
                "maximum_risk": risk_data[1] if risk_data[1] else 0.0,
                "high_risk_events": risk_data[2] if risk_data[2] else 0
            },
            "hourly_distribution": dict(hourly_data),
            "last_updated": datetime.now().isoformat()
        }

    def _get_recent_events(self, limit, event_type_filter=None):
        """Get recent security events for display"""
        if not hasattr(self.server, 'analyzer'):
            return []

        conn = sqlite3.connect(self.server.analyzer.database_path)
        cursor = conn.cursor()

        if event_type_filter:
            cursor.execute("""
                SELECT event_id, timestamp, event_type, severity, description, risk_score
                FROM security_events
                WHERE event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (event_type_filter, limit))
        else:
            cursor.execute("""
                SELECT event_id, timestamp, event_type, severity, description, risk_score
                FROM security_events
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return events

    def _generate_dashboard_html(self):
        """Generate main dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Analytics Dashboard</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>🔒 Security Analytics Dashboard</h1>
            <div class="header-controls">
                <select id="timeWindow">
                    <option value="1h">Last Hour</option>
                    <option value="24h" selected>Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                </select>
                <button id="refreshBtn">🔄 Refresh</button>
                <button id="exportBtn">📊 Export Report</button>
            </div>
        </header>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Events</h3>
                <div class="metric-value" id="totalEvents">-</div>
                <div class="metric-change" id="eventsChange">-</div>
            </div>
            <div class="metric-card">
                <h3>Average Risk</h3>
                <div class="metric-value" id="avgRisk">-</div>
                <div class="metric-change" id="riskChange">-</div>
            </div>
            <div class="metric-card">
                <h3>High Risk Events</h3>
                <div class="metric-value" id="highRiskEvents">-</div>
                <div class="metric-change" id="highRiskChange">-</div>
            </div>
            <div class="metric-card">
                <h3>Critical Alerts</h3>
                <div class="metric-value" id="criticalAlerts">-</div>
                <div class="metric-change" id="alertsChange">-</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <h3>Event Distribution by Hour</h3>
                <canvas id="hourlyChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Severity Distribution</h3>
                <canvas id="severityChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Top Event Types</h3>
                <canvas id="eventTypesChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Risk Trend</h3>
                <canvas id="riskTrendChart"></canvas>
            </div>
        </div>

        <div class="events-section">
            <div class="section-header">
                <h3>Recent Security Events</h3>
                <div class="event-filters">
                    <select id="eventTypeFilter">
                        <option value="">All Types</option>
                        <option value="security_violation">Security Violations</option>
                        <option value="emergency_triggered">Emergency Events</option>
                        <option value="access_denied">Access Denied</option>
                        <option value="permission_check">Permission Checks</option>
                    </select>
                </div>
            </div>
            <div class="events-list" id="eventsList">
                <div class="loading">Loading events...</div>
            </div>
        </div>

        <div class="alerts-section" id="alertsSection" style="display: none;">
            <h3>🚨 Active Alerts</h3>
            <div id="alertsList"></div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
        """

    def _generate_css(self):
        """Generate CSS styles for dashboard"""
        return """
/* Security Dashboard Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f0f;
    color: #e0e0e0;
    line-height: 1.6;
}

.dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 12px;
    border: 1px solid #333;
}

.dashboard-header h1 {
    color: #00d4ff;
    font-size: 2rem;
    font-weight: 600;
}

.header-controls {
    display: flex;
    gap: 12px;
    align-items: center;
}

select, button {
    padding: 8px 16px;
    border: 1px solid #444;
    border-radius: 6px;
    background: #2a2a2a;
    color: #e0e0e0;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}

button:hover, select:hover {
    border-color: #00d4ff;
    background: #333;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #333;
    text-align: center;
    transition: transform 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: #00d4ff;
}

.metric-card h3 {
    color: #999;
    font-size: 0.9rem;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #00d4ff;
    margin-bottom: 8px;
}

.metric-change {
    font-size: 0.85rem;
    color: #888;
}

.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-container {
    background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #333;
}

.chart-container h3 {
    color: #00d4ff;
    margin-bottom: 20px;
    font-size: 1.1rem;
}

.events-section {
    background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
    border-radius: 12px;
    border: 1px solid #333;
    overflow: hidden;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #333;
}

.section-header h3 {
    color: #00d4ff;
    font-size: 1.2rem;
}

.events-list {
    max-height: 400px;
    overflow-y: auto;
}

.event-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    border-bottom: 1px solid #2a2a2a;
    transition: background 0.2s ease;
}

.event-item:hover {
    background: rgba(0, 212, 255, 0.05);
}

.event-info {
    flex: 1;
}

.event-type {
    color: #00d4ff;
    font-weight: 500;
    font-size: 0.9rem;
}

.event-description {
    color: #ccc;
    font-size: 0.85rem;
    margin-top: 2px;
}

.event-meta {
    text-align: right;
    color: #888;
    font-size: 0.8rem;
}

.severity-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    margin-top: 4px;
}

.severity-0, .severity-1, .severity-2 { background: #2d5a27; color: #81c784; }
.severity-3, .severity-4 { background: #5d4037; color: #ffb74d; }
.severity-5, .severity-6 { background: #d32f2f; color: #fff; }
.severity-7, .severity-8 { background: #7b1fa2; color: #fff; }

.risk-score {
    font-weight: 600;
    margin-top: 4px;
}

.risk-low { color: #81c784; }
.risk-medium { color: #ffb74d; }
.risk-high { color: #e57373; }
.risk-critical { color: #f44336; }

.loading {
    text-align: center;
    padding: 40px;
    color: #888;
}

.alerts-section {
    background: linear-gradient(145deg, #2e1a1a, #3e2a2a);
    border: 1px solid #d32f2f;
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
}

.alert-item {
    background: rgba(211, 47, 47, 0.1);
    border: 1px solid #d32f2f;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.alert-title {
    color: #f44336;
    font-weight: 600;
    margin-bottom: 8px;
}

.alert-description {
    color: #ccc;
    font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        gap: 15px;
        text-align: center;
    }

    .metrics-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }

    .charts-grid {
        grid-template-columns: 1fr;
    }

    .section-header {
        flex-direction: column;
        gap: 12px;
    }
}

/* Chart container sizing */
canvas {
    max-width: 100%;
    height: auto !important;
}
        """

    def _generate_javascript(self):
        """Generate JavaScript for dashboard functionality"""
        return """
// Security Dashboard JavaScript
let charts = {};
let metricsData = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadDashboardData();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

function initializeEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', loadDashboardData);
    document.getElementById('timeWindow').addEventListener('change', loadDashboardData);
    document.getElementById('eventTypeFilter').addEventListener('change', loadEvents);
    document.getElementById('exportBtn').addEventListener('click', exportReport);
}

async function loadDashboardData() {
    try {
        const timeWindow = document.getElementById('timeWindow').value;

        // Load metrics
        const metricsResponse = await fetch(`/api/metrics?window=${timeWindow}`);
        metricsData = await metricsResponse.json();

        updateMetrics(metricsData);
        updateCharts(metricsData);

        // Load events
        await loadEvents();

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

function updateMetrics(data) {
    document.getElementById('totalEvents').textContent = data.total_events.toLocaleString();
    document.getElementById('avgRisk').textContent = data.risk_metrics.average_risk.toFixed(2);
    document.getElementById('highRiskEvents').textContent = data.risk_metrics.high_risk_events;

    // Calculate critical alerts (severity 6+)
    const criticalAlerts = Object.entries(data.severity_distribution)
        .filter(([severity, count]) => parseInt(severity) >= 6)
        .reduce((sum, [severity, count]) => sum + count, 0);

    document.getElementById('criticalAlerts').textContent = criticalAlerts;

    // Update change indicators (simplified for demo)
    document.getElementById('eventsChange').textContent = '📈 Active monitoring';
    document.getElementById('riskChange').textContent = getRiskChangeText(data.risk_metrics.average_risk);
    document.getElementById('highRiskChange').textContent = data.risk_metrics.high_risk_events > 0 ? '⚠️ Attention needed' : '✅ Normal';
    document.getElementById('alertsChange').textContent = criticalAlerts > 0 ? '🚨 Critical' : '✅ Clear';
}

function getRiskChangeText(avgRisk) {
    if (avgRisk < 0.3) return '✅ Low risk';
    if (avgRisk < 0.6) return '⚠️ Medium risk';
    return '🚨 High risk';
}

function updateCharts(data) {
    // Hourly distribution chart
    updateHourlyChart(data.hourly_distribution);

    // Severity distribution chart
    updateSeverityChart(data.severity_distribution);

    // Event types chart
    updateEventTypesChart(data.event_types);

    // Risk trend chart (simplified)
    updateRiskTrendChart(data.risk_metrics);
}

function updateHourlyChart(hourlyData) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');

    if (charts.hourly) {
        charts.hourly.destroy();
    }

    const hours = Array.from({length: 24}, (_, i) => i.toString().padStart(2, '0'));
    const counts = hours.map(hour => hourlyData[hour] || 0);

    charts.hourly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.map(h => h + ':00'),
            datasets: [{
                label: 'Events per Hour',
                data: counts,
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } }
            },
            scales: {
                x: { ticks: { color: '#999' } },
                y: { ticks: { color: '#999' } }
            }
        }
    });
}

function updateSeverityChart(severityData) {
    const ctx = document.getElementById('severityChart').getContext('2d');

    if (charts.severity) {
        charts.severity.destroy();
    }

    const severityNames = {
        '0': 'Trace', '1': 'Debug', '2': 'Info', '3': 'Notice',
        '4': 'Warning', '5': 'Error', '6': 'Critical', '7': 'Alert', '8': 'Emergency'
    };

    const severityColors = {
        '0': '#4caf50', '1': '#4caf50', '2': '#2196f3', '3': '#ff9800',
        '4': '#ff9800', '5': '#f44336', '6': '#d32f2f', '7': '#9c27b0', '8': '#9c27b0'
    };

    const labels = Object.keys(severityData).map(s => severityNames[s] || s);
    const values = Object.values(severityData);
    const colors = Object.keys(severityData).map(s => severityColors[s] || '#666');

    charts.severity = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } }
            }
        }
    });
}

function updateEventTypesChart(eventTypesData) {
    const ctx = document.getElementById('eventTypesChart').getContext('2d');

    if (charts.eventTypes) {
        charts.eventTypes.destroy();
    }

    const labels = Object.keys(eventTypesData);
    const values = Object.values(eventTypesData);

    charts.eventTypes = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(label => label.replace('_', ' ')),
            datasets: [{
                label: 'Event Count',
                data: values,
                backgroundColor: '#00d4ff',
                borderColor: '#0099cc',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } }
            },
            scales: {
                x: {
                    ticks: { color: '#999', maxRotation: 45 }
                },
                y: { ticks: { color: '#999' } }
            }
        }
    });
}

function updateRiskTrendChart(riskMetrics) {
    const ctx = document.getElementById('riskTrendChart').getContext('2d');

    if (charts.riskTrend) {
        charts.riskTrend.destroy();
    }

    // Simple risk visualization
    const data = [
        { label: 'Current Average', value: riskMetrics.average_risk },
        { label: 'Maximum Risk', value: riskMetrics.maximum_risk }
    ];

    charts.riskTrend = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: 'Risk Score',
                data: data.map(d => d.value),
                backgroundColor: data.map(d => d.value >= 0.8 ? '#f44336' : d.value >= 0.5 ? '#ff9800' : '#4caf50'),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } }
            },
            scales: {
                x: { ticks: { color: '#999' } },
                y: {
                    ticks: { color: '#999' },
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

async function loadEvents() {
    try {
        const eventTypeFilter = document.getElementById('eventTypeFilter').value;
        const url = eventTypeFilter ?
            `/api/events?limit=50&type=${eventTypeFilter}` :
            '/api/events?limit=50';

        const response = await fetch(url);
        const events = await response.json();

        displayEvents(events);

    } catch (error) {
        console.error('Error loading events:', error);
        showError('Failed to load events');
    }
}

function displayEvents(events) {
    const eventsList = document.getElementById('eventsList');

    if (events.length === 0) {
        eventsList.innerHTML = '<div class="loading">No events found</div>';
        return;
    }

    const eventsHtml = events.map(event => {
        const severity = getSeverityName(event.severity);
        const severityClass = `severity-${event.severity}`;
        const riskClass = getRiskClass(event.risk_score);
        const timestamp = new Date(event.timestamp).toLocaleString();

        return `
            <div class="event-item">
                <div class="event-info">
                    <div class="event-type">${event.event_type.replace('_', ' ')}</div>
                    <div class="event-description">${escapeHtml(event.description)}</div>
                    <div class="severity-badge ${severityClass}">${severity}</div>
                </div>
                <div class="event-meta">
                    <div>${timestamp}</div>
                    <div class="risk-score ${riskClass}">Risk: ${(event.risk_score || 0).toFixed(2)}</div>
                </div>
            </div>
        `;
    }).join('');

    eventsList.innerHTML = eventsHtml;
}

function getSeverityName(severity) {
    const names = {
        0: 'Trace', 1: 'Debug', 2: 'Info', 3: 'Notice',
        4: 'Warning', 5: 'Error', 6: 'Critical', 7: 'Alert', 8: 'Emergency'
    };
    return names[severity] || 'Unknown';
}

function getRiskClass(riskScore) {
    if (!riskScore) return 'risk-low';
    if (riskScore >= 0.8) return 'risk-critical';
    if (riskScore >= 0.6) return 'risk-high';
    if (riskScore >= 0.3) return 'risk-medium';
    return 'risk-low';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function exportReport() {
    try {
        const timeWindow = document.getElementById('timeWindow').value;
        const response = await fetch(`/api/report?period=${timeWindow}`);
        const report = await response.json();

        // Convert to JSON and download
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security_report_${report.report_id}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showSuccess('Report exported successfully');

    } catch (error) {
        console.error('Error exporting report:', error);
        showError('Failed to export report');
    }
}

function showError(message) {
    // Simple error notification
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: #f44336; color: white; padding: 12px 20px;
        border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    `;
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function showSuccess(message) {
    // Simple success notification
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: #4caf50; color: white; padding: 12px 20px;
        border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    `;
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}
        """

    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass


class SecurityAnalyticsDashboard:
    """Security Analytics Dashboard Server"""

    def __init__(self, database_path: str = "enhanced_security.db", port: int = 8080):
        self.database_path = database_path
        self.port = port
        self.analyzer = SecurityLogAnalyzer(database_path)
        self.server = None
        self.server_thread = None

    def start(self, open_browser: bool = True):
        """Start the dashboard server"""
        # Create custom handler class with analyzer
        def handler_factory(*args, **kwargs):
            return SecurityDashboardHandler(*args, analyzer=self.analyzer, **kwargs)

        # Create HTTP server
        self.server = HTTPServer(('localhost', self.port), handler_factory)
        self.server.analyzer = self.analyzer  # Attach analyzer to server

        # Start server in background thread
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
            name="SecurityDashboardServer"
        )
        self.server_thread.start()

        dashboard_url = f"http://localhost:{self.port}"
        print(f"🔒 Security Analytics Dashboard started at: {dashboard_url}")

        if open_browser:
            try:
                webbrowser.open(dashboard_url)
                print("🌐 Opening dashboard in web browser...")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print(f"Please open your browser and navigate to: {dashboard_url}")

        return dashboard_url

    def stop(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("🔒 Security Analytics Dashboard stopped")

    def wait_for_shutdown(self):
        """Wait for server shutdown"""
        if self.server_thread:
            try:
                self.server_thread.join()
            except KeyboardInterrupt:
                print("\n🔒 Shutting down Security Analytics Dashboard...")
                self.stop()


def main():
    """Command line interface for security dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description="Security Analytics Dashboard")
    parser.add_argument("--database", "-d", default="enhanced_security.db",
                       help="Security database path")
    parser.add_argument("--port", "-p", type=int, default=8080,
                       help="Dashboard port")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't open browser automatically")

    args = parser.parse_args()

    # Create and start dashboard
    dashboard = SecurityAnalyticsDashboard(args.database, args.port)

    try:
        dashboard.start(open_browser=not args.no_browser)
        print("\n📊 Dashboard is running. Press Ctrl+C to stop.")
        dashboard.wait_for_shutdown()

    except KeyboardInterrupt:
        print("\n🔒 Shutting down Security Analytics Dashboard...")
        dashboard.stop()

    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        dashboard.stop()


if __name__ == "__main__":
    main()