# CORA - Plano de nomenclatura, batimento e rastreabilidade

Data de criacao: 2026-05-05

## 1. Objetivo

Estabelecer um processo documentado, auditavel e replicavel para:

1. Inventariar os documentos oficiais de conflito de interesses.
2. Verificar se os documentos ja ingeridos/processados estao contidos no universo oficial.
3. Definir um padrao canonico de nomenclatura para todos os formatos do mesmo documento.
4. Renomear PDFs, Markdown e TXT de forma consistente, somente apos validacao.
5. Gerar uma trilha permanente de rastreabilidade para expansao futura do acervo.

Este plano nao autoriza renomeacao nem ingestao por si so. Ele define a governanca
para que essas acoes sejam feitas em etapas posteriores.

## 2. Contexto conhecido

- Assistente: CORA.
- Dominio: conflito de interesses.
- Pinecone index: `agentes-juridicos`.
- Pinecone namespace: `notas_conflito_interesse`.
- Pasta oficial do corpus: `corpus/NOTAS-CONFLITO-INTERESSE`.
- Processados locais conhecidos:
  - `corpus/processed_conflito_interesse`
  - `corpus/processed_conflito_interesse_incremental_20260320`
- Conversoes locais conhecidas:
  - `corpus/NOTAS-CONFLITO-INTERESSE/markdown`
  - `corpus/NOTAS-CONFLITO-INTERESSE/txt`
  - `corpus/input_conflito_incremental_20260320`

## 3. Principio central

A unidade de controle nao deve ser o arquivo fisico. A unidade de controle deve
ser o documento logico.

Um documento logico pode ter varias variantes de formato:

- `.pdf`
- `.md`
- `.txt`
- artefato processado `.json`
- registro vetorial no Pinecone

Todas as variantes do mesmo documento logico devem compartilhar o mesmo
`base_name`, mudando apenas a extensao.

Exemplo:

```text
14_2021_50600.015980.2018.91_e.pdf
14_2021_50600.015980.2018.91_e.md
14_2021_50600.015980.2018.91_e.txt
```

## 4. Padrao canonico para Nota Tecnica

O padrao ja relembrado e adotado para Nota Tecnica e:

```text
{sequencial_no_ano}_{ano_documento}_{processo_com_pontos}_e.{ext}
```

Exemplo:

```text
14_2021_50600.015980.2018.91_e.md
```

Regras:

- `sequencial_no_ano`: numero sequencial do corpus naquele ano, nao o numero
  interno da nota.
- `ano_documento`: ano do documento principal, preferencialmente extraido do
  numero da nota/documento; se ausente, usar data de assinatura; se ainda
  ausente, usar pasta/ano como fallback documentado.
- `processo_com_pontos`: numero do processo com `/` e `-` convertidos para `.`.
- `e`: sufixo legado preservado para as Notas Tecnicas ja padronizadas.
- `ext`: extensao real do arquivo, por exemplo `pdf`, `md` ou `txt`.

## 5. Documentos que nao sao Nota Tecnica

Todos os documentos tambem precisam ser renomeados. Entretanto, documentos que
nao sao Nota Tecnica precisam de um sufixo proprio, para evitar que o padrao
oculte o tipo documental.

### 5.1 Proposta de padrao geral

```text
{sequencial_no_ano}_{ano_documento}_{processo_com_pontos}_{tipo}.{ext}
```

### 5.2 Proposta de codigos de tipo

| Tipo documental | Codigo proposto | Exemplo |
| --- | --- | --- |
| Nota Tecnica | `e` | `14_2021_50600.015980.2018.91_e.pdf` |
| Oficio | `of` | `26_2022_50600.045817.2022.30_of.pdf` |
| Despacho | `desp` | `27_2022_00096.013072.2022.19_desp.pdf` |
| Parecer | `par` | `31_2024_00000.000000.2024.00_par.pdf` |

### 5.3 Decisao adotada

Foi adotada a regra de manter `e` para Nota Tecnica, por compatibilidade com o
acervo ja processado, e usar codigos explicitos para os demais tipos:
`of`, `desp`, `par`.

Nao havera codigo generico para documento indefinido. Todo documento deve ter
tipo documental definido antes de receber nome canonico. Quando houver duvida,
o processo deve parar naquele item e solicitar decisao manual.

## 6. Sequencial no ano

O sequencial deve ser unico por ano dentro do corpus canonico, e nao separado
por tipo documental.

Motivo: o acervo existente ja usa sequenciais anuais globais, nao sequenciais
por tipo.

Exemplo:

```text
25_2022_..._e.pdf
26_2022_..._of.pdf
27_2022_..._desp.pdf
```

Regras:

