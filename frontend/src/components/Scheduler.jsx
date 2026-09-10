import React, { useState, useEffect } from 'react';
import { socketService } from '../api/socket';
import { apiCall } from '../api/client';
import GlassCard from './GlassCard';
import { Calendar, Clock, Plus, Trash2, Edit } from 'lucide-react';

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const Scheduler = ({ roomId }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ title: '', start_time: '', duration_minutes: 30 });
  const [timers, setTimers] = useState({});

  const fetchItems = async () => {
    try {
      const data = await apiCall(`/rooms/${roomId}/schedule/`);
      setItems(data);
      const initTimers = {};
      data.forEach((it) => {
        const end = new Date(it.start_time).getTime() + it.duration_minutes * 60000;
        const remaining = Math.max(0, Math.floor((end - Date.now()) / 1000));
        initTimers[it.id] = remaining;
      });
      setTimers(initTimers);
    } catch (e) {
      console.error('Failed to load schedule', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
    const interval = setInterval(() => {
      setTimers((prev) => {
        const updated = { ...prev };
        Object.keys(updated).forEach((id) => {
          if (updated[id] > 0) updated[id] -= 1;
        });
        return updated;
      });
    }, 1000);

    socketService.connect();
    const handler = (data) => {
      const { room_id, timers: socketTimers } = data;
      if (parseInt(room_id) === roomId) {
        setTimers((prev) => {
          const updated = { ...prev };
          socketTimers.forEach((t) => {
            updated[t.id] = t.remaining;
          });
          return updated;
        });
      }
    };
    socketService.on('timer_update', handler);

    return () => {
      clearInterval(interval);
      socketService.off('timer_update', handler);
    };
  }, [roomId]);

  const openModal = (item = null) => {
    if (item) {
      setEditItem(item);
      setForm({
        title: item.title,
        start_time: item.start_time.replace(' ', 'T'),
        duration_minutes: item.duration_minutes,
      });
    } else {
      setEditItem(null);
      setForm({ title: '', start_time: '', duration_minutes: 30 });
    }
    setShowModal(true);
  };

  const closeModal = () => setShowModal(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const saveItem = async () => {
    const payload = {
      title: form.title,
      start_time: form.start_time.replace('T', ' '),
      duration_minutes: Number(form.duration_minutes),
    };
    try {
      if (editItem) {
        await apiCall(`/rooms/${roomId}/schedule/${editItem.id}`, { method: 'DELETE' });
      }
      await apiCall(`/rooms/${roomId}/schedule/`, { method: 'POST', body: JSON.stringify(payload) });
      await fetchItems();
    } catch (e) {
      console.error('Failed to save schedule item', e);
    } finally {
      closeModal();
    }
  };

  const deleteItem = async (id) => {
    if (!window.confirm('Delete this schedule item?')) return;
    try {
      await apiCall(`/rooms/${roomId}/schedule/${id}`, { method: 'DELETE' });
      await fetchItems();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  return (
    <GlassCard title="Study Schedule">
      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading schedule...</p>
      ) : (
        <>
          {items.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No upcoming study sessions scheduled.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {items.map((it) => (
                <li key={it.id} style={{ display: 'flex', alignItems: 'center', padding: '0.65rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{it.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span><Calendar size={12} style={{ verticalAlign: 'middle' }} /> {new Date(it.start_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</span>
                      <span>•</span>
                      <span><Clock size={12} style={{ verticalAlign: 'middle' }} /> {it.duration_minutes} min</span>
                    </div>
                    {timers[it.id] > 0 && (
                      <div style={{ marginTop: '0.3rem', color: 'var(--accent-rose)', fontWeight: 700, fontSize: '0.8rem' }}>
                        Timer: {formatTime(timers[it.id])}
                      </div>
                    )}
                  </div>
                  <button onClick={() => openModal(it)} style={{ background: 'none', border: 'none', color: 'var(--accent-sky)', padding: '0.3rem' }} title="Edit">
                    <Edit size={14} />
                  </button>
                  <button onClick={() => deleteItem(it.id)} style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', padding: '0.3rem' }} title="Delete">
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <button
            onClick={() => openModal()}
            className="btn-secondary"
            style={{ marginTop: '0.85rem', width: '100%', padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
          >
            <Plus size={15} /> Add Session
          </button>
        </>
      )}

      {showModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={closeModal}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="glass-panel"
            style={{
              padding: '1.75rem',
              width: '100%',
              maxWidth: '380px',
            }}
          >
            <h3 style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '1.15rem' }}>{editItem ? 'Edit Session' : 'New Session'}</h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600 }}>Title</label>
              <input
                type="text"
                name="title"
                value={form.title}
                onChange={handleChange}
                placeholder="e.g. Chapter 4 Review"
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600 }}>Start Time</label>
              <input
                type="datetime-local"
                name="start_time"
                value={form.start_time}
                onChange={handleChange}
              />
            </div>
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600 }}>Duration (minutes)</label>
              <input
                type="number"
                name="duration_minutes"
                min={1}
                value={form.duration_minutes}
                onChange={handleChange}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button onClick={closeModal} className="btn-secondary" style={{ padding: '0.6rem 1rem', fontSize: '0.85rem' }}>
                Cancel
              </button>
              <button onClick={saveItem} className="btn-primary" style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem' }}>
                {editItem ? 'Update' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </GlassCard>
  );
};

export default Scheduler;
