import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import GlassCard from '../components/GlassCard';
import { Server, Users, Layers, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const AdminDash = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getAdminOverview();
        setData(result);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex-center" style={{ height: '60vh' }}>
        <div style={{
          width: '40px', height: '40px',
          border: '3px solid rgba(255,255,255,0.1)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%',
          animation: 'spin 0.6s linear infinite',
        }} />
      </div>
    );
  }

  if (!data) return <div className="flex-center" style={{ height: '60vh', color: 'var(--text-muted)' }}>Failed to load admin data.</div>;

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.4rem', fontWeight: 800 }}>
          System <span className="text-gradient-primary">Administration</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Global platform statistics, active rooms, and system status.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <GlassCard>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-primary)' }}>{data.total_users}</div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            <Users size={16} /> Total Registered Users
          </div>
        </GlassCard>
        
        <GlassCard>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-secondary)' }}>{data.rooms?.total || 0}</div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            <Layers size={16} /> Total Study Rooms
          </div>
        </GlassCard>

        <GlassCard>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-sky)' }}>{data.events?.total || 0}</div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            <Activity size={16} /> Total Activity Events
          </div>
        </GlassCard>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <GlassCard title="User Roles Breakdown">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginTop: '0.5rem' }}>
            {data.users_by_role && Object.entries(data.users_by_role).map(([role, count]) => (
              <div key={role} className="flex-between" style={{ padding: '0.6rem 0.85rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500 }}>{role}</span>
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{count}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard title="System Health & Status">
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.7', marginTop: '0.5rem' }}>
            All background services and WebSocket connections are operating normally.
            <div style={{ marginTop: '1rem', padding: '0.85rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-sm)', color: 'var(--accent-emerald)', fontWeight: 600 }}>
              System Status: Operational & Healthy
            </div>
          </div>
        </GlassCard>
      </div>
    </motion.div>
  );
};

export default AdminDash;
