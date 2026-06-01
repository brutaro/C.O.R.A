# PRD - C.O.R.A. com Firebase

## 1. Resumo Executivo

Este documento define o produto, o fluxo funcional e os requisitos do `C.O.R.A.` - `Conflito de Interesses: Orientacao, Registro e Analise`.

O C.O.R.A. sera um assistente tematico separado da L.A.R.A. em codigo, frontend, backend, branding, historico e configuracao operacional. A base tecnica inicial sera uma copia controlada do assistente anterior, ajustada para as necessidades do novo produto.

Decisoes centrais desta fase:

- frontend proprio em `CORA/frontend`;
- backend proprio em `CORA/backend`;
- copia derivada da L.A.R.A., sem compartilhamento operacional de scripts;
- consultas exclusivas ao namespace Pinecone `notas_conflito_interesse`;
- historico proprio no Firebase;
- mesma estetica estrutural do frontend da L.A.R.A., com identidade visual propria;
- sem plataforma de observabilidade dedicada nesta etapa;
- nada sera preparado para GitHub nesta fase.

## 2. Contexto

Hoje, a L.A.R.A. ja possui um produto funcional, com frontend, backend, corpus vetorial e fluxos operacionais proprios.

O novo produto de conflito de interesses nao deve nascer como extensao do assistente anterior. Ele deve nascer como um assistente novo, ainda que derivado dele, para permitir:

- evolucao independente;
- deploy independente no futuro;
- repositorio futuro previsto em `https://github.com/brutaro/C.O.R.A.` sem acoplamento ao codigo da L.A.R.A.;
- configuracao propria;
- autenticacao e historico proprios;
- manutencao isolada;
- menor risco de acoplamento operacional.

## 3. Problema

O corpus de conflito de interesses ja foi ingerido em `notas_conflito_interesse`, mas ainda nao existe um assistente proprio para esse dominio.

Se o novo produto compartilhar backend e scripts com a L.A.R.A., surgem riscos operacionais:

- regressao no assistente atual;
- acoplamento de configuracoes;
- dificuldade de manutencao separada;
- maior risco de mistura entre regras de negocio;
- barreira para futura extracao em repositorio proprio.

## 4. Objetivo do Produto

Disponibilizar o C.O.R.A. como assistente especializado em conflito de interesses para que o usuario possa:

- entrar com conta Google;
- iniciar, retomar e consultar historico proprio;
- fazer perguntas apenas sobre conflito de interesses;
- receber respostas baseadas exclusivamente no namespace `notas_conflito_interesse`;
- usar uma interface familiar a da L.A.R.A., mas com identidade propria;
- operar sobre uma base de codigo propria, sem compartilhar scripts com o assistente anterior.

## 5. Metas

### 5.1 Metas de produto

- criar um assistente tematico reutilizavel;
- separar experiencia, corpus e historico da L.A.R.A.;
- permitir evolucao independente do produto.

### 5.2 Metas tecnicas

- copiar a base do assistente anterior para uma estrutura nova;
- ajustar a copia para o dominio de conflito de interesses;
- manter namespace fixo `notas_conflito_interesse`;
- persistir historico no Firebase;
- evitar qualquer dependencia operacional de scripts da L.A.R.A.

## 6. Nao Objetivos

Esta fase nao contempla:

- compartilhamento de backend entre C.O.R.A. e L.A.R.A.;
- migracao de conversas antigas da L.A.R.A.;
- plataforma de observabilidade dedicada;
- deploy em GitHub;
- multiassistente dinamico com namespace livre definido pelo cliente;
- analytics avancado de produto;
- unificacao de login entre os dois assistentes.

## 7. Decisoes de Produto

