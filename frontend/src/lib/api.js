import { auth } from './firebase';

export async function fetchWithAuth(input, init = {}) {
  const executeRequest = async (forceRefresh = true) => {
    const headers = new Headers(init.headers || {});
    const token = await auth.currentUser?.getIdToken(forceRefresh);

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(input, {
      ...init,
      headers,
    });
  };

  let response = await executeRequest(true);

  if (response.status === 401 && auth.currentUser) {
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
        return data.detail;
      }
    } else {
      const text = await response.text();

      if (response.status === 401 && text.includes('<title>401 Unauthorized</title>')) {
        return 'Cloud Run bloqueou a requisicao antes do backend. No Cloud Run, deixe o servico com acesso publico e mantenha a autenticacao Firebase no app.';
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
