import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import GlassCard from '../components/GlassCard';
import { Plus, LogIn, Users, Brain, TrendingUp, Sparkles, ArrowRight, Hash, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showJoin, setShowJoin] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [roomCode, setRoomCode] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [roomsData, analyticsData] = await Promise.all([
          api.getMyRooms(),
          api.getUserAnalytics().catch(() => null)
        ]);
        setRooms(roomsData?.rooms || []);
        setAnalytics(analyticsData);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    try {
      const created = await api.createRoom({ name: roomName });
      setShowCreate(false);
      setRoomName('');
      navigate(`/room/${created.id}`);
    } catch (err) {
      alert(err.message || 'Failed to create room');
    }
  };

  const handleJoinRoom = async (e) => {
    e.preventDefault();
    try {
      const room = await api.joinRoom(roomCode);
      setShowJoin(false);
      setRoomCode('');
      navigate(`/room/${room.id}`);
    } catch (err) {
      alert(err.message || 'Failed to join room');
    }
  };

  if (loading) {
    return (
      <div className="flex-center" style={{ height: '60vh' }}>
        <div style={{
          width: '48px', height: '48px',
          border: '3px solid rgba(255, 255, 255, 0.1)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%',
          animation: 'spin 0.6s linear infinite',
        }} />
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Page Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.4rem', fontWeight: 800 }}>
          Welcome back, <span className="text-gradient-primary">{user?.name}</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', fontWeight: 500 }}>
          Here is your study overview and active learning rooms.
        </p>
      </div>

      {/* Overview Analytics Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        
        {/* Focus Score */}
        <GlassCard title="Cognitive Focus Score" action={<Brain size={22} color="var(--accent-primary)" />}>
          <div className="flex-between">
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                <span style={{ fontSize: '3.5rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
                  {analytics?.focus_score || 0}
                </span>
                <span style={{ fontSize: '1.25rem', color: 'var(--text-muted)', fontWeight: 600 }}>/100</span>
              </div>
              <div style={{
                marginTop: '1.25rem',
                height: '8px',
                width: '180px',
                background: 'rgba(255,255,255,0.06)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${analytics?.focus_score || 0}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                    borderRadius: '4px',
                  }}
                />
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.85rem',
                borderRadius: '99px',
                background: analytics?.burnout_risk === 'high' ? 'rgba(244, 63, 94, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                color: analytics?.burnout_risk === 'high' ? 'var(--accent-rose)' : 'var(--accent-emerald)',
                fontWeight: 600,
                fontSize: '0.85rem',
                border: `1px solid ${analytics?.burnout_risk === 'high' ? 'rgba(244,63,94,0.3)' : 'rgba(16,185,129,0.3)'}`
              }}>
                <CheckCircle2 size={14} />
                {analytics?.burnout_risk ? `Status: ${analytics.burnout_risk.toUpperCase()}` : 'Status: Optimal'}
              </span>
            </div>
          </div>
        </GlassCard>

        {/* Learning Activity */}
        <GlassCard title="Learning Activity" action={<TrendingUp size={22} color="var(--accent-secondary)" />}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
                {analytics?.total_events || 0}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontWeight: 500 }}>
                Study Actions
              </div>
            </div>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
                {analytics?.quiz_performance ? `${analytics.quiz_performance}%` : 'N/A'}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontWeight: 500 }}>
                Quiz Accuracy
              </div>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <button
          className="btn-primary"
          onClick={() => { setShowCreate(!showCreate); setShowJoin(false); }}
        >
          <Plus size={18} /> Create Room
        </button>
        <button
          className="btn-secondary"
          onClick={() => { setShowJoin(!showJoin); setShowCreate(false); }}
        >
          <LogIn size={18} /> Join with Code
        </button>
      </div>

      {/* Create Room Form */}
      {showCreate && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} style={{ overflow: 'hidden', marginBottom: '2rem' }}>
          <GlassCard style={{ borderLeft: '4px solid var(--accent-primary)' }}>
            <form onSubmit={handleCreateRoom} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '250px' }}>
                <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>Room Name</label>
                <input type="text" value={roomName} onChange={(e) => setRoomName(e.target.value)} required placeholder="e.g. Organic Chemistry Group" />
              </div>
              <button type="submit" className="btn-primary">
                <Sparkles size={18} /> Create & Enter
              </button>
            </form>
          </GlassCard>
        </motion.div>
      )}

      {/* Join Room Form */}
      {showJoin && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} style={{ overflow: 'hidden', marginBottom: '2rem' }}>
          <GlassCard style={{ borderLeft: '4px solid var(--accent-secondary)' }}>
            <form onSubmit={handleJoinRoom} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '250px' }}>
                <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>Room Code</label>
                <input type="text" value={roomCode} onChange={(e) => setRoomCode(e.target.value)} required placeholder="Enter 6-digit room code..." style={{ letterSpacing: '0.05em' }} />
              </div>
              <button type="submit" className="btn-primary">
                <ArrowRight size={18} /> Join Room
              </button>
            </form>
          </GlassCard>
        </motion.div>
      )}

      {/* Rooms List Section */}
      <div style={{ marginTop: '2.5rem' }}>
        <h2 style={{ fontSize: '1.35rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}>
          <Users size={20} color="var(--accent-primary)" /> My Study Rooms
        </h2>

        {rooms.length === 0 ? (
          <div className="glass-panel" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
            <Users size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem', opacity: 0.5 }} />
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.3rem' }}>No Study Rooms Joined</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Create a new room or join an existing study group with a code.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {rooms.map((room) => (
              <motion.div
                key={room.id}
                whileHover={{ y: -3 }}
                transition={{ duration: 0.2 }}
              >
                <GlassCard
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/room/${room.id}`)}
                >
                  <div className="flex-between" style={{ marginBottom: '1.25rem' }}>
                    <h3 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--text-primary)', fontWeight: 700 }}>
                      {room.name}
                    </h3>
                    <ArrowRight size={18} style={{ color: 'var(--accent-sky)' }} />
                  </div>
                  <div className="flex-between" style={{ background: 'rgba(0,0,0,0.25)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-sky)', fontWeight: 600, fontSize: '0.9rem' }}>
                      <Hash size={14} /> Code: {room.code}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 500 }}>Room #{room.id}</span>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Dashboard;
