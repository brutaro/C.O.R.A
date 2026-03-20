# Guia de Instalacao e Uso - Gerador de PDF C.O.R.A.

Este documento descreve passo a passo como instalar e usar o gerador de PDF com suporte a emojis usando Puppeteer.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

1. **Python 3.x** (versão 3.7 ou superior)
   - Verificar instalação: `python3 --version` ou `python --version`
   - Download: https://www.python.org/downloads/

2. **Node.js** (versão 14 ou superior)
   - Verificar instalação: `node --version`
   - Download: https://nodejs.org/
   - O Node.js inclui o `npm` (gerenciador de pacotes)

3. **npm** (vem com Node.js)
   - Verificar instalação: `npm --version`

## 🚀 Instalação

### Passo 1: Copiar arquivos necessários

Copie os seguintes arquivos para o novo projeto:

```
gerar_pdf.py          # Script principal Python
package.json          # Configuração do Node.js com dependências
package-lock.json     # Lock file do npm (opcional, mas recomendado)
node_modules/         # Módulos do Node.js (NÃO copie, será reinstalado)
```

**⚠️ IMPORTANTE:** NÃO copie a pasta `node_modules/`. Ela será recriada no passo seguinte.

### Passo 2: Instalar dependências do Node.js

No diretório do novo projeto, execute:

```bash
npm install
```

Este comando irá:
- Ler o arquivo `package.json`
- Instalar o Puppeteer e todas as suas dependências
- Criar a pasta `node_modules/` automaticamente
- Baixar o Chromium necessário para o Puppeteer

**Tempo estimado:** 2-5 minutos (dependendo da conexão)

### Passo 3: Verificar instalação

Para verificar se tudo está instalado corretamente:

```bash
# Verificar Node.js
node --version

# Verificar npm
npm --version

# Verificar se Puppeteer foi instalado
ls node_modules/puppeteer
```

## 📝 Formato do Arquivo de Entrada

O script espera um arquivo de texto com o seguinte formato:

```
<b>PERGUNTA DO USUÁRIO:</b> [texto da pergunta]

<b>RESPOSTA:</b>

[texto da resposta, pode conter emojis e tags HTML <b>]

📚 Título de uma seção

Texto da seção...

⏳ Outra seção

Mais texto...

{
  "fontes": 10,
  "references": [
    {
      "score": 0.719310164,
      "source": "180/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"
    },
    {
      "score": 0.707536101,
      "source": "17/2025/DECOR/CGU/AGU"
    }
  ]
}
```

### Características do formato:

- **Pergunta**: Deve começar com `<b>PERGUNTA DO USUÁRIO:</b>` ou `PERGUNTA DO USUÁRIO:`
- **Resposta**: Deve começar com `<b>RESPOSTA:</b>` ou `RESPOSTA:`
- **Emojis**: Suportados nativamente (📚, 🗓️, ⏳, 📝, etc.)
- **Tags HTML**: Tags `<b>` são preservadas para negrito
- **Referências**: JSON opcional no final do arquivo com array de referências

## 🎯 Uso

### Comando básico:

```bash
python gerar_pdf.py [arquivo_entrada.txt] [arquivo_saida.pdf]
```

### Exemplos:

```bash
# Usando nomes padrão (resposta.txt -> resposta.pdf)
python gerar_pdf.py

# Especificando arquivo de entrada
python gerar_pdf.py resposta.txt

# Especificando entrada e saída
python gerar_pdf.py resposta.txt documento.pdf

# Usando Python 3 explicitamente
python3 gerar_pdf.py resposta.txt resposta.pdf
```

### Saída esperada:

```
PDF gerado com sucesso: /caminho/completo/para/resposta.pdf
```

## 📄 Estrutura do PDF Gerado

O PDF gerado terá a seguinte estrutura:

1. **Título Principal** (centralizado, fonte 14pt)
   - "C.O.R.A. - CONFLITO DE INTERESSES: ORIENTACAO, REGISTRO E ANALISE"

2. **Pergunta do Usuário** (fonte 12pt, negrito)
   - Texto da pergunta formatado

