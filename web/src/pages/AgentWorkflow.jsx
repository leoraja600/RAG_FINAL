import React from 'react';
import { Play, CheckCircle2, AlertCircle } from 'lucide-react';
import './AgentWorkflow.css';

const AgentWorkflow = () => {
  return (
    <div className="agent-workflow">
      <div className="header-row">
        <div>
          <h1 className="page-title">Multi-Agent Workflow</h1>
          <p className="page-subtitle">Visualize how EKI-Agent processes your query</p>
        </div>
        <button className="btn-run-example"><Play size={16}/> Run Example</button>
      </div>

      <div className="workflow-container glass-panel">
        <div className="workflow-diagram">
          <div className="node user-node">
            <span className="node-title">User Query</span>
            <span className="node-desc">"What is the Financial Stability Report?"</span>
          </div>
          
          <div className="connector vertical"></div>
          
          <div className="agents-row">
            <div className="node agent-node">
              <span className="node-title">Query Planner</span>
              <span className="node-desc">Analyzes query & determines tasks</span>
            </div>
            <div className="node agent-node active-node">
              <span className="node-title">Retrieval Agent</span>
              <span className="node-desc">Hybrid search (vector + keyword)</span>
            </div>
            <div className="node agent-node">
              <span className="node-title">Document Agent</span>
              <span className="node-desc">Processes & extracts context</span>
            </div>
            <div className="node agent-node">
              <span className="node-title">Reasoning Agent</span>
              <span className="node-desc">Generates answer with citations</span>
            </div>
          </div>
          
          <div className="connector vertical"></div>
          
          <div className="node critic-node">
            <span className="node-title">Critic / Validation Agent</span>
            <span className="node-desc">Evaluates answer, checks grounding, triggers self-correction if needed</span>
          </div>
          
          <div className="connector-fork">
            <div className="path path-no">
              <span>No (Self-Correct)</span>
              <div className="arrow-up-left"></div>
            </div>
            <div className="path path-yes">
              <div className="connector vertical short"></div>
              <span>Answer Valid?</span>
              <div className="connector vertical short"></div>
            </div>
          </div>
          
          <div className="node final-node">
            <span className="node-title"><CheckCircle2 size={16} className="text-green"/> Final Answer</span>
            <span className="node-desc">With citations & provenance</span>
          </div>
        </div>

        <div className="execution-steps">
          <h3>Agent Execution Steps</h3>
          <ul className="steps-list">
            <li className="step-item completed">
              <div className="step-badge">1</div>
              <div className="step-info">
                <h4>Query Planning</h4>
                <p>• Understand query<br/>• Identify document types<br/>• Plan retrieval strategy</p>
              </div>
              <span className="step-time">0.8s</span>
            </li>
            <li className="step-item active">
              <div className="step-badge pulse">2</div>
              <div className="step-info">
                <h4>Hybrid Retrieval</h4>
                <p>• Semantic search (Vector DB)<br/>• Keyword search (BM25)<br/>• Rerank results</p>
              </div>
              <span className="step-time">1.4s</span>
            </li>
            <li className="step-item pending">
              <div className="step-badge">3</div>
              <div className="step-info">
                <h4>Document Processing</h4>
                <p>• Extract relevant chunks</p>
              </div>
              <span className="step-time">--</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AgentWorkflow;
