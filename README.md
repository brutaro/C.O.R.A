# C.O.R.A.

`C.O.R.A.` significa `Conflito de Interesses: Orientacao, Registro e Analise`.

Esta pasta concentra a nova frente local do assistente tematico de conflito de interesses.

Estado atual desta etapa:

- frontend derivado da L.A.R.A. e mantido localmente em `CORA/frontend`;
- backend derivado da L.A.R.A. e mantido localmente em `CORA/backend`;
- namespace do produto definido como `notas_conflito_interesse`;
- Redis mantido como memoria contextual;
- exportacao em PDF mantida no produto;
- autenticacao Google e historico migrados para Firebase Auth + Firestore;
- regras locais do Firestore preparadas em `CORA/firestore.rules`;
- repositorio futuro definido como `https://github.com/brutaro/C.O.R.A.`;
- nada sera preparado para GitHub nesta fase.

Diretrizes atuais:

- manter a mesma estetica estrutural do frontend da L.A.R.A.;
- trocar apenas nome, textos publicos e identidade visual;
- manter backend proprio, sem compartilhamento operacional de scripts com a L.A.R.A.;
- usar Firebase Auth + Firestore na primeira versao funcional;
- seguir o PRD em `docs/PRD_ASSISTENTE_CONFLITO_INTERESSES_FIREBASE.md`;
- nao introduzir plataforma de observabilidade dedicada nesta etapa.

Arquivos Firebase locais:

- `CORA/.firebaserc`
- `CORA/firebase.json`
- `CORA/firestore.rules`
- `CORA/firestore.indexes.json`

Execucao local:

- diagnostico rapido: `./scripts/dev-doctor.sh`
- subir tudo: `./scripts/dev-up.sh`
- status: `./scripts/dev-status.sh`
- parar tudo: `./scripts/dev-down.sh`

Fluxo local esperado:

- backend em `http://localhost:8001`
- frontend em `http://localhost:3000`
- health em `http://localhost:8001/api/health`

Pre-requisitos locais:

- `backend/.venv` criado com as dependencias Python
- `frontend/node_modules` instalado
- `backend/reportlab/node_modules` instalado para o PDF
- `backend/.env` presente
- `frontend/.env` presente

Observacao operacional:

- o Firestore foi criado em modo de teste no console;
- a base de regras definitiva ja foi preparada localmente, mas ainda precisa ser publicada no projeto Firebase.

Deploy via Railway:

- o deploy de producao deve usar o `Dockerfile` da raiz do projeto;
- o arquivo de variaveis para importacao no Railway fica em `CORA/.env.railway.example`;
- para o backend validar Firebase no Railway, use `FIREBASE_SERVICE_ACCOUNT_JSON`;
- para login Google em producao, adicione o dominio publico do Railway aos `Authorized domains` do Firebase Auth.
