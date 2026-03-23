import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Plus, MessageSquare, Sun, Moon, LogOut, User, MoreVertical, Edit, Trash2, X, Check, Download, Menu } from 'lucide-react';
import {
  createConversation,
  deleteConversation,
  getConversationExportData,
  listConversations,
  renameConversation,
} from '../lib/firestore';
import { fetchWithAuth, getApiErrorMessage } from '../lib/api';
import './Sidebar.css';

function Sidebar({ isOpen, onToggle, onNewChat, user, onSignOut, currentConversationId, onConversationSelect, onConversationDeleted }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);
  const editInputRef = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
      document.body.setAttribute('data-theme', savedTheme);
    } else {
      document.body.setAttribute('data-theme', 'dark');
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        menuOpenId &&
        !event.target.closest('.conversation-menu-button') &&
        !event.target.closest('.conversation-menu-dropdown')
      ) {
        setMenuOpenId(null);
      }
    };

    if (menuOpenId) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpenId]);

  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  const fetchConversations = useCallback(async () => {
    if (!user?.uid) {
      return;
    }

    try {
      setLoading(true);
      const data = await listConversations(user.uid);
      setConversations(data);
    } catch (error) {
      console.error('Erro ao buscar conversas no Firestore:', error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user?.uid) {
      fetchConversations();
    }
  }, [user?.uid, fetchConversations]);

  useEffect(() => {
    if (isOpen && window.innerWidth <= 768) {
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
    } else {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    }

    return () => {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    };
  }, [isOpen]);

  useEffect(() => {
    if (currentConversationId && user?.uid) {
      const timer = setTimeout(() => {
        fetchConversations();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [currentConversationId, user?.uid, fetchConversations]);

  const createNewConversation = async () => {
    if (!user?.uid) {
      return;
    }

    try {
      const conversation = await createConversation(user);
      await fetchConversations();
      onNewChat();
      if (onConversationSelect) {
        onConversationSelect(conversation.id);
      }
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
    }
  };

  const handleConversationClick = (conversationId) => {
    if (onConversationSelect) {
      onConversationSelect(conversationId);
    }
    if (window.innerWidth <= 768 && isOpen) {
      onToggle();
    }
  };

  const toggleTheme = () => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setIsDarkMode(!isDarkMode);
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const formatDate = (dateString) => {
    if (!dateString) {
      return 'Agora';
    }

    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Hoje';
    if (days === 1) return 'Ontem';
    if (days < 7) return `${days} dias atrás`;
    return date.toLocaleDateString('pt-BR');
  };

  const handleMenuToggle = (event, conversationId) => {
    event.stopPropagation();
    setMenuOpenId(menuOpenId === conversationId ? null : conversationId);
  };

  const handleRename = (event, conversation) => {
    event.stopPropagation();
    setMenuOpenId(null);
    setEditingId(conversation.id);
    setEditingTitle(conversation.title);
  };

  const handleSaveRename = async (conversationId) => {
    if (!editingTitle.trim() || !user?.uid) {
      return;
    }

    try {
      await renameConversation(user.uid, conversationId, editingTitle.trim());
      setEditingId(null);
      setEditingTitle('');
      await fetchConversations();
    } catch (error) {
      console.error('Erro ao renomear conversa:', error);
      alert('Erro ao renomear conversa. Tente novamente.');
    }
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const handleDelete = async (event, conversationId) => {
    event.stopPropagation();
    setMenuOpenId(null);

    const confirmMessage = currentConversationId === conversationId
      ? 'Você está excluindo a conversa ativa. Todas as mensagens serão perdidas. Deseja continuar?'
      : 'Tem certeza que deseja excluir esta conversa? Todas as mensagens serão perdidas.';

    if (!window.confirm(confirmMessage) || !user?.uid) {
      return;
    }

    try {
      await deleteConversation(user.uid, conversationId);

      if (currentConversationId === conversationId) {
        if (onConversationDeleted) {
          onConversationDeleted();
        }
        if (onNewChat) {
          onNewChat();
        }
      }

      await fetchConversations();
    } catch (error) {
      console.error('Erro ao excluir conversa:', error);
      alert('Erro ao excluir conversa. Tente novamente.');
    }
  };

  const handleDownload = async (event, conversationId, title) => {
    event.stopPropagation();
    setMenuOpenId(null);
    setDownloadingId(conversationId);

    try {
      if (!user?.uid) {
        throw new Error('Sessao do usuario nao encontrada.');
      }

      const exportPayload = await getConversationExportData(user.uid, conversationId, title);
      const response = await fetchWithAuth('/api/conversations/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportPayload),
      });

      if (!response.ok) {
        throw new Error(await getApiErrorMessage(response));
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const sanitizedTitle = (title || '')
        .trim()
        .replace(/[^a-zA-Z0-9_-]+/g, '_')
        .replace(/_+/g, '_') || conversationId;

      const link = document.createElement('a');
      link.href = url;
      link.download = `cora_conversa_${sanitizedTitle}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao baixar PDF:', error);
      alert(error.message || 'Erro ao baixar PDF. Tente novamente.');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleKeyDown = (event, conversationId) => {
    if (event.key === 'Enter') {
      handleSaveRename(conversationId);
    } else if (event.key === 'Escape') {
      handleCancelRename();
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          className="sidebar-toggle-floating"
          onClick={onToggle}
          aria-label="Abrir menu"
        >
          <div className="toggle-icon">☰</div>
        </button>
      )}

      {isOpen && window.innerWidth <= 768 && (
        <div
          className="sidebar-overlay active"
          onClick={onToggle}
          aria-label="Fechar menu"
        />
      )}

      <aside className={`sidebar ${isOpen ? 'sidebar-open' : 'sidebar-hidden'}`}>
        <div className="sidebar-header">
          <button
            className="sidebar-toggle"
            onClick={onToggle}
            aria-label="Fechar menu"
          >
            <Menu size={24} />
          </button>
          <h2>C.O.R.A.</h2>
        </div>

        <div className="sidebar-content">
          <button className="new-chat-button" onClick={createNewConversation}>
            <Plus size={16} />
            <span>Nova conversa</span>
          </button>

          <div className="sidebar-section">
            <h3>Histórico</h3>
            <div className="conversation-list">
              {loading ? (
                <div className="conversation-loading">
                  <p>Carregando...</p>
                </div>
              ) : conversations.length > 0 ? (
                conversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className={`conversation-item ${currentConversationId === conversation.id ? 'active' : ''}`}
                    onClick={() => handleConversationClick(conversation.id)}
                  >
                    <MessageSquare size={16} />
                    <div className="conversation-info">
                      {editingId === conversation.id ? (
                        <div className="conversation-edit">
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editingTitle}
                            onChange={(event) => setEditingTitle(event.target.value)}
                            onKeyDown={(event) => handleKeyDown(event, conversation.id)}
                            className="conversation-edit-input"
                            onClick={(event) => event.stopPropagation()}
                            onBlur={(event) => {
                              if (!event.relatedTarget?.closest('.conversation-edit-buttons')) {
                                handleCancelRename();
                              }
                            }}
                          />
                          <div className="conversation-edit-buttons">
                            <button
                              className="edit-button-save"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleSaveRename(conversation.id);
                              }}
                              title="Salvar"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              className="edit-button-cancel"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleCancelRename();
                              }}
                              title="Cancelar"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <span className="conversation-title">{conversation.title}</span>
                          <span className="conversation-date">{formatDate(conversation.updated_at)}</span>
                        </>
                      )}
                    </div>
                    {editingId !== conversation.id && (
                      <div className="conversation-menu">
                        <button
                          className="conversation-menu-button"
                          onClick={(event) => handleMenuToggle(event, conversation.id)}
                          title="Opções"
                        >
                          <MoreVertical size={16} />
                        </button>
                        {menuOpenId === conversation.id && (
                          <div className="conversation-menu-dropdown">
                            <button
                              className="menu-item"
                              onClick={(event) => handleDownload(event, conversation.id, conversation.title)}
                              disabled={downloadingId === conversation.id}
                            >
                              <Download size={14} />
                              <span>{downloadingId === conversation.id ? 'Baixando...' : 'Baixar PDF'}</span>
                            </button>
                            <button
                              className="menu-item"
                              onClick={(event) => handleRename(event, conversation)}
                            >
                              <Edit size={14} />
                              <span>Renomear</span>
                            </button>
                            <button
                              className="menu-item menu-item-danger"
                              onClick={(event) => handleDelete(event, conversation.id)}
                            >
                              <Trash2 size={14} />
                              <span>Excluir</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="conversation-empty">
                  <p>Nenhuma conversa ainda</p>
                  <p>Clique em "Nova conversa" para começar!</p>
                </div>
              )}
            </div>
          </div>

          <div className="sidebar-footer">
            {user && (
              <div className="user-info">
                <User size={16} />
                <span className="user-email">{user.email}</span>
              </div>
            )}
            <div className="footer-buttons">
              <button
                className="theme-toggle-button"
                onClick={toggleTheme}
                aria-label={isDarkMode ? 'Ativar modo claro' : 'Ativar modo escuro'}
                title={isDarkMode ? 'Modo Claro' : 'Modo Escuro'}
              >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              {onSignOut && (
                <button
                  className="signout-button"
                  onClick={onSignOut}
                  aria-label="Sair"
                  title="Sair"
                >
                  <LogOut size={20} />
                </button>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
