import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { socketService } from '../api/socket';
import GlassCard from './GlassCard';
import { Camera, CameraOff, Sliders } from 'lucide-react';

const LiveMetrics = ({ roomId }) => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [simulatedLoad, setSimulatedLoad] = useState(0.5);
  const [useWebcam, setUseWebcam] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await api.getLiveMetrics(roomId);
        setMetrics(data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, [roomId]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const toggleWebcam = async () => {
    if (useWebcam) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
      setUseWebcam(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setUseWebcam(true);
        
        const trackInterval = setInterval(() => {
          if (!streamRef.current || !streamRef.current.active) {
            clearInterval(trackInterval);
            return;
          }
          const variation = (Math.random() * 0.2) - 0.1;
          let newLoad = simulatedLoad + variation;
          newLoad = Math.max(0, Math.min(1, newLoad));
          socketService.sendWebcamLoad(newLoad, user?.id, roomId);
        }, 3000);
        
      } catch (err) {
        alert("Webcam access denied or unavailable.");
        console.error(err);
      }
    }
  };

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    setSimulatedLoad(val);
    if (!useWebcam) {
      socketService.sendWebcamLoad(val, user?.id, roomId);
    }
  };

  const avgLoad = metrics?.group_avg_load || 0;
  let statusColor = 'var(--accent-emerald)';
  let statusText = 'Optimal Focus';
  if (avgLoad > 0.8) { statusColor = 'var(--accent-rose)'; statusText = 'High Load'; }
  else if (avgLoad < 0.3) { statusColor = 'var(--accent-amber)'; statusText = 'Light Engagement'; }

  return (
    <GlassCard title="Live Cognitive Load">
      <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
        <div style={{
          position: 'relative', width: '100px', height: '100px', margin: '0 auto',
          display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%',
          background: `conic-gradient(${statusColor} ${avgLoad * 100}%, rgba(255,255,255,0.06) 0)`
        }}>
          <div style={{
            width: '84px', height: '84px', borderRadius: '50%',
            background: 'var(--bg-primary)', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center'
          }}>
            <span style={{ fontSize: '1.35rem', fontWeight: 800 }}>{Math.round(avgLoad * 100)}%</span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>AVG LOAD</span>
          </div>
        </div>
        <div style={{ marginTop: '0.65rem', fontWeight: 600, fontSize: '0.9rem', color: statusColor }}>{statusText}</div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{metrics?.total_users || 0} active members</div>
      </div>

      <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '1rem' }}>
        <div className="flex-between" style={{ marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 500 }}>
            <Camera size={14} /> Focus Webcam Tracker
          </div>
          <button 
            onClick={toggleWebcam}
            className="btn-secondary"
            style={{ 
              padding: '0.3rem 0.65rem', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)'
            }}
          >
            {useWebcam ? <><CameraOff size={12} /> Stop</> : <><Camera size={12} /> Start</>}
          </button>
        </div>
        
        {useWebcam && (
          <div style={{ width: '100%', height: '110px', background: '#000', borderRadius: 'var(--radius-sm)', overflow: 'hidden', marginBottom: '0.85rem', position: 'relative' }}>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            <div style={{ position: 'absolute', top: 6, right: 6, width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-rose)' }} />
          </div>
        )}

        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 500 }}>
          <Sliders size={14} /> Manual Load Adjustment
        </div>
        <input 
          type="range" 
          min="0" max="1" step="0.05" 
          value={simulatedLoad} 
          onChange={handleSliderChange}
          style={{ width: '100%' }}
        />
        <div className="flex-between" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          <span>Low</span>
          <span>High</span>
        </div>
      </div>
    </GlassCard>
  );
};

export default LiveMetrics;
