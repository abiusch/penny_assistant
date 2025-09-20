#!/usr/bin/env python3
"""
Security Log Analysis Tools and Utilities
Part of Phase A3: Enhanced Security Logging

Comprehensive tools for analyzing, reviewing, and managing security logs:
- Interactive log review interface
- Security trend analysis
- Anomaly detection reports
- Compliance reporting
- Log search and filtering
- Visual analytics and charts
- Export utilities
"""

import json
import sqlite3
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import hashlib
import re

try:
    from enhanced_security_logging import (
        EnhancedSecurityLogger, SecurityEventType, SecuritySeverity,
        LogRetentionPolicy, SecurityEvent
    )
except ImportError as e:
    print(f"Warning: Could not import enhanced security logging: {e}")


@dataclass
class LogAnalysisReport:
    """Security log analysis report structure"""
    report_id: str
    timestamp: str
    time_period: str
    total_events: int

    # Event Analysis
    event_breakdown: Dict[str, int]
    severity_distribution: Dict[str, int]
    top_sources: List[Tuple[str, int]]

    # Security Analysis
    risk_summary: Dict[str, float]
    threat_indicators: List[Dict[str, Any]]
    anomalies_detected: List[Dict[str, Any]]

    # Compliance
    policy_violations: List[Dict[str, Any]]
    retention_compliance: Dict[str, int]

    # Recommendations
    security_recommendations: List[str]
    urgent_actions: List[str]


