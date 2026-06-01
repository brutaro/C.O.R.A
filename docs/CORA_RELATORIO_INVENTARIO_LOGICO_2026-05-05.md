# CORA - Relatorio do inventario logico

Data: 2026-05-05

## Escopo da etapa

Esta etapa gerou o inventario por documento logico, agrupando as variantes
fisicas do mesmo documento:

- PDF oficial.
- Markdown convertido.
- TXT convertido.
- JSON processado local.

Nao houve nova ingestao no Pinecone.

Atualizacao posterior: o documento `9_2022_50600.007751.2022.80_e`, que
aparecia como possivel orfao local, foi localizado fora da pasta oficial e
incorporado ao acervo `corpus/NOTAS-CONFLITO-INTERESSE` em PDF, Markdown e TXT.

Atualizacao posterior: foi executada a renomeacao canonica da pasta oficial.
A etapa renomeou 388 arquivos e terminou sem bloqueios de nomenclatura.

## Fonte de verificacao Pinecone

A verificacao desta etapa usou os artefatos locais processados como proxy do
conjunto ja enviado ao Pinecone:

- `corpus/processed_conflito_interesse`
- `corpus/processed_conflito_interesse_incremental_20260320`

Namespace de referencia:

```text
notas_conflito_interesse
```

Index de referencia:

```text
agentes-juridicos
```

Consulta remota direta ao Pinecone: executada em modo read-only apos a geracao
do inventario logico.

Resultado remoto:

| Namespace | Vetores |
| --- | ---: |
| `notas_conflito_interesse` | 1791 |
| `notas_tecnicas_senor` | 3823 |

O namespace `notas_conflito_interesse` tem 1791 vetores no Pinecone. Esse total
coincide com a soma dos `records` dos 86 artefatos locais processados
`corpus/processed_conflito_interesse*`, tambem igual a 1791. Portanto, para esta etapa,
os artefatos locais processados sao uma representacao consistente do conjunto
remoto em quantidade de vetores.

## Artefatos gerados

- `corpus/output/cora_inventario_logico.csv`
- `corpus/output/cora_inventario_logico.json`
- `corpus/output/cora_inventario_logico.md`
- `corpus/output/cora_pinecone_namespace_stats_2026-05-05.json`
- Script: `corpus/scripts/cora_logical_inventory.py`

## Resultado numerico

| Metrica | Quantidade |
| --- | ---: |
| PDFs oficiais | 131 |
| Arquivos convertidos MD/TXT | 264 |
| Artefatos processados locais | 86 |
| Itens fisicos avaliados | 481 |
| Documentos logicos identificados | 131 |

## Status de contencao

| Status | Quantidade | Significado |
| --- | ---: | --- |
| `contained` | 86 | Processado local encontrado no universo oficial |
| `official_missing_from_pinecone_local` | 45 | Documento oficial ainda nao processado localmente |

Assim, os 86 documentos processados locais estao contidos no universo oficial.
Nao ha mais item `pinecone_orphan_local` no inventario atual.

## Duplicidades oficiais resolvidas

As tres duplicidades oficiais que afetavam documentos ja processados foram
resolvidas pela remocao de um conjunto duplicado em PDF/MD/TXT para cada SEI.
Depois da regeneracao do inventario, nao ha mais status `ambiguous_match`.

| SEI | Processo | Motivo |
| --- | --- | --- |
| 9966264 | 50600.035565/2021-50 | Mantido apenas um conjunto oficial |
| 11165649 | 50600.014009/2022-21 | Mantido apenas um conjunto oficial |
| 16216761 | 50600.036864/2023-73 | Mantido apenas um conjunto oficial |

## Duplicidade oficial resolvida

A antiga duplicidade oficial do SEI `21312534`, ainda nao processada
localmente, foi resolvida por remocao manual de uma versao de cada formato e
renomeacao canonica do conjunto remanescente:

| SEI | Processo | Nota | Arquivos |
| --- | --- | --- | --- |
| 21312534 | 50600.015472/2025-32 | 81/2025/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE | `27_2025_50600.015472.2025.32_e.*` |

Com isso, nao ha mais item `duplicate_official_review` no batimento final.

## Orfao local resolvido

O artefato processado local abaixo nao possuia PDF/MD/TXT correspondente na
pasta oficial. A busca ampliada localizou derivados do mesmo documento em
`/Users/brutx/Documents/projects/pdf_anonimyzer/ETL_COLEG`, e o documento foi
incorporado ao acervo oficial:

```text
corpus/processed_conflito_interesse/9_2022_50600.007751.2022.80_e_processed.json
```

Metadados:

| Campo | Valor |
| --- | --- |
| Processo | 50600.007751/2022-80 |
| Nota | 34/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE |
| Arquivo original processado | 9_2022_50600.007751.2022.80_e.md |
| Fonte SEI registrada | 10612486 |
| Codigo verificador citado no texto | 10621803 |

