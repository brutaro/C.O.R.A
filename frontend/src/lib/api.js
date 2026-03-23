import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';

async function waitForAuthenticatedUser(timeoutMs = 5000) {
  if (auth.currentUser) {
    return auth.currentUser;
  }

  return new Promise((resolve) => {
    let settled = false;
    let timeoutId = null;
    let unsubscribe = () => {};

    const finalize = (user) => {
      if (settled) {
        return;
      }

      settled = true;
      window.clearTimeout(timeoutId);
      unsubscribe();
      resolve(user || null);
    };

    unsubscribe = onAuthStateChanged(auth, (user) => {
      finalize(user);
    });

    timeoutId = window.setTimeout(() => {
      finalize(null);
    }, timeoutMs);
  });
}

async function resolveAuthUser(preferredUser) {
  if (preferredUser) {
    return preferredUser;
  }

  if (auth.currentUser) {
    return auth.currentUser;
  }

  return waitForAuthenticatedUser();
}

export async function fetchWithAuth(input, init = {}, preferredUser = null) {
  const executeRequest = async (forceRefresh = true) => {
    const headers = new Headers(init.headers || {});
    const firebaseUser = await resolveAuthUser(preferredUser);
    const token = await firebaseUser?.getIdToken(forceRefresh);

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(input, {
      ...init,
      headers,
    });
  };

  let response = await executeRequest(true);

  if (response.status === 401) {
    response = await executeRequest(true);
  }

  return response;
}

export async function getApiErrorMessage(response) {
  const defaultMessage = `Erro: ${response.status}`;

  try {
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      const data = await response.json();
      if (data?.detail) {
        if (typeof data.detail === 'object') {
          const detailMessage = data.detail.message || defaultMessage;
          const detailError = data.detail.error ? `: ${data.detail.error}` : '';
          return `${detailMessage}${detailError}`;
        }
        return data.detail;
      }
    } else {
      const text = await response.text();

      if (response.status === 401 && text.includes('<title>401 Unauthorized</title>')) {
        return 'A plataforma bloqueou a requisicao antes do backend. Verifique se o servico esta publico e se o proxy esta encaminhando o header Authorization.';
      }

      if (text) {
        return text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
      }
    }
  } catch (error) {
    console.error('Erro ao interpretar resposta da API:', error);
  }

  if (response.status === 401) {
    return 'Falha de autenticacao. Faca login novamente.';
  }

  if (response.status === 403) {
    return 'Acesso negado para esta operacao.';
  }

  return defaultMessage;
}
