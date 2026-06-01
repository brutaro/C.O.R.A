# C.O.R.A. - Documentacao tecnica das entregas de maio de 2026

Periodo de referencia: maio de 2026

## 1. Visao geral

O C.O.R.A. (`Conflito de Interesses: Orientacao, Registro e Analise`) foi consolidado como assistente juridico especializado em notas tecnicas de conflito de interesses. A solucao foi organizada como frente propria, separada operacionalmente da L.A.R.A., embora parte da base de codigo tenha sido reaproveitada.

As entregas de maio de 2026 tiveram os seguintes objetivos tecnicos:

- organizar os artefatos do C.O.R.A. em uma pasta propria do projeto;
- garantir isolamento de namespace, autenticacao, historico e memoria;
- preparar ambiente local em Docker para aproximar a execucao local do Railway;
- atualizar o modelo Gemini padrao;
- melhorar a recuperacao de notas especificas no Pinecone;
- melhorar a apresentacao visual das respostas no chat e nos PDFs;
- remover truncamento artificial do contexto recuperado do Pinecone antes do envio ao Gemini;
- documentar o estado atual para continuidade segura do desenvolvimento.

## 2. Regras operacionais e limites de arquitetura

Foram adotadas as seguintes regras tecnicas:

- operacoes de versionamento remoto para `https://github.com/brutaro/C.O.R.A.git` somente ocorrem com aprovacao explicita;
- o C.O.R.A. usa exclusivamente o namespace Pinecone `notas_conflito_interesse`;
- embora compartilhe o mesmo index name de outros assistentes, o C.O.R.A. nao deve consultar namespaces da L.A.R.A.;
- autenticacao de usuario, historico de conversas e base de analytics usam Firebase/Firestore;
- Supabase nao e base de autenticacao, historico ou analytics do C.O.R.A.;
- Redis e usado apenas como memoria contextual curta, escopada por usuario e conversa;
- segredos, service accounts, `.env` reais e corpus pesado nao devem ser versionados.

## 3. Organizacao do projeto

A frente do C.O.R.A. foi reunida em `CORA/`, com a seguinte organizacao:

- `CORA/backend`: backend FastAPI, agente RAG, autenticacao, PDF e integracoes;
- `CORA/frontend`: frontend React, chat, login e historico;
- `CORA/corpus`: acervo, artefatos processados, scripts e relatorios de ingestao;
- `CORA/docs`: documentacao tecnica, gerencial, inventarios e relatorios;
- `CORA/scripts`: scripts operacionais locais;
- `CORA/Dockerfile`: build integrado de frontend e backend;
- `CORA/docker-compose.yml`: orquestracao local do servico;
- `CORA/.env.docker.example`: exemplo de variaveis para Docker local;
- `CORA/.env.railway.example`: exemplo de variaveis para Railway.

Tambem foram ajustados `.gitignore` e `.dockerignore` para reduzir risco de inclusao de segredos, corpus, caches, ambientes virtuais, builds locais e artefatos temporarios.

## 4. Base de conhecimento Pinecone

O C.O.R.A. foi configurado para operar sobre o namespace:

```text
notas_conflito_interesse
```

Foi criado scanner read-only para auditar o namespace:

```text
CORA/corpus/scripts/cora_scan_pinecone_namespace_status.py
```

O levantamento confirmou:

- `131` notas/documentos distintos;
- `2367` vetores;
- namespace auditado: `notas_conflito_interesse`.

Relatorios relacionados:

- `CORA/corpus/output/cora_pinecone_namespace_stats_2026-05-13.md`;
- `CORA/corpus/output/cora_pinecone_namespace_stats_2026-05-13.json`;
- aliases `latest` correspondentes.

## 5. Firebase, Firestore e historico

O C.O.R.A. usa Firebase Auth para login e Firestore para persistencia das conversas.

Estrutura logica utilizada:

