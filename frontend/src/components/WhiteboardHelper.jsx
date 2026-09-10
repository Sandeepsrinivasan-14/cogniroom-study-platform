import React, { useState } from 'react';
import { getAuthToken } from '../api/client';
import GlassCard from './GlassCard';
import { RefreshCw } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const WhiteboardHelper = ({ roomId, getCanvasRef }) => {
  const [cleanedImg, setCleanedImg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleClean = async () => {
    if (!getCanvasRef) return;
    const canvas = getCanvasRef();
    if (!canvas) return;
    setLoading(true);
    try {
      const blob = await new Promise((res) => canvas.toBlob(res, 'image/png'));
      const form = new FormData();
      form.append('file', blob, 'whiteboard.png');
      // Multipart upload: don't set Content-Type (browser adds the boundary),
      // but do send the bearer token like every other authenticated call.
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/whiteboard/clean?room_id=${roomId}`, {
        method: 'POST',
        body: form,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error(`Whiteboard clean failed (${response.status})`);
      }
      const data = await response.json();
      setCleanedImg(`data:image/png;base64,${data.cleaned_image_base64}`);
    } catch (e) {
      console.error('Whiteboard clean failed', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassCard title="Whiteboard AI Helper" style={{ marginTop: '1rem' }}>
      <button
        onClick={handleClean}
        disabled={loading}
        style={{
          background: 'var(--accent-blue)',
          border: 'none',
          color: '#fff',
          padding: '0.4rem 1rem',
          borderRadius: 'var(--radius-sm)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}
      >
        <RefreshCw size={16} /> Clean Whiteboard
      </button>
      {cleanedImg && (
        <div style={{ marginTop: '1rem' }}>
          <img src={cleanedImg} alt="Cleaned whiteboard" style={{ maxWidth: '100%' }} />
        </div>
      )}
    </GlassCard>
  );
};

export default WhiteboardHelper;
