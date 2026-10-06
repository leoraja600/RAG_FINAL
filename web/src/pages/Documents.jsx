import React, { useState, useEffect } from 'react';
import { Folder, FileText, Search, MoreVertical, Star, Clock } from 'lucide-react';
import './Documents.css';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocs = documents.filter(doc => 
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="documents-page">
      <div className="header-row">
        <div>
          <h1 className="page-title">Document Explorer</h1>
          <p className="page-subtitle">Browse and manage raw files before vectorization</p>
        </div>
      </div>

      <div className="docs-container">
        <div className="docs-sidebar glass-panel">
          <div className="docs-search">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search files..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <div className="nav-section">
            <h4 className="nav-title">Quick Access</h4>
            <ul className="nav-list">
              <li className="nav-item active"><Clock size={16}/> Recent</li>
              <li className="nav-item"><Star size={16}/> Starred</li>
              <li className="nav-item"><Folder size={16}/> All Files</li>
            </ul>
          </div>

          <div className="nav-section">
            <h4 className="nav-title">Departments</h4>
            <ul className="nav-list">
              <li className="nav-item"><Folder size={16} className="text-blue"/> Finance</li>
              <li className="nav-item"><Folder size={16} className="text-purple"/> HR</li>
              <li className="nav-item"><Folder size={16} className="text-green"/> Engineering</li>
              <li className="nav-item"><Folder size={16} className="text-orange"/> Marketing</li>
            </ul>
          </div>
        </div>

        <div className="docs-content glass-panel">
          <div className="docs-toolbar">
            <h3>Recent Files ({filteredDocs.length})</h3>
            <div className="toolbar-actions">
              <button className="btn-secondary">New Folder</button>
              <button 
                className="btn-primary"
                onClick={() => document.getElementById('global-upload-input')?.click()}
              >
                Upload File
              </button>
            </div>
          </div>

          <div className="files-grid">
            {loading ? (
              <div style={{color: 'var(--text-secondary)'}}>Loading documents...</div>
            ) : filteredDocs.length === 0 ? (
              <div style={{color: 'var(--text-secondary)'}}>No documents found.</div>
            ) : (
              filteredDocs.map((doc, i) => {
                const ext = doc.filename ? doc.filename.split('.').pop().toLowerCase() : 'txt';
                let iconClass = 'txt';
                if (ext === 'pdf') iconClass = 'pdf';
                if (ext === 'csv' || ext === 'xlsx') iconClass = 'csv';
                if (ext === 'pptx') iconClass = 'pptx';
                
                return (
                  <div key={i} className="file-card">
                    <div className={`file-icon-wrapper ${iconClass}`}><FileText size={32}/></div>
                    <div className="file-details">
                      <span className="file-name" title={doc.filename}>{doc.filename}</span>
                      <span className="file-meta">{new Date(doc.created_at + 'Z').toLocaleDateString()}</span>
                    </div>
                    <button className="btn-icon"><MoreVertical size={16}/></button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documents;