- `users/{uid}`;
- `users/{uid}/conversations/{conversationId}`;
- `users/{uid}/conversations/{conversationId}/messages/{messageId}`.

Arquivos relevantes:

- `CORA/frontend/src/lib/firebase.js`;
- `CORA/frontend/src/lib/firestore.js`;
- `CORA/backend/auth.py`;
- `CORA/backend/firebase_config.py`;
- `CORA/firestore.rules`;
- `CORA/firestore.indexes.json`.

As conversas do C.O.R.A. carregam metadados de produto para evitar mistura com outros assistentes:

- `assistant_slug = "cora"`;
- `assistant_name = "C.O.R.A."`;
- `knowledge_namespace = "notas_conflito_interesse"`.

## 6. Isolamento de conversas e memoria Redis

Foi analisado o risco de vazamento de contexto entre historicos de conversa. O backend passou a tratar `uid` e `conversation_id` como escopo obrigatorio da memoria contextual.

Correcoes implementadas:

- exigencia de `conversation_id` para consultas do chat;
- validacao da conversa no Firestore do usuario autenticado;
- validacao de `assistant_slug = "cora"`;
- validacao de `knowledge_namespace = "notas_conflito_interesse"`;
- composicao da chave Redis por usuario e conversa;
- prefixo Redis padrao `cora:session`;
- endpoints de limpeza e estatisticas de sessao usando o mesmo escopo.

Arquivos relevantes:

- `CORA/backend/main.py`;
- `CORA/backend/src/memory/redis_memory.py`;
- `CORA/docker-compose.yml`;
- `CORA/.env.railway.example`;
- `CORA/.env.docker.example`;
- `CORA/README.md`.

Estado esperado no healthcheck:

- `auth_provider: firebase`;
- `history_store: firestore`;
- `memory_store: redis`;
- `knowledge_namespace: notas_conflito_interesse`.

## 7. Modelo Gemini

O modelo padrao foi atualizado para:

```text
gemini-3.1-flash-lite
```

Arquivos e variaveis relacionados:

- `CORA/backend/src/agents/simple_research_agent.py`;
- `DEFAULT_GEMINI_MODEL`;
- `GEMINI_MODEL=gemini-3.1-flash-lite`;
- `CORA/.env.railway.example`;
- `CORA/.env.docker.example`;
- `CORA/docker-compose.yml`;
- scripts de processamento do corpus que usam Gemini como default.

Configuracao atual do agente:

- `temperature = 0.2`;
- `top_p = 0.7`;
- `top_k = 40`;
- `max_output_tokens = 8192`.
- `GEMINI_INPUT_TOKEN_BUDGET = 30000`, usado como referencia de telemetria e controle de custo.

Observacao: `max_output_tokens` limita a resposta gerada, nao a entrada de contexto enviada ao modelo.

## 8. Recuperacao RAG e nota tecnica especifica

Foi corrigido o comportamento de perguntas sobre nota tecnica especifica.

Exemplo de consulta-alvo:

```text
O que a Nota Tecnica no 188/2023/SENOR/COLEG analisou?
```

Comportamento esperado apos ajuste:

- detectar referencia explicita a nota tecnica;
- resolver a nota alvo antes de montar o contexto;
- buscar contexto com filtro Pinecone por `numero_nota_tecnica`;
- aplicar filtro defensivo local por `numero_nota_tecnica` e `arquivo_original`;
- nao aproveitar memoria Redis quando a pergunta identifica uma nota especifica;
- deduplicar referencias finais;
- responder apenas com referencias da nota solicitada.

Variaveis relevantes apos as medicoes de custo:

- `PINECONE_TOP_K=10` para perguntas amplas;
- `PINECONE_SPECIFIC_NOTE_LOOKUP_TOP_K=20`;
- `PINECONE_SPECIFIC_NOTE_CONTEXT_TOP_K=15`;
- `PINECONE_SPECIFIC_NOTE_MAX_CHUNKS=0`;
- `PINECONE_SIMILARITY_THRESHOLD=0.3`;
- `PINECONE_FINAL_RESULT_COUNT=10`.