1. O nome publico do novo assistente sera `C.O.R.A.`.
2. `C.O.R.A.` significa `Conflito de Interesses: Orientacao, Registro e Analise`.
3. O produto tera pasta propria `CORA/`.
4. O frontend sera uma copia ajustada do frontend da L.A.R.A.
5. O backend sera uma copia ajustada do backend da L.A.R.A.
6. O C.O.R.A. nao compartilhara scripts operacionais com a L.A.R.A.
7. O C.O.R.A. consultara apenas o namespace `notas_conflito_interesse`.
8. O cliente nao podera escolher namespace manualmente.
9. O historico do C.O.R.A. nao sera salvo no Supabase da L.A.R.A.
10. A primeira versao funcional do C.O.R.A. usara Firebase Auth + Firestore, sem etapa transitoria em Supabase.
11. Nada sera preparado para GitHub nesta etapa.

## 8. Estrutura do Produto

Estrutura local esperada:

- `CORA/frontend`
- `CORA/backend`
- `CORA/README.md`

Diretriz estrutural:

- tudo deve partir de copia da L.A.R.A.;
- a copia deve ser ajustada para o novo produto;
- a partir desta fase, o C.O.R.A. passa a ser tratado como base independente.

## 9. Escopo do MVP

O MVP deve entregar:

- uma aplicacao de chat separada da L.A.R.A. no frontend;
- um backend separado da L.A.R.A. no codigo e na operacao;
- login com Google via Firebase Auth;
- sessao persistida no navegador;
- criacao de perfil do usuario no Firebase;
- lista de conversas do usuario autenticado;
- criacao de nova conversa;
- envio de pergunta ao backend proprio do C.O.R.A.;
- resolucao RAG com namespace fixo `notas_conflito_interesse`;
- memoria contextual com Redis;
- salvamento de mensagens e historico no Firebase;
- retomada de conversas anteriores;
- exportacao da resposta e da conversa em PDF;
- logout;
- mensagens de erro claras;
- identidade visual propria do C.O.R.A. sobre a mesma base estetica da L.A.R.A.

## 10. Arquitetura Alvo

### 10.1 Componentes

- frontend do C.O.R.A.;
- backend do C.O.R.A.;
- Firebase Auth;
- Firestore;
- Pinecone;
- Redis de memoria conversacional;
- mecanismo de exportacao de PDF.

### 10.2 Responsabilidades

**Frontend**

- autenticar usuario;
- obter token Firebase;
- carregar e persistir conversas no Firebase;
- enviar perguntas ao backend do C.O.R.A.;
- exibir respostas e referencias;
- aplicar identidade visual propria.

**Backend**

- validar o token exigido para o fluxo do C.O.R.A.;
- processar perguntas do C.O.R.A.;
- consultar apenas `notas_conflito_interesse`;
- manter memoria contextual com Redis;
- manter a funcionalidade de exportacao em PDF;
- devolver resposta, fontes e metadados;
- manter configuracao propria do produto.

**Firebase Auth**

- login com Google;
- manutencao de sessao;
- emissao de ID token.

**Firestore**

- armazenar perfil do usuario;
- armazenar conversas e mensagens;
- listar historico por usuario autenticado.

**Pinecone**

- armazenar e recuperar chunks exclusivamente do corpus de conflito de interesses em `notas_conflito_interesse`.

## 11. Fluxo End-to-End

### 11.1 Login

1. Usuario acessa o C.O.R.A.
2. A interface exibe login Google.
3. O usuario autentica via Firebase.
4. O frontend recebe sessao e token.
5. O frontend cria ou atualiza o perfil no Firebase.
6. O frontend carrega a lista de conversas do usuario.

### 11.2 Nova conversa

1. Usuario clica em nova conversa.
2. O frontend cria o documento de conversa no Firebase.
3. O documento recebe titulo inicial.
4. O titulo pode ser atualizado com base na primeira pergunta.

### 11.3 Envio de pergunta

1. O frontend salva a mensagem do usuario.
2. O frontend obtem o token de autenticacao.
3. O frontend chama o backend proprio do C.O.R.A.
4. O backend resolve internamente o namespace `notas_conflito_interesse`.
5. O backend executa busca vetorial e gera resposta.
6. O frontend salva a resposta e atualiza a tela.

