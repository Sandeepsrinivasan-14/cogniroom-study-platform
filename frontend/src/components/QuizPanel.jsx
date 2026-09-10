import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Brain, Wand2, RefreshCw, CheckCircle2 } from 'lucide-react';

const QuizPanel = ({ roomId }) => {
  const [quizzes, setQuizzes] = useState([]);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [aiTopic, setAiTopic] = useState('');
  const [showAiGen, setShowAiGen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [scoreResult, setScoreResult] = useState(null);

  useEffect(() => {
    loadQuizzes();
  }, [roomId]);

  const loadQuizzes = async () => {
    try {
      setLoading(true);
      const data = await api.getQuizzes(roomId);
      setQuizzes(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAI = async (e) => {
    e.preventDefault();
    if (!aiTopic.trim()) return;
    
    try {
      setGenerating(true);
      const res = await api.generateQuiz({ topic: aiTopic, count: 5, difficulty: 'medium' });
      
      if (res && res.questions && res.questions.length > 0) {
        await api.createQuiz(roomId, {
          title: `Quiz: ${aiTopic}`,
          questions: res.questions.map(q => ({ text: q.question }))
        });
        await loadQuizzes();
        setShowAiGen(false);
        setAiTopic('');
      }
    } catch (err) {
      alert("Failed to generate: " + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const answerPayload = {
        answers: Object.entries(answers).map(([qId, ans]) => ({
          question_id: parseInt(qId),
          answer: ans
        }))
      };
      const result = await api.submitQuiz(activeQuiz.id, answerPayload);
      setScoreResult(result);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (activeQuiz) {
    if (scoreResult) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--accent-emerald)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '1rem',
          }}>
            <CheckCircle2 size={32} color="var(--accent-emerald)" />
          </div>
          <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontWeight: 800 }}>
            Score: <span className="text-gradient-primary">{scoreResult.score} / {scoreResult.total_questions}</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>Great job completing this practice quiz!</p>
          <button className="btn-primary" onClick={() => { setActiveQuiz(null); setScoreResult(null); setAnswers({}); }}>
            Back to Quizzes
          </button>
        </div>
      );
    }

    return (
      <div style={{ padding: '1.5rem', height: '100%', overflowY: 'auto' }}>
        <div className="flex-between" style={{ marginBottom: '1.5rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--glass-border)' }}>
          <h2 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700 }}>{activeQuiz.title}</h2>
          <button className="btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem' }} onClick={() => setActiveQuiz(null)}>Back</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '1.75rem' }}>
          {activeQuiz.questions.map((q, i) => (
            <div key={q.id} style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.85rem', display: 'flex', gap: '0.5rem', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--accent-sky)' }}>{i + 1}.</span> {q.text}
              </div>
              <input 
                type="text" 
                placeholder="Type your answer..." 
                value={answers[q.id] || ''}
                onChange={(e) => setAnswers({...answers, [q.id]: e.target.value})}
              />
            </div>
          ))}
        </div>

        <button 
          className="btn-primary" 
          style={{ width: '100%', padding: '0.85rem' }}
          onClick={handleSubmit}
          disabled={loading || Object.keys(answers).length === 0}
        >
          {loading ? 'Submitting...' : 'Submit Answers'}
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex-between" style={{ marginBottom: '1.25rem' }}>
        <h2 style={{ fontSize: '1.15rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}>
          <Brain size={18} color="var(--accent-primary)" /> Practice Quizzes
        </h2>
        <button 
          className="btn-primary" 
          style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
          onClick={() => setShowAiGen(!showAiGen)}
        >
          <Wand2 size={15} /> AI Generator
        </button>
      </div>

      {showAiGen && (
        <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.25)', padding: '1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem' }}>
          <form onSubmit={handleGenerateAI} style={{ display: 'flex', gap: '0.75rem' }}>
            <input 
              type="text" 
              placeholder="Topic (e.g. Organic Chemistry, Calculus)" 
              value={aiTopic}
              onChange={(e) => setAiTopic(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary" disabled={generating} style={{ flexShrink: 0, padding: '0.65rem 1rem', fontSize: '0.85rem' }}>
              {generating ? <RefreshCw size={15} className="spin" /> : 'Generate'}
            </button>
          </form>
        </div>
      )}

      {loading && !generating ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', margin: 'auto' }}>Loading quizzes...</div>
      ) : quizzes.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', margin: 'auto' }}>
          No quizzes created yet. Use AI Generator to create one!
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
          {quizzes.map(q => (
            <div 
              key={q.id}
              style={{ 
                background: 'rgba(15, 23, 42, 0.4)', 
                border: '1px solid var(--glass-border)', 
                padding: '1.25rem', 
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--accent-primary)'; }}
              onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
              onClick={() => { setActiveQuiz(q); setAnswers({}); }}
            >
              <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', fontWeight: 600 }}>{q.title}</h3>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                {q.questions.length} Questions
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default QuizPanel;
