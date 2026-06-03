import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './design/Button';
import { 
  Sparkles, Folder, Settings, BarChart2, CreditCard, Shield, LogOut 
} from 'lucide-react';

export default function Sidebar() {
  const { user, orgs, currentOrg, logoutUser, selectOrg, loadWorkspaces } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [creatingOrg, setCreatingOrg] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');

  const handleOrgChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const slug = e.target.value;
    if (slug === 'CREATE_NEW') {
      // Toggle local overlay modal or redirect
      const name = prompt("Enter new workspace name:");
      if (name && name.trim()) {
        createNewWorkspace(name);
      }
      return;
    }
    selectOrg(slug);
  };

  const createNewWorkspace = async (name: string) => {
    try {
      const { api } = await import('../utils/api');
      await api.post('/api/workspaces/', { name });
      await loadWorkspaces();
    } catch (err) {
      console.error(err);
      alert("Failed to create workspace");
    }
  };

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const getLinkStyle = (path: string) => {
    return {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.6rem 0.8rem',
      borderRadius: '8px',
      color: isActive(path) ? 'hsl(var(--text-primary))' : 'hsl(var(--text-muted))',
      textDecoration: 'none',
      background: isActive(path) ? 'hsl(var(--border-muted) / 0.4)' : 'transparent',
      fontWeight: isActive(path) ? 600 : 500,
      transition: 'all 0.2s ease',
    };
  };

  return (
    <aside className="sidebar">
      <div>
        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem', textDecoration: 'none', color: 'inherit' }}>
          <Sparkles size={24} color="hsl(var(--accent-primary))" />
          <span style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>
            Viral<span style={{ color: 'hsl(var(--accent-primary))' }}>Ops</span>
          </span>
        </Link>

        {orgs.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'hsl(var(--text-dim))', display: 'block', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Workspace</label>
            <select 
              value={currentOrg?.slug} 
              onChange={handleOrgChange} 
              style={{ fontSize: '0.85rem', padding: '0.5rem', width: '100%', cursor: 'pointer' }}
            >
              {orgs.map(org => (
                <option key={org.slug} value={org.slug}>{org.name}</option>
              ))}
              <option value="CREATE_NEW">+ Create Workspace</option>
            </select>
          </div>
        )}

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <Link to="/dashboard" style={getLinkStyle('/dashboard')}>
            <Folder size={18} /> Projects
          </Link>
          
          <Link to="/preferences" style={getLinkStyle('/preferences')}>
            <Settings size={18} /> Brand Voice
          </Link>

          <Link to="/analytics" style={getLinkStyle('/analytics')}>
            <BarChart2 size={18} /> Analytics
          </Link>

          <Link to="/billing" style={getLinkStyle('/billing')}>
            <CreditCard size={18} /> Billing
          </Link>

          <Link to="/admin" style={getLinkStyle('/admin')}>
            <Shield size={18} /> Admin Center
          </Link>
        </nav>
      </div>

      <div>
        <div style={{ borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '1rem', marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-primary))' }}>{user?.username}</div>
          <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))' }}>Workspace Member</div>
        </div>
        <Button variant="secondary" onClick={handleLogout} style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem', justifyContent: 'center' }}>
          <LogOut size={16} /> Logout
        </Button>
      </div>
    </aside>
  );
}
