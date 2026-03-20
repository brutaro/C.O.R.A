import React, { useState } from 'react';
import { User, Bot, Clock, FileText, Copy, Check } from 'lucide-react';
import './Chat.css';

function Chat({ messages, isLoading }) {
  const [copiedId, setCopiedId] = useState(null);

  const getReferenceNamespace = (message) => {
    const namespaces = [...new Set((message.references || []).map((ref) => ref.namespace).filter(Boolean))];
    if (namespaces.length === 0) {
      return null;
    }
    return namespaces.join(', ');
  };

  const handleCopy = async (message) => {
    // Formata o conteúdo para cópia
    let copyText = message.content;
    const referenceNamespace = getReferenceNamespace(message);

    // Adiciona referências se houver
    if (message.references && message.references.length > 0) {
      copyText += '\n\nReferências consultadas:\n';
      if (referenceNamespace) {
        copyText += `Namespace utilizado: ${referenceNamespace}\n`;
      }
      message.references.forEach(ref => {
        copyText += `- ${ref.source} (Relevância: ${(ref.score * 100).toFixed(1)}%)\n`;
      });
    }

    try {
      // Tenta API moderna primeiro
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(copyText);
      } else {
        throw new Error('Clipboard API unavailable');
      }
    } catch (err) {
      // Fallback para método antigo (funciona em HTTP/Mobile)
      try {
        const textArea = document.createElement("textarea");
        textArea.value = copyText;

        // Garante que o elemento não seja visível mas esteja no DOM
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        document.body.appendChild(textArea);

        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (!successful) throw new Error('execCommand failed');
      } catch (fallbackErr) {
        console.error('Erro ao copiar (fallback):', fallbackErr);
        alert('Não foi possível copiar o texto. Seu navegador pode estar bloqueando o acesso à área de transferência.');
        return;
      }
    }

    setCopiedId(message.id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatMessage = (content) => {
    // Converte markdown simples para HTML
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^(.*)$/gim, '<p>$1</p>');
  };

  if (messages.length === 0) {
    return (
      <div className="chat-empty">
        <div className="empty-content">
          <Bot size={48} className="empty-icon" />
          <h2>C.O.R.A. - Conflito de Interesses</h2>
          <p>Ola! Eu sou a C.O.R.A., sua assistente para orientacao e analise em conflito de interesses.</p>
          <div className="suggestions">
            <h3>Você pode perguntar sobre:</h3>
            <div className="suggestion-tags">
              <span className="tag">Acumulacao de atividades</span>
              <span className="tag">Exercicio de atividade privada</span>
              <span className="tag">Impedimentos e vedacoes</span>
              <span className="tag">Consultas sobre notas tematicas</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat">
      {messages.map((message) => (
        <div key={message.id} className={`message ${message.role} ${message.isError ? 'error' : ''}`}>
          <div className="message-avatar">
            {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
          </div>

          <div className="message-content">
            <div className="message-header">
              <span className="message-role">
                {message.role === 'user' ? 'Voce' : 'C.O.R.A.'}
              </span>
              <span className="message-time">
                <Clock size={12} />
                {formatTimestamp(message.timestamp)}
              </span>
            </div>

            <div
              className="message-text"
              dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
            />

            {message.references && message.references.length > 0 && (
              <div className="message-references">
                <h4>
                  <FileText size={14} />
                  Referências consultadas:
                </h4>
                {getReferenceNamespace(message) && (
                  <p className="reference-namespace">
                    Namespace utilizado: {getReferenceNamespace(message)}
                  </p>
                )}
                <ul className="references-list">
                  {message.references.map((ref, index) => (
                    <li key={index} className="reference-item">
                      {ref.url ? (
                        <a
                          href={ref.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="reference-source reference-link"
                        >
                          {ref.source}
                        </a>
                      ) : (
                        <span className="reference-source">{ref.source}</span>
                      )}
                      <span className="reference-score">
                        Relevância: {(ref.score * 100).toFixed(1)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {message.references && message.references.length > 0 && (
              <div className="message-stats">
                <span className="reference-count">
                  📊 {message.references.length} fontes
                </span>
              </div>
            )}

            {message.role === 'assistant' && !message.isError && (
              <div className="message-actions">
                <button
                  className="copy-button"
                  onClick={() => handleCopy(message)}
                  title="Copiar resposta"
                >
                  {copiedId === message.id ? (
                    <>
                      <Check size={14} />
                      <span>Copiado!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copiar resposta</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="message assistant loading-message">
          <div className="message-avatar">
            <Bot size={20} />
          </div>
          <div className="message-content">
            <div className="message-header">
              <span className="message-role">C.O.R.A.</span>
            </div>
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Chat;