Arquivos incorporados:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2022/9_2022_50600.007751.2022.80_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2022/9_2022_50600.007751.2022.80_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2022/9_2022_50600.007751.2022.80_e.txt
```

Hash SHA-256 dos arquivos incorporados:

| Arquivo | SHA-256 |
| --- | --- |
| PDF | `8b622f67c30646bcfbf61e25a5c567990cdc4d1ad480d204be77ed363f59cc7f` |
| MD | `51def4a17970f18ccb5694bb1187a50ec3b1863d79fc9d148a0e7cc6bb00a70d` |
| TXT | `51def4a17970f18ccb5694bb1187a50ec3b1863d79fc9d148a0e7cc6bb00a70d` |

Observacao: o PDF e o Markdown incorporados sao as versoes anonimizadas
encontradas, coerentes com o conteudo processado no Pinecone. O Markdown bruto
original permanece fora do acervo oficial em
`/Users/brutx/Documents/projects/pdf_anonimyzer/ETL_COLEG/.pipeline_tmp/01_raw_md/9_2022_50600.007751.2022.80_e.md`.

## PDF vazio reparado

Durante a renomeacao, foi identificado que o PDF oficial abaixo estava vazio,
embora o documento processado local existisse:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2022/3_2022_50600.001987.2022.11_e.pdf
corpus/processed_conflito_interesse/3_2022_50600.001987.2022.11_e_processed.json
```

O PDF vazio foi substituido pela versao anonimizada correspondente encontrada
em `/Users/brutx/Documents/projects/pdf_anonimyzer/ETL_COLEG`, e foram
adicionados os formatos Markdown e TXT canonicos:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2022/3_2022_50600.001987.2022.11_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2022/3_2022_50600.001987.2022.11_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2022/3_2022_50600.001987.2022.11_e.txt
```

Hashes SHA-256 atuais:

| Arquivo | SHA-256 |
| --- | --- |
| PDF | `50963e34374b4afd8f11c87f8cfe8f668ae5200a1e0488b7f941955901e9569e` |
| MD | `06ca356265393febe9c66a1381c6c3fbf75f5279c02c1c61d2ef05d9ad62a0c8` |
| TXT | `06ca356265393febe9c66a1381c6c3fbf75f5279c02c1c61d2ef05d9ad62a0c8` |

## Oficiais ausentes de processado local

Foram identificados 45 documentos logicos oficiais sem artefato processado local:

| Tipo documental | Quantidade |
| --- | ---: |
| Nota Tecnica | 36 |
| Oficio | 4 |
| Despacho | 5 |

Distribuicao por ano:

| Tipo | Ano | Quantidade |
| --- | --- | ---: |
| Despacho | 2021 | 1 |
| Despacho | 2022 | 2 |
| Despacho | 2023 | 1 |
| Despacho | 2025 | 1 |
| Nota Tecnica | 2021 | 14 |
| Nota Tecnica | 2022 | 3 |
| Nota Tecnica | 2024 | 2 |
| Nota Tecnica | 2025 | 14 |
| Nota Tecnica | 2026 | 3 |
| Oficio | 2022 | 1 |
| Oficio | 2023 | 1 |
| Oficio | 2025 | 2 |

Esses documentos serao candidatos ao plano de nomenclatura e posterior ingestao,
desde que passem pelas salvaguardas.

## Correcao apos OCR

O documento abaixo havia ficado sem processo extraivel porque o PDF original
nao estava OCRizado. Apos nova extracao, o item foi identificado corretamente:

```text
corpus/NOTAS-CONFLITO-INTERESSE/CGU/TIAGO OLIVEIRA MOREIRA - Nota_Técnica.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/CGU/TIAGO OLIVEIRA MOREIRA - Nota_Técnica.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/CGU/TIAGO OLIVEIRA MOREIRA - Nota_Técnica.txt
```

Metadados identificados:

| Campo | Valor |
| --- | --- |
| Tipo documental | Nota Tecnica |
| Processo | 00190.100053/2022-53 |
| Nota | 154/2022/CGECI/DPC/STPC |
| Status atual | `official_missing_from_pinecone_local` |
| Nome canonico proposto no batimento | `30_2022_00190.100053.2022.53_e.pdf` |

Com isso, nao ha mais item `metadata_incomplete` no inventario logico atual.

## Ajustes metodologicos aplicados

Durante a etapa, foram aplicados dois ajustes para reduzir falso positivo:

1. `fonte_sei` de artefato processado so conecta documentos quando e unico e
   tambem existe como SEI de arquivo no corpus oficial.
2. Tipo documental passou a priorizar nome/cabecalho do documento, evitando que
   mencoes soltas a "despacho" ou "oficio" no corpo alterem a classificacao.
3. Quando um item possui tipo `indefinido` mas outro artefato do mesmo documento
   possui tipo definido, o tipo `indefinido` nao e tratado como conflito
   documental por si so.

## Proxima decisao

Pendencia remanescente:

1. Nao ha pendencia de nomenclatura na pasta oficial.
2. Permanecem 45 documentos oficiais sem artefato processado local, candidatos
   a ingestao futura quando autorizado.

Sufixos adotados na renomeacao canonica:

- `e` para Nota Tecnica.
- `of` para Oficio.
- `desp` para Despacho.
- `par` para Parecer.
