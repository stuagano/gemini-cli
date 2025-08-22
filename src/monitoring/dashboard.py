"""
DORA Metrics Dashboard
Real-time dashboard for monitoring DORA metrics and system health
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from .dora_metrics import DORAMetricsTracker

logger = logging.getLogger(__name__)

class DORADashboard:
    """Dashboard for visualizing DORA metrics and trends"""
    
    def __init__(self, tracker: DORAMetricsTracker):
        self.tracker = tracker
        self.app = FastAPI(title="DORA Metrics Dashboard")
        self.templates = Jinja2Templates(directory="templates")
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "DORA Metrics Dashboard"
            })
        
        @self.app.get("/api/metrics/{repository}")
        async def get_repository_metrics(repository: str, period_days: int = 7):
            """Get metrics for a specific repository"""
            metrics = await self.tracker.calculate_metrics(repository, period_days)
            return {
                "metrics": self._format_metrics_for_frontend(metrics),
                "charts": await self._generate_charts_data(repository)
            }
        
        @self.app.get("/api/dashboard/summary")
        async def get_dashboard_summary():
            """Get summary data for dashboard"""
            # Get metrics for all repositories (for demo, using single repo)
            repositories = ["gemini-cli"]  # This could be dynamic
            
            summary = {}
            for repo in repositories:
                metrics = await self.tracker.calculate_metrics(repo, 7)
                summary[repo] = self._format_metrics_for_frontend(metrics)
            
            return summary
        
        @self.app.get("/api/charts/{repository}")
        async def get_charts_data(repository: str):
            """Get chart data for repository"""
            return await self._generate_charts_data(repository)
        
        @self.app.get("/api/real-time/{repository}")
        async def get_realtime_data(repository: str):
            """Get real-time metrics for live dashboard"""
            # Get last 24 hours of data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            deployments = await self.tracker._get_deployments(repository, start_time, end_time)
            incidents = await self.tracker._get_incidents(repository, start_time, end_time)
            
            return {
                "deployments_today": len(deployments),
                "incidents_today": len(incidents),
                "last_deployment": deployments[-1] if deployments else None,
                "active_incidents": [i for i in incidents if not i.get('resolution_time')],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_metrics_for_frontend(self, metrics) -> Dict:
        """Format metrics for frontend consumption"""
        return {
            "deployment_frequency": {
                "value": round(metrics.deployment_frequency, 2),
                "unit": "per day",
                "level": metrics.deployment_frequency_level,
                "color": self._get_performance_color(metrics.deployment_frequency_level)
            },
            "lead_time": {
                "value": round(metrics.lead_time_for_changes, 1),
                "unit": "hours",
                "level": metrics.lead_time_level,
                "color": self._get_performance_color(metrics.lead_time_level)
            },
            "mttr": {
                "value": round(metrics.mean_time_to_recovery, 1),
                "unit": "hours",
                "level": metrics.mttr_level,
                "color": self._get_performance_color(metrics.mttr_level)
            },
            "change_failure_rate": {
                "value": round(metrics.change_failure_rate, 1),
                "unit": "%",
                "level": metrics.change_failure_level,
                "color": self._get_performance_color(metrics.change_failure_level)
            },
            "summary": {
                "total_deployments": metrics.total_deployments,
                "total_incidents": metrics.total_incidents,
                "period_start": metrics.period_start.isoformat(),
                "period_end": metrics.period_end.isoformat(),
                "overall_performance": self._calculate_overall_performance(metrics)
            }
        }
    
    def _get_performance_color(self, level: str) -> str:
        """Get color for performance level"""
        colors = {
            "Elite": "#22c55e",    # Green
            "High": "#3b82f6",     # Blue
            "Medium": "#f59e0b",   # Orange
            "Low": "#ef4444"       # Red
        }
        return colors.get(level, "#6b7280")
    
    def _calculate_overall_performance(self, metrics) -> Dict:
        """Calculate overall performance score"""
        levels = [
            metrics.deployment_frequency_level,
            metrics.lead_time_level,
            metrics.mttr_level,
            metrics.change_failure_level
        ]
        
        elite_count = levels.count("Elite")
        high_count = levels.count("High")
        
        if elite_count >= 3:
            overall = "Elite"
        elif elite_count + high_count >= 3:
            overall = "High"
        elif elite_count + high_count >= 2:
            overall = "Medium"
        else:
            overall = "Low"
        
        score = (elite_count * 4 + high_count * 3 + 
                levels.count("Medium") * 2 + levels.count("Low") * 1) / 4
        
        return {
            "level": overall,
            "score": round(score, 1),
            "color": self._get_performance_color(overall)
        }
    
    async def _generate_charts_data(self, repository: str) -> Dict:
        """Generate chart data for dashboard"""
        trends = await self.tracker.get_trends(repository, weeks=12)
        
        # Deployment frequency chart
        deployment_chart = {
            "type": "line",
            "data": {
                "labels": trends["weeks"],
                "datasets": [{
                    "label": "Deployments per Day",
                    "data": trends["deployment_frequency"],
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Deployment Frequency Trend"}
                }
            }
        }
        
        # Lead time chart
        lead_time_chart = {
            "type": "line",
            "data": {
                "labels": trends["weeks"],
                "datasets": [{
                    "label": "Lead Time (hours)",
                    "data": trends["lead_time"],
                    "borderColor": "#10b981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Lead Time Trend"}
                }
            }
        }
        
        # MTTR chart
        mttr_chart = {
            "type": "bar",
            "data": {
                "labels": trends["weeks"],
                "datasets": [{
                    "label": "MTTR (hours)",
                    "data": trends["mttr"],
                    "backgroundColor": "#f59e0b",
                    "borderColor": "#d97706",
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Mean Time to Recovery"}
                }
            }
        }
        
        # Change failure rate chart
        failure_chart = {
            "type": "line",
            "data": {
                "labels": trends["weeks"],
                "datasets": [{
                    "label": "Failure Rate (%)",
                    "data": trends["change_failure_rate"],
                    "borderColor": "#ef4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Change Failure Rate"}
                }
            }
        }
        
        return {
            "deployment_frequency": deployment_chart,
            "lead_time": lead_time_chart,
            "mttr": mttr_chart,
            "change_failure_rate": failure_chart
        }
    
    async def generate_static_report(self, repository: str, output_path: str):
        """Generate static HTML report"""
        metrics = await self.tracker.calculate_metrics(repository, 30)  # 30 days
        trends = await self.tracker.get_trends(repository, 12)  # 12 weeks
        
        # Create plotly figures
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Deployment Frequency', 'Lead Time', 
                          'Mean Time to Recovery', 'Change Failure Rate'),
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                   [{"secondary_y": True}, {"secondary_y": True}]]
        )
        
        # Add deployment frequency
        fig.add_trace(
            go.Scatter(x=trends["weeks"], y=trends["deployment_frequency"],
                      mode='lines+markers', name='Deployments/day',
                      line=dict(color='blue')),
            row=1, col=1
        )
        
        # Add lead time
        fig.add_trace(
            go.Scatter(x=trends["weeks"], y=trends["lead_time"],
                      mode='lines+markers', name='Lead Time (h)',
                      line=dict(color='green')),
            row=1, col=2
        )
        
        # Add MTTR
        fig.add_trace(
            go.Bar(x=trends["weeks"], y=trends["mttr"],
                   name='MTTR (h)', marker_color='orange'),
            row=2, col=1
        )
        
        # Add change failure rate
        fig.add_trace(
            go.Scatter(x=trends["weeks"], y=trends["change_failure_rate"],
                      mode='lines+markers', name='Failure Rate (%)',
                      line=dict(color='red')),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text=f"DORA Metrics Report - {repository}",
            showlegend=False,
            height=800
        )
        
        # Save as HTML
        fig.write_html(output_path, include_plotlyjs='cdn')
        
        return output_path

# Template for dashboard HTML
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .metric-card {
            @apply bg-white rounded-lg shadow-md p-6 m-4;
        }
        .metric-value {
            @apply text-3xl font-bold;
        }
        .metric-label {
            @apply text-sm text-gray-600 uppercase tracking-wide;
        }
        .performance-badge {
            @apply px-3 py-1 rounded-full text-sm font-medium;
        }
    </style>
</head>
<body class="bg-gray-100">
    <div id="app" class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-gray-900">DORA Metrics Dashboard</h1>
            <p class="text-gray-600 mt-2">Software delivery performance metrics</p>
        </header>
        
        <div id="metrics-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <!-- Metrics cards will be inserted here -->
        </div>
        
        <div id="charts-grid" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Charts will be inserted here -->
        </div>
    </div>
    
    <script>
        // Dashboard JavaScript
        class DORADashboard {
            constructor() {
                this.repository = 'gemini-cli';
                this.refreshInterval = 60000; // 1 minute
                this.init();
            }
            
            async init() {
                await this.loadMetrics();
                await this.loadCharts();
                this.startAutoRefresh();
            }
            
            async loadMetrics() {
                try {
                    const response = await fetch(`/api/metrics/${this.repository}`);
                    const data = await response.json();
                    this.renderMetrics(data.metrics);
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }
            
            async loadCharts() {
                try {
                    const response = await fetch(`/api/charts/${this.repository}`);
                    const chartsData = await response.json();
                    this.renderCharts(chartsData);
                } catch (error) {
                    console.error('Error loading charts:', error);
                }
            }
            
            renderMetrics(metrics) {
                const grid = document.getElementById('metrics-grid');
                grid.innerHTML = '';
                
                Object.entries(metrics).forEach(([key, metric]) => {
                    if (key === 'summary') return;
                    
                    const card = document.createElement('div');
                    card.className = 'metric-card';
                    card.innerHTML = `
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="metric-label">${key.replace('_', ' ')}</div>
                                <div class="metric-value" style="color: ${metric.color}">
                                    ${metric.value} ${metric.unit}
                                </div>
                            </div>
                            <div class="performance-badge" style="background-color: ${metric.color}20; color: ${metric.color}">
                                ${metric.level}
                            </div>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            }
            
            renderCharts(chartsData) {
                const grid = document.getElementById('charts-grid');
                grid.innerHTML = '';
                
                Object.entries(chartsData).forEach(([key, chartConfig]) => {
                    const container = document.createElement('div');
                    container.className = 'bg-white rounded-lg shadow-md p-6';
                    
                    const canvas = document.createElement('canvas');
                    canvas.id = `chart-${key}`;
                    container.appendChild(canvas);
                    grid.appendChild(container);
                    
                    new Chart(canvas, chartConfig);
                });
            }
            
            startAutoRefresh() {
                setInterval(() => {
                    this.loadMetrics();
                }, this.refreshInterval);
            }
        }
        
        // Initialize dashboard when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            new DORADashboard();
        });
    </script>
</body>
</html>
"""

def create_dashboard_app(tracker: DORAMetricsTracker) -> FastAPI:
    """Create and configure the dashboard app"""
    dashboard = DORADashboard(tracker)
    
    # Create templates directory and save template
    import os
    os.makedirs('templates', exist_ok=True)
    with open('templates/dashboard.html', 'w') as f:
        f.write(DASHBOARD_TEMPLATE)
    
    return dashboard.app