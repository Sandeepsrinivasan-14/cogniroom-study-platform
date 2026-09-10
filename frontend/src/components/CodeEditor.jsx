import React, { useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

import js from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';

SyntaxHighlighter.registerLanguage('javascript', js);

const CodeEditor = ({ initialCode = '// Write code or notes here...\nfunction studySession() {\n  console.log("Collaborative Learning Active");\n}', language = 'javascript', onChange }) => {
  const [code, setCode] = useState(initialCode);

  const handleChange = (e) => {
    const newCode = e.target.value;
    setCode(newCode);
    if (onChange) onChange(newCode);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem', background: 'rgba(11, 15, 23, 0.6)' }}>
      <div style={{ marginBottom: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Interactive Code Workspace</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>JavaScript / Text</span>
      </div>
      <textarea
        value={code}
        onChange={handleChange}
        style={{
          flex: 1,
          resize: 'none',
          fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
          fontSize: '0.875rem',
          padding: '0.85rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--glass-border)',
          background: 'rgba(15, 23, 42, 0.6)',
          color: '#f8fafc',
          outline: 'none',
          lineHeight: 1.6,
        }}
      />
      <div style={{ flex: 1, overflow: 'auto', marginTop: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
        <SyntaxHighlighter language={language} style={atomOneDark} customStyle={{ margin: 0, padding: '0.85rem', background: 'rgba(15, 23, 42, 0.8)', fontSize: '0.85rem' }}>
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default CodeEditor;
