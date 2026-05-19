# C.O.R.A.

`C.O.R.A.` significa `Conflito de Interesses: Orientacao, Registro e Analise`.

Esta pasta concentra a nova frente local do assistente tematico de conflito de interesses.

Estado atual desta etapa:

- frontend derivado da L.A.R.A. e mantido localmente em `CORA/frontend`;
- backend derivado da L.A.R.A. e mantido localmente em `CORA/backend`;
- modelo Gemini padrao: `gemini-3.1-flash-lite`;
- formatacao visual das respostas controlada por `ENABLE_CHAT_FORMATTING`;
- namespace do produto definido como `notas_conflito_interesse`;
- Redis mantido como memoria contextual;
- memoria Redis escopada por usuario e conversa, com prefixo `cora:session`;
- consultas a uma nota tecnica especifica filtram o Pinecone por `numero_nota_tecnica` antes de montar o contexto;
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

Acervo e pipeline CORA:

- corpus oficial: `CORA/corpus/NOTAS-CONFLITO-INTERESSE`;
- planilhas-fonte do recorte: `CORA/corpus/source_lists`;
- backups de metadados do recorte inicial: `CORA/corpus/backups_metadados`;
- artefatos processados: `CORA/corpus/processed_conflito_interesse*`;
- relatórios e inventários: `CORA/corpus/output`;
- scripts de ingestão, auditoria e upsert: `CORA/corpus/scripts`;
- documentação do produto e relatórios: `CORA/docs`.

Execucao local recomendada, emulando Railway:

- subir container: `./scripts/docker-up.sh`
- status do container: `./scripts/docker-status.sh`
- parar container: `./scripts/docker-down.sh`
- app integrada em `http://localhost:8080`
- health em `http://127.0.0.1:8080/api/health`

Este fluxo usa o `Dockerfile` da raiz da CORA, gera o build do React e serve frontend + API no mesmo processo/container, como no deploy. O arquivo `docker-compose.yml` usa `backend/.env` como fonte das variaveis privadas e força `PINECONE_NAMESPACE=notas_conflito_interesse`, `GEMINI_MODEL=gemini-3.1-flash-lite` e `REDIS_KEY_PREFIX=cora:session`.

Configuracao Docker local:

- `backend/.env` precisa existir;
- por padrao, o compose monta `cora-9d120-firebase-adminsdk-fbsvc-9db52ba42d.json` como segredo local em `/run/secrets/cora-firebase-service-account.json`;
- para usar outro caminho ou porta, copie `.env.docker.example` para `.env.docker` e ajuste `FIREBASE_SERVICE_ACCOUNT_FILE` ou `CORA_DOCKER_PORT`.

Execucao local legada, com backend e frontend separados:

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
