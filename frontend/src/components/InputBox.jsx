import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import './InputBox.css';

function InputBox({ onSendMessage, isLoading }) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="input-container">
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-wrapper">
          <div className="input-field">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Faca sua pergunta sobre conflito de interesses aqui..."
              className="message-input"
              disabled={isLoading}
              rows={1}
              maxLength={2000}
            />
          </div>

          <button
            type="submit"
            className="send-button"
            disabled={!message.trim() || isLoading}
            title="Enviar mensagem"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>

        {message.length > 1800 && (
          <div className="character-count">
            {message.length}/2000 caracteres
          </div>
        )}
      </form>

      <div className="input-footer">
        <p>
          C.O.R.A. pode cometer erros. Verifique informacoes importantes.
        </p>
      </div>
    </div>
  );
}

export default InputBox;
