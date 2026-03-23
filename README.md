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

- backend: `cd CORA/backend && source .venv/bin/activate && uvicorn main:app --reload --port 8001`
- frontend: `cd CORA/frontend && npm start`

Observacao operacional:

- o Firestore foi criado em modo de teste no console;
- a base de regras definitiva ja foi preparada localmente, mas ainda precisa ser publicada no projeto Firebase.
- em Cloud Run, o backend pode usar a service account anexada ao servico via credenciais padrao do Google; `FIREBASE_SERVICE_ACCOUNT_JSON` e `FIREBASE_SERVICE_ACCOUNT_PATH` ficam opcionais para esse ambiente.
