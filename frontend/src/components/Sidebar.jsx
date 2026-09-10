import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Home, BarChart2, User, LogOut, LayoutDashboard, Settings, Sparkles } from 'lucide-react';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [hoveredItem, setHoveredItem] = useState(null);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <Home size={18} /> },
    { name: 'Analytics', path: '/analytics', icon: <BarChart2 size={18} /> },
    { name: 'Profile', path: '/profile', icon: <User size={18} /> },
  ];

  if (user?.role === 'mentor' || user?.role === 'admin') {
    navItems.push({ name: 'Mentor View', path: '/mentor', icon: <LayoutDashboard size={18} /> });
  }
  
  if (user?.role === 'admin') {
    navItems.push({ name: 'Admin Panel', path: '/admin', icon: <Settings size={18} /> });
  }

  return (
    <aside
      className="glass-panel"
      style={{
        width: '250px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        margin: '1rem 0 1rem 1rem',
        position: 'relative',
        zIndex: 10,
        borderRadius: 'var(--radius-lg)',
      }}
    >
      {/* Logo */}
      <div style={{ marginBottom: '2rem', padding: '0.5rem 0.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.3)',
          }}>
            <Sparkles size={18} color="white" />
          </div>
          <div>
            <h2 className="text-gradient-primary" style={{ fontSize: '1.25rem', margin: 0, fontWeight: 800 }}>
              CogniRoom
            </h2>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const isHovered = hoveredItem === item.path;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onMouseEnter={() => setHoveredItem(item.path)}
              onMouseLeave={() => setHoveredItem(null)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                color: isActive ? '#ffffff' : isHovered ? 'var(--text-primary)' : 'var(--text-secondary)',
                background: isActive
                  ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))'
                  : isHovered
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'transparent',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.9rem',
                transition: 'all 0.2s ease',
                textDecoration: 'none',
                boxShadow: isActive ? '0 4px 15px rgba(99, 102, 241, 0.3)' : 'none',
              }}
            >
              <span>{item.icon}</span>
              {item.name}
            </NavLink>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      <div style={{ marginTop: 'auto', paddingTop: '1.25rem', borderTop: '1px solid var(--glass-border)' }}>
        <div style={{ marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            color: 'var(--accent-sky)',
            fontSize: '0.9rem',
          }}>
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {user?.name}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
              {user?.role}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            width: '100%',
            padding: '0.65rem 0.85rem',
            color: 'var(--text-muted)',
            transition: 'all 0.2s ease',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            fontWeight: 500,
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = 'var(--accent-rose)';
            e.currentTarget.style.background = 'rgba(244, 63, 94, 0.08)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.background = 'none';
          }}
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
