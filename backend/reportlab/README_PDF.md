# Gerador de PDF - C.O.R.A.

Script para gerar PDFs de perguntas e respostas com suporte completo a emojis.

## Requisitos

- Python 3.x
- Node.js (v14 ou superior)
- Puppeteer (instalado via npm)

## Instalação

```bash
npm install
```

## Uso

```bash
python gerar_pdf.py [arquivo_entrada.txt] [arquivo_saida.pdf]
```

Exemplo:
```bash
python gerar_pdf.py resposta.txt resposta.pdf
```

## Formato do arquivo de entrada

O arquivo de texto deve conter:

1. **PERGUNTA DO USUÁRIO:** (ou `<b>PERGUNTA DO USUÁRIO:</b>`)
   - Texto da pergunta

2. **RESPOSTA:** (ou `<b>RESPOSTA:</b>`)
   - Texto da resposta (pode conter emojis)

3. **Referências em JSON** (opcional, no final do arquivo):
```json
{
  "fontes": 10,
  "references": [
    {
      "score": 0.719,
      "source": "180/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"
    }
  ]
}
```

## Características

- ✅ Suporte completo a emojis Unicode
- ✅ Formatação HTML preservada (tags `<b>`)
- ✅ Referências formatadas em tabela
- ✅ Numeração de páginas automática
- ✅ Layout profissional
