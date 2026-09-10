import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Layers } from 'lucide-react';

const FlashcardViewer = ({ roomId }) => {
  const [decks, setDecks] = useState([]);
  const [activeDeck, setActiveDeck] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDecks = async () => {
      try {
        const data = await api.getFlashcardDecks(roomId);
        setDecks(data);
      } catch (err) {
        console.error('Failed to load flashcards', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDecks();
  }, [roomId]);

  if (activeDeck) {
    const card = activeDeck.flashcards[currentIndex];
    return (
      <div style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div className="flex-between" style={{ width: '100%', marginBottom: '1.5rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--glass-border)' }}>
          <h2 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{activeDeck.title}</h2>
          <button className="btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem' }} onClick={() => { setActiveDeck(null); setCurrentIndex(0); setIsFlipped(false); }}>Close</button>
        </div>

        {card ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%', maxWidth: '540px' }}>
            
            <div style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.85rem', fontWeight: 500 }}>
              Card {currentIndex + 1} of {activeDeck.flashcards.length}
            </div>

            <div 
              style={{ 
                width: '100%', 
                minHeight: '260px', 
                background: isFlipped ? 'rgba(99, 102, 241, 0.08)' : 'rgba(15, 23, 42, 0.5)',
                border: '1px solid',
                borderColor: isFlipped ? 'var(--accent-primary)' : 'var(--glass-border)',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2.5rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                boxShadow: 'var(--shadow-glass)',
                position: 'relative'
              }}
              onClick={() => setIsFlipped(!isFlipped)}
            >
              <div style={{ position: 'absolute', top: '1rem', right: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                {isFlipped ? 'ANSWER' : 'QUESTION'} (Click to flip)
              </div>
              <h3 style={{ fontSize: '1.25rem', textAlign: 'center', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {isFlipped ? card.back : card.front}
              </h3>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button 
                className="btn-secondary" 
                disabled={currentIndex === 0}
                style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem' }}
                onClick={() => { setCurrentIndex(c => c - 1); setIsFlipped(false); }}
              >
                Previous
              </button>
              <button 
                className="btn-primary" 
                disabled={currentIndex === activeDeck.flashcards.length - 1}
                style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem' }}
                onClick={() => { setCurrentIndex(c => c + 1); setIsFlipped(false); }}
              >
                Next Card
              </button>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No cards in this deck.</div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ fontSize: '1.15rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}>
        <Layers size={18} color="var(--accent-secondary)" /> Study Decks
      </h2>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.85rem' }}>Loading decks...</div>
      ) : decks.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '3rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-lg)', fontSize: '0.9rem' }}>
          No flashcard decks found for this room.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
          {decks.map(deck => (
            <div 
              key={deck.id}
              className="glass-panel"
              style={{ padding: '1.25rem', cursor: 'pointer', transition: 'all 0.2s' }}
              onClick={() => setActiveDeck(deck)}
              onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
              onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--glass-border)'}
            >
              <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', fontWeight: 600 }}>{deck.title}</h3>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                {deck.flashcards.length} Cards {deck.topic_tag ? `• ${deck.topic_tag}` : ''}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FlashcardViewer;
