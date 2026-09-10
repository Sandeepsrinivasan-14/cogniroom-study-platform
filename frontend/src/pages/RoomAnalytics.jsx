import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import GlassCard from '../components/GlassCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { Users, Activity, AlertTriangle, ArrowLeft, BrainCircuit } from 'lucide-react';

const RoomAnalytics = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await api.getRoomAnalytics(roomId);
        setAnalytics(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [roomId]);

  if (loading) return <div className="flex-center" style={{ height: '100%' }}>Loading room analytics...</div>;
  if (!analytics) return <div className="flex-center" style={{ height: '100%', color: 'var(--text-muted)' }}>Could not load analytics for this room.</div>;

  // Transform data for charts
  const interactionData = analytics.events_by_type ? Object.entries(analytics.events_by_type).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value
  })) : [];

  const atRiskIds = new Set((analytics.at_risk_members || []).map(m => String(m.user_id)));
  const memberStatusData = analytics.events_by_user ? Object.entries(analytics.events_by_user).map(([uid, count]) => ({
    name: `User ${uid}`,
    events: count,
    atRisk: atRiskIds.has(String(uid))
  })) : [];

  // Mock timeline data for the room since historical timeseries isn't fully exported by backend yet
  const timelineData = [
    { time: '0m', load: 30, events: 5 },
    { time: '10m', load: 45, events: 12 },
    { time: '20m', load: 60, events: 8 },
    { time: '30m', load: analytics.avg_cognitive_load ? analytics.avg_cognitive_load * 100 : 75, events: 20 },
  ];

  return (
    <div style={{ paddingBottom: '2rem' }}>
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button 
          onClick={() => navigate(`/room/${roomId}`)}
          style={{ background: 'rgba(255,255,255,0.1)', border: 'none', padding: '0.5rem', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', cursor: 'pointer' }}
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 style={{ fontSize: '2rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <BrainCircuit color="var(--accent-cyan)" /> Room Analytics
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>Session Insights & Group Performance metrics.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <GlassCard>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--accent-blue)' }}>{analytics.total_events || 0}</div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} /> Total Interactions
          </div>
        </GlassCard>

        <GlassCard style={{ borderTop: `4px solid ${analytics.avg_cognitive_load > 0.8 ? 'var(--danger)' : 'var(--success)'}` }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: analytics.avg_cognitive_load > 0.8 ? 'var(--danger)' : 'var(--success)' }}>
            {analytics.avg_cognitive_load ? `${(analytics.avg_cognitive_load * 100).toFixed(0)}%` : 'N/A'}
          </div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BrainCircuit size={16} /> Avg Group Load
          </div>
        </GlassCard>
        
        <GlassCard style={{ borderTop: `4px solid ${analytics.at_risk_members?.length > 0 ? 'var(--warning)' : 'var(--success)'}` }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: analytics.at_risk_members?.length > 0 ? 'var(--warning)' : 'var(--success)' }}>
            {analytics.at_risk_members?.length || 0}
          </div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} /> At-Risk Members
          </div>
        </GlassCard>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', '@media (max-width: 1024px)': { gridTemplateColumns: '1fr' } }}>
        <GlassCard title="Session Timeline">
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="var(--text-secondary)" />
                <YAxis yAxisId="left" stroke="var(--accent-blue)" />
                <YAxis yAxisId="right" orientation="right" stroke="var(--accent-cyan)" />
                <Tooltip 
                  contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)' }} 
                />
                <Line yAxisId="left" type="monotone" dataKey="load" name="Cognitive Load (%)" stroke="var(--accent-blue)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line yAxisId="right" type="monotone" dataKey="events" name="Interactions" stroke="var(--accent-cyan)" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard title="Interaction Breakdown">
          <div style={{ height: '300px', width: '100%' }}>
            {interactionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={interactionData} layout="vertical" margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={false} />
                  <XAxis type="number" stroke="var(--text-secondary)" />
                  <YAxis dataKey="name" type="category" stroke="var(--text-secondary)" width={80} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)' }} 
                  />
                  <Bar dataKey="value" fill="var(--accent-violet)" radius={[0, 4, 4, 0]}>
                    {interactionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['var(--accent-blue)', 'var(--accent-cyan)', 'var(--accent-violet)', 'var(--success)', 'var(--warning)'][index % 5]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex-center" style={{ height: '100%', color: 'var(--text-muted)' }}>No event data recorded yet.</div>
            )}
          </div>
        </GlassCard>
      </div>

      <h2 style={{ fontSize: '1.25rem', marginTop: '2rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Users size={20} /> Member Status
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
        {memberStatusData.length > 0 ? memberStatusData.map((m, i) => (
          <div key={i} style={{ 
            background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)', 
            borderLeft: `3px solid ${m.atRisk ? 'var(--warning)' : 'var(--success)'}`
          }}>
            <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem' }}>{m.name}</h3>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{m.events} interactions</div>
            {m.atRisk && <div style={{ color: 'var(--warning)', fontSize: '0.75rem', marginTop: '0.5rem', fontWeight: 600 }}>⚠️ Burnout Risk Detected</div>}
          </div>
        )) : (
          <div style={{ color: 'var(--text-muted)' }}>No members found.</div>
        )}
      </div>

    </div>
  );
};

export default RoomAnalytics;