3. **Resposta** (fonte 12pt, negrito como subtítulo)
   - Texto da resposta justificado
   - **Linha em branco automática antes de cada item que começa com emoji**
   - Emojis renderizados corretamente
   - Tags `<b>` convertidas para negrito

4. **Referências Consultadas** (fonte 12pt, negrito)
   - Tabela com:
     - Nome da referência (alinhado à esquerda)
     - Relevância em porcentagem (alinhado à direita)

## 🔧 Solução de Problemas

### Erro: "Cannot find module 'puppeteer'"

**Solução:**
```bash
npm install
```

### Erro: "node: command not found"

**Solução:** Instale o Node.js (veja Pré-requisitos)

### Erro: "python: command not found"

**Solução:** 
- Use `python3` ao invés de `python`
- Ou instale o Python (veja Pré-requisitos)

### PDF não está sendo gerado

**Verificações:**
1. Verifique se o arquivo de entrada existe
2. Verifique se há espaço em disco
3. Verifique as permissões de escrita no diretório
4. Execute com caminhos absolutos para debug:
   ```bash
   python gerar_pdf.py /caminho/completo/resposta.txt /caminho/completo/saida.pdf
   ```

### Emojis não aparecem no PDF

**Solução:** O Puppeteer usa o Chromium que tem suporte nativo a emojis. Se os emojis não aparecem:
1. Verifique se o arquivo de entrada está em UTF-8
2. Verifique se o sistema operacional tem fontes de emoji instaladas
3. No macOS e Linux, os emojis devem funcionar automaticamente

### Linhas em branco não aparecem antes dos emojis

**Solução:** O script detecta automaticamente linhas que começam com emoji e adiciona espaçamento. Se não funcionar:
1. Verifique se a linha realmente começa com emoji (sem espaços antes)
2. Verifique se o emoji está em um range Unicode suportado

## 📦 Estrutura de Arquivos do Projeto

```
projeto/
├── gerar_pdf.py          # Script principal (OBRIGATÓRIO)
├── package.json          # Configuração npm (OBRIGATÓRIO)
├── package-lock.json     # Lock file npm (RECOMENDADO)
├── node_modules/         # Dependências (NÃO COPIAR, gerado por npm install)
├── resposta.txt          # Arquivo de exemplo (OPCIONAL)
└── README_PDF.md         # Documentação (OPCIONAL)
```

## 🔄 Atualização

Para atualizar o Puppeteer para a versão mais recente:

```bash
npm update puppeteer
```

## 📚 Dependências

- **Puppeteer**: ^24.30.0 (ou superior)
  - Biblioteca Node.js para controlar o Chromium
  - Usado para converter HTML em PDF com renderização completa

- **Python**: Bibliotecas padrão apenas
  - `sys`, `os`, `json`, `subprocess`, `tempfile`, `re`
  - Não requer instalação adicional de pacotes Python

## ⚙️ Configurações Avançadas

### Alterar margens do PDF

Edite o arquivo `gerar_pdf.py`, procure por:

```python
margin: {{
    top: '2.5cm',
    right: '2cm',
    bottom: '2.5cm',
    left: '2cm'
}},
```

### Alterar tamanho da fonte

Edite o CSS no arquivo `gerar_pdf.py`, procure por:

```css
body {{
    font-size: 11pt;
    ...
}}
```

### Alterar espaçamento antes de emojis

Edite o arquivo `gerar_pdf.py`, procure por:

```python
html_paragrafos.append('<p style="margin-bottom: 0.3cm; height: 0.3cm;"></p>')
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique a seção "Solução de Problemas" acima
2. Verifique os logs de erro no terminal
3. Execute o script com `python -u gerar_pdf.py` para ver saída não-bufferizada

## ✅ Checklist de Instalação

- [ ] Python 3.x instalado
- [ ] Node.js instalado
- [ ] Arquivo `gerar_pdf.py` copiado
- [ ] Arquivo `package.json` copiado
- [ ] Comando `npm install` executado com sucesso
- [ ] Teste com `python gerar_pdf.py resposta.txt` funcionando
- [ ] PDF gerado com emojis visíveis
- [ ] Linhas em branco aparecem antes de itens com emoji

---

**Versão:** 1.0.0  
**Última atualização:** Novembro 2024
