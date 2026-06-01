# CORA - Relatorio de renomeacao canonica

Data: 2026-05-05

## Escopo

Renomear os arquivos da pasta oficial `corpus/NOTAS-CONFLITO-INTERESSE` para o padrao
canonico definido para o acervo CORA.

Nao houve ingestao no Pinecone nesta etapa.

## Padrao aplicado

```text
{sequencial_no_ano}_{ano_documento}_{processo_com_pontos}_{tipo}.{ext}
```

Sufixos adotados:

| Tipo documental | Sufixo |
| --- | --- |
| Nota Tecnica | `e` |
| Oficio | `of` |
| Despacho | `desp` |
| Parecer | `par` |

## Resultado da aplicacao

Plano aplicado:

```text
corpus/output/cora_full_canonical_rename_plan.json
```

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

Resultado:

| Metrica | Quantidade |
| --- | ---: |
| Arquivos renomeados | 388 |
| Arquivos ja canonicos antes da aplicacao | 3 |
| Arquivos canonicos no plano final | 393 |
| Arquivos bloqueados no plano final | 0 |
| Documentos logicos bloqueados | 0 |

## Verificacao pos-renomeacao

Inventario logico regenerado:

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

Conclusao: os 86 documentos processados locais continuam contidos no universo
oficial. Nao ha `pinecone_orphan_local` nem `ambiguous_match`.

## Reparacao adicional

Durante a validacao foi identificado que o arquivo abaixo estava vazio:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2022/3_2022_50600.001987.2022.11_e.pdf
```

Ele foi substituido pela versao anonimizada correspondente localizada em:

```text
/Users/brutx/Documents/projects/pdf_anonimyzer/ETL_COLEG/output_final/pdf_anon/3_2022_50600.001987.2022.11_e.pdf
```

Tambem foram adicionados os formatos faltantes:

```text
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2022/3_2022_50600.001987.2022.11_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2022/3_2022_50600.001987.2022.11_e.txt
```

## Duplicidade resolvida

O antigo bloqueio do SEI `21312534`, processo
`50600.015472/2025-32`, Nota Tecnica
`81/2025/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE`, foi resolvido por remocao
manual de uma versao de cada formato e aplicacao da renomeacao canonica final.

Arquivos finais:

```text
corpus/NOTAS-CONFLITO-INTERESSE/2025/27_2025_50600.015472.2025.32_e.pdf
corpus/NOTAS-CONFLITO-INTERESSE/markdown/2025/27_2025_50600.015472.2025.32_e.md
corpus/NOTAS-CONFLITO-INTERESSE/txt/2025/27_2025_50600.015472.2025.32_e.txt
```

O plano final `corpus/output/cora_full_canonical_rename_plan.json` registra 393
operacoes como `noop`, isto e, todos os arquivos oficiais PDF/MD/TXT ja estao
com nome canonico.
