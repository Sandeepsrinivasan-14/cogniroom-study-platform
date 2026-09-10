import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Shield, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'student' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const particlesInit = useCallback(async engine => {
    await loadFull(engine);
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData);
      }
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 800);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      padding: '1.5rem',
    }}>
      {/* Subtle, soft ambient background particles */}
      <Particles
        id="tsparticles-auth"
        init={particlesInit}
        options={{
          background: { color: { value: "transparent" } },
          fpsLimit: 60,
          particles: {
            color: { value: ["#818cf8", "#c084fc", "#38bdf8"] },
            move: { enable: true, speed: 0.6, direction: "none", random: true },
            number: { density: { enable: true, area: 1000 }, value: 35 },
            opacity: { value: { min: 0.1, max: 0.25 } },
            shape: { type: "circle" },
            size: { value: { min: 2, max: 6 } },
          },
        }}
        style={{ position: "absolute", inset: 0, zIndex: 0 }}
      />

      {/* Auth Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '2.5rem 2.25rem',
          position: 'relative',
          zIndex: 10,
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.6rem',
            marginBottom: '0.75rem',
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 20px rgba(99, 102, 241, 0.3)',
            }}>
              <Sparkles size={22} color="white" />
            </div>
            <h1 className="text-gradient-primary" style={{ fontSize: '2rem', margin: 0, fontWeight: 800 }}>
              CogniRoom
            </h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', fontWeight: 500 }}>
            {isLogin ? 'Welcome back! Sign in to continue' : 'Create an account to get started'}
          </p>
        </div>

        {success && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              position: 'absolute', inset: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(11, 15, 23, 0.95)',
              borderRadius: 'inherit',
              zIndex: 20,
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: '64px', height: '64px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid var(--accent-emerald)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 1rem',
              }}>
                <Shield size={32} color="var(--accent-emerald)" />
              </div>
              <p style={{ fontWeight: 700, fontSize: '1.25rem', color: 'var(--accent-emerald)' }}>
                Authenticated Successfully
              </p>
            </div>
          </motion.div>
        )}

        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            style={{
              background: 'rgba(244, 63, 94, 0.1)',
              color: 'var(--accent-rose)',
              padding: '0.85rem 1rem',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1.5rem',
              fontSize: '0.9rem',
              fontWeight: 500,
              textAlign: 'center',
              border: '1px solid rgba(244, 63, 94, 0.25)',
            }}
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {!isLogin && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
                Full Name
              </label>
              <input type="text" name="name" value={formData.name} onChange={handleChange} required placeholder="John Doe" />
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
              Email Address
            </label>
            <input type="email" name="email" value={formData.email} onChange={handleChange} required placeholder="you@example.com" />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
              Password
            </label>
            <input type="password" name="password" value={formData.password} onChange={handleChange} required placeholder="••••••••" />
          </div>

          {!isLogin && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
                Account Type
              </label>
              <select name="role" value={formData.role} onChange={handleChange}>
                <option value="student">Student</option>
                <option value="mentor">Mentor</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{
              marginTop: '0.5rem',
              padding: '0.9rem',
              width: '100%',
            }}
          >
            {loading ? (
              <div style={{
                width: '20px', height: '20px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: 'white',
                borderRadius: '50%',
                animation: 'spin 0.6s linear infinite',
              }} />
            ) : (
              <>
                {isLogin ? 'Sign In' : 'Create Account'}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.75rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            style={{
              color: 'var(--accent-sky)',
              fontWeight: 600,
              marginLeft: '0.3rem',
            }}
          >
            {isLogin ? 'Sign up' : 'Sign in'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default AuthPage;
