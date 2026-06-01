# CORA - Relatório de upsert diferencial

Data: `2026-05-06`

## Escopo

Este relatório documenta o upsert diferencial dos documentos oficiais de conflito de interesse que estavam em `corpus/NOTAS-CONFLITO-INTERESSE/markdown` e ainda não constavam no espelho local validado do namespace Pinecone.

- Pinecone index: `agentes-juridicos`
- Pinecone namespace: `notas_conflito_interesse`
- Pasta de entrada: `corpus/NOTAS-CONFLITO-INTERESSE/markdown`
- Diretório processado diferencial: `corpus/processed_conflito_interesse_diff_20260506`

## Base diferencial

O lote diferencial foi gerado a partir do relatório:

- `corpus/output/cora_markdown_diff_upsert_candidates.json`
- `corpus/output/cora_markdown_diff_upsert_candidates.jsonl`
- `corpus/output/cora_markdown_diff_upsert_candidates.csv`
- `corpus/output/cora_markdown_diff_upsert_candidates.md`

Resumo do lote:

- Documentos Markdown candidatos: `45`
- Conteúdo Markdown vazio: `0`
- Caracteres totais em Markdown: `1.076.333`
- Base comparativa anterior: `86` documentos processados locais, usados como espelho validado do namespace
- Órfãos processados locais antes do upsert: `0`

Distribuição por tipo documental:

- `nota_tecnica`: `36`
- `despacho`: `5`
- `oficio`: `4`

Distribuição por ano:

- `2021`: `15`
- `2022`: `6`
- `2023`: `2`
- `2024`: `2`
- `2025`: `17`
- `2026`: `3`

## Processamento

Foi criado o executor específico:

- `corpus/scripts/cora_process_diff_candidates.py`

Ele processou somente os `45` candidatos diferenciais, gravando artefatos `*_processed.json` em diretório isolado:

- `corpus/processed_conflito_interesse_diff_20260506`

Relatório de processamento:

- `corpus/processed_conflito_interesse_diff_20260506/processing_report_20260506_112523.json`

Resultado:

- Arquivos processados: `45`
- Records/chunks gerados: `576`
- Enriquecimento semântico: `45` com `semantic_source: gemini`
- Falhas de processamento: `0`

## Canonicalização dos metadados

Após o processamento, os artefatos foram canonicalizados com base no cadastro diferencial, para garantir que os metadados usados no upsert refletissem a nomenclatura oficial.

Foi criado o script:

- `corpus/scripts/cora_canonicalize_processed_diff.py`

Relatório definitivo da canonicalização:

- `corpus/processed_conflito_interesse_diff_20260506/canonicalization_report_20260506_112759.json`

Correções aplicadas:

- Arquivos casados com candidatos: `45/45`
- Records tratados: `576`
- Tipos documentais corrigidos: `9`
- Processos corrigidos para o padrão canônico do nome do arquivo: `19`
- IDs duplicados de records: `0`
- Arquivos sem processo após canonicalização: `0`

Metadados canônicos aplicados aos documentos e records:

- `document_id`
- `document_business_id`
- `candidate_id`
- `canonical_base`
- `nomenclatura_cora`
- `tipo_documento`
- `tipo_documental`
- `tipo_documento_rotulo`
- `numero_processo`
- `numero_processo_canonico`
- `numero_processo_nome_arquivo`
- `processo_com_pontos`
- `ano_documento`
- `numero_documento`
- `numero_documento_interno`
- `arquivo_original`
- `pinecone_index`
- `pinecone_namespace`

Quando o pipeline havia extraído valor diferente, o valor original foi preservado em campos `*_pipeline`.

## Dry-run de upsert

Antes do envio real, foi executado:

```bash
python3 corpus/scripts/upsert_processed_conflito_interesse.py --processed-dir corpus/processed_conflito_interesse_diff_20260506 --namespace notas_conflito_interesse --dry-run
```

Relatório:

- `corpus/processed_conflito_interesse_diff_20260506/upsert_report_20260506_112813.json`

Resultado:

- Namespace alvo: `notas_conflito_interesse`
- Arquivos simulados: `45`
- Records simulados: `576`
- Status: `dry_run`

## Upsert real

Com o dry-run validado, foi executado o upsert real:

```bash
python3 corpus/scripts/upsert_processed_conflito_interesse.py --processed-dir corpus/processed_conflito_interesse_diff_20260506 --namespace notas_conflito_interesse
```

Relatório:

- `corpus/processed_conflito_interesse_diff_20260506/upsert_report_20260506_113526.json`

Resultado:

- Arquivos enviados: `45`
- Records enviados: `576`
- Status por arquivo: `45` com `ok`
- Verificação amostral: todos os documentos tiveram amostras localizadas no namespace
- Falhas reportadas: `0`

## Validação externa do namespace

Após o upsert, foi consultado o índice Pinecone.

Resultado:

- `notas_conflito_interesse`: `2367` vetores
- `notas_tecnicas_senor`: `3823` vetores

Conferência aritmética:

- Vetores anteriores em `notas_conflito_interesse`: `1791`
- Vetores diferenciais enviados: `576`
- Total esperado: `2367`
- Total observado: `2367`

Verificação de atualização em `2026-05-13`:

- Relatório atualizado: `corpus/output/cora_pinecone_namespace_stats_2026-05-13.md`
- Snapshot JSON: `corpus/output/cora_pinecone_namespace_stats_2026-05-13.json`
- Atalho do snapshot atual: `corpus/output/cora_pinecone_namespace_stats_latest.json`
- Namespace listado: `notas_conflito_interesse`
- IDs remotos listados: `2367`
- Notas/documentos distintos no namespace: `131`
- Vetores/chunks no namespace: `2367`
- Conferência com espelho local: `131` documentos processados e `2367` records
- Status: relatório anterior `cora_pinecone_namespace_stats_2026-05-05.json` estava defasado em `576` vetores

## Conclusão

O upsert diferencial da CORA foi concluído com sucesso no namespace `notas_conflito_interesse`.

O lote oficial agora tem os `45` documentos diferenciais processados, canonicalizados e ingeridos, preservando rastreabilidade por arquivo, por candidato, por processo canônico e por relatório de execução.