Politica adotada:

- perguntas amplas permanecem conservadoras, com `top_k=10`;
- aumentos para `12` ou `15` devem ser testados caso a caso;
- nao foi adotado `top_k=50` para perguntas amplas, pois testes anteriores indicaram degradacao de qualidade e aumento desnecessario de tokens;
- perguntas sobre nota especifica usam fluxo proprio: a busca inicial usa `15` chunks e pode expandir ate o total informado pelo metadado da nota;
- `PINECONE_SPECIFIC_NOTE_MAX_CHUNKS=0` significa "sem teto fixo": o `top_k` passa a ser variavel e acompanha `total_chunks` da nota resolvida;
- valores positivos em `PINECONE_SPECIFIC_NOTE_MAX_CHUNKS` continuam servindo como limite operacional opcional;
- uma vez resolvida a nota exata por metadado, o corte por similaridade semantica deixa de ser aplicado aos chunks dessa nota, para evitar amputar trechos validos do documento.

Observacao tecnica:

- Pinecone aceitou filtro server-side por `numero_nota_tecnica`;
- filtro por `arquivo_original` nao deve ser presumido como server-side, pois depende de campo indexado para filtro;
- `arquivo_original` permanece como defesa local.
- a comparacao de identificador usa fronteira numerica, evitando que `2/2022/DINOR/COLEG` seja confundida com `102/2022/DINOR/COLEG`, `22/2022/DINOR/COLEG` ou equivalentes.

Validacao realizada:

- consulta sobre `188/2023/SENOR/COLEG`;
- retorno com `status = success`;
- `references_count = 1`;
- referencia unica correspondente a nota alvo.

Validacao adicional de maio de 2026:

- a Nota Tecnica `188/2023/SENOR/COLEG` possui `18` chunks;
- o fluxo novo iniciou com `15` chunks;
- o metadado `total_chunks=18` permitiu expandir para `18`;
- os chunks foram ordenados de `1` a `18` antes da montagem do contexto;
- prompt final medido: `10.195` tokens reais pelo contador do Gemini;
- resultado ficou dentro do orcamento operacional de `30.000` tokens.

## 9. Abertura do contexto recuperado do Pinecone

Foi identificado truncamento artificial do contexto antes do envio ao Gemini.

Comportamento anterior:

- `PINECONE_CONTEXT_EXCERPT_CHARS` tinha default `2200`;
- `_select_context_excerpt()` normalizava o texto e retornava apenas os primeiros 2200 caracteres;
- `_format_context()` montava o prompt final com esse trecho ja cortado;
- o Gemini recebia somente o excerto, nao o chunk completo retornado pelo Pinecone.

Mediacao tecnica realizada antes da correcao:

- pergunta ampla: 10 resultados, 6 truncados;
- pergunta sobre nota especifica: 12 resultados, 6 truncados;
- prompt final medido em uma consulta de amostra: 5.911 tokens;
- conclusao: o gargalo nao era a janela do Gemini, mas o corte aplicado pelo backend.

Correcao implementada:

- default de `PINECONE_CONTEXT_EXCERPT_CHARS` alterado para `0`;
- valor `0` ou negativo passa a significar "sem corte";
- valores positivos continuam funcionando como limite operacional opcional;
- exemplos de ambiente Docker e Railway atualizados para `PINECONE_CONTEXT_EXCERPT_CHARS=0`.

Arquivos alterados:

- `CORA/backend/src/agents/simple_research_agent.py`;
- `CORA/.env.docker.example`;
- `CORA/.env.railway.example`;
- `CORA/backend/tests/test_context_excerpt.py`.

Validacoes:

- `py_compile` do agente;
- teste unitario cobrindo `0` como contexto integral;
- teste unitario cobrindo limite positivo como comportamento ainda suportado;
- suite `pytest` relevante com `39 passed`;
- rebuild do Docker local;
- verificacao dentro do container confirmando default `0` e condicao `max_chars <= 0`.

