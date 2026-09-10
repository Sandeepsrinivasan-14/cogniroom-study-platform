import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import GlassCard from '../components/GlassCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { AlertTriangle, GraduationCap } from 'lucide-react';
import { motion } from 'framer-motion';

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, activityData] = await Promise.all([
          api.getUserAnalytics(),
          api.getMe().then(user => api.getUserActivity(user.id))
        ]);
        setAnalytics(analyticsData);
        setActivity(activityData);
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

  if (!analytics) return <div className="flex-center" style={{ height: '60vh', color: 'var(--text-muted)' }}>Not enough data to display analytics. Participate in study rooms to generate insights.</div>;

  const trendData = [
    { day: 'Mon', focus: Math.max(0, analytics.focus_score - 15) },
    { day: 'Tue', focus: Math.max(0, analytics.focus_score - 5) },
    { day: 'Wed', focus: Math.min(100, analytics.focus_score + 10) },
    { day: 'Thu', focus: Math.max(0, analytics.focus_score - 2) },
    { day: 'Fri', focus: analytics.focus_score },
  ];

  const activityData = activity?.by_type ? Object.entries(activity.by_type).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value
  })) : [];

  const getGradeColor = (grade) => {
    switch(grade) {
      case 'A': return 'var(--accent-emerald)';
      case 'B': return 'var(--accent-sky)';
      case 'C': return 'var(--accent-amber)';
      default: return 'var(--accent-rose)';
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.4rem', fontWeight: 800 }}>
          Learning <span className="text-gradient-primary">Analytics</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Personalized insights into your focus, performance, and study patterns.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Burnout Risk Gauge */}
        <GlassCard title="Burnout Risk">
          <div className="flex-between">
            <div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: analytics.burnout_risk === 'high' ? 'var(--accent-rose)' : analytics.burnout_risk === 'medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                textTransform: 'capitalize'
              }}>
                {analytics.burnout_risk || 'Low Risk'}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.5rem' }}>
                <AlertTriangle size={14} /> AI Cognitive Assessment
              </div>
            </div>
            {analytics.burnout_confidence && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{Math.round(analytics.burnout_confidence * 100)}%</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confidence</div>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Predicted Grade */}
        <GlassCard title="Projected Performance">
          <div className="flex-between">
            <div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: getGradeColor(analytics.predicted_grade) }}>
                Grade {analytics.predicted_grade || 'A'}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
                <GraduationCap size={16} /> Projected Grade
              </div>
            </div>
            {analytics.grade_confidence && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{Math.round(analytics.grade_confidence * 100)}%</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confidence</div>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Stats Summary */}
        <GlassCard title="Study Summary">
           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
             <div>
               <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{analytics.avg_cognitive_load ? (analytics.avg_cognitive_load * 100).toFixed(0) + '%' : 'N/A'}</div>
               <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Avg Cognitive Load</div>
             </div>
             <div>
               <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{analytics.total_events || 0}</div>
               <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Total Interactions</div>
             </div>
           </div>
        </GlassCard>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        <GlassCard title="Weekly Focus Trend">
          <div style={{ height: '280px', width: '100%', marginTop: '1rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="day" stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
                <YAxis stroke="var(--text-muted)" domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', color: '#fff' }} 
                  itemStyle={{ color: 'var(--accent-primary)' }}
                />
                <Line type="monotone" dataKey="focus" stroke="var(--accent-primary)" strokeWidth={2.5} dot={{ r: 4, fill: 'var(--accent-primary)' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard title="Interaction Types">
          <div style={{ height: '280px', width: '100%', marginTop: '1rem' }}>
            {activityData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activityData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                  <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
                  <YAxis dataKey="name" type="category" stroke="var(--text-muted)" width={90} tick={{ fontSize: 11 }} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', color: '#fff' }} 
                  />
                  <Bar dataKey="value" fill="var(--accent-primary)" radius={[0, 4, 4, 0]}>
                    {activityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['var(--accent-primary)', 'var(--accent-secondary)', 'var(--accent-sky)', 'var(--accent-emerald)', 'var(--accent-amber)'][index % 5]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex-center" style={{ height: '100%', color: 'var(--text-muted)', fontSize: '0.9rem' }}>No activity data available</div>
            )}
          </div>
        </GlassCard>
      </div>
    </motion.div>
  );
};

export default Analytics;
