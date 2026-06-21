import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi there! I am the Telegram Suite support AI. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Send the entire conversation history for context
      const chatHistory = messages.map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }]
      }));
      // Add the latest user message
      chatHistory.push({ role: 'user', parts: [{ text: userMessage.content }] });

      const res = await fetch('/api/support/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: chatHistory })
      });

      const data = await res.json();
      
      if (data.status === 'success') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: data.detail || 'Sorry, I am having trouble connecting to the support server right now. Please try again later.' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-widget-container">
      {/* Chat Window */}
      <div className={`chat-window ${isOpen ? 'open' : ''}`}>
        <div className="chat-header">
          <div className="chat-header-info">
            <div className="chat-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a2 2 0 0 1 2 2c0 1.1-.9 2-2 2a2 2 0 0 1-2-2c0-1.1.9-2 2-2zm0 14c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm7.5-6h-1.28c-.46-3.03-2.82-5.49-5.81-6.07C12.31 3.98 12.16 4 12 4s-.31-.02-.41-.07C8.6 4.51 6.24 6.97 5.78 10H4.5C3.12 10 2 11.12 2 12.5S3.12 15 4.5 15h1.28c.46 3.03 2.82 5.49 5.81 6.07.1.05.25.07.41.07s.31-.02.41-.07c2.99-.58 5.35-3.04 5.81-6.07h1.28c1.38 0 2.5-1.12 2.5-2.5S20.88 10 19.5 10z"/>
              </svg>
            </div>
            <div>
              <h3>AI Support</h3>
              <span className="chat-status">Online</span>
            </div>
          </div>
          <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message-wrapper ${msg.role}`}>
              <div className="chat-bubble">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-message-wrapper assistant">
              <div className="chat-bubble typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={!input.trim() || loading}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </form>
      </div>

      {/* Floating Action Button */}
      <button className={`chat-fab ${isOpen ? 'hide' : ''}`} onClick={() => setIsOpen(true)}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
      </button>
    </div>
  );
}

export default ChatWidget;
