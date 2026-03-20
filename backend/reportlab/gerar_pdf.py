#Script para gerar PDF de perguntas e respostas usando Puppeteer (suporte a emojis)
__version__='1.0.0'
__doc__='Script para gerar PDF de perguntas e respostas usando Puppeteer'

import sys, os, json
import subprocess
import tempfile
import re

def parseResposta(fn, output_file='resposta.pdf'):
    # Garantir que output_file seja um caminho absoluto
    if not os.path.isabs(output_file):
        output_file = os.path.abspath(output_file)
    text = open(fn, 'r', encoding='utf-8').read()
    
    # Separar as seções
    pergunta = ""
    resposta = ""
    referencias = []
    
    # Extrair pergunta
    if '<b>PERGUNTA DO USUÁRIO:</b>' in text:
        idx_pergunta = text.index('<b>PERGUNTA DO USUÁRIO:</b>')
        idx_resposta = text.index('<b>RESPOSTA:</b>')
        pergunta = text[idx_pergunta + len('<b>PERGUNTA DO USUÁRIO:</b>'):idx_resposta].strip()
    elif 'PERGUNTA DO USUÁRIO:' in text:
        idx_pergunta = text.index('PERGUNTA DO USUÁRIO:')
        idx_resposta = text.index('RESPOSTA:')
        pergunta = text[idx_pergunta + len('PERGUNTA DO USUÁRIO:'):idx_resposta].strip()
    
    # Extrair resposta
    if '<b>RESPOSTA:</b>' in text:
        idx_resposta = text.index('<b>RESPOSTA:</b>')
        if '{' in text and '"references"' in text:
            idx_json = text.rindex('{')
            resposta = text[idx_resposta + len('<b>RESPOSTA:</b>'):idx_json].strip()
        else:
            resposta = text[idx_resposta + len('<b>RESPOSTA:</b>'):].strip()
    elif 'RESPOSTA:' in text:
        idx_resposta = text.index('RESPOSTA:')
        if '{' in text and '"references"' in text:
            idx_json = text.rindex('{')
            resposta = text[idx_resposta + len('RESPOSTA:'):idx_json].strip()
        else:
            resposta = text[idx_resposta + len('RESPOSTA:'):].strip()
    
    # Limpar JSON da resposta
    resposta_linhas = resposta.split('\n')
    resposta_limpa = []
    dentro_json = False
    for linha in resposta_linhas:
        linha_stripped = linha.strip()
        if linha_stripped.startswith('{') or '"references"' in linha_stripped or '"score"' in linha_stripped or '"fontes"' in linha_stripped:
            dentro_json = True
            continue
        if dentro_json and (linha_stripped.startswith('}') or linha_stripped == ']'):
            dentro_json = False
            continue
        if not dentro_json:
            resposta_limpa.append(linha)
    resposta = '\n'.join(resposta_limpa).strip()
    
    # Extrair referências do JSON
    if '{' in text and '"references"' in text:
        try:
            idx_fontes = text.rfind('"fontes"')
            idx_references = text.rfind('"references"')
            idx_start = min(idx_fontes, idx_references) if idx_fontes > 0 and idx_references > 0 else (idx_fontes if idx_fontes > 0 else idx_references)
            
            if idx_start > 0:
                idx_json = text.rfind('{', 0, idx_start + 10)
                if idx_json > 0:
                    idx_end = text.rfind('}', idx_json)
                    if idx_end > idx_json:
                        json_text = text[idx_json:idx_end+1].strip()
                        data = json.loads(json_text)
                        if 'references' in data:
                            for ref in data['references']:
                                source = ref.get('source', '')
                                score = ref.get('score', 0)
                                url = ref.get('url', '')
                                relevancia = f"{score * 100:.1f}%"
                                referencias.append((source, relevancia, url))
        except (json.JSONDecodeError, ValueError) as e:
            try:
                idx_json = text.rindex('{')
                json_text = text[idx_json:]
                idx_close = json_text.rindex('}')
                json_text = json_text[:idx_close+1].strip()
                data = json.loads(json_text)
                if 'references' in data:
                    for ref in data['references']:
                        source = ref.get('source', '')
                        score = ref.get('score', 0)
                        url = ref.get('url', '')
                        relevancia = f"{score * 100:.1f}%"
                        referencias.append((source, relevancia, url))
            except:
                pass
    
    # Converter quebras de linha em parágrafos HTML
    def texto_para_html(texto):
        # Função para verificar se uma string começa com emoji
        def comeca_com_emoji(texto):
            if not texto or not texto.strip():
                return False
            # Remove espaços iniciais para verificar o primeiro caractere
            texto_limpo = texto.strip()
            if not texto_limpo:
                return False
            primeiro_char = texto_limpo[0]
            # Verifica se é um emoji (ranges Unicode de emojis)
            codigo = ord(primeiro_char)
            # Ranges comuns de emojis (mais completo)
            emoji_ranges = [
                (0x1F300, 0x1F9FF),  # Miscellaneous Symbols and Pictographs
                (0x1F600, 0x1F64F),  # Emoticons
                (0x1F680, 0x1F6FF),  # Transport and Map Symbols
                (0x2600, 0x26FF),    # Miscellaneous Symbols
                (0x2700, 0x27BF),    # Dingbats
                (0xFE00, 0xFE0F),    # Variation Selectors
                (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
                (0x1F1E0, 0x1F1FF),  # Regional Indicator Symbols
                (0x2300, 0x23FF),    # Miscellaneous Technical (inclui ⏳)
                (0x2B00, 0x2BFF),    # Miscellaneous Symbols and Arrows
            ]
            # Verifica se está em algum range de emoji
            for inicio, fim in emoji_ranges:
                if inicio <= codigo <= fim:
                    return True
            # Verifica também caracteres especiais comuns que podem ser emojis
            if codigo >= 0x2000 and codigo <= 0x206F:  # General Punctuation
                return False
            # Verifica se é um caractere que não é letra, número ou pontuação comum
            if not (primeiro_char.isalnum() or primeiro_char in '.,;:!?()[]{}\'"-'):
                # Pode ser um emoji ou símbolo especial
                return True
            return False
        
        # Dividir em linhas
        linhas = texto.split('\n')
        html_paragrafos = []
        
        for linha in linhas:
            linha_stripped = linha.strip()
            if not linha_stripped:
                continue
            
            # Verifica se a linha começa com emoji
            if comeca_com_emoji(linha_stripped):
                # Sempre adiciona linha em branco antes de um item com emoji (exceto se for o primeiro)
                if html_paragrafos:
                    html_paragrafos.append('<p style="margin-bottom: 0.3cm; height: 0.3cm;"></p>')
            
            # Escapar HTML mas preservar tags <b> e emojis
            para = linha_stripped.replace('&', '&amp;')
            para = para.replace('<b>', '___TAG_B_OPEN___').replace('</b>', '___TAG_B_CLOSE___')
            para = para.replace('<', '&lt;').replace('>', '&gt;')
            para = para.replace('___TAG_B_OPEN___', '<b>').replace('___TAG_B_CLOSE___', '</b>')
            html_paragrafos.append(f'<p>{para}</p>')
        
        return '\n'.join(html_paragrafos)
    
    # Construir HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Emoji", "Apple Color Emoji", "Segoe UI", Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #000;
            }}
            .titulo-principal {{
                font-size: 14pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 0.5cm;
            }}
            .secao-titulo {{
                font-size: 12pt;
                font-weight: bold;
                margin-top: 0.4cm;
                margin-bottom: 0.2cm;
            }}
            .pergunta-texto {{
                margin-bottom: 0.3cm;
            }}
            .resposta-texto {{
                text-align: justify;
                margin-bottom: 0.1cm;
            }}
            table.referencias-tabela {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 0.2cm;
            }}
            table.referencias-tabela td {{
                padding: 0.1cm 0.2cm;
                vertical-align: top;
            }}
            .referencia-nome {{
                text-align: left;
            }}
            .referencia-link {{
                color: #2563eb;
                text-decoration: none;
            }}
            .referencia-link:hover {{
                text-decoration: underline;
            }}
            .referencia-relevancia {{
                text-align: right;
                width: 4cm;
                font-size: 10pt;
            }}
            p {{
                margin: 0.1cm 0;
            }}
            p:empty {{
                margin: 0.3cm 0;
                height: 0.3cm;
            }}
            @media print {{
                .page-number {{
                    position: fixed;
                    bottom: 0.75cm;
                    right: 2cm;
                    font-size: 9pt;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="titulo-principal">C.O.R.A. - CONFLITO DE INTERESSES: ORIENTACAO, REGISTRO E ANALISE</div>
        <div style="margin-bottom: 0.5cm;"></div>
        
        <div class="secao-titulo">PERGUNTA DO USUÁRIO</div>
        <div class="pergunta-texto">{texto_para_html(pergunta)}</div>
        
        <div class="secao-titulo">RESPOSTA</div>
        <div class="resposta-texto">{texto_para_html(resposta)}</div>
        
        <div class="secao-titulo" style="margin-top: 0.6cm;">REFERÊNCIAS CONSULTADAS</div>
    """
    
    # Adicionar referências
    import html as html_module
    if referencias:
        html_content += '<table class="referencias-tabela">'
        for ref, relevancia, url in referencias:
            ref_escaped = html_module.escape(ref)
            if url:
                ref_html = f'<a href="{url}" class="referencia-link" target="_blank">{ref_escaped}</a>'
            else:
                ref_html = ref_escaped
            html_content += f'<tr><td class="referencia-nome">{ref_html}</td><td class="referencia-relevancia">Relevância: {relevancia}</td></tr>'
        html_content += '</table>'
    
    html_content += """
    </body>
    </html>
    """
    
    # Salvar HTML temporário
    temp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    temp_html.write(html_content)
    temp_html.close()
    
    # Script Puppeteer para converter HTML para PDF
    output_file_abs = os.path.abspath(output_file)
    temp_html_abs = os.path.abspath(temp_html.name)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    puppeteer_path = os.path.join(project_dir, 'node_modules', 'puppeteer')
    puppeteer_script = f"""
    const puppeteer = require('{puppeteer_path}');
    const path = require('path');
    
    (async () => {{
        const browser = await puppeteer.launch({{ headless: true }});
        const page = await browser.newPage();
        await page.goto('file://{temp_html_abs}', {{ waitUntil: 'networkidle0' }});
        await page.pdf({{
            path: '{output_file_abs}',
            format: 'A4',
            margin: {{
                top: '2.5cm',
                right: '2cm',
                bottom: '2.5cm',
                left: '2cm'
            }},
            printBackground: true
        }});
        await browser.close();
        console.log('PDF salvo em: {output_file_abs}');
    }})();
    """
    
    # Salvar script Puppeteer temporário
    temp_js = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
    temp_js.write(puppeteer_script)
    temp_js.close()
    
    # Executar Puppeteer usando node diretamente
    try:
        # Usar node diretamente com puppeteer local
        result = subprocess.run(['node', temp_js.name], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout)
        if os.path.exists(output_file_abs):
            print(f'PDF gerado com sucesso: {output_file_abs}')
        else:
            print(f'AVISO: PDF não encontrado em {output_file_abs}')
            print(f'Verificando diretório atual: {os.getcwd()}')
    except subprocess.CalledProcessError as e:
        # Tentar método alternativo: usar node diretamente com require do puppeteer local
        try:
            # Ajustar o script para usar o caminho relativo
            output_file_abs = os.path.abspath(output_file)
            temp_html_abs = os.path.abspath(temp_html.name)
            project_dir = os.path.dirname(os.path.abspath(__file__))
            puppeteer_path = os.path.join(project_dir, 'node_modules', 'puppeteer')
            puppeteer_script_v2 = f"""
            const puppeteer = require('{puppeteer_path}');
            
            (async () => {{
                const browser = await puppeteer.launch({{ headless: true }});
                const page = await browser.newPage();
                await page.goto('file://{temp_html_abs}', {{ waitUntil: 'networkidle0' }});
                await page.pdf({{
                    path: '{output_file_abs}',
                    format: 'A4',
                    margin: {{
                        top: '2.5cm',
                        right: '2cm',
                        bottom: '2.5cm',
                        left: '2cm'
                    }},
                    printBackground: true
                }});
                await browser.close();
                console.log('PDF salvo em: {output_file_abs}');
            }})();
            """
            temp_js_v2 = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
            temp_js_v2.write(puppeteer_script_v2)
            temp_js_v2.close()
            
            result = subprocess.run(['node', temp_js_v2.name], 
                                  cwd=os.path.dirname(os.path.abspath(__file__)),
                                  capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout)
            if os.path.exists(output_file_abs):
                print(f'PDF gerado com sucesso: {output_file_abs}')
            else:
                print(f'AVISO: PDF não encontrado em {output_file_abs}')
            os.unlink(temp_js_v2.name)
        except Exception as e2:
            print(f'Erro ao gerar PDF: {e.stderr if "e" in locals() else str(e2)}')
            if hasattr(e2, 'stdout') and e2.stdout:
                print(f'Stdout: {e2.stdout}')
            if hasattr(e2, 'stderr') and e2.stderr:
                print(f'Stderr: {e2.stderr}')
            raise
    finally:
        # Limpar arquivos temporários
        try:
            os.unlink(temp_html.name)
            os.unlink(temp_js.name)
        except:
            pass

def run(input_file='resposta.txt', output_file='resposta.pdf'):
    if os.path.isfile(input_file):
        parseResposta(input_file, output_file)
    else:
        print(f'Erro: Arquivo {input_file} não encontrado')

if __name__=='__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'resposta.txt'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'resposta.pdf'
    run(input_file, output_file)
