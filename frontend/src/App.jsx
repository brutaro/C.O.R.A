import React, { useEffect, useState } from 'react';
import {
  getRedirectResult,
  onAuthStateChanged,
  signInWithPopup,
  signInWithRedirect,
  signOut,
} from 'firebase/auth';
import { auth, googleProvider } from './lib/firebase';
import {
  addMessage,
  createConversation,
  ensureUserProfile,
  loadConversationMessages,
  updateConversationTitle,
} from './lib/firestore';
import { fetchWithAuth, getApiErrorMessage } from './lib/api';
import AuthComponent from './components/Auth';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import InputBox from './components/InputBox';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 768);
  const [currentConversationId, setCurrentConversationId] = useState(null);

  useEffect(() => {
    getRedirectResult(auth).catch((error) => {
      console.error('Erro no retorno do login Firebase:', error);
      setAuthError('Nao foi possivel concluir o login com Google.');
    });

    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      try {
        if (firebaseUser) {
          await ensureUserProfile(firebaseUser);
          setUser(firebaseUser);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Erro ao preparar sessao Firebase:', error);
        setAuthError('Nao foi possivel preparar a sessao do usuario.');
      } finally {
        setLoading(false);
        setAuthBusy(false);
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768 && !sidebarOpen) {
        setSidebarOpen(true);
      }
      if (window.innerWidth <= 768 && sidebarOpen) {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen]);

  const getFirebaseAuthErrorMessage = (error) => {
    const errorCode = error?.code || '';

    if (errorCode === 'auth/unauthorized-domain') {
      return 'Este dominio nao esta autorizado no Firebase. Abra o C.O.R.A. em localhost.';
    }

    if (errorCode === 'auth/popup-closed-by-user') {
      return 'O login com Google foi cancelado antes da conclusao.';
    }

    if (errorCode === 'auth/popup-blocked') {
      return 'O navegador bloqueou a janela de login do Google. Libere pop-ups e tente novamente.';
    }

    return 'Nao foi possivel entrar com Google. Tente novamente.';
  };

  const handleGoogleSignIn = async () => {
    setAuthBusy(true);
    setAuthError('');

    try {
      const isMobile = /Android|iPhone|iPad|iPod/i.test(window.navigator.userAgent);
      if (isMobile) {
        await signInWithRedirect(auth, googleProvider);
        return;
      }
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error('Erro ao autenticar com Google:', error);
      setAuthError(getFirebaseAuthErrorMessage(error));
      setAuthBusy(false);
    }
  };

  const createOrGetConversation = async () => {
    if (currentConversationId) {
      return currentConversationId;
    }

    if (!user?.uid) {
      throw new Error('Sessao nao encontrada');
    }

    const conversation = await createConversation(user);
    setCurrentConversationId(conversation.id);
    return conversation.id;
  };

  const handleConversationSelect = async (conversationId) => {
    if (!user?.uid) {
      return;
    }

    try {
      const loadedMessages = await loadConversationMessages(user.uid, conversationId);
      setMessages(loadedMessages);
      setCurrentConversationId(conversationId);
      if (window.innerWidth <= 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error);
    }
  };

  const handleSendMessage = async (question) => {
    if (!question.trim() || isLoading) {
      return;
    }

    if (!user?.uid) {
      setMessages((previous) => [
        ...previous,
        {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: '❌ Erro: Sessao nao encontrada. Faca login novamente.',
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
      return;
    }

    let conversationId;
    try {
      conversationId = await createOrGetConversation();
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
      setMessages((previous) => [
        ...previous,
        {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: '❌ Erro ao criar conversa. Tente novamente.',
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
      return;
    }

    if (messages.length === 0) {
      const shortTitle = question.length > 50 ? `${question.substring(0, 50)}...` : question;
      try {
        await updateConversationTitle(user.uid, conversationId, shortTitle);
      } catch (error) {
        console.error('Erro ao atualizar titulo da conversa:', error);
      }
    }

    const userMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages((previous) => [...previous, userMessage]);

    try {
      await addMessage(user.uid, conversationId, 'user', question);
    } catch (error) {
      console.error('Erro ao salvar mensagem do usuario no Firestore:', error);
    }

    setIsLoading(true);

    try {
      const response = await fetchWithAuth('/api/consulta', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pergunta: question,
          session_id: conversationId,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(await getApiErrorMessage(response));
      }

      const result = await response.json();
      const assistantMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: result.resposta_completa || result.resumo,
        references: result.references || [],
        isError: result.status === 'error',
        timestamp: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, assistantMessage]);

      try {
        await addMessage(user.uid, conversationId, 'assistant', assistantMessage.content, {
          metadata: {
            references: result.references || [],
            fontes: result.fontes || 0,
            workflow_id: result.workflow_id || null,
            duracao: result.duracao || null,
          },
          status: assistantMessage.isError ? 'error' : 'saved',
        });
      } catch (error) {
        console.error('Erro ao salvar resposta no Firestore:', error);
      }
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      setMessages((previous) => [
        ...previous,
        {
          id: `error_${Date.now()}`,
          role: 'assistant',
          content: `❌ Erro ao processar sua pergunta: ${error.message}.`,
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };

  const toggleSidebar = () => {
    setSidebarOpen((previous) => !previous);
  };

  const handleSignOut = async () => {
    await signOut(auth);
    setMessages([]);
    setCurrentConversationId(null);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Carregando...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <AuthComponent
        onSignIn={handleGoogleSignIn}
        loading={authBusy}
        error={authError}
      />
    );
  }

  return (
    <div className="app">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={toggleSidebar}
        onNewChat={clearChat}
        user={user}
        onSignOut={handleSignOut}
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onConversationDeleted={clearChat}
      />

      <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="chat-container">
          <Chat
            messages={messages}
            isLoading={isLoading}
          />
        </div>

        <InputBox
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;
