import React, { useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  MessageSquare, BookOpen, FileText, Settings,
  BarChart2, Workflow, UploadCloud, UserCircle, Loader2
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = () => {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('access_level', 'public'); // Default for now

    try {
      const response = await fetch('http://127.0.0.1:8000/documents/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        alert(`Successfully indexed ${data.chunks} chunks from ${data.filename}`);
      } else {
        alert('Upload failed: ' + (data.detail || 'Unknown error'));
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to backend for upload.');
    } finally {
      setUploading(false);
      // Reset input
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-icon">🧠</div>
        <h2>EKI-Agent</h2>
      </div>

      <nav className="nav-menu">
        <NavLink to="/" className={({isActive}) => isActive ? "nav-item active" : "nav-item"} end>
          <MessageSquare size={18} /> Chat
        </NavLink>
        <NavLink to="/knowledge" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <BookOpen size={18} /> Knowledge Base
        </NavLink>
        <NavLink to="/documents" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <FileText size={18} /> Documents
        </NavLink>
        <NavLink to="/workflow" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Workflow size={18} /> Agent Workflow
        </NavLink>
        <NavLink to="/analytics" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <BarChart2 size={18} /> Analytics
        </NavLink>
        <NavLink to="/settings" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Settings size={18} /> Settings
        </NavLink>
      </nav>

      <div className="sidebar-section">
        <div className="section-title">ENTERPRISE ACCESS</div>
        <div className="role-selector">
          <UserCircle size={20} className="role-icon" />
          <div className="role-details">
            <span className="role-label">User Role</span>
            <span className="role-value">admin</span>
          </div>
        </div>
        <div className="info-box">
          ℹ️ Demo mode: public documents are available to all roles; department documents are available to matching roles.
        </div>
      </div>

      <div className="sidebar-section">
        <div className="section-title">UPLOAD KNOWLEDGE</div>
        <div className="upload-dropzone" onClick={handleUploadClick}>
          <input 
            id="global-upload-input"
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            style={{ display: 'none' }} 
            accept=".pdf,.pptx,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
          />
          {uploading ? (
            <Loader2 size={24} className="upload-icon spinning" />
          ) : (
            <UploadCloud size={24} className="upload-icon" />
          )}
          <p>Drag and drop files here<br/><span>or click to browse</span></p>
          <span className="upload-limit">Max file size: 20MB per file<br/>(PDF, PPTX, XLSX, CSV, TXT, IMG)</span>
          <button className="btn-browse" disabled={uploading}>
            {uploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
