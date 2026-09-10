import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import GlassCard from '../components/GlassCard';
import { User, Mail, Shield, Camera, Bell, Moon, LogOut } from 'lucide-react';
import { motion } from 'framer-motion';

const Profile = () => {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState(true);
  const [cameraAutoStart, setCameraAutoStart] = useState(false);

  if (!user) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} style={{ maxWidth: '850px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.4rem', fontWeight: 800 }}>
          User <span className="text-gradient-primary">Profile</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Manage your personal details, permissions, and app preferences.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '1.5rem' }}>
        
        {/* Profile Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <GlassCard>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
              <div style={{ 
                width: '72px', height: '72px', borderRadius: '50%', 
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 8px 20px rgba(99, 102, 241, 0.3)'
              }}>
                <span style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>
                  {user.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h2 style={{ fontSize: '1.5rem', margin: 0, fontWeight: 700 }}>{user.name}</h2>
                <span style={{
                  display: 'inline-block',
                  color: 'var(--accent-sky)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  marginTop: '0.2rem',
                  textTransform: 'capitalize'
                }}>
                  {user.role} Account
                </span>
              </div>
            </div>

            <div style={{ paddingTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>Full Name</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                  <User size={16} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.95rem', fontWeight: 500 }}>{user.name}</span>
                </div>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>Email Address</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                  <Mail size={16} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.95rem', fontWeight: 500 }}>{user.email}</span>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.35rem', fontWeight: 600 }}>Role & Access Level</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                  <Shield size={16} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.95rem', fontWeight: 500, textTransform: 'capitalize' }}>{user.role}</span>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Preferences & Sign Out */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <GlassCard title="Preferences">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              <div className="flex-between">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Bell size={16} color="var(--accent-secondary)" />
                  <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>Notifications</span>
                </div>
                <div 
                  onClick={() => setNotifications(!notifications)}
                  style={{ 
                    width: '38px', height: '20px', borderRadius: '10px', 
                    background: notifications ? 'var(--accent-primary)' : 'rgba(255,255,255,0.15)',
                    position: 'relative', cursor: 'pointer', transition: 'all 0.2s'
                  }}
                >
                  <div style={{ 
                    position: 'absolute', top: '2px', left: notifications ? '20px' : '2px', 
                    width: '16px', height: '16px', borderRadius: '50%', background: 'white', transition: 'all 0.2s' 
                  }} />
                </div>
              </div>

              <div className="flex-between">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Camera size={16} color="var(--accent-sky)" />
                  <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>Auto Camera</span>
                </div>
                <div 
                  onClick={() => setCameraAutoStart(!cameraAutoStart)}
                  style={{ 
                    width: '38px', height: '20px', borderRadius: '10px', 
                    background: cameraAutoStart ? 'var(--accent-primary)' : 'rgba(255,255,255,0.15)',
                    position: 'relative', cursor: 'pointer', transition: 'all 0.2s'
                  }}
                >
                  <div style={{ 
                    position: 'absolute', top: '2px', left: cameraAutoStart ? '20px' : '2px', 
                    width: '16px', height: '16px', borderRadius: '50%', background: 'white', transition: 'all 0.2s' 
                  }} />
                </div>
              </div>

              <div className="flex-between">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Moon size={16} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Dark Mode</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.06)', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>Active</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard style={{ borderLeft: '4px solid var(--accent-rose)' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: 'var(--accent-rose)', fontWeight: 600 }}>Sign Out</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              End your active session.
            </p>
            <button 
              onClick={logout}
              className="btn-secondary"
              style={{ 
                width: '100%', 
                color: 'var(--accent-rose)',
                borderColor: 'rgba(244,63,94,0.3)',
                background: 'rgba(244,63,94,0.08)'
              }}
            >
              <LogOut size={16} /> Sign Out
            </button>
          </GlassCard>
        </div>

      </div>
    </motion.div>
  );
};

export default Profile;
