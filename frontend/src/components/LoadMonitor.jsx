import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { socketService } from '../api/socket';
import { useAuth } from '../context/AuthContext';
import { Camera } from 'lucide-react';

// Simple gauge component
const Gauge = ({ value }) => {
  const percent = Math.round(value * 100);
  const color = value < 0.33 ? '#10b981' : value < 0.66 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{
      width: '120px',
      height: '120px',
      borderRadius: '50%',
      background: `rgba(0,0,0,0.3)`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      boxShadow: '0 0 10px rgba(0,0,0,0.5)',
    }}>
      <div style={{
        width: `${percent}%`,
        height: '100%',
        borderRadius: 'inherit',
        background: color,
        position: 'absolute',
        left: 0,
        top: 0,
        transition: 'width 0.4s ease',
      }} />
      <span style={{
        fontSize: '1.2rem',
        fontWeight: 600,
        color: 'var(--text-primary)',
        zIndex: 1,
      }}>{percent}%</span>
    </div>
  );
};

const LoadMonitor = ({ roomId }) => {
  const { user } = useAuth();
  const userId = user?.id || 0;
  const videoRef = React.useRef(null);
  const [load, setLoad] = useState(0);
  const [hasCamera, setHasCamera] = useState(false);

  // Initialize webcam stream
  useEffect(() => {
    if (!navigator.mediaDevices?.getUserMedia) {
      console.warn('Webcam not supported');
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
          setHasCamera(true);
        }
      })
      .catch((err) => console.error('Failed to get webcam:', err));
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((t) => t.stop());
      }
    };
  }, []);

  // Simulated load (replace with real model later)
  useEffect(() => {
    const interval = setInterval(() => {
      const simulated = Math.random(); // 0‑1 float
      setLoad(simulated);
      // POST to backend via API helper
      api.postLoad(roomId, { user_id: userId, load_score: simulated }).catch(console.error);
      // Broadcast via socket for other participants
      socketService.sendWebcamLoad(simulated, userId, roomId);
    }, 5000); // every 5 seconds as per plan
    return () => clearInterval(interval);
  }, [roomId, userId]);

  // Listen for remote load updates (optional UI expansion)
  useEffect(() => {
    const handler = (data) => {
      // Currently we display only local user's gauge.
    };
    socketService.on('webcam_load_update', handler);
    return () => socketService.off('webcam_load_update', handler);
  }, []);

  return (
    <div className="glass-panel" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.8rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Camera size={20} />
        <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>Cognitive Load</h3>
      </div>
      {hasCamera ? (
        <video ref={videoRef} style={{ width: '100%', maxHeight: '150px', borderRadius: 'var(--radius-sm)', objectFit: 'cover' }} muted />
      ) : (
        <div style={{ width: '100%', height: '150px', background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
          No camera
        </div>
      )}
      <Gauge value={load} />
    </div>
  );
};

export default LoadMonitor;
