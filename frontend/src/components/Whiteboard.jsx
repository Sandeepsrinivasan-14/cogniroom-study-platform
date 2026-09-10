import React, { useRef, useState, useEffect } from 'react';
import { socketService } from '../api/socket';
import WhiteboardHelper from '../components/WhiteboardHelper';

const Whiteboard = ({ roomId }) => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState('#6366f1');
  const [ctx, setCtx] = useState(null);

  const getCanvasRef = () => canvasRef.current;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const context = canvas.getContext('2d');
    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.lineWidth = 3;
    setCtx(context);

    context.fillStyle = '#0b0f17';
    context.fillRect(0, 0, canvas.width, canvas.height);

    const handleDraw = (data) => {
      if (!context) return;
      context.beginPath();
      context.moveTo(data.x0, data.y0);
      context.lineTo(data.x1, data.y1);
      context.strokeStyle = data.color;
      context.stroke();
      context.closePath();
    };

    socketService.on('whiteboard_update', handleDraw);
    return () => {
      socketService.off('whiteboard_update', handleDraw);
    };
  }, []);

  const startDraw = (e) => {
    setIsDrawing(true);
    draw(e);
  };

  const endDraw = () => {
    setIsDrawing(false);
    if (ctx) ctx.beginPath();
  };

  const draw = (e) => {
    if (!isDrawing || !ctx) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.lineWidth = 3;
    ctx.strokeStyle = color;
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);

    socketService.sendWhiteboardUpdate({
      x0: x - 1,
      y0: y - 1,
      x1: x,
      y1: y,
      color: color,
    }, roomId);
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0.65rem 1rem', display: 'flex', alignItems: 'center', gap: '0.65rem', background: 'rgba(15, 23, 42, 0.5)', borderBottom: '1px solid var(--glass-border)' }}>
        {['#ffffff', '#6366f1', '#a855f7', '#38bdf8', '#10b981', '#f59e0b', '#f43f5e'].map(c => (
          <button
            key={c}
            onClick={() => setColor(c)}
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              background: c,
              border: color === c ? '2px solid white' : 'none',
              transform: color === c ? 'scale(1.2)' : 'scale(1)',
              transition: 'all 0.15s ease',
            }}
          />
        ))}
        <button
          onClick={() => {
            if (ctx) {
              ctx.fillStyle = '#0b0f17';
              ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            }
          }}
          className="btn-secondary"
          style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem', marginLeft: 'auto' }}
        >
          Clear Canvas
        </button>
      </div>
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <canvas
          ref={canvasRef}
          onMouseDown={startDraw}
          onMouseUp={endDraw}
          onMouseOut={endDraw}
          onMouseMove={draw}
          style={{ cursor: 'crosshair', width: '100%', height: '100%', touchAction: 'none' }}
        />
      </div>
      <WhiteboardHelper roomId={roomId} getCanvasRef={getCanvasRef} />
    </div>
  );
};

export default Whiteboard;
