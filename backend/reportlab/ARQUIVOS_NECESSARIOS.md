# 📦 Lista de Arquivos Necessários para o Novo Projeto

## ✅ Arquivos OBRIGATÓRIOS (copiar)

Estes arquivos são **essenciais** e devem ser copiados:

### 1. `gerar_pdf.py`
- **Descrição:** Script principal Python que gera o PDF
- **Tamanho:** ~15 KB
- **Localização:** Raiz do projeto
- **Obrigatório:** ✅ SIM

### 2. `package.json`
- **Descrição:** Configuração do Node.js com dependências (Puppeteer)
- **Tamanho:** ~352 bytes
- **Localização:** Raiz do projeto
- **Obrigatório:** ✅ SIM
- **Conteúdo:**
  ```json
  {
    "name": "pdf-generator-lara",
    "version": "1.0.0",
    "description": "Gerador de PDF com suporte a emojis usando Puppeteer",
    "dependencies": {
      "puppeteer": "^24.30.0"
    }
  }
  ```

## 📋 Arquivos RECOMENDADOS (copiar)

Estes arquivos são recomendados mas não obrigatórios:

### 3. `package-lock.json`
- **Descrição:** Lock file do npm que garante versões exatas das dependências
- **Tamanho:** ~40 KB
- **Localização:** Raiz do projeto
- **Obrigatório:** ❌ NÃO (mas recomendado para garantir consistência)
- **Benefício:** Garante que todos instalem exatamente as mesmas versões

### 4. `INSTALACAO.md`
- **Descrição:** Documentação completa de instalação e uso
- **Tamanho:** ~7.2 KB
- **Localização:** Raiz do projeto
- **Obrigatório:** ❌ NÃO (mas muito útil)

### 5. `README_PDF.md`
- **Descrição:** Documentação rápida de uso
- **Tamanho:** ~1.0 KB
- **Localização:** Raiz do projeto
- **Obrigatório:** ❌ NÃO

## ❌ Arquivos NÃO COPIAR

### `node_modules/`
- **Descrição:** Pasta com todas as dependências do Node.js
- **Tamanho:** ~51 MB
- **Obrigatório:** ❌ NÃO COPIAR
- **Motivo:** Será recriado automaticamente com `npm install`
- **Ação:** Execute `npm install` no novo projeto

## 📊 Resumo

### Mínimo necessário (2 arquivos):
```
gerar_pdf.py
package.json
```

### Recomendado (4-5 arquivos):
```
gerar_pdf.py
package.json
package-lock.json
INSTALACAO.md
README_PDF.md (opcional)
```

## 🚀 Comandos para Copiar

### Opção 1: Copiar apenas o essencial
```bash
cp gerar_pdf.py /caminho/novo/projeto/
cp package.json /caminho/novo/projeto/
```

### Opção 2: Copiar tudo recomendado
```bash
cp gerar_pdf.py package.json package-lock.json INSTALACAO.md README_PDF.md /caminho/novo/projeto/
```

### Opção 3: Usar tar (preserva estrutura)
```bash
tar -czf pdf_generator.tar.gz gerar_pdf.py package.json package-lock.json INSTALACAO.md README_PDF.md
# Depois no novo projeto:
tar -xzf pdf_generator.tar.gz
```

## 📝 Após Copiar os Arquivos

No novo projeto, execute:

```bash
# 1. Instalar dependências
npm install

# 2. Testar
python gerar_pdf.py resposta.txt resposta.pdf
```

## ✅ Verificação Final

Após copiar e instalar, verifique:

```bash
# Verificar se os arquivos estão presentes
ls -la gerar_pdf.py package.json

# Verificar se node_modules foi criado
ls -d node_modules

# Verificar se Puppeteer está instalado
ls node_modules/puppeteer

# Testar o script
python gerar_pdf.py --help  # ou use um arquivo de teste
```

## 📦 Tamanho Total dos Arquivos

- **Mínimo (2 arquivos):** ~15 KB
- **Recomendado (5 arquivos):** ~64 KB
- **node_modules (NÃO copiar):** ~51 MB (será baixado com `npm install`)

---

**Nota:** O `node_modules/` é grande e não deve ser copiado. Sempre execute `npm install` no novo projeto para recriar as dependências.