### 11.4 Retomada

1. Usuario abre conversa anterior.
2. O frontend consulta mensagens no Firebase.
3. A interface renderiza o historico completo.
4. Nova pergunta segue no mesmo contexto de conversa.

## 12. Requisitos Funcionais

### RF-01. Produto separado

O C.O.R.A. deve existir como produto separado da L.A.R.A. em frontend, backend, branding, historico e configuracao.

### RF-02. Copia isolada

O C.O.R.A. deve nascer como copia ajustada da L.A.R.A., mas passar a ser mantido como base propria.

### RF-03. Namespace fixo

Toda consulta do C.O.R.A. deve ser resolvida apenas no namespace `notas_conflito_interesse`.

### RF-04. Resolucao server-side

O cliente nao pode escolher livremente o namespace. O backend do C.O.R.A. deve resolver isso internamente.

### RF-05. Login Google

O sistema deve permitir autenticacao via Google com Firebase Auth.

### RF-06. Historico proprio

O sistema deve manter historico proprio do C.O.R.A. no Firebase, sem uso das tabelas de conversa da L.A.R.A.

### RF-07. Retomada de conversa

O sistema deve permitir abrir conversas anteriores e continuar o dialogo.

### RF-08. Identidade visual

O frontend do C.O.R.A. deve manter a mesma estrutura, layout e comportamento visual da L.A.R.A., alterando apenas elementos de marca e paleta.

### RF-09. Memoria contextual

O C.O.R.A. deve utilizar Redis como memoria contextual de conversa.

### RF-10. Exportacao em PDF

O C.O.R.A. deve manter a funcionalidade de exportacao da resposta e da conversa em PDF.

## 13. Requisitos Nao Funcionais

### RNF-01. Seguranca

- somente usuarios autenticados podem acessar historico e API protegida;
- regras de acesso devem isolar dados por usuario;
- o backend nao pode aceitar roteamento arbitrario para outros namespaces.

### RNF-02. Isolamento de corpus

- o C.O.R.A. nao pode consultar `notas_tecnicas_senor`;
- o C.O.R.A. nao pode consultar `__default__`;
- o C.O.R.A. deve operar apenas sobre `notas_conflito_interesse`.

### RNF-03. Isolamento de codigo

- o C.O.R.A. nao deve compartilhar scripts operacionais com a L.A.R.A.;
- alteracoes futuras no C.O.R.A. nao devem depender de editar a pasta da L.A.R.A.

### RNF-04. Compatibilidade visual

- a experiencia deve ser imediatamente reconhecivel para usuarios da L.A.R.A.;
- mudancas de identidade nao devem alterar usabilidade nem responsividade.

### RNF-05. Operacao

- nesta fase nao havera plataforma de observabilidade dedicada;
- logs operacionais basicos sao suficientes para suporte inicial.

## 14. Identidade Visual

Paleta sugerida para o C.O.R.A., mantendo a estetica do L.A.R.A. com uma identidade ligada a integridade, controle e conformidade:

- primaria: `#0f766e`
- hover primaria: `#0b5f5a`
- profunda: `#094b47`
- alerta/compliance: `#d97706`

Diretrizes:

- manter fundos, espacamento, grid e composicao da L.A.R.A.;
- aplicar a nova paleta em botoes, estados ativos, links e destaques;
- manter alto contraste nos modos claro e escuro.

## 15. Dados Minimos no Firebase

### 15.1 Colecoes sugeridas

- `users/{uid}`
- `users/{uid}/conversations/{conversation_id}`
- `users/{uid}/conversations/{conversation_id}/messages/{message_id}`

### 15.2 Campos minimos de conversa

- `conversation_id`
- `title`
- `assistant_slug`
- `assistant_name`
- `knowledge_namespace`
- `created_at`
- `updated_at`
- `status`

Valores esperados:

- `assistant_slug = "cora"`
- `assistant_name = "C.O.R.A."`
- `knowledge_namespace = "notas_conflito_interesse"`

## 16. Backend do C.O.R.A.

O backend do C.O.R.A. deve ser uma copia derivada do backend da L.A.R.A., ajustada para o novo produto.

Requisitos obrigatorios:

- manter codigo proprio em `CORA/backend`;
- consultar apenas `notas_conflito_interesse`;
- ter configuracao propria;
- manter Redis como memoria contextual;
- manter suporte a exportacao em PDF;
- permitir evolucao futura sem editar a base da L.A.R.A.

## 17. Riscos

### 17.1 Derivacao incompleta

Se a copia do backend ou do frontend for parcial demais, o produto pode continuar dependente da estrutura anterior de forma invisivel.

### 17.2 Corpus restrito

Perguntas mais amplas poderao ter cobertura insuficiente. Isso e esperado pelo posicionamento tematico do produto.

### 17.3 Escopo de autenticacao

O clone funcional do C.O.R.A. deve usar Firebase Auth + Firestore para autenticacao Google e historico de conversas. A recuperacao de conhecimento permanece exclusiva no Pinecone, via namespace `notas_conflito_interesse`, e nao depende do Firebase para gerar respostas.

As consultas semanticas do C.O.R.A. devem usar a busca textual nativa do Pinecone no indice integrado, sem dependencia de modelo externo de embedding em tempo de consulta. O modelo `text-embedding-004` nao deve ser usado neste assistente.

## 18. Dependencias

- namespace `notas_conflito_interesse` existente e populado;
- base atual da L.A.R.A. disponivel para copia inicial;
- projeto Firebase configurado;
- Google Sign-In habilitado;
- Firestore habilitado;
- Redis disponivel para memoria contextual;
- pasta local dedicada `CORA/`.

## 19. Plano de Entrega

### Fase 0. Preparacao

- consolidar PRD;
- manter pasta `CORA/`;
- criar `CORA/backend` como copia inicial;
- ajustar identidade visual do clone do frontend;
- registrar namespace fixo do produto;
- nao preparar nada para GitHub.

### Fase 1. Derivacao estrutural

- copiar frontend da L.A.R.A. para o C.O.R.A.;
- copiar backend da L.A.R.A. para o C.O.R.A.;
- remover acoplamentos diretos com a base anterior;
- ajustar naming e configuracoes do novo produto.

### Fase 2. Frente funcional

- integrar Firebase Auth;
- persistir historico no Firebase;
- adaptar o backend do C.O.R.A. ao namespace `notas_conflito_interesse`;
- manter Redis como memoria contextual;
- manter exportacao em PDF no backend e no frontend.

### Fase 3. Validacao

- testar autenticacao;
- testar persistencia de conversa;
- validar consulta exclusiva em `notas_conflito_interesse`;
- validar independencia operacional em relacao a L.A.R.A.

## 20. Criterios de Aceite

1. Existe uma pasta local dedicada `CORA/`.
2. Existe um frontend proprio em `CORA/frontend`.
3. Existe um backend proprio em `CORA/backend`.
4. O produto e identificado publicamente como `C.O.R.A.`.
5. O frontend do C.O.R.A. preserva a mesma estrutura visual da L.A.R.A.
6. O branding visual do C.O.R.A. e proprio.
7. O backend do C.O.R.A. resolve consultas apenas em `notas_conflito_interesse`.
8. O C.O.R.A. nao toca `notas_tecnicas_senor`.
9. O historico do C.O.R.A. nao usa as tabelas de conversa da L.A.R.A.
10. O C.O.R.A. utiliza Redis como memoria contextual.
11. O C.O.R.A. mantem a exportacao em PDF.
12. Nao ha plataforma de observabilidade dedicada nesta fase.

## 21. Decisoes Pendentes

- dominio ou subdominio do produto;
- politica de retencao de historico;