class SecurityLogAnalyzer:
    """Comprehensive security log analysis and review tools"""

    def __init__(self, database_path: str = "enhanced_security.db"):
        self.database_path = database_path
        self.analysis_cache = {}

    def generate_comprehensive_report(self,
                                    time_period: str = "24h",
                                    include_charts: bool = False) -> LogAnalysisReport:
        """Generate comprehensive security analysis report"""

        report_id = hashlib.md5(f"{time_period}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        # Calculate time window
        if time_period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif time_period == "24h":
            start_time = datetime.now() - timedelta(days=1)
        elif time_period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif time_period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            start_time = datetime.now() - timedelta(days=1)

        start_time_str = start_time.isoformat()

        # Gather data
        events = self._get_events_in_period(start_time_str)

        # Analyze events
        event_breakdown = self._analyze_event_types(events)
        severity_distribution = self._analyze_severity_distribution(events)
        top_sources = self._analyze_top_sources(events)

        # Security analysis
        risk_summary = self._calculate_risk_summary(events)
        threat_indicators = self._extract_threat_indicators(events)
        anomalies = self._detect_anomalies(events)

        # Compliance analysis
        policy_violations = self._identify_policy_violations(events)
        retention_compliance = self._check_retention_compliance(events)

        # Generate recommendations
        recommendations, urgent_actions = self._generate_recommendations(events, risk_summary)

        report = LogAnalysisReport(
            report_id=report_id,
            timestamp=datetime.now().isoformat(),
            time_period=time_period,
            total_events=len(events),
            event_breakdown=event_breakdown,
            severity_distribution=severity_distribution,
            top_sources=top_sources,
            risk_summary=risk_summary,
            threat_indicators=threat_indicators,
            anomalies_detected=anomalies,
            policy_violations=policy_violations,
            retention_compliance=retention_compliance,
            security_recommendations=recommendations,
            urgent_actions=urgent_actions
        )

        return report

    def _get_events_in_period(self, start_time: str) -> List[Dict[str, Any]]:
        """Get all security events in specified time period"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM security_events
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (start_time,))

        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return events

    def _analyze_event_types(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of event types"""
        breakdown = {}
        for event in events:
            event_type = event['event_type']
            breakdown[event_type] = breakdown.get(event_type, 0) + 1

        return dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

    def _analyze_severity_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze severity level distribution"""
        distribution = {}
        severity_names = {
            0: "TRACE", 1: "DEBUG", 2: "INFO", 3: "NOTICE",
            4: "WARNING", 5: "ERROR", 6: "CRITICAL", 7: "ALERT", 8: "EMERGENCY"
        }

        for event in events:
            severity_level = event['severity']
            severity_name = severity_names.get(severity_level, f"UNKNOWN_{severity_level}")
            distribution[severity_name] = distribution.get(severity_name, 0) + 1

        return distribution

    def _analyze_top_sources(self, events: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Analyze top event sources"""
        sources = {}
        for event in events:
            source = f"{event['source_component']}.{event['source_function']}"
            sources[source] = sources.get(source, 0) + 1

        return sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]

    def _calculate_risk_summary(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate risk summary statistics"""
        risk_scores = [event['risk_score'] for event in events if event['risk_score'] is not None]

        if not risk_scores:
            return {
                "average_risk": 0.0,
                "maximum_risk": 0.0,
                "minimum_risk": 0.0,
                "high_risk_events": 0,
                "critical_risk_events": 0
            }

        return {
            "average_risk": sum(risk_scores) / len(risk_scores),
            "maximum_risk": max(risk_scores),
            "minimum_risk": min(risk_scores),
            "high_risk_events": len([r for r in risk_scores if r >= 0.7]),
            "critical_risk_events": len([r for r in risk_scores if r >= 0.9])
        }

    def _extract_threat_indicators(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and analyze threat indicators"""
        threat_indicators = []
        indicator_counts = {}

        for event in events:
            if event['threat_indicators'] and event['threat_indicators'] != '[]':
                try:
                    indicators = json.loads(event['threat_indicators'])
                    for indicator in indicators:
                        indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1

                        threat_indicators.append({
                            "indicator": indicator,
                            "event_id": event['event_id'],
                            "timestamp": event['timestamp'],
                            "severity": event['severity'],
                            "risk_score": event['risk_score']
                        })
                except json.JSONDecodeError:
                    continue

        # Sort by frequency and return top indicators
        return sorted(threat_indicators, key=lambda x: indicator_counts[x["indicator"]], reverse=True)[:20]

    def _detect_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalous patterns in events"""
        anomalies = []

        if len(events) < 10:
            return anomalies

        # Analyze event frequency patterns
        hourly_counts = {}
        for event in events:
            try:
                event_time = datetime.fromisoformat(event['timestamp'])
                hour_key = event_time.strftime('%Y-%m-%d %H')
                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
            except ValueError:
                continue

        if hourly_counts:
            counts = list(hourly_counts.values())
            average_count = sum(counts) / len(counts)
            threshold = average_count * 3  # 3x average is anomalous

            for hour, count in hourly_counts.items():
                if count >= threshold:
                    anomalies.append({
                        "type": "high_frequency",
                        "description": f"Unusually high event frequency: {count} events in hour {hour}",
                        "severity": "WARNING",
                        "details": {
                            "hour": hour,
                            "event_count": count,
                            "average_count": average_count,
                            "threshold": threshold
                        }
                    })

        # Detect unusual event patterns
        event_type_sequences = []
        for i in range(len(events) - 2):
            sequence = tuple(events[i+j]['event_type'] for j in range(3))
            event_type_sequences.append(sequence)

        # Look for repeated unusual sequences
        sequence_counts = {}
        for seq in event_type_sequences:
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

        for sequence, count in sequence_counts.items():
            if count >= 3 and 'security_violation' in sequence:
                anomalies.append({
                    "type": "repeated_pattern",
                    "description": f"Repeated security pattern detected: {' → '.join(sequence)}",
                    "severity": "WARNING",
                    "details": {
                        "pattern": sequence,
                        "occurrences": count
                    }
                })

        return anomalies

    def _identify_policy_violations(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential policy violations"""
        violations = []

        # Check for PII handling violations
        pii_events = [e for e in events if e.get('contains_pii')]
        for event in pii_events:
            if not event.get('anonymization_applied'):
                violations.append({
                    "type": "pii_handling",
                    "description": "PII detected but anonymization not applied",
                    "event_id": event['event_id'],
                    "severity": "HIGH",
                    "timestamp": event['timestamp']
                })

        # Check for excessive privilege escalation attempts
        escalation_events = [e for e in events if e.get('event_type') == 'privilege_escalation']
        if len(escalation_events) > 5:
            violations.append({
                "type": "excessive_escalation",
                "description": f"Excessive privilege escalation attempts: {len(escalation_events)}",
                "severity": "MEDIUM",
                "count": len(escalation_events)
            })

        # Check for emergency events without proper resolution
        emergency_events = [e for e in events if e.get('event_type') == 'emergency_triggered']
        resolution_events = [e for e in events if e.get('event_type') == 'emergency_resolved']

        if len(emergency_events) > len(resolution_events):
            violations.append({
                "type": "unresolved_emergencies",
                "description": f"Emergency events without resolution: {len(emergency_events) - len(resolution_events)}",
                "severity": "HIGH",
                "unresolved_count": len(emergency_events) - len(resolution_events)
            })

        return violations

    def _check_retention_compliance(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Check retention policy compliance"""
        compliance = {}
        current_time = datetime.now()

        retention_thresholds = {
            "immediate": timedelta(0),
            "short_term": timedelta(days=1),
            "medium_term": timedelta(days=7),
            "long_term": timedelta(days=30)
        }

        for event in events:
            retention_policy = event.get('retention_policy', 'short_term')

            try:
                event_time = datetime.fromisoformat(event['timestamp'])
                age = current_time - event_time

                if retention_policy in retention_thresholds:
                    threshold = retention_thresholds[retention_policy]
                    if age > threshold:
                        compliance[f"{retention_policy}_overdue"] = compliance.get(f"{retention_policy}_overdue", 0) + 1
                    else:
                        compliance[f"{retention_policy}_compliant"] = compliance.get(f"{retention_policy}_compliant", 0) + 1
                else:
                    compliance[f"{retention_policy}_compliant"] = compliance.get(f"{retention_policy}_compliant", 0) + 1

            except ValueError:
                compliance["invalid_timestamp"] = compliance.get("invalid_timestamp", 0) + 1

        return compliance

    def _generate_recommendations(self, events: List[Dict[str, Any]], risk_summary: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Generate security recommendations and urgent actions"""
        recommendations = []
        urgent_actions = []

        # Risk-based recommendations
        if risk_summary["average_risk"] > 0.6:
            recommendations.append("Average risk level is elevated - review security policies")

        if risk_summary["critical_risk_events"] > 0:
            urgent_actions.append(f"Address {risk_summary['critical_risk_events']} critical risk events immediately")

        # Event pattern recommendations
        event_types = [e['event_type'] for e in events]
        violation_count = event_types.count('security_violation')

        if violation_count > len(events) * 0.1:  # More than 10% violations
            urgent_actions.append("High rate of security violations detected - immediate review required")

        # PII handling recommendations
        pii_events = len([e for e in events if e.get('contains_pii')])
        if pii_events > 0:
            recommendations.append(f"Review PII handling procedures - {pii_events} events contain PII")

        # Session security
        sessions = set(e['session_id'] for e in events if e.get('session_id'))
        if len(sessions) > 100:
            recommendations.append("High number of active sessions - consider session management review")

        # Emergency events
        emergency_events = len([e for e in events if e.get('event_type') == 'emergency_triggered'])
        if emergency_events > 3:
            urgent_actions.append(f"Multiple emergency events ({emergency_events}) - investigate root causes")

        # General recommendations
        if len(events) > 1000:
            recommendations.append("High event volume - consider implementing additional filtering")

        if not recommendations:
            recommendations.append("Security posture appears stable - continue monitoring")

        return recommendations, urgent_actions

    def search_events(self,
                     query: str,
                     start_time: Optional[str] = None,
                     end_time: Optional[str] = None,
                     event_types: Optional[List[str]] = None,
                     min_severity: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search security events with advanced filtering"""

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Build search query
        sql_query = """
            SELECT * FROM security_events
            WHERE (description LIKE ? OR parameters LIKE ? OR context LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if start_time:
            sql_query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            sql_query += " AND timestamp <= ?"
            params.append(end_time)

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            sql_query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)

        if min_severity is not None:
            sql_query += " AND severity >= ?"
            params.append(min_severity)

        sql_query += " ORDER BY timestamp DESC LIMIT 1000"

        cursor.execute(sql_query, params)
        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return events

    def export_report(self, report: LogAnalysisReport, format: str = "json") -> str:
        """Export analysis report in specified format"""

        if format.lower() == "json":
            return json.dumps(report.__dict__, indent=2, default=str)

        elif format.lower() == "markdown":
            return self._generate_markdown_report(report)

        elif format.lower() == "csv":
            return self._generate_csv_summary(report)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _generate_markdown_report(self, report: LogAnalysisReport) -> str:
        """Generate markdown format report"""
        md = []
        md.append(f"# Security Analysis Report")
        md.append(f"**Report ID:** {report.report_id}")
        md.append(f"**Generated:** {report.timestamp}")
        md.append(f"**Time Period:** {report.time_period}")
        md.append(f"**Total Events:** {report.total_events}")
        md.append("")

        # Event breakdown
        md.append("## Event Breakdown")
        for event_type, count in report.event_breakdown.items():
            md.append(f"- **{event_type}:** {count}")
        md.append("")

        # Severity distribution
        md.append("## Severity Distribution")
        for severity, count in report.severity_distribution.items():
            md.append(f"- **{severity}:** {count}")
        md.append("")

        # Risk summary
        md.append("## Risk Summary")
        md.append(f"- **Average Risk:** {report.risk_summary['average_risk']:.2f}")
        md.append(f"- **Maximum Risk:** {report.risk_summary['maximum_risk']:.2f}")
        md.append(f"- **High Risk Events:** {report.risk_summary['high_risk_events']}")
        md.append(f"- **Critical Risk Events:** {report.risk_summary['critical_risk_events']}")
        md.append("")

        # Urgent actions
        if report.urgent_actions:
            md.append("## 🚨 Urgent Actions Required")
            for action in report.urgent_actions:
                md.append(f"- {action}")
            md.append("")

        # Recommendations
        md.append("## Recommendations")
        for rec in report.security_recommendations:
            md.append(f"- {rec}")
        md.append("")

        # Anomalies
        if report.anomalies_detected:
            md.append("## Anomalies Detected")
            for anomaly in report.anomalies_detected[:5]:  # Top 5
                md.append(f"- **{anomaly['type']}:** {anomaly['description']}")
            md.append("")

        return "\n".join(md)

    def _generate_csv_summary(self, report: LogAnalysisReport) -> str:
        """Generate CSV summary of key metrics"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Metric", "Value"])

        # Basic metrics
        writer.writerow(["Report ID", report.report_id])
        writer.writerow(["Time Period", report.time_period])
        writer.writerow(["Total Events", report.total_events])
        writer.writerow(["Average Risk", f"{report.risk_summary['average_risk']:.2f}"])
        writer.writerow(["High Risk Events", report.risk_summary['high_risk_events']])
        writer.writerow(["Critical Risk Events", report.risk_summary['critical_risk_events']])

        # Top event types
        for event_type, count in list(report.event_breakdown.items())[:5]:
            writer.writerow([f"Events: {event_type}", count])

        return output.getvalue()

    def interactive_review(self):
        """Start interactive security log review session"""
        print("🔍 Security Log Interactive Review")
        print("=" * 50)

        while True:
            print("\nOptions:")
            print("1. Generate comprehensive report")
            print("2. Search events")
            print("3. Analyze time period")
            print("4. Export report")
            print("5. Exit")

            choice = input("\nSelect option (1-5): ").strip()

            if choice == "1":
                self._interactive_generate_report()
            elif choice == "2":
                self._interactive_search()
            elif choice == "3":
                self._interactive_time_analysis()
            elif choice == "4":
                self._interactive_export()
            elif choice == "5":
                print("Exiting interactive review.")
                break
            else:
                print("Invalid option. Please try again.")

    def _interactive_generate_report(self):
        """Interactive report generation"""
        print("\nGenerating comprehensive report...")
        period = input("Time period (1h/24h/7d/30d) [24h]: ").strip() or "24h"

        report = self.generate_comprehensive_report(period)

        print(f"\n📊 Security Report Summary:")
        print(f"Report ID: {report.report_id}")
        print(f"Total Events: {report.total_events}")
        print(f"Average Risk: {report.risk_summary['average_risk']:.2f}")
        print(f"High Risk Events: {report.risk_summary['high_risk_events']}")

        if report.urgent_actions:
            print(f"\n🚨 Urgent Actions ({len(report.urgent_actions)}):")
            for action in report.urgent_actions[:3]:
                print(f"- {action}")

        print(f"\n💡 Recommendations ({len(report.security_recommendations)}):")
        for rec in report.security_recommendations[:3]:
            print(f"- {rec}")

    def _interactive_search(self):
        """Interactive event search"""
        query = input("\nEnter search query: ").strip()
        if not query:
            print("No query provided.")
            return

        events = self.search_events(query)

        print(f"\n🔍 Found {len(events)} events matching '{query}':")
        for event in events[:10]:  # Show top 10
            severity_name = {0: "TRACE", 1: "DEBUG", 2: "INFO", 3: "NOTICE", 4: "WARNING",
                           5: "ERROR", 6: "CRITICAL", 7: "ALERT", 8: "EMERGENCY"}.get(event['severity'], "UNKNOWN")
            print(f"- [{event['timestamp']}] {severity_name}: {event['description']}")

    def _interactive_time_analysis(self):
        """Interactive time period analysis"""
        start_date = input("Start date (YYYY-MM-DD) [yesterday]: ").strip()
        if not start_date:
            start_time = (datetime.now() - timedelta(days=1)).isoformat()
        else:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d").isoformat()
            except ValueError:
                print("Invalid date format.")
                return

        events = self._get_events_in_period(start_time)

        print(f"\n📈 Time Period Analysis:")
        print(f"Events since {start_date or 'yesterday'}: {len(events)}")

        # Hourly breakdown
        hourly_counts = {}
        for event in events:
            try:
                hour = datetime.fromisoformat(event['timestamp']).strftime('%H:00')
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            except ValueError:
                continue

        if hourly_counts:
            print("\nHourly distribution:")
            for hour in sorted(hourly_counts.keys()):
                bar = "█" * min(hourly_counts[hour], 20)
                print(f"{hour}: {bar} ({hourly_counts[hour]})")

    def _interactive_export(self):
        """Interactive report export"""
        period = input("Time period for export (1h/24h/7d/30d) [24h]: ").strip() or "24h"
        format_choice = input("Export format (json/markdown/csv) [json]: ").strip() or "json"

        report = self.generate_comprehensive_report(period)
        exported_content = self.export_report(report, format_choice)

        filename = f"security_report_{report.report_id}.{format_choice}"

        try:
            with open(filename, 'w') as f:
                f.write(exported_content)
            print(f"\n✅ Report exported to: {filename}")
        except Exception as e:
            print(f"\n❌ Export failed: {e}")


def main():
    """Command line interface for security log analysis"""
    parser = argparse.ArgumentParser(description="Security Log Analysis Tools")
    parser.add_argument("--database", "-d", default="enhanced_security.db",
                       help="Security database path")
    parser.add_argument("--report", "-r", action="store_true",
                       help="Generate comprehensive report")
    parser.add_argument("--period", "-p", default="24h",
                       help="Time period (1h/24h/7d/30d)")
    parser.add_argument("--search", "-s", help="Search events")
    parser.add_argument("--export", "-e", help="Export format (json/markdown/csv)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Start interactive review")

    args = parser.parse_args()

    analyzer = SecurityLogAnalyzer(args.database)

    if args.interactive:
        analyzer.interactive_review()
    elif args.report:
        report = analyzer.generate_comprehensive_report(args.period)

        if args.export:
            content = analyzer.export_report(report, args.export)
            filename = f"security_report_{report.report_id}.{args.export}"
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Report exported to: {filename}")
        else:
            print(f"Security Report - {report.report_id}")
            print(f"Total Events: {report.total_events}")
            print(f"Average Risk: {report.risk_summary['average_risk']:.2f}")

            if report.urgent_actions:
                print(f"\nUrgent Actions:")
                for action in report.urgent_actions:
                    print(f"- {action}")

    elif args.search:
        events = analyzer.search_events(args.search)
        print(f"Found {len(events)} events matching '{args.search}'")
        for event in events[:10]:
            print(f"- {event['timestamp']}: {event['description']}")

    else:
        print("Use --help for usage information")


if __name__ == "__main__":
    main()