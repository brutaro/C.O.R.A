# Relatorio gerencial para PGD - C.O.R.A.

Periodo de referencia: maio de 2026

## 1. Identificacao da demanda

A demanda consistiu na estruturacao e evolucao do C.O.R.A., assistente de inteligencia artificial voltado a consultas sobre conflito de interesses no servico publico federal, com base em notas tecnicas especializadas no tema.

O trabalho buscou transformar uma frente inicialmente derivada de outro assistente juridico em produto proprio, com ambiente, base de conhecimento, autenticacao, historico, memoria, formato de resposta e exportacao documental adequados ao seu escopo.

## 2. Objetivo do trabalho realizado

O objetivo foi preparar o C.O.R.A. para uso com maior seguranca, previsibilidade e qualidade de resposta.

Foram priorizados:

- organizacao do produto em area propria;
- separacao tecnica em relacao a outros assistentes;
- uso exclusivo da base de conhecimento de conflito de interesses;
- validacao da quantidade de documentos disponiveis;
- execucao local integrada em Docker;
- melhoria do isolamento entre conversas;
- melhoria da precisao em perguntas sobre notas especificas;
- melhoria visual das respostas no chat;
- melhoria da exportacao de respostas em PDF;
- ampliacao do contexto enviado ao modelo de linguagem;
- documentacao das entregas para continuidade do projeto.

## 3. Principais entregas realizadas

Foi consolidada uma estrutura propria para o C.O.R.A. dentro do projeto, reunindo backend, frontend, documentacao, corpus, scripts e configuracoes operacionais. Essa organizacao facilita manutencao, auditoria, continuidade evolutiva e eventual extracao futura do produto.

Foi preservada a regra de uso exclusivo do namespace `notas_conflito_interesse` na base vetorial. Essa separacao reduz o risco de mistura entre documentos de conflito de interesses e bases documentais de outros assistentes.

Foi realizada verificacao da base de conhecimento no Pinecone. O levantamento identificou `131` notas/documentos distintos e `2367` vetores no namespace do C.O.R.A.

O C.O.R.A. foi estruturado para usar Firebase Auth como mecanismo de login e Firestore como base de historico de conversas. A memoria contextual curta foi mantida em Redis, com separacao por usuario e conversa.

Foi criado ambiente local integrado em Docker, permitindo executar frontend e backend em conjunto de forma semelhante ao ambiente de producao. Isso reduz divergencias entre validacao local e operacao em nuvem.

O modelo de linguagem padrao foi atualizado para `gemini-3.1-flash-lite`, mantendo a configuracao coerente nos ambientes local e de producao.

Foi revisado o isolamento entre historicos de conversa. O sistema passou a validar a conversa do usuario e a separar a memoria contextual por usuario e por conversa, reduzindo o risco de uma conversa herdar informacoes de outra.

Foi corrigido o comportamento de perguntas sobre notas tecnicas especificas. Quando o usuario pergunta sobre uma nota determinada, como `188/2023/SENOR/COLEG`, o sistema passa a buscar e responder com base na nota solicitada, evitando mistura com notas semelhantes.

Foi implementada melhoria visual das respostas. As respostas passaram a usar Markdown de forma mais rica, com titulos, listas, numeracoes, destaques, tabelas quando cabiveis e blocos de observacao, preservando a redacao da resposta gerada pelo modelo.

Foi ajustada a exportacao em PDF para interpretar a formatacao Markdown, evitando que o documento exportado mostre marcadores brutos como `###`, `**texto**` ou `>`. O PDF passou tambem a exibir referencias de forma mais organizada, com melhor legibilidade e alinhamento visual.

Foi removido o corte artificial de contexto aplicado aos trechos recuperados do Pinecone. Antes, cada trecho enviado ao modelo podia ser limitado a 2200 caracteres. A configuracao atual permite enviar o conteudo integral dos chunks recuperados, aproveitando melhor a janela de contexto do Gemini.

Tambem foi aperfeicoada a estrategia de recuperacao para equilibrar qualidade e custo. As perguntas amplas permanecem com recuperacao conservadora, evitando excesso de documentos e tokens. Para perguntas sobre uma nota tecnica especifica, o sistema passou a usar `top_k` variavel: identifica a nota, verifica a quantidade de chunks informada pelos metadados e envia a nota completa para o modelo quando a consulta esta restrita a esse documento.

Foi adicionada ancoragem conversacional de nota tecnica. Com isso, quando o usuario pergunta primeiro sobre uma nota especifica e, em seguida, faz nova pergunta sobre "a nota", "a conclusao" ou outro aspecto do mesmo documento, o assistente continua usando a nota ativa da conversa, sem retornar automaticamente para uma busca ampla.

Tambem foram registradas orientacoes tecnicas reutilizaveis em skills globais, para que os padroes de formatacao, PDF, Dockerizacao, Railway e fluxo de evolucao de assistentes possam ser reaplicados em outros projetos.

## 4. Resultados obtidos

Ao final desta etapa de maio de 2026, o C.O.R.A. encontra-se funcional e validado em ambiente local integrado.

Foram confirmados:

- assistente disponivel;
- namespace correto: `notas_conflito_interesse`;
- autenticacao baseada em Firebase;
- historico baseado em Firestore;
- memoria contextual baseada em Redis;
- modelo Gemini configurado;
- ambiente local em Docker;
- ambiente de producao conferido;
- exportacao em PDF funcional;
- respostas formatadas no chat;
- referencias exibidas de forma mais clara;
- contexto Pinecone enviado ao modelo sem corte artificial de 2200 caracteres.
- recuperacao de nota especifica com expansao controlada e medicao de tokens.
- continuidade conversacional em torno da nota tecnica ativa.

