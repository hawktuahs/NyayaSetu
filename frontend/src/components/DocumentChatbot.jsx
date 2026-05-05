import { useState, useRef, useEffect, Fragment } from 'react';
import { chatWithDocument } from '../api/client';

function MessageFormatter({ text, onJumpToPage }) {
  if (!text) return null;

  // Split by newlines first
  const lines = text.split('\n');
  
  return (
    <>
      {lines.map((line, i) => {
        // Parse bold markdown **text**
        let parts = line.split(/(\*\*.*?\*\*)/g);
        
        return (
          <Fragment key={i}>
            {parts.map((part, j) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={j}>{part.slice(2, -2)}</strong>;
              }
              
              // Parse [Page X: "quote"] or [Page X] citations
              const citeRegex = /\[Page\s+(\d+)(?::\s*"([^"]+)")?\]/g;
              let match;
              let lastIndex = 0;
              const elements = [];
              let k = 0;
              
              // We must reset lastIndex since citeRegex is global and we are re-using it on different parts? 
              // Wait, citeRegex is defined locally above, so it's fresh. But let's just use matchAll or exec.
              while ((match = citeRegex.exec(part)) !== null) {
                if (match.index > lastIndex) {
                  elements.push(<span key={`text-${k++}`}>{part.slice(lastIndex, match.index)}</span>);
                }
                const pageNum = parseInt(match[1], 10);
                const quote = match[2] || '';
                
                elements.push(
                  <button 
                    key={`btn-${k++}`}
                    className="btn btn-ghost" 
                    style={{ padding: '0 4px', fontSize: 10, height: 18, minHeight: 18, color: 'var(--saffron)', display: 'inline-flex', verticalAlign: 'middle', margin: '0 4px' }}
                    onClick={() => onJumpToPage && onJumpToPage(pageNum, quote)}
                    title={quote ? `Highlight: "${quote}"` : ''}
                  >
                    📄 P.{pageNum}
                  </button>
                );
                lastIndex = citeRegex.lastIndex;
              }
              
              if (lastIndex < part.length) {
                elements.push(<span key={`text-${k++}`}>{part.slice(lastIndex)}</span>);
              }
              
              if (elements.length > 0) {
                return <Fragment key={j}>{elements}</Fragment>;
              }

              return <span key={j}>{part}</span>;
            })}
            {i < lines.length - 1 && <br />}
          </Fragment>
        );
      })}
    </>
  );
}

export default function DocumentChatbot({ caseId, onJumpToPage }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI assistant for this judgment. What would you like to know?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatWithDocument(caseId, newMessages);
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.reply }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button 
        className="btn btn-primary" 
        style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000, borderRadius: '50%', width: 60, height: 60, fontSize: 24, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
        onClick={() => setIsOpen(true)}
        title="Ask the AI about this document"
      >
        💬
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20, width: 350, height: 500,
      backgroundColor: 'var(--card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column',
      boxShadow: '0 8px 32px rgba(0,0,0,0.5)', zIndex: 1000, overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div style={{ fontWeight: 600, color: 'var(--text-1)' }}>🤖 Legal AI Assistant</div>
        <button onClick={() => setIsOpen(false)} style={{
          background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer', fontSize: 16
        }}>✕</button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            padding: '10px 14px',
            borderRadius: '12px',
            backgroundColor: m.role === 'user' ? 'var(--saffron)' : 'var(--bg)',
            color: m.role === 'user' ? '#fff' : 'var(--text-1)',
            fontSize: 13,
            lineHeight: 1.5,
            borderBottomRightRadius: m.role === 'user' ? 4 : 12,
            borderBottomLeftRadius: m.role === 'assistant' ? 4 : 12,
          }}>
            <MessageFormatter text={m.content} onJumpToPage={onJumpToPage} />
          </div>
        ))}
        {isLoading && (
          <div style={{ alignSelf: 'flex-start', padding: '10px 14px', backgroundColor: 'var(--bg)', borderRadius: '12px', fontSize: 13, color: 'var(--text-2)' }}>
            <span className="spinner" style={{ width: 12, height: 12, marginRight: 8 }}></span> Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: 12, borderTop: '1px solid var(--border)', backgroundColor: 'var(--card)',
        display: 'flex', gap: 8
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius)',
            border: '1px solid var(--border)', backgroundColor: 'var(--bg)', color: 'var(--text-1)',
            outline: 'none', fontSize: 13
          }}
          disabled={isLoading}
        />
        <button 
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="btn btn-primary"
          style={{ padding: '8px 16px' }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