## 9.1. Telemetria de recuperacao e custo

Foi adicionada telemetria de recuperacao no retorno interno do agente e nos logs.

Campos principais:

- modo de recuperacao (`pergunta_ampla` ou `nota_especifica`);
- quantidade de resultados enviados ao modelo;
- caracteres de contexto;
- caracteres do prompt;
- estimativa local de tokens;
- orcamento de entrada configurado;
- indicacao se o prompt esta dentro do orcamento;
- nota alvo, quando houver;
- chunks enviados;
- total de chunks da nota, quando informado pelo Pinecone;
- indicacao de completude da nota especifica.

Medicoes realizadas:

| Modo | Configuracao | Resultados/chunks | Tokens reais |
|---|---:|---:|---:|
| Pergunta ampla | `top_k=10` | `10` resultados | `6.192` |
| Pergunta ampla | `top_k=12` | `12` resultados | `7.442` |
| Pergunta ampla | `top_k=15` | `15` resultados | `9.028` |
| Nota especifica anterior | `top_k=12` | `12` chunks | `6.736` |
| Nota especifica medida | `top_k=15` | `15` chunks | `8.523` |
| Nota especifica nova | `15 -> 18` chunks | nota completa | `10.195` |

Conclusao tecnica:

- pergunta ampla deve permanecer em `top_k=10` por padrao;
- nota especifica pode usar expansao controlada porque o filtro restringe o contexto ao documento alvo;
- o custo da nota completa testada ficou aceitavel e abaixo do orcamento configurado;
- a solucao evita abertura indiscriminada de contexto em perguntas amplas;
- a validacao posterior com a Nota Tecnica `2/2022/DINOR/COLEG` confirmou recuperacao completa de `31` chunks quando a nota e resolvida por metadado.
- a validacao posterior com notas de `34` e `36` chunks confirmou que o Pinecone retornou todos os chunks quando `top_k=total_chunks`, filtro de nota ativo e threshold semantico desligado.

## 9.2. Ancoragem conversacional de nota tecnica

Foi implementada ancoragem conversacional para perguntas subsequentes sobre a mesma nota.

Problema observado:

- o usuario perguntou sobre a Nota Tecnica `21/2025/SENOR/COLEG`;
- a resposta usou uma unica nota como referencia;
- na pergunta seguinte, "E qual conclusao a nota chega?", o assistente saiu da nota ativa e executou busca ampla.

Comportamento corrigido:

- quando uma consulta sobre nota especifica e processada com sucesso, o backend registra a nota como `active_note_target` da conversa no Redis;
- perguntas seguintes sem nova nota explicita permanecem ancoradas nessa nota ativa;
- a ancoragem e descartada quando ha mudanca clara de escopo, como pedido por outras notas, comparacao, entendimento geral ou precedentes;
- se o usuario mencionar outra nota, a nova nota passa a ser resolvida normalmente;
- mensagens nao substantivas, como agradecimento simples, nao acionam recuperacao ancorada.

Validacao realizada:

- pergunta inicial: `O que diz especificamente a nota 21/2025/SENOR/COLEG -?`;
- pergunta seguinte: `E qual conclusao a nota chega?`;
- modo de recuperacao validado: `same_note_follow_up`;
- referencia retornada: apenas `21/2025/SENOR/COLEG | 5_2025_50600.004061.2025.11_e.md`;
- chunks enviados: `1` a `16`;
- completude: `true`.

## 10. Formatacao visual das respostas

Foi implementada melhoria visual das respostas do C.O.R.A. sem alterar a redacao da LLM.

Requisito funcional:

- a resposta da LLM deve ser preservada verbatim;
- o pos-processamento pode apenas reorganizar visualmente Markdown, quebras, listas, destaques e observacoes;
- nao pode resumir, reescrever, criar fatos, remover fundamentos ou mudar nuance juridica.

