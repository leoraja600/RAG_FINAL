import React, { useState, useEffect } from 'react';
import { Activity, Clock, Target, Database, TrendingUp, Users } from 'lucide-react';
import './Analytics.css';

const Analytics = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then(res => res.json())
      .then(data => setStats(data.stats))
      .catch(console.error);
  }, []);

  return (
    <div className="analytics-page">
      <div className="header-row">
        <div>
          <h1 className="page-title">Analytics & System Monitoring</h1>
          <p className="page-subtitle">Track system performance, usage, and insights</p>
        </div>
      </div>

      <div className="metrics-row">
        <div className="metric-card glass-panel">
          <div className="metric-header">
            <Activity size={18} className="text-purple"/>
            <span>Total Queries</span>
          </div>
          <div className="metric-value">{stats ? stats.queries : '--'} <span className="trend positive">↑ 12%</span></div>
        </div>
        
        <div className="metric-card glass-panel">
          <div className="metric-header">
            <Clock size={18} className="text-blue"/>
            <span>Avg Response Time</span>
          </div>
          <div className="metric-value">5.7s <span className="trend positive">↓ 1.3s</span></div>
        </div>

        <div className="metric-card glass-panel">
          <div className="metric-header">
            <Target size={18} className="text-red"/>
            <span>Retrieval Accuracy</span>
          </div>
          <div className="metric-value">92% <span className="trend positive">↑ 4%</span></div>
        </div>

        <div className="metric-card glass-panel">
          <div className="metric-header">
            <Database size={18} className="text-purple"/>
            <span>Documents Indexed</span>
          </div>
          <div className="metric-value">{stats ? stats.documents : '--'} <span className="trend positive">↑ 8%</span></div>
        </div>

        <div className="metric-card glass-panel">
          <div className="metric-header">
            <Users size={18} className="text-blue"/>
            <span>Active Users</span>
          </div>
          <div className="metric-value">36 <span className="trend positive">↑ 20%</span></div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-panel glass-panel">
          <h3>Query Trends</h3>
          <div className="mock-chart area-chart">
            {/* SVG mock for area chart */}
            <svg viewBox="0 0 400 100" preserveAspectRatio="none">
              <path d="M0,80 Q50,90 100,50 T200,40 T300,70 T400,20 L400,100 L0,100 Z" fill="rgba(123, 97, 255, 0.2)" />
              <path d="M0,80 Q50,90 100,50 T200,40 T300,70 T400,20" fill="none" stroke="var(--accent-purple)" strokeWidth="3" />
            </svg>
            <div className="x-axis">
              <span>Sep 7</span><span>Sep 12</span><span>Sep 17</span><span>Sep 22</span><span>Sep 27</span><span>Oct 2</span><span>Oct 6</span>
            </div>
          </div>
        </div>

        <div className="chart-panel glass-panel">
          <h3>System Performance</h3>
          <div className="mock-chart line-chart">
             {/* SVG mock for multi-line chart */}
             <svg viewBox="0 0 400 100" preserveAspectRatio="none">
              <path d="M0,40 L50,45 L100,30 L150,50 L200,35 L250,40 L300,20 L350,30 L400,15" fill="none" stroke="var(--accent-green)" strokeWidth="2" />
              <circle cx="200" cy="35" r="4" fill="var(--accent-green)" />
              
              <path d="M0,70 L50,65 L100,75 L150,60 L200,80 L250,65 L300,70 L350,55 L400,60" fill="none" stroke="var(--accent-purple)" strokeWidth="2" />
              <circle cx="200" cy="80" r="4" fill="var(--accent-purple)" />
            </svg>
            <div className="x-axis">
              <span>Sep 7</span><span>Sep 12</span><span>Sep 17</span><span>Sep 22</span><span>Sep 27</span><span>Oct 2</span><span>Oct 6</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
