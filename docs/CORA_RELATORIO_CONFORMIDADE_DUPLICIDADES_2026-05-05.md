# CORA - Relatorio de conformidade apos saneamento de duplicidades

Data: 2026-05-05

## Escopo

Este relatorio verifica a acao manual de remocao das tres duplicidades oficiais
que apareciam como `ambiguous_match` no inventario logico CORA.

Nao houve renomeacao de arquivos e nao houve ingestao no Pinecone nesta etapa.
Posteriormente, o documento `9_2022_50600.007751.2022.80_e`, que aparecia como
`pinecone_orphan_local`, foi localizado e incorporado ao acervo oficial.
Em etapa posterior, foi aplicada a renomeacao canonica dos arquivos univocos da
pasta oficial.

## Resultado da verificacao de arquivos

Foram pesquisados os SEIs `9966264`, `11165649` e `16216761` na pasta
`corpus/NOTAS-CONFLITO-INTERESSE`.

Resultado encontrado:

| SEI | Resultado | Arquivos remanescentes |
| --- | --- | --- |
| 9966264 | Conforme | 1 PDF, 1 MD, 1 TXT |
| 11165649 | Conforme | 1 PDF, 1 MD, 1 TXT |
| 16216761 | Conforme | 1 PDF, 1 MD, 1 TXT |

Arquivos remanescentes apos a renomeacao canonica:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2021/12_2021_50600.035565.2021.50_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2021/12_2021_50600.035565.2021.50_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2021/12_2021_50600.035565.2021.50_e.txt

corpus/NOTAS-CONFLITO-INTERESSE/2022/15_2022_50600.014009.2022.21_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2022/15_2022_50600.014009.2022.21_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2022/15_2022_50600.014009.2022.21_e.txt

corpus/NOTAS-CONFLITO-INTERESSE/2023/19_2023_50600.036864.2023.73_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2023/19_2023_50600.036864.2023.73_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2023/19_2023_50600.036864.2023.73_e.txt
```

## Inventario logico regenerado final

Artefatos regenerados:

- `corpus/output/cora_inventario_logico.csv`
- `corpus/output/cora_inventario_logico.json`
- `corpus/output/cora_inventario_logico.md`
- `corpus/output/cora_batimento_renomeacao.csv`
- `corpus/output/cora_batimento_renomeacao.json`
- `corpus/output/cora_batimento_renomeacao.md`
- `corpus/output/cora_renaming_doublecheck.csv`
- `corpus/output/cora_renaming_doublecheck.json`
- `corpus/output/cora_renaming_doublecheck.md`

Resultado do inventario logico:

| Metrica | Quantidade |
| --- | ---: |
| PDFs oficiais | 131 |
| Arquivos convertidos MD/TXT | 264 |
| Artefatos processados locais | 86 |
| Itens fisicos avaliados | 481 |
| Documentos logicos | 131 |

Status de contencao:

| Status | Quantidade |
| --- | ---: |
| `contained` | 86 |
| `official_missing_from_pinecone_local` | 45 |
| `ambiguous_match` | 0 |

Conclusao: as tres ambiguidades anteriores foram resolvidas. Nao ha mais
`ambiguous_match` nem `pinecone_orphan_local` no inventario logico.

## Incorporacao do orfao local

O documento processado abaixo foi incorporado ao acervo oficial:

```text
corpus/processed_conflito_interesse/9_2022_50600.007751.2022.80_e_processed.json
```

Arquivos oficiais agora presentes:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2022/9_2022_50600.007751.2022.80_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2022/9_2022_50600.007751.2022.80_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2022/9_2022_50600.007751.2022.80_e.txt
```

Metadados:

| Campo | Valor |
| --- | --- |
| Processo | 50600.007751/2022-80 |
| Nota | 34/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE |
| Codigo verificador | 10621803 |
| Status atual | `contained` |

## Batimento de renomeacao regenerado

Resultado final:

| Status | Quantidade |
| --- | ---: |
| `already_processed` | 86 |
| `converted_not_processed` | 36 |
| `non_note_review` | 9 |

O antigo item em `duplicate_official_review` foi resolvido. O SEI `21312534`
agora possui um unico conjunto fisico canonico:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2025/27_2025_50600.015472.2025.32_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2025/27_2025_50600.015472.2025.32_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2025/27_2025_50600.015472.2025.32_e.txt
```

Metadados:

| Campo | Valor |
| --- | --- |
| SEI | 21312534 |
| Processo | 50600.015472/2025-32 |
| Nota | 81/2025/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE |

Esse caso esta conforme no inventario final.

## Renomeacao canonica executada

Plano aplicado:

| Metrica | Quantidade |
| --- | ---: |
| Arquivos renomeados | 388 |
| Arquivos ja canonicos no plano final | 393 |
| Arquivos bloqueados no plano final | 0 |
| Documentos logicos bloqueados | 0 |

Digests dos planos aplicados:

```text
81900bbdd32a5afa13a5ac2854251633940c3182366bd7ac5f409ed715120673
a4d92380884b87d625dd52e26d4578d0182428b2d7c262fd39cd0436e04682a5
```

Manifestos de reversao:

```text
corpus/output/cora_full_canonical_rename_undo_20260505_155103.json
corpus/output/cora_full_canonical_rename_undo_20260505_160217.json
```

Plano pos-renomeacao:

- `corpus/output/cora_full_canonical_rename_plan.csv`
- `corpus/output/cora_full_canonical_rename_plan.json`
- `corpus/output/cora_full_canonical_rename_plan.md`

## Conformidade

| Criterio | Resultado |
| --- | --- |
| As tres duplicidades processadas foram removidas em PDF/MD/TXT | Conforme |
| Inventario logico sem `ambiguous_match` | Conforme |
| Inventario logico sem `pinecone_orphan_local` | Conforme |
| Quantidade remota do Pinecone segue representada pelos 86 processados locais | Conforme, sem mudanca nesta etapa |
| Renomeacao executada | Conforme |
| Ingestao executada | Nao executada |
| Pendencias remanescentes registradas | Nao ha pendencia de nomenclatura |

## Pendencias para a proxima etapa

1. Nao ha pendencia de nomenclatura na pasta oficial.
2. Os 45 documentos oficiais ainda nao processados permanecem candidatos a
   ingestao futura quando autorizado.
