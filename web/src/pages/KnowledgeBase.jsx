import React, { useState, useEffect } from 'react';
import { BookOpen, FileText, Upload, MoreHorizontal, File, FileSpreadsheet, FileBarChart2 } from 'lucide-react';
import './KnowledgeBase.css';

const KnowledgeBase = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

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

  const getFileIcon = (filename) => {
    if (!filename) return <File size={16} />;
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'pdf') return <FileText size={16} className="text-red" />;
    if (ext === 'xlsx' || ext === 'csv') return <FileSpreadsheet size={16} className="text-green" />;
    if (ext === 'pptx') return <FileBarChart2 size={16} className="text-orange" />;
    return <File size={16} className="text-blue" />;
  };

  const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks || 0), 0);
  const departments = new Set(documents.map(d => d.access_level)).size;

  return (
    <div className="knowledge-base">
      <div className="kb-header">
        <div>
          <h1 className="page-title">Knowledge Base</h1>
          <p className="page-subtitle">Manage, search, and analyze your enterprise documents</p>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => document.getElementById('global-upload-input')?.click()}
        >
          <Upload size={16}/> Upload Documents
        </button>
      </div>

      <div className="kb-stats-grid">
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper"><FileText size={20} className="text-blue"/></div>
          <div className="stat-details">
            <span className="stat-label">Total Documents</span>
            <span className="stat-value">{documents.length}</span>
          </div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper"><BookOpen size={20} className="text-purple"/></div>
          <div className="stat-details">
            <span className="stat-label">Total Chunks</span>
            <span className="stat-value">{totalChunks.toLocaleString()}</span>
          </div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper"><FileSpreadsheet size={20} className="text-green"/></div>
          <div className="stat-details">
            <span className="stat-label">Departments</span>
            <span className="stat-value">{departments}</span>
          </div>
        </div>
      </div>

      <div className="kb-table-container glass-panel">
        <table className="kb-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Department</th>
              <th>Chunks</th>
              <th>Uploaded On</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" style={{textAlign:'center', padding:'2rem'}}>Loading documents...</td></tr>
            ) : documents.length === 0 ? (
              <tr><td colSpan="7" style={{textAlign:'center', padding:'2rem'}}>No documents indexed yet.</td></tr>
            ) : (
              documents.map((doc, i) => {
                const ext = doc.filename ? doc.filename.split('.').pop().toUpperCase() : 'UNKNOWN';
                return (
                  <tr key={i}>
                    <td>
                      <div className="doc-name">
                        {getFileIcon(doc.filename)}
                        {doc.filename}
                      </div>
                    </td>
                    <td><span className="doc-type">{ext}</span></td>
                    <td style={{textTransform:'capitalize'}}>{doc.access_level}</td>
                    <td>{doc.chunks}</td>
                    <td>{new Date(doc.created_at + 'Z').toLocaleDateString()}</td>
                    <td><span className="badge-success">● Indexed</span></td>
                    <td><button className="btn-icon"><MoreHorizontal size={16}/></button></td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default KnowledgeBase;