Tambem foi validado que consulta sobre nota tecnica especifica retorna referencia correspondente a nota solicitada, sem ampliar indevidamente a resposta para outras notas similares.

## 5. Beneficios para a area

As entregas realizadas aumentam a confiabilidade do assistente e reduzem riscos de erro em uso real.

Os principais beneficios sao:

- maior organizacao do produto;
- reducao de risco de mistura entre bases documentais;
- reducao de risco de vazamento de contexto entre conversas;
- maior precisao em consultas sobre notas especificas;
- respostas mais legiveis para o usuario final;
- PDFs mais adequados para compartilhamento e registro;
- melhor aproveitamento da capacidade do modelo de linguagem;
- ambiente local mais parecido com producao;
- maior previsibilidade para evolucoes futuras;
- melhor rastreabilidade tecnica e gerencial.

## 6. Controles e cuidados adotados

Durante o trabalho foram observados cuidados para garantir qualidade, seguranca e aderencia ao escopo da solucao:

- preservacao do namespace `notas_conflito_interesse`;
- separacao entre C.O.R.A. e outros assistentes;
- manutencao de informacoes sensiveis fora da documentacao gerencial;
- uso de Firebase e Firestore como bases de autenticacao e historico;
- separacao da memoria contextual por usuario e conversa;
- validacao de comportamento para nota tecnica especifica;
- manutencao do corpus fora da imagem Docker final;
- validacao do funcionamento em ambiente local integrado;
- registro de pendencias tecnicas para acompanhamento posterior.

## 7. Validacoes executadas

Foram executadas validacoes tecnicas e funcionais para confirmar as entregas:

- conferencia da quantidade de documentos e vetores no namespace do C.O.R.A.;
- checagem de funcionamento do assistente local;
- consulta ao indicador de saude da aplicacao;
- verificacao de configuracao de Firebase, Firestore, Redis, Pinecone e Gemini;
- teste de isolamento entre conversas;
- teste de busca por nota tecnica especifica;
- testes automatizados de formatacao das respostas;
- testes automatizados de renderizacao Markdown no PDF;
- teste automatizado para garantir que o contexto do Pinecone nao seja truncado quando configurado como aberto;
- testes automatizados sobre limite de resultados, ordenacao de chunks e completude da nota especifica;
- testes automatizados sobre manutencao e troca de escopo da nota ativa;
- medicoes de tokens para perguntas amplas e para nota tecnica especifica;
- reconstrucao e reinicializacao do ambiente Docker local.

A suite de testes relevante executada nesta etapa resultou em `31` testes aprovados.

Nas medicoes realizadas, a pergunta ampla padrao permaneceu em aproximadamente `6.192` tokens reais. A consulta sobre a Nota Tecnica `188/2023/SENOR/COLEG` passou a enviar os `18` chunks da nota, em ordem, com aproximadamente `10.195` tokens reais, abaixo do orcamento operacional de `30.000` tokens.

Tambem foi validado que uma pergunta subsequente sobre a Nota Tecnica `21/2025/SENOR/COLEG` permaneceu ancorada na mesma nota, com uma unica referencia e envio dos `16` chunks do documento.

## 8. Estado atual da entrega

Em maio de 2026, o C.O.R.A. esta em estado funcional para continuidade de uso, validacao e evolucao.

O ambiente atual utiliza:

- Firebase para autenticacao;
- Firestore para historico;
- Redis para memoria curta;
- Pinecone no namespace `notas_conflito_interesse`;
- Gemini `gemini-3.1-flash-lite`;
- Docker local integrado;
- exportacao em PDF com Markdown renderizado;
- respostas visualmente formatadas no chat;
- contexto recuperado do Pinecone sem corte artificial de 2200 caracteres.
- estrategia de recuperacao que evita `top_k` excessivo em perguntas amplas e amplia apenas a nota especifica quando necessario.

## 9. Proximas etapas recomendadas

Como proximas etapas, recomenda-se:

- acompanhar respostas em uso real para identificar ajustes de prompt e recuperacao;
- ampliar testes com diferentes notas tecnicas e perguntas amplas;
- substituir futuramente o renderizador simples de Markdown do PDF por parser completo com sanitizacao segura;
- monitorar custo e latencia com o contexto mais aberto;
- acompanhar custo e latencia do modo de contexto completo para nota especifica, no qual o sistema usa todos os chunks informados pelo metadado da nota;
- conferir periodicamente o alinhamento das variaveis de ambiente;
- manter atualizadas as documentacoes tecnica e gerencial;
- reaplicar as skills globais criadas em outros assistentes quando pertinente.

## 10. Conclusao

As entregas de maio de 2026 estruturaram o C.O.R.A. como assistente especializado mais seguro, organizado e adequado ao uso sobre notas tecnicas de conflito de interesses.

O produto passou a contar com separacao clara de base documental, autenticacao Firebase, historico Firestore, memoria Redis escopada por conversa, execucao local integrada em Docker, modelo Gemini atualizado, busca mais precisa por nota especifica, respostas visualmente melhores, PDF mais fiel ao chat e contexto Pinecone sem truncamento artificial.

Essas entregas fortalecem a continuidade do desenvolvimento e aumentam a confiabilidade do assistente para uso e evolucao futura.
