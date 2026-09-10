import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { socketService } from '../api/socket';
import ChatPanel from '../components/ChatPanel';
import Whiteboard from '../components/Whiteboard';
import QuizPanel from '../components/QuizPanel';
import FlashcardViewer from '../components/FlashcardViewer';
import AIPanel from '../components/AIPanel';
import LiveMetrics from '../components/LiveMetrics';
import CodeEditor from '../components/CodeEditor';
import { PenTool, Brain, Layers, ArrowLeft, Code } from 'lucide-react';
import Scheduler from '../components/Scheduler';
import { motion, AnimatePresence } from 'framer-motion';

const tabs = [
  { id: 'whiteboard', label: 'Whiteboard', icon: <PenTool size={18} /> },
  { id: 'quizzes', label: 'Quizzes', icon: <Brain size={18} /> },
  { id: 'flashcards', label: 'Flashcards', icon: <Layers size={18} /> },
  { id: 'code', label: 'Code Editor', icon: <Code size={18} /> },
];

const RoomView = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('whiteboard');

  useEffect(() => {
    socketService.joinRoom(roomId);
    return () => {};
  }, [roomId]);

  return (
    <div style={{ height: 'calc(100vh - 4rem)', display: 'flex', flexDirection: 'column' }}>
      {/* Room Top Bar */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-secondary"
            style={{ padding: '0.6rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}
          >
            <ArrowLeft size={18} /> Dashboard
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.5rem', margin: 0, fontWeight: 700, color: 'var(--text-primary)' }}>
              Study Room
            </h1>
            <span style={{
              color: 'var(--text-secondary)',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid var(--glass-border)',
              padding: '0.25rem 0.75rem',
              borderRadius: '99px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}>
              ID: #{roomId}
            </span>
          </div>
        </div>
      </motion.div>

      {/* 3-Column Layout */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '320px 1fr 340px', gap: '1.25rem', minHeight: 0 }}>

        {/* Left Column: Chat Panel */}
        <motion.div 
          initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}
          className="glass-panel" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
        >
          <ChatPanel roomId={roomId} />
        </motion.div>

        {/* Center Column: Interactive Workspace Tabs */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
          className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
        >
          {/* Tab Navigation */}
          <div style={{
            display: 'flex',
            background: 'rgba(15, 23, 42, 0.5)',
            padding: '0.4rem',
            gap: '0.4rem',
            borderBottom: '1px solid var(--glass-border)'
          }}>
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  style={{
                    flex: 1,
                    padding: '0.65rem 1rem',
                    color: isActive ? '#ffffff' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.9rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    background: isActive ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' : 'transparent',
                    borderRadius: 'var(--radius-sm)',
                    transition: 'all 0.2s ease',
                    boxShadow: isActive ? '0 4px 15px rgba(99, 102, 241, 0.3)' : 'none',
                  }}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.icon} {tab.label}
                </button>
              );
            })}
          </div>

          {/* Active Workspace View */}
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                style={{ position: 'absolute', inset: 0 }}
              >
                {activeTab === 'whiteboard' && <Whiteboard roomId={roomId} />}
                {activeTab === 'quizzes' && <QuizPanel roomId={roomId} />}
                {activeTab === 'flashcards' && <FlashcardViewer roomId={roomId} />}
                {activeTab === 'code' && <CodeEditor roomId={roomId} />}
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Right Column: Scheduler, Live Metrics & AI Assistant */}
        <motion.div 
          initial={{ opacity: 0, x: 15 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', overflowY: 'auto' }}
        >
          <div className="glass-panel"><Scheduler roomId={roomId} /></div>
          <div className="glass-panel"><LiveMetrics roomId={roomId} /></div>
          <div className="glass-panel" style={{ flex: 1, minHeight: '280px' }}><AIPanel roomId={roomId} /></div>
        </motion.div>
      </div>
    </div>
  );
};

export default RoomView;