Arquivos relevantes:

- `CORA/pompt-desenvolvimento-formatacao.md`;
- `CORA/backend/prompts/research_agent_template.txt`;
- `CORA/backend/src/formatting/chat_formatter.py`;
- `CORA/backend/src/agents/simple_research_agent.py`;
- `CORA/backend/tests/test_chat_formatter.py`;
- `CORA/backend/tests/test_response_cleaning.py`;
- `CORA/frontend/src/components/Chat.jsx`;
- `CORA/frontend/src/components/Chat.css`.

Caracteristicas implementadas:

- orientacao ao modelo para gerar Markdown mais rico;
- preservacao de palavras, numeros, artigos, prazos, citacoes e referencias;
- feature flag `ENABLE_CHAT_FORMATTING`;
- formatador conservador no backend;
- suporte a listas, numeracao, sequencias, quotes, enfase e tabelas quando cabivel;
- renderer Markdown no frontend para exibir a resposta formatada;
- testes para garantir que listas numeradas nao sejam convertidas indevidamente em bullets;
- testes para preservar texto tecnico, citacoes, artigos, datas, percentuais e blocos de codigo.

## 11. Exportacao PDF com Markdown renderizado

Foi ajustado o PDF para deixar de exibir marcadores brutos de Markdown, como `###`, `**texto**` e `>`.

Arquivos relevantes:

- `CORA/backend/main.py`;
- `CORA/backend/tests/test_pdf_markdown_rendering.py`.

Suporte implementado no renderer HTML do PDF:

- titulos Markdown (`#`, `##`, `###`);
- negrito inline com `**texto**`;
- listas ordenadas;
- listas com letras `a)`, `b)`, `c)`;
- bullets;
- quotes com `>`;
- tabelas Markdown simples;
- estilos para corpo da resposta, listas, tabelas e citacoes.

Referencias no PDF:

- bloco visual proprio para "Referencias consultadas";
- exibicao do namespace utilizado;
- nome da fonte com estilo visual alinhado ao chat;
- relevancia apresentada ao lado;
- links renderizados quando disponiveis;
- fonte reduzida e sem negrito excessivo para melhorar encaixe em linha;
- marcadores/listas com cor alinhada a identidade visual.

Pendencia tecnica registrada:

- substituir futuramente o renderer Markdown simples por parser Markdown completo com sanitizacao por allowlist segura.

Registro relacionado:

- `CORA/docs/CORA_TODO.md`.

## 12. Docker local e otimizacao da imagem

Foi criada e validada infraestrutura Docker local para emular o ambiente Railway.

Arquivos relevantes:

- `CORA/Dockerfile`;
- `CORA/docker-compose.yml`;
- `CORA/.env.docker.example`;
- `CORA/scripts/docker-up.sh`;
- `CORA/scripts/docker-down.sh`;
- `CORA/scripts/docker-status.sh`;
- `CORA/README.md`.

Caracteristicas:

- build multi-stage com Node para React;
- runtime Python para FastAPI;
- frontend e backend servidos no mesmo container;
- healthcheck em `/api/health`;
- variaveis padrao coerentes com o C.O.R.A.;
- montagem local da service account Firebase como segredo read-only;
- exclusao de corpus, docs, scripts auxiliares e relatorios da imagem final;
- imagem local otimizada mantida como `cora-local:latest`.

Estado local validado:

- container: `cora_local`;
- app: `http://localhost:8081`;
- health: `http://127.0.0.1:8081/api/health`;
- namespace: `notas_conflito_interesse`;
- modelo: `gemini-3.1-flash-lite`;
- Firebase configurado;
- Redis configurado;
- Pinecone configurado.

## 13. Railway e ambiente de producao

O ambiente Railway foi conferido de forma read-only e validado apos a consolidacao das melhorias.

Dados operacionais identificados:

