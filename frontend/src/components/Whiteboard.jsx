import React, { useRef, useEffect, useState } from 'react';
import { socketService } from '../api/socket';
import WhiteboardHelper from '../components/WhiteboardHelper';

const BG = '#0b0f17';
const PALETTE = ['#ffffff', '#6366f1', '#a855f7', '#38bdf8', '#10b981', '#f59e0b', '#f43f5e'];

const Whiteboard = ({ roomId }) => {
  const canvasRef = useRef(null);
  const ctxRef = useRef(null);
  const drawingRef = useRef(false);
  const lastRef = useRef({ x: 0, y: 0 });
  const colorRef = useRef(PALETTE[1]);
  const [color, setColor] = useState(PALETTE[1]);

  const getCanvasRef = () => canvasRef.current;

  // Handlers are bound once; keep the current colour in a ref they can read.
  useEffect(() => { colorRef.current = color; }, [color]);

  // Match the canvas backing store to its container (DPR-aware) and keep the
  // drawing across resizes. Runs on mount and whenever the container resizes,
  // so the canvas is never stuck at the default 300x150.
  const resizeCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !canvas.parentElement) return;
    const { width, height } = canvas.parentElement.getBoundingClientRect();
    if (width === 0 || height === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const nextW = Math.round(width * dpr);
    const nextH = Math.round(height * dpr);
    if (canvas.width === nextW && canvas.height === nextH) return;

    // Snapshot the existing pixels before resizing clears them.
    let snapshot = null;
    if (canvas.width > 0 && canvas.height > 0) {
      snapshot = document.createElement('canvas');
      snapshot.width = canvas.width;
      snapshot.height = canvas.height;
      snapshot.getContext('2d').drawImage(canvas, 0, 0);
    }

    canvas.width = nextW;
    canvas.height = nextH;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); // draw in CSS pixels
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 3;

    // Repaint background, then the previous drawing on top of it.
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (snapshot) ctx.drawImage(snapshot, 0, 0);
    ctx.restore();

    ctxRef.current = ctx;
  };

  useEffect(() => {
    resizeCanvas();

    const ro = new ResizeObserver(resizeCanvas);
    if (canvasRef.current?.parentElement) ro.observe(canvasRef.current.parentElement);
    window.addEventListener('resize', resizeCanvas);

    const handleDraw = (data) => {
      const ctx = ctxRef.current;
      if (!ctx) return;
      ctx.save();
      ctx.strokeStyle = data.color;
      ctx.beginPath();
      ctx.moveTo(data.x0, data.y0);
      ctx.lineTo(data.x1, data.y1);
      ctx.stroke();
      ctx.restore();
    };
    socketService.on('whiteboard_update', handleDraw);

    return () => {
      ro.disconnect();
      window.removeEventListener('resize', resizeCanvas);
      socketService.off('whiteboard_update', handleDraw);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pointerPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const startDraw = (e) => {
    drawingRef.current = true;
    lastRef.current = pointerPos(e);
  };

  const endDraw = () => {
    drawingRef.current = false;
  };

  const draw = (e) => {
    if (!drawingRef.current) return;
    const ctx = ctxRef.current;
    if (!ctx) return;

    const { x, y } = pointerPos(e);
    const from = lastRef.current;

    ctx.save();
    ctx.strokeStyle = colorRef.current;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.restore();

    socketService.sendWhiteboardUpdate(
      { x0: from.x, y0: from.y, x1: x, y1: y, color: colorRef.current },
      roomId
    );

    lastRef.current = { x, y };
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0.65rem 1rem', display: 'flex', alignItems: 'center', gap: '0.65rem', background: 'rgba(15, 23, 42, 0.5)', borderBottom: '1px solid var(--glass-border)' }}>
        {PALETTE.map(c => (
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
          onClick={clearCanvas}
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
