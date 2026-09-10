import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import GlassCard from '../components/GlassCard';
import { Users, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

const MentorDash = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getMentorOverview();
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

  if (!data) return <div className="flex-center" style={{ height: '60vh', color: 'var(--text-muted)' }}>Failed to load mentor data.</div>;

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.4rem', fontWeight: 800 }}>
          Mentor <span className="text-gradient-primary">Dashboard</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Real-time monitoring and support for your study rooms.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <GlassCard>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-primary)' }}>{data.total_rooms}</div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            <Users size={16} /> Total Rooms Monitored
          </div>
        </GlassCard>
        
        <GlassCard>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
            {data.rooms.reduce((acc, room) => acc + (room.high_risk_students || 0), 0)}
          </div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            <AlertTriangle size={16} /> At-Risk Students
          </div>
        </GlassCard>
      </div>

      <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 700 }}>Monitored Rooms</h2>
      
      {data.rooms.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No rooms currently active.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {data.rooms.map(room => {
            const riskCount = room.high_risk_students || 0;
            return (
              <GlassCard key={room.room_id} style={{ padding: '1.25rem 1.5rem' }}>
                <div className="flex-between">
                  <div>
                    <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.1rem', fontWeight: 600 }}>
                      {room.room_name} <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>#{room.room_id}</span>
                    </h3>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {room.total_members || 0} Members • {room.total_events || 0} Interactions
                    </div>
                  </div>
                  
                  <div style={{ textAlign: 'right' }}>
                    {riskCount > 0 ? (
                      <span style={{ color: 'var(--accent-amber)', fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <AlertTriangle size={15} /> {riskCount} At Risk
                      </span>
                    ) : (
                      <span style={{ color: 'var(--accent-emerald)', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <CheckCircle2 size={15} /> All Optimal
                      </span>
                    )}
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      )}
    </motion.div>
  );
};

export default MentorDash;