1. Preservar sequenciais ja existentes em artefatos processados.
2. Para documentos novos, usar o proximo numero livre do mesmo ano.
3. Em caso de duplicidade oficial, o sequencial so deve ser atribuido depois
   de escolher qual arquivo representa o documento logico.
4. O sequencial nunca deve ser inferido do numero interno da nota, oficio ou
   despacho.

## 7. Batimento Pinecone versus universo oficial

Antes de qualquer renomeacao definitiva, precisamos responder:

> Tudo que esta no Pinecone/processed esta contido no universo oficial
> `corpus/NOTAS-CONFLITO-INTERESSE`?

### 7.1 Universo oficial

O universo oficial e composto por todos os documentos sob:

```text
corpus/NOTAS-CONFLITO-INTERESSE
```

Inclui:

- PDFs oficiais.
- Markdown convertido.
- TXT convertido.

Exclui:

- Artefatos processados.
- Relatorios temporarios.
- Backups fora da pasta oficial.

### 7.2 Fontes para o universo Pinecone

Ordem de preferencia:

1. Consulta real ao Pinecone no namespace `notas_conflito_interesse`.
2. Relatorios de upsert existentes.
3. Artefatos locais `corpus/processed_conflito_interesse*`.

Se a consulta real ao Pinecone nao estiver disponivel, o relatorio deve declarar
que a verificacao foi feita por artefatos locais e nao por leitura direta do
indice remoto.

### 7.3 Chaves de batimento

As chaves devem ser avaliadas em camadas:

1. `fonte_sei` ou codigo verificador principal.
2. Processo + numero interno do documento.
3. Nome canonico ja existente.
4. Hash normalizado do texto.
5. Similaridade textual, somente como evidencia auxiliar e nunca como unica
   prova de identidade.

Nao usar SEI meramente citado no corpo do texto como prova suficiente de match.

### 7.4 Classificacoes esperadas

| Status | Significado | Acao |
| --- | --- | --- |
| `contained` | Documento Pinecone encontrado no universo oficial | OK |
| `official_missing_from_pinecone` | Documento oficial ainda nao ingerido/processado | Candidato a ingestao futura |
| `pinecone_orphan` | Documento no Pinecone nao encontrado no universo oficial | Revisao obrigatoria |
| `ambiguous_match` | Mais de um candidato oficial para o mesmo Pinecone | Decisao manual |
| `metadata_incomplete` | Falta processo, ano, tipo ou identificador | Revisao manual obrigatoria |
| `document_type_undefined` | Tipo documental nao definido com seguranca | Perguntar antes de prosseguir |

## 8. Plano de inventario por documento logico

Cada documento logico deve receber um identificador interno estavel:

```text
logical_doc_id
```

Proposta:

```text
doc_{ano_documento}_{processo_com_pontos}_{tipo}_{hash_curto}
```

Esse ID nao precisa aparecer no nome do arquivo. Ele existe para rastreabilidade.

### Campos minimos do inventario

- `logical_doc_id`
- `tipo_documental`
- `ano_documento`
- `numero_processo`
- `processo_com_pontos`
- `numero_documento_interno`
- `fonte_sei`
- `codigo_verificador`
- `titulo_original`
- `pasta_origem`
- `pdf_path_original`
- `md_path_original`
- `txt_path_original`
- `processed_json_path`
- `pinecone_index`
- `pinecone_namespace`
- `pinecone_document_id`
- `match_method`
- `match_confidence`
- `status_contencao`

## 9. Plano de renomeacao

O plano de renomeacao deve ser gerado antes de qualquer alteracao em disco.

### 9.1 Campos minimos do plano

- `logical_doc_id`
- `tipo_documental`
- `old_pdf_path`
- `new_pdf_path`
- `old_md_path`
- `new_md_path`
- `old_txt_path`
- `new_txt_path`
- `old_processed_json_path`
- `new_processed_json_path`, se aplicavel
- `old_base_name`
- `new_base_name`
- `source_sha256_pdf`
- `source_sha256_md`
- `source_sha256_txt`
- `target_exists`
- `collision_status`
- `approved_for_apply`
- `blockers`
- `warnings`

### 9.2 Regras de aplicacao

1. Nunca renomear se o destino ja existir.
2. Nunca renomear apenas uma extensao quando existem outras variantes do mesmo
   documento sem plano equivalente.
3. Nunca sobrescrever arquivo.
4. Nunca alterar documento processado ou ingerido sem registrar a relacao entre
   nome antigo e novo.
5. Sempre gravar manifesto de undo antes ou durante a aplicacao.
6. Aplicacao real deve exigir confirmacao explicita por digest do plano.

## 10. Documento de rastreabilidade

