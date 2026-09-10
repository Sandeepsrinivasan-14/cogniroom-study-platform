import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { socketService } from '../api/socket';
import { Send, MessageCircle } from 'lucide-react';

const ChatPanel = ({ roomId }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    const handleNewMessage = (data) => {
      setMessages(prev => [...prev, { ...data, _animKey: Date.now() + Math.random() }]);
    };

    socketService.on('chatmessage', handleNewMessage);

    return () => {
      socketService.off('chatmessage', handleNewMessage);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setIsSending(true);
    socketService.sendChatMessage(newMessage, user.id, roomId);
    setNewMessage('');
    setTimeout(() => setIsSending(false), 300);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        padding: '1rem 1.25rem',
        borderBottom: '1px solid var(--glass-border)',
        background: 'rgba(15, 23, 42, 0.4)',
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '0.95rem',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: 'var(--accent-emerald)',
            display: 'inline-block',
            boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
          }} />
          <MessageCircle size={16} style={{ color: 'var(--accent-sky)' }} />
          Room Chat
        </h3>
      </div>

      {/* Messages List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}>
        {messages.length === 0 ? (
          <div style={{
            color: 'var(--text-muted)',
            textAlign: 'center',
            marginTop: '3rem',
            fontSize: '0.85rem',
          }}>
            <MessageCircle size={28} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
            <p>No messages yet.</p>
            <p style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>Start the conversation with your team!</p>
          </div>
        ) : (
          messages.map((msg, i) => {
            const isMe = msg.user_id === user.id;
            return (
              <div
                key={msg._animKey || i}
                style={{
                  alignSelf: isMe ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                }}
              >
                <div style={{
                  background: isMe
                    ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))'
                    : 'rgba(255, 255, 255, 0.05)',
                  color: isMe ? '#ffffff' : 'var(--text-primary)',
                  padding: '0.65rem 0.9rem',
                  borderRadius: isMe ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                  boxShadow: isMe
                    ? '0 4px 12px rgba(99, 102, 241, 0.25)'
                    : 'none',
                  wordBreak: 'break-word',
                  fontSize: '0.875rem',
                  lineHeight: 1.5,
                  border: isMe ? 'none' : '1px solid var(--glass-border)',
                }}>
                  {msg.message}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '0.75rem 1rem',
        borderTop: '1px solid var(--glass-border)',
        background: 'rgba(15, 23, 42, 0.4)',
      }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            style={{
              flex: 1,
              padding: '0.65rem 0.9rem',
              borderRadius: '99px',
              fontSize: '0.85rem',
            }}
          />
          <button
            type="submit"
            style={{
              background: newMessage.trim()
                ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))'
                : 'rgba(255, 255, 255, 0.06)',
              color: 'white',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
              flexShrink: 0,
            }}
            disabled={!newMessage.trim()}
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
