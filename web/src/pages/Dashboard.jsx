import React, { useState } from 'react';
import { Sparkles, CheckCircle2, ShieldCheck, Play, Paperclip, ChevronDown, AlignLeft } from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleRunAgent = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, user_role: 'admin' })
      });
      const data = await response.json();
      console.log('Agent Response:', data);
      setResult(data);
    } catch (err) {
      console.error(err);
      alert('Error connecting to backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="hero-section">
        <h3 className="hero-subtitle">🧠 EKI-Agent: Agentic Multimodal RAG • Hybrid Retrieval • Self-Correction • Provenance</h3>
        <h1 className="hero-title">Ask the <span className="gradient-text">enterprise</span><br/>knowledge base</h1>
        <p className="hero-description">
          Get accurate answers from your organization's documents, reports, and data<br/>
          using advanced AI agents with citations and provenance.
        </p>
        
        <div className="feature-pills">
          <span className="pill"><Sparkles size={14} className="pill-icon text-blue"/> Multi-format Support</span>
          <span className="pill"><AlignLeft size={14} className="pill-icon text-purple"/> Cited Sources</span>
          <span className="pill"><CheckCircle2 size={14} className="pill-icon text-yellow"/> Self-Correction</span>
          <span className="pill"><ShieldCheck size={14} className="pill-icon text-blue"/> Enterprise Ready</span>
        </div>
      </div>

      <div className="query-section glass-panel">
        <div className="query-tabs">
          <button className="tab active"><Sparkles size={16}/> Ask a Question</button>
          <button className="tab"><Paperclip size={16}/> Upload & Analyze</button>
          <button className="tab"><AlignLeft size={16}/> Summarize</button>
          <button className="tab">Compare</button>
          <button className="tab">Agent Workflows</button>
        </div>
        
        <div className="query-input-wrapper">
          <textarea 
            placeholder="What would you like to know from your enterprise knowledge base?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="query-textarea"
            rows={4}
          />
          <div className="char-count">{query.length}/4000</div>
        </div>
        
        <div className="query-controls">
          <div className="controls-left">
            <button 
              className="control-btn"
              onClick={() => document.getElementById('global-upload-input')?.click()}
            >
              <Paperclip size={16}/> Attach Files
            </button>
            <div className="control-divider"></div>
            <span className="control-label">Search Mode</span>
            <button className="control-btn drop-btn">Hybrid (Semantic + Keyword) <ChevronDown size={14}/></button>
            <button className="control-btn drop-btn"><AlignLeft size={16}/> All Documents <ChevronDown size={14}/></button>
          </div>
          
          <button 
            className="btn-run" 
            onClick={handleRunAgent}
            disabled={loading || !query.trim()}
          >
            <Play size={16} fill="currentColor"/> 
            {loading ? 'Running...' : 'Run EKI-Agent'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing query & retrieving context...</p>
        </div>
      )}

      {result && (
        <div className="result-section">
          <div className="answer-card glass-panel">
            <h3 className="card-title"><Sparkles size={18} className="text-green"/> Answer</h3>
            <p className="answer-text">{result.answer}</p>
          </div>
          
          {result.citations && result.citations.length > 0 && (
            <div className="citations-card glass-panel">
              <h3 className="card-title">Retrieved Context ({result.citations.length} Chunks)</h3>
              <div className="citations-list">
                {result.citations.map((c, i) => (
                  <div key={i} className="citation-item">
                    <div className="citation-header">
                      <span className="citation-source">Chunk {i+1} - {c.source || 'Unknown Source'} (Page {c.page || '?'})</span>
                      <span className="citation-score">{c.score ? c.score.toFixed(2) : ''}</span>
                    </div>
                    <p className="citation-text">"{c.text}"</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
