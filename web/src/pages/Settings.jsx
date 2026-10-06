import React from 'react';
import { Settings as SettingsIcon, Key, User, Shield, HardDrive, Bell } from 'lucide-react';
import './Settings.css';

const Settings = () => {
  return (
    <div className="settings-page">
      <div className="header-row">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure your EKI-Agent environment and preferences</p>
        </div>
      </div>

      <div className="settings-container">
        <div className="settings-sidebar">
          <button className="settings-tab active"><SettingsIcon size={16}/> General</button>
          <button className="settings-tab"><Key size={16}/> API Keys</button>
          <button className="settings-tab"><User size={16}/> Role Management</button>
          <button className="settings-tab"><HardDrive size={16}/> Vector Database</button>
          <button className="settings-tab"><Shield size={16}/> Security</button>
          <button className="settings-tab"><Bell size={16}/> Notifications</button>
        </div>

        <div className="settings-content glass-panel">
          
          <section className="settings-section">
            <h3>General Preferences</h3>
            <p className="section-desc">Manage your basic application settings.</p>
            
            <div className="form-group">
              <label>Default LLM Model</label>
              <select className="form-input">
                <option>qwen/qwen3.8-27b</option>
                <option>llama-3.1-70b-versatile</option>
                <option>mixtral-8x7b-32768</option>
              </select>
            </div>

            <div className="form-group">
              <label>System Prompt (Global)</label>
              <textarea 
                className="form-input" 
                rows={4} 
                defaultValue="You are EKI-Agent, an enterprise knowledge AI. Always cite your sources and provide highly accurate answers based strictly on the provided context."
              />
            </div>
          </section>

          <hr className="divider" />

          <section className="settings-section">
            <h3>Retrieval Configuration</h3>
            <p className="section-desc">Tune how the agent fetches information.</p>
            
            <div className="form-row">
              <div className="form-group flex-1">
                <label>Top-K Chunks to Retrieve</label>
                <input type="number" className="form-input" defaultValue={10} />
              </div>
              <div className="form-group flex-1">
                <label>Minimum Relevance Score</label>
                <input type="number" className="form-input" defaultValue={0.65} step={0.05} />
              </div>
            </div>

            <div className="form-group checkbox-group">
              <input type="checkbox" id="hybrid" defaultChecked />
              <label htmlFor="hybrid">Enable Hybrid Search (Semantic + BM25)</label>
            </div>
            
            <div className="form-group checkbox-group">
              <input type="checkbox" id="rerank" defaultChecked />
              <label htmlFor="rerank">Use Cross-Encoder Reranking</label>
            </div>
          </section>

          <div className="settings-actions">
            <button className="btn-secondary">Cancel</button>
            <button className="btn-primary">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
