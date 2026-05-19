import React, { useState } from 'react';
import { User, Bot, Clock, FileText, Copy, Check } from 'lucide-react';
import './Chat.css';

function Chat({ messages, isLoading }) {
  const [copiedId, setCopiedId] = useState(null);

  const escapeHtml = (content) => {
    return String(content || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  const escapeHtmlPreservingBasicFormatting = (content) => {
    const text = String(content || '')
      .replace(/<strong>/gi, '___TAG_STRONG_OPEN___')
      .replace(/<\/strong>/gi, '___TAG_STRONG_CLOSE___')
      .replace(/<b>/gi, '___TAG_STRONG_OPEN___')
      .replace(/<\/b>/gi, '___TAG_STRONG_CLOSE___');

    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/___TAG_STRONG_OPEN___/g, '<strong>')
      .replace(/___TAG_STRONG_CLOSE___/g, '</strong>');
  };

  const formatInlineMarkdown = (content) => {
    return content
      .replace(/`([^`\n]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  };

  const formatInline = (content) => {
    return formatInlineMarkdown(escapeHtmlPreservingBasicFormatting(content));
  };

  const isTableSeparator = (line) => (
    /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)
  );

  const isTableRow = (line) => /^\s*\|.*\|\s*$/.test(line);

  const parseTableCells = (line) => (
    line
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim())
  );

  const renderTable = (rows) => {
    if (rows.length < 2) {
      return '';
    }

    const [header, ...body] = rows;
    const headerHtml = header.map((cell) => `<th>${formatInline(cell)}</th>`).join('');
    const bodyHtml = body
      .map((row) => `<tr>${row.map((cell) => `<td>${formatInline(cell)}</td>`).join('')}</tr>`)
      .join('');

    return `<div class="markdown-table-wrapper"><table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`;
  };

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
    const lines = String(content || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    const html = [];
    let paragraph = [];
    let listItems = [];
    let listType = null;
    let listStart = null;
    let inCodeBlock = false;
    let codeLines = [];

    const flushParagraph = () => {
      if (paragraph.length > 0) {
        html.push(`<p>${formatInline(paragraph.join(' '))}</p>`);
        paragraph = [];
      }
    };

    const flushList = () => {
      if (listItems.length === 0) {
        return;
      }

      const tag = listType === 'ul' ? 'ul' : 'ol';
      const typeAttr = listType === 'ol-alpha' ? ' type="a"' : '';
      const startAttr = listStart && listStart > 1 ? ` start="${listStart}"` : '';
      html.push(`<${tag}${typeAttr}${startAttr}>${listItems.map((item) => `<li>${formatInline(item)}</li>`).join('')}</${tag}>`);
      listItems = [];
      listType = null;
      listStart = null;
    };

    const flushCode = () => {
      html.push(`<pre><code>${escapeHtml(codeLines.join('\n')).trimEnd()}</code></pre>`);
      codeLines = [];
    };

    const getListDescriptor = (value) => {
      const clean = String(value || '').trim();
      const ordered = clean.match(/^(\d+)\.\s+(.+)$/);
      if (ordered) {
        return { type: 'ol', start: Number(ordered[1]), content: ordered[2] };
      }

      const alpha = clean.match(/^([a-z])\)\s+(.+)$/i);
      if (alpha) {
        return {
          type: 'ol-alpha',
          start: alpha[1].toLowerCase().charCodeAt(0) - 96,
          content: alpha[2],
        };
      }

      const bullet = clean.match(/^[-*]\s+(.+)$/);
      if (bullet) {
        return { type: 'ul', start: null, content: bullet[1] };
      }

      return null;
    };

    const nextMeaningfulLine = (startIndex) => {
      for (let nextIndex = startIndex; nextIndex < lines.length; nextIndex += 1) {
        const nextLine = lines[nextIndex].trim();
        if (nextLine) {
          return nextLine;
        }
      }
      return '';
    };

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      const trimmed = line.trim();

      if (trimmed.startsWith('```')) {
        flushParagraph();
        flushList();
        if (inCodeBlock) {
          flushCode();
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
          codeLines = [];
        }
        continue;
      }

      if (inCodeBlock) {
        codeLines.push(line);
        continue;
      }

      if (!trimmed) {
        flushParagraph();
        if (listType) {
          const nextList = getListDescriptor(nextMeaningfulLine(index + 1));
          if (nextList && nextList.type === listType) {
            continue;
          }
        }
        flushList();
        continue;
      }

      if (isTableRow(trimmed) && isTableSeparator(lines[index + 1] || '')) {
        flushParagraph();
        flushList();
        const rows = [parseTableCells(trimmed)];
        index += 2;
        while (index < lines.length && isTableRow(lines[index])) {
          rows.push(parseTableCells(lines[index]));
          index += 1;
        }
        index -= 1;
        html.push(renderTable(rows));
        continue;
      }

      const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);
      if (headingMatch) {
        flushParagraph();
        flushList();
        const level = headingMatch[1].length;
        html.push(`<h${level}>${formatInline(headingMatch[2])}</h${level}>`);
        continue;
      }

      const quoteMatch = trimmed.match(/^>\s*(.*)$/);
      if (quoteMatch) {
        flushParagraph();
        flushList();
        const quoteLines = [quoteMatch[1]];
        while (index + 1 < lines.length) {
          const nextQuote = lines[index + 1].trim().match(/^>\s*(.*)$/);
          if (!nextQuote) {
            break;
          }
          quoteLines.push(nextQuote[1]);
          index += 1;
        }
        html.push(`<blockquote>${quoteLines.map((quoteLine) => `<p>${formatInline(quoteLine)}</p>`).join('')}</blockquote>`);
        continue;
      }

      const listDescriptor = getListDescriptor(trimmed);
      if (listDescriptor?.type === 'ol') {
        flushParagraph();
        if (listType && listType !== 'ol') {
          flushList();
        }
        listType = 'ol';
        if (listStart === null) {
          listStart = listDescriptor.start;
        }
        listItems.push(listDescriptor.content);
        continue;
      }

      if (listDescriptor?.type === 'ol-alpha') {
        flushParagraph();
        if (listType && listType !== 'ol-alpha') {
          flushList();
        }
        listType = 'ol-alpha';
        if (listStart === null) {
          listStart = listDescriptor.start;
        }
        listItems.push(listDescriptor.content);
        continue;
      }

      if (listDescriptor?.type === 'ul') {
        flushParagraph();
        if (listType && listType !== 'ul') {
          flushList();
        }
        listType = 'ul';
        listItems.push(listDescriptor.content);
        continue;
      }

      flushList();
      paragraph.push(trimmed);
    }

    if (inCodeBlock) {
      flushCode();
    }
    flushParagraph();
    flushList();

    return html.join('');
  };

  if (messages.length === 0) {
    return (
      <div className="chat-empty">
        <div className="empty-content">
          <Bot size={48} className="empty-icon" />
          <h2>C.O.R.A. - Conflito de Interesses: Orientacao, Registro e Analise</h2>
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
                      {/^https?:\/\//i.test(ref.url || '') ? (
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
                  Fontes: {message.references.length}
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