Depois da definicao e aprovacao do plano, deve ser gerado um documento de
rastreabilidade permanente.

### 10.1 Formatos recomendados

1. `corpus/output/cora_rastreabilidade_documentos.csv`
2. `corpus/output/cora_rastreabilidade_documentos.json`
3. `docs/CORA_RASTREABILIDADE_DOCUMENTOS.md`

O CSV serve para auditoria tabular.
O JSON serve para automacao.
O Markdown serve para leitura humana e memoria institucional.

### 10.2 Campos obrigatorios

- `logical_doc_id`
- `status_final`
- `tipo_documental`
- `ano_documento`
- `numero_processo`
- `fonte_sei`
- `numero_documento_interno`
- `nome_original_pdf`
- `nome_original_md`
- `nome_original_txt`
- `nome_canonico_pdf`
- `nome_canonico_md`
- `nome_canonico_txt`
- `sha256_pdf_antes`
- `sha256_pdf_depois`
- `sha256_md_antes`
- `sha256_md_depois`
- `sha256_txt_antes`
- `sha256_txt_depois`
- `pinecone_index`
- `pinecone_namespace`
- `pinecone_document_id`
- `processed_json_path`
- `match_method`
- `decisao_manual`, se houver
- `responsavel_decisao`, se houver
- `data_decisao`, se houver
- `data_aplicacao`
- `plan_digest`
- `undo_manifest`

## 11. Salvaguardas obrigatorias

### 11.1 Antes do plano

- Regerar inventario dos arquivos oficiais.
- Regerar inventario das conversoes.
- Regerar inventario dos processados.
- Comparar com o namespace Pinecone quando possivel.

### 11.2 Durante o plano

- Validar formato do nome proposto.
- Validar ano e processo no nome.
- Validar tipo documental.
- Validar sequencial livre.
- Validar existencia de todas as variantes.
- Validar ausencia de colisao de destino.
- Registrar hashes.

### 11.3 Antes da aplicacao

- Rodar dry-run.
- Conferir `plan_digest`.
- Bloquear se qualquer hash de origem mudou.
- Bloquear se qualquer destino passou a existir.
- Bloquear se algum arquivo saiu da pasta oficial.

### 11.4 Depois da aplicacao

- Recalcular hashes.
- Validar que todos os arquivos esperados existem nos novos caminhos.
- Validar que nenhum arquivo esperado ficou no caminho antigo.
- Gerar manifesto de undo.
- Atualizar documento de rastreabilidade.

## 12. Decisoes adotadas e pendencias

Decisoes adotadas na renomeacao canonica de 2026-05-05:

1. Codigos de tipo para documentos nao Nota Tecnica:
   - `of`
   - `desp`
   - `par`
2. Documentos CGU entram no mesmo sequencial anual global.
3. Documentos sem processo extraivel devem ser bloqueados para revisao manual,
   sem criar nome canonico automatico.
4. Deve ser definido o tipo documental de qualquer documento inicialmente classificado
   como indefinido. Nao usar sufixo generico.
5. Arquivos processados `.json` nao foram renomeados fisicamente; permanecem
   como evidencia de ingestao e sao referenciados na rastreabilidade.
6. Nomes ja existentes no padrao canonico foram preservados; os demais arquivos
   oficiais PDF/MD/TXT foram normalizados para o padrao definido.

Pendencia atual: nao ha pendencia de nomenclatura na pasta oficial. Restam
documentos oficiais ainda nao ingeridos, que dependem de autorizacao futura de
ingestao.

## 13. Ordem recomendada de execucao futura

1. Aprovar este plano.
2. Aprovar codigos de tipo documental.
3. Gerar inventario por documento logico.
4. Gerar relatorio Pinecone versus universo oficial.
5. Resolver `pinecone_orphan`, `ambiguous_match` e `metadata_incomplete`.
6. Gerar plano de nomenclatura completo para PDF, MD e TXT.
7. Gerar documento preliminar de rastreabilidade.
8. Rodar double check.
9. Aprovar digest do plano.
10. Aplicar renomeacao.
11. Rodar verificacao pos-aplicacao.
12. Emitir documento final de rastreabilidade.
13. Somente depois disso iniciar nova ingestao no Pinecone.

## 14. Criterio de pronto

O processo so estara pronto para renomeacao quando:

- Todos os documentos logicos tiverem status definido.
- Todos os documentos Pinecone/processados estiverem classificados como
  `contained`, `pinecone_orphan` ou `ambiguous_match`.
- Nao houver `pinecone_orphan` sem decisao.
- Nao houver colisao de nomes.
- Todos os tipos documentais tiverem codigo aprovado.
- O plano de renomeacao tiver digest estavel.
- O documento de rastreabilidade preliminar estiver gerado.
