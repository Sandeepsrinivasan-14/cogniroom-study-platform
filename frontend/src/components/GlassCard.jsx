import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({ children, style, className = '', title, action }) => {
  return (
    <motion.div
      className={`glass-panel glass-panel-hover ${className}`}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      style={{
        padding: '1.75rem',
        display: 'flex',
        flexDirection: 'column',
        ...style,
      }}
    >
      {(title || action) && (
        <div className="flex-between" style={{ 
          marginBottom: '1.25rem', 
          borderBottom: '1px solid var(--glass-border)', 
          paddingBottom: '0.85rem',
        }}>
          {title && (
            <h3 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 700, color: 'var(--text-primary)' }}>
              {title}
            </h3>
          )}
          {action && <div>{action}</div>}
        </div>
      )}
      <div style={{ flex: 1 }}>{children}</div>
    </motion.div>
  );
};

export default GlassCard;