- projeto: `C.O.R.A.`;
- ambiente: `production`;
- servico: `C.O.R.A`;
- dominio publico: `https://cora-production-ac8a.up.railway.app/`;
- health: `https://cora-production-ac8a.up.railway.app/api/health`;
- `targetPort`: `8080`;
- `knowledge_namespace`: `notas_conflito_interesse`;
- `auth_provider`: `firebase`;
- `history_store`: `firestore`;
- `memory_store`: `redis`.

Regra operacional mantida:

- nenhuma acao destrutiva deve ser executada no Railway.

## 14. Skills e padroes reutilizaveis

Foram criadas ou instaladas skills globais para reaproveitar o conhecimento aplicado no C.O.R.A. em outros assistentes.

Skills relevantes:

- `markdown-chat-pdf`: padrao de respostas ricas em Markdown, preservacao verbatim e PDF coerente com chat;
- `agent-pr-flow`: fluxo seguro para propostas de alteracao em projetos de agentes e assistentes;
- `docker-development`: melhores praticas de Dockerizacao de projetos;
- `use-railway`: operacao e diagnostico de infraestrutura Railway.

O objetivo dessas skills e permitir reproducao das tecnicas aplicadas no C.O.R.A. em outros assistentes juridicos ou administrativos.

## 15. Validacoes executadas

Validacoes realizadas ao longo das entregas:

- scanner read-only do namespace Pinecone;
- checagem de quantidade de notas e vetores;
- testes de isolamento por usuario e conversa;
- teste de nota tecnica especifica;
- `py_compile` de arquivos Python alterados;
- testes `unittest`;
- suite `pytest` relevante com `26 passed`;
- rebuild Docker local;
- healthcheck local;
- inspecao do codigo embarcado no container;
- verificacao do health de producao;
- verificacao de logs de erro de runtime quando aplicavel.

Observacao sobre ambiente de teste:

- `pytest` foi instalado na `.venv` local do backend para viabilizar execucao direta da suite de regressao;
- segredos nao foram registrados na documentacao.

## 16. Estado atual em maio de 2026

O C.O.R.A. encontra-se funcional como assistente especializado em conflito de interesses, com:

- frontend React;
- backend FastAPI;
- Firebase Auth;
- Firestore para historico;
- Redis para memoria curta;
- Pinecone no namespace `notas_conflito_interesse`;
- Gemini `gemini-3.1-flash-lite`;
- Docker local integrado;
- ambiente Railway validado;
- respostas com Markdown mais rico;
- PDF renderizando Markdown em vez de exibir marcadores brutos;
- referencias visualmente ajustadas no PDF;
- busca por nota especifica isolada;
- contexto Pinecone enviado ao Gemini sem corte artificial de 2200 caracteres.

## 17. Pendencias e cuidados

Pendencias tecnicas recomendadas:

- publicar ou conferir regras definitivas do Firestore no projeto Firebase;
- garantir que variaveis reais do Railway estejam alinhadas com `.env.railway.example`, especialmente `PINECONE_CONTEXT_EXCERPT_CHARS=0`;
- substituir o renderer Markdown simples do PDF por parser completo com sanitizacao segura;
- ampliar testes de perguntas amplas e perguntas por nota especifica;
- monitorar custo e latencia apos abertura do contexto integral dos chunks recuperados;
- manter corpus e segredos fora da imagem Docker e do versionamento;
- registrar novas melhorias nas skills globais correspondentes.

Checklist tecnico antes de novas entregas:

- confirmar `PINECONE_NAMESPACE=notas_conflito_interesse`;
- confirmar `GEMINI_MODEL=gemini-3.1-flash-lite`;
- confirmar Firebase Auth e Firestore;
- confirmar Redis com prefixo `cora:session`;
- rodar testes de formatacao e PDF;
- rodar teste de contexto Pinecone sem truncamento;
- validar Docker local;
- validar health de producao quando houver nova publicacao.
