import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import GlassCard from './GlassCard';
import { Lightbulb, ShieldAlert, Sparkles } from 'lucide-react';

const AIPanel = ({ roomId }) => {
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAI = async () => {
      try {
        const [userData, roomData] = await Promise.all([
          api.getAgentSuggestions().catch(() => null),
          api.getRoomSuggestions(roomId).catch(() => null)
        ]);
        
        setSuggestions({
          user: userData,
          room: roomData
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAI();
    const interval = setInterval(fetchAI, 30000);
    return () => clearInterval(interval);
  }, [roomId]);

  if (loading && !suggestions) {
    return (
      <GlassCard title="AI Assistant">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          <Sparkles size={16} /> Analyzing study session...
        </div>
      </GlassCard>
    );
  }

  const renderSuggestion = (item, i) => {
    const isWarning = item.severity === 'high' || item.type === 'advice';
    return (
      <div key={i} style={{ 
        padding: '0.85rem 1rem', 
        borderRadius: 'var(--radius-sm)', 
        background: isWarning ? 'rgba(245, 158, 11, 0.08)' : 'rgba(99, 102, 241, 0.08)',
        borderLeft: `3px solid ${isWarning ? 'var(--accent-amber)' : 'var(--accent-primary)'}`,
        marginBottom: '0.65rem',
        fontSize: '0.85rem'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '0.2rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {isWarning ? <ShieldAlert size={14} color="var(--accent-amber)" /> : <Lightbulb size={14} color="var(--accent-sky)" />}
          {item.label}
        </div>
        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>{item.message}</div>
      </div>
    );
  };

  return (
    <GlassCard title="AI Co-Pilot">
      <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
        {suggestions?.user?.combined?.map((item, i) => renderSuggestion(item, i))}
        {suggestions?.room?.map((item, i) => renderSuggestion(item, i + 10))}
        
        {(!suggestions?.user?.combined?.length && !suggestions?.room?.length) && (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No insights available yet. Participate in study tools to generate co-pilot advice.
          </div>
        )}
      </div>
    </GlassCard>
  );
};

export default AIPanel;
