import React from 'react';
import { Search, Bell, User } from 'lucide-react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="search-container">
        <Search size={18} className="search-icon" />
        <input 
          type="text" 
          placeholder="Search across documents, reports, and knowledge base..." 
          className="search-input"
        />
        <div className="search-shortcut">Ctrl K</div>
      </div>
      
      <div className="header-actions">
        <button className="action-btn">
          <Bell size={20} />
          <span className="badge"></span>
        </button>
        <div className="user-profile">
          <div className="avatar">A</div>
          <span>Admin</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
