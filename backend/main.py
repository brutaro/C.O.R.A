#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 FastAPI com Agente de Pesquisa Simplificado
Integração direta sem orquestrador para máxima performance
"""

import asyncio
import html
import logging
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Importa o agente simplificado
import sys
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

sys.path.append(str(BACKEND_DIR.parent))
from src.agents.simple_research_agent import SimpleResearchAgent

# Importa autenticação JWT (do mesmo diretório)
sys.path.insert(0, str(BACKEND_DIR))
from auth import verify_token
from firebase_config import get_firestore_client

# Configuração de logging com mais detalhes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ASSISTANT_NAME = "C.O.R.A."
ASSISTANT_SLUG = "cora"
ASSISTANT_DESCRIPTION = "Conflito de Interesses: Orientacao, Registro e Analise"
KNOWLEDGE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "notas_conflito_interesse")
EXPECTED_KNOWLEDGE_NAMESPACE = "notas_conflito_interesse"
PUBLIC_LOCAL_HOST = os.getenv("PUBLIC_LOCAL_HOST", "localhost")

research_agent = None
research_agent_error: Optional[str] = None

# Inicializa FastAPI
app = FastAPI(
    title=f"{ASSISTANT_NAME} - {ASSISTANT_DESCRIPTION}",
    description="Sistema especializado em conflito de interesses com autenticacao Firebase",
    version="2.0.0"
)

# Configuração CORS
# Lê origens permitidas da variável de ambiente ou usa padrão
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
# Se CORS_ORIGINS não estiver definido ou for "*", permite todas as origens
if cors_origins_str == "*":
    allowed_origins = ["*"]
else:
    # Separa múltiplas origens por vírgula
    allowed_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"✅ CORS configurado com origens: {allowed_origins}")


@app.middleware("http")
async def redirect_loopback_host(request: Request, call_next):
    """Evita falha de login Firebase quando a app é aberta em 127.0.0.1."""
    hostname = request.url.hostname or ""
    if (
        request.method in {"GET", "HEAD"}
        and hostname in {"127.0.0.1", "0.0.0.0"}
        and not request.url.path.startswith("/api/")
    ):
        port = request.url.port
        target_host = PUBLIC_LOCAL_HOST if not port else f"{PUBLIC_LOCAL_HOST}:{port}"
        redirected_url = request.url.replace(netloc=target_host)
        return RedirectResponse(str(redirected_url), status_code=307)

    return await call_next(request)

def _get_agent_dependency_status() -> Dict[str, Any]:
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return {
        "gemini_api_key_configured": bool(gemini_api_key),
        "pinecone_api_key_configured": bool(os.getenv("PINECONE_API_KEY")),
        "redis_host_configured": bool(os.getenv("REDIS_HOST")),
        "redis_password_configured": bool(os.getenv("REDIS_PASSWORD")),
        "knowledge_namespace": KNOWLEDGE_NAMESPACE,
    }


def _initialize_research_agent() -> Optional[SimpleResearchAgent]:
    global research_agent, research_agent_error

    try:
        research_agent = SimpleResearchAgent()
        research_agent_error = None
        logger.info("✅ Agente de pesquisa inicializado")
    except Exception as e:
        research_agent = None
        research_agent_error = str(e)
        logger.error("❌ Erro ao inicializar agente: %s", e)

    return research_agent


def _require_research_agent() -> SimpleResearchAgent:
    agent = research_agent or _initialize_research_agent()
    if agent:
        return agent

    dependency_status = _get_agent_dependency_status()
    detail = research_agent_error or "Falha desconhecida na inicializacao do agente"
    raise HTTPException(
        status_code=500,
        detail={
            "message": "Agente nao disponivel",
            "error": detail,
            "dependency_status": dependency_status,
        },
    )


_initialize_research_agent()

# Frontend React está em web/frontend (gerenciado separadamente)

# Modelos Pydantic
class ConsultaRequest(BaseModel):
    pergunta: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ConsultaResponse(BaseModel):
    resposta_completa: str
    fontes: int
    references: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_id: str
    duracao: float
    timestamp: str
    status: str = "success"


class ConversationPdfMessagePayload(BaseModel):
    role: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationPdfRequest(BaseModel):
    conversation_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[ConversationPdfMessagePayload] = Field(default_factory=list)

# Métricas globais
metrics = {
    "total_consultas": 0,
    "consultas_sucesso": 0,
    "consultas_erro": 0,
    "tempo_medio": 0.0,
    "tempos_processamento": []
}


def _get_firestore_client():
    try:
        return get_firestore_client()
    except Exception as exc:
        logger.error("❌ Falha ao inicializar Firestore: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Configuracao do Firebase/Firestore ausente. Contate o administrador."
        ) from exc


def _sanitize_filename(value: str) -> str:
    if not value:
        return "conversa"
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return sanitized or "conversa"


def _sanitize_memory_component(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.=-]+", "_", (value or "").strip())
    return sanitized[:256]


def _build_memory_session_id(uid: str, conversation_id: str) -> str:
    user_component = _sanitize_memory_component(uid)
    conversation_component = _sanitize_memory_component(conversation_id)
    if not user_component or not conversation_component:
        raise HTTPException(status_code=400, detail="Identificador de conversa invalido.")
    return f"{user_component}:{conversation_component}"


def _normalize_request_id(value: Optional[str]) -> str:
    return value.strip() if isinstance(value, str) else ""


def _format_datetime(value: Optional[str]) -> str:
    if not value:
        return "-"
    try:
        # Normaliza timezone se vier como Z
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return value


async def _firestore_get_conversation(uid: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    client = _get_firestore_client()

    def _request() -> Optional[Dict[str, Any]]:
        snapshot = (
            client.collection("users")
            .document(uid)
            .collection("conversations")
            .document(conversation_id)
            .get()
        )

        if not snapshot.exists:
            return None

        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    try:
        return await asyncio.to_thread(_request)
    except Exception as exc:
        logger.error(
            "❌ Falha ao consultar Firestore (conversation=%s, uid=%s): %s",
            conversation_id,
            uid,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar dados da conversa no Firestore do backend",
        ) from exc


async def _firestore_get_messages(uid: str, conversation_id: str) -> List[Dict[str, Any]]:
    client = _get_firestore_client()

    def _request() -> List[Dict[str, Any]]:
        docs = (
            client.collection("users")
            .document(uid)
            .collection("conversations")
            .document(conversation_id)
            .collection("messages")
            .order_by("created_at")
            .stream()
        )

        messages: List[Dict[str, Any]] = []
        for snapshot in docs:
          data = snapshot.to_dict() or {}
          data["id"] = snapshot.id
          messages.append(data)
        return messages

    try:
        return await asyncio.to_thread(_request)
    except Exception as exc:
        logger.error(
            "❌ Falha ao consultar Firestore (messages, conversation=%s, uid=%s): %s",
            conversation_id,
            uid,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar mensagens da conversa no Firestore do backend",
        ) from exc


async def _resolve_memory_session_id(
    user: Dict[str, Any],
    conversation_id: Optional[str],
    session_id: Optional[str] = None,
) -> str:
    uid = _normalize_request_id(user.get("uid"))
    requested_conversation_id = _normalize_request_id(conversation_id) or _normalize_request_id(session_id)

    if not uid:
        raise HTTPException(status_code=401, detail="Usuario autenticado nao identificado.")

    if not requested_conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id e obrigatorio para isolar o historico.")

    conversation = await _firestore_get_conversation(uid, requested_conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada para o usuario autenticado.")

    if conversation.get("assistant_slug") != ASSISTANT_SLUG:
        raise HTTPException(status_code=403, detail="Conversa nao pertence ao assistente CORA.")

    if conversation.get("knowledge_namespace") != EXPECTED_KNOWLEDGE_NAMESPACE:
        raise HTTPException(status_code=403, detail="Conversa fora do namespace autorizado do CORA.")

    return _build_memory_session_id(uid, requested_conversation_id)


def _comeca_com_emoji(texto: str) -> bool:
    """Verifica se uma string começa com emoji"""
    if not texto or not texto.strip():
        return False
    texto_limpo = texto.strip()
    if not texto_limpo:
        return False
    primeiro_char = texto_limpo[0]
    codigo = ord(primeiro_char)
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
    for inicio, fim in emoji_ranges:
        if inicio <= codigo <= fim:
            return True
    if codigo >= 0x2000 and codigo <= 0x206F:
        return False
    if not (primeiro_char.isalnum() or primeiro_char in '.,;:!?()[]{}\'"-'):
        return True
    return False


def _formatar_markdown_inline(texto: str) -> str:
    """Converte marcadores inline seguros de Markdown em HTML."""
    safe = str(texto or "")
    safe = safe.replace("<strong>", "___TAG_STRONG_OPEN___").replace("</strong>", "___TAG_STRONG_CLOSE___")
    safe = safe.replace("<b>", "___TAG_STRONG_OPEN___").replace("</b>", "___TAG_STRONG_CLOSE___")
    safe = html.escape(safe)
    safe = safe.replace("___TAG_STRONG_OPEN___", "<strong>").replace("___TAG_STRONG_CLOSE___", "</strong>")
    safe = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", safe)
    safe = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"(^|[^*])\*([^*\n]+)\*", r"\1<em>\2</em>", safe)
    return safe


def _eh_separador_tabela_markdown(linha: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", linha or ""))


def _eh_linha_tabela_markdown(linha: str) -> bool:
    return bool(re.match(r"^\s*\|.*\|\s*$", linha or ""))


def _parse_celulas_tabela_markdown(linha: str) -> List[str]:
    return [
        celula.strip()
        for celula in linha.strip().strip("|").split("|")
    ]


def _renderizar_tabela_markdown(linhas: List[List[str]]) -> str:
    if len(linhas) < 2:
        return ""

    cabecalho, *corpo = linhas
    ths = "".join(f"<th>{_formatar_markdown_inline(celula)}</th>" for celula in cabecalho)
    trs = []
    for linha in corpo:
        tds = "".join(f"<td>{_formatar_markdown_inline(celula)}</td>" for celula in linha)
        trs.append(f"<tr>{tds}</tr>")

    return (
        '<table class="markdown-tabela">'
        f"<thead><tr>{ths}</tr></thead>"
        f"<tbody>{''.join(trs)}</tbody>"
        "</table>"
    )


def _detalhe_lista_markdown(linha: str) -> Optional[Dict[str, Any]]:
    texto = str(linha or "").strip()

    numerada = re.match(r"^(\d+)\.\s+(.+)$", texto)
    if numerada:
        return {"tipo": "ol", "inicio": int(numerada.group(1)), "conteudo": numerada.group(2)}

    letra = re.match(r"^([a-z])\)\s+(.+)$", texto, flags=re.IGNORECASE)
    if letra:
        return {
            "tipo": "ol-alpha",
            "inicio": ord(letra.group(1).lower()) - 96,
            "conteudo": letra.group(2),
        }

    marcador = re.match(r"^[-*]\s+(.+)$", texto)
    if marcador:
        return {"tipo": "ul", "inicio": None, "conteudo": marcador.group(1)}

    return None


def _texto_para_html(texto: str) -> str:
    """Renderiza Markdown simples no HTML usado pelo PDF."""
    linhas = str(texto or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    partes_html: List[str] = []
    paragrafo: List[str] = []
    itens_lista: List[str] = []
    tipo_lista: Optional[str] = None
    inicio_lista: Optional[int] = None
    em_codigo = False
    linhas_codigo: List[str] = []

    def proxima_linha_util(indice: int) -> str:
        for proximo_indice in range(indice, len(linhas)):
            candidata = linhas[proximo_indice].strip()
            if candidata:
                return candidata
        return ""

    def flush_paragrafo() -> None:
        nonlocal paragrafo
        if not paragrafo:
            return
        conteudo = " ".join(paragrafo)
        classe = ' class="emoji-paragrafo"' if _comeca_com_emoji(conteudo) else ""
        partes_html.append(f"<p{classe}>{_formatar_markdown_inline(conteudo)}</p>")
        paragrafo = []

    def flush_lista() -> None:
        nonlocal itens_lista, tipo_lista, inicio_lista
        if not itens_lista:
            return

        tag = "ul" if tipo_lista == "ul" else "ol"
        tipo_attr = ' type="a"' if tipo_lista == "ol-alpha" else ""
        inicio_attr = f' start="{inicio_lista}"' if inicio_lista and inicio_lista > 1 else ""
        itens = "".join(f"<li>{_formatar_markdown_inline(item)}</li>" for item in itens_lista)
        partes_html.append(f"<{tag}{tipo_attr}{inicio_attr}>{itens}</{tag}>")
        itens_lista = []
        tipo_lista = None
        inicio_lista = None

    def flush_codigo() -> None:
        nonlocal linhas_codigo
        partes_html.append(f"<pre><code>{html.escape(chr(10).join(linhas_codigo)).rstrip()}</code></pre>")
        linhas_codigo = []

    indice = 0
    while indice < len(linhas):
        linha = linhas[indice]
        stripped = linha.strip()

        if stripped.startswith("```"):
            flush_paragrafo()
            flush_lista()
            if em_codigo:
                flush_codigo()
                em_codigo = False
            else:
                em_codigo = True
                linhas_codigo = []
            indice += 1
            continue

        if em_codigo:
            linhas_codigo.append(linha)
            indice += 1
            continue

        if not stripped:
            flush_paragrafo()
            if tipo_lista:
                proxima_lista = _detalhe_lista_markdown(proxima_linha_util(indice + 1))
                if proxima_lista and proxima_lista["tipo"] == tipo_lista:
                    indice += 1
                    continue
            flush_lista()
            indice += 1
            continue

        if _eh_linha_tabela_markdown(stripped) and indice + 1 < len(linhas) and _eh_separador_tabela_markdown(linhas[indice + 1]):
            flush_paragrafo()
            flush_lista()
            tabela = [_parse_celulas_tabela_markdown(stripped)]
            indice += 2
            while indice < len(linhas) and _eh_linha_tabela_markdown(linhas[indice]):
                tabela.append(_parse_celulas_tabela_markdown(linhas[indice]))
                indice += 1
            partes_html.append(_renderizar_tabela_markdown(tabela))
            continue

        titulo = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if titulo:
            flush_paragrafo()
            flush_lista()
            nivel = min(len(titulo.group(1)), 3)
            partes_html.append(f"<h{nivel}>{_formatar_markdown_inline(titulo.group(2))}</h{nivel}>")
            indice += 1
            continue

        citacao = re.match(r"^>\s*(.*)$", stripped)
        if citacao:
            flush_paragrafo()
            flush_lista()
            citacoes = [citacao.group(1)]
            indice += 1
            while indice < len(linhas):
                proxima_citacao = re.match(r"^>\s*(.*)$", linhas[indice].strip())
                if not proxima_citacao:
                    break
                citacoes.append(proxima_citacao.group(1))
                indice += 1
            conteudo = "".join(f"<p>{_formatar_markdown_inline(item)}</p>" for item in citacoes if item.strip())
            partes_html.append(f"<blockquote>{conteudo}</blockquote>")
            continue

        detalhe_lista = _detalhe_lista_markdown(stripped)
        if detalhe_lista:
            flush_paragrafo()
            if tipo_lista and tipo_lista != detalhe_lista["tipo"]:
                flush_lista()
            tipo_lista = detalhe_lista["tipo"]
            if inicio_lista is None:
                inicio_lista = detalhe_lista["inicio"]
            itens_lista.append(detalhe_lista["conteudo"])
            indice += 1
            continue

        flush_lista()
        paragrafo.append(stripped)
        indice += 1

    if em_codigo:
        flush_codigo()
    flush_paragrafo()
    flush_lista()

    return "\n".join(partes_html)


def _build_conversation_html(
    conversation: Dict[str, Any],
    messages: List[Dict[str, Any]],
    user_email: Optional[str]
) -> str:
    """Constrói HTML no formato do exemplo reportlab, processando mensagens em pares"""
    exported_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    owner = html.escape(user_email or "Usuário autenticado")

    def _remover_rotulos(texto: str) -> str:
        """Remove rótulos como 'PERGUNTA DO USUÁRIO:' e 'RESPOSTA:' do texto"""
        if not texto:
            return texto
        # Remove rótulos com ou sem tags HTML, em qualquer posição
        texto = re.sub(r'(\s*<b>)?\s*PERGUNTA\s+DO\s+USUÁRIO\s*:?\s*(</b>)?\s*', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'(\s*<b>)?\s*RESPOSTA\s*:?\s*(</b>)?\s*', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'^\s*\n+\s*', '', texto)
        return texto.strip()

    # Processar mensagens em pares (pergunta-resposta)
    blocos = []  # Lista de blocos: cada bloco tem {pergunta, resposta, referencias}
    pergunta_atual = None
    resposta_atual = None
    referencias_atual = []

    for message in messages:
        role = message.get("role", "assistant")
        content_raw = message.get("content", "") or ""
        metadata = message.get("metadata") or {}
        refs = metadata.get("references") if isinstance(metadata, dict) else None

        # Remove rótulos do conteúdo
        content_limpo = _remover_rotulos(content_raw)

        if role == "user":
            # Se já havia uma pergunta pendente (sem resposta), salva o bloco incompleto
            if pergunta_atual is not None:
                blocos.append({
                    "pergunta": pergunta_atual,
                    "resposta": resposta_atual or "",
                    "referencias": referencias_atual
                })
            # Inicia novo bloco com a nova pergunta
            pergunta_atual = content_limpo
            resposta_atual = None
            referencias_atual = []
        else:  # role == "assistant"
            # Adiciona à resposta atual (pode haver múltiplas mensagens do assistente)
            if resposta_atual:
                resposta_atual += "\n\n" + content_limpo
            else:
                resposta_atual = content_limpo

            # Coleta referências
            if refs:
                for ref in refs:
                    if isinstance(ref, dict):
                        source = ref.get("source") or ref.get("title") or ref.get("name") or ""
                        score = ref.get("score", 0)
                        url = ref.get("url", "")
                        relevancia = f"{score * 100:.1f}%"
                        referencias_atual.append((source, relevancia, url))

    # Adiciona o último bloco se houver
    if pergunta_atual is not None:
        blocos.append({
            "pergunta": pergunta_atual,
            "resposta": resposta_atual or "",
            "referencias": referencias_atual
        })

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
            .resposta-texto h1,
            .resposta-texto h2,
            .resposta-texto h3 {{
                text-align: left;
                line-height: 1.25;
                margin: 0.45cm 0 0.18cm 0;
                page-break-after: avoid;
            }}
            .resposta-texto h1 {{
                font-size: 15pt;
            }}
            .resposta-texto h2 {{
                font-size: 13pt;
                border-bottom: 1px solid #d0d0d0;
                padding-bottom: 0.08cm;
            }}
            .resposta-texto h3 {{
                font-size: 12pt;
                color: #0f766e;
            }}
            .resposta-texto ul,
            .resposta-texto ol {{
                margin: 0.18cm 0 0.25cm 0.55cm;
                padding-left: 0.35cm;
                text-align: left;
            }}
            .resposta-texto li {{
                margin: 0.08cm 0;
                padding-left: 0.08cm;
            }}
            .resposta-texto blockquote {{
                margin: 0.32cm 0;
                padding: 0.18cm 0.25cm;
                border-left: 4px solid #d97706;
                background: #f1f8f7;
                border-radius: 0.08cm;
                text-align: left;
                page-break-inside: avoid;
            }}
            .resposta-texto blockquote p {{
                margin: 0.06cm 0;
            }}
            .resposta-texto pre {{
                background: #f4f4f5;
                border: 1px solid #d0d0d0;
                border-radius: 0.08cm;
                padding: 0.2cm;
                white-space: pre-wrap;
                text-align: left;
            }}
            .resposta-texto code {{
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
                font-size: 10pt;
                background: #f4f4f5;
                padding: 0.02cm 0.06cm;
                border-radius: 0.05cm;
            }}
            .resposta-texto pre code {{
                background: transparent;
                padding: 0;
            }}
            table.markdown-tabela {{
                width: 100%;
                border-collapse: collapse;
                margin: 0.28cm 0;
                page-break-inside: avoid;
                text-align: left;
                font-size: 10pt;
            }}
            table.markdown-tabela th,
            table.markdown-tabela td {{
                border: 1px solid #d0d0d0;
                padding: 0.15cm 0.18cm;
                vertical-align: top;
            }}
            table.markdown-tabela th {{
                background: #e7f3f1;
                font-weight: bold;
            }}
            table.markdown-tabela tr:nth-child(even) td {{
                background: #fafafa;
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
            .referencia-relevancia {{
                text-align: right;
                width: 4cm;
                font-size: 10pt;
            }}
            .referencia-link {{
                color: #2563eb;
                text-decoration: none;
            }}
            .referencia-link:hover {{
                text-decoration: underline;
            }}
            p {{
                margin: 0.1cm 0;
            }}
            p:empty {{
                margin: 0.3cm 0;
                height: 0.3cm;
            }}
            .meta-info {{
                font-size: 10pt;
                color: #666;
                margin-bottom: 0.3cm;
            }}
            .linha-separadora {{
                width: 100%;
                border-top: 1px solid #000;
                margin: 0.6cm 0;
                padding: 0;
            }}
            .bloco-conversa {{
                margin-bottom: 0.8cm;
            }}
        </style>
    </head>
    <body>
        <div class="titulo-principal">C.O.R.A. - CONFLITO DE INTERESSES: ORIENTACAO, REGISTRO E ANALISE</div>
        <div class="meta-info"><strong>Usuário:</strong> {owner} | <strong>Gerado em:</strong> {exported_at}</div>
        <div style="margin-bottom: 0.5cm;"></div>
    """

    # Processar cada bloco (pergunta-resposta-referências)
    for i, bloco in enumerate(blocos):
        pergunta_limpa = _limpar_texto_preservando_emoji(bloco["pergunta"])
        resposta_limpa = _limpar_texto_preservando_emoji(bloco["resposta"])

        # Remover a pergunta do início da resposta se ela estiver duplicada lá
        if pergunta_limpa and resposta_limpa:
            pergunta_original = pergunta_limpa.strip()
            resposta_original = resposta_limpa.strip()

            # Normaliza para comparação (remove espaços extras, converte para minúsculas)
            pergunta_para_comparar = re.sub(r'\s+', ' ', pergunta_original.lower())
            resposta_para_comparar = re.sub(r'\s+', ' ', resposta_original.lower())

            # Verifica se a resposta começa com a pergunta
            if resposta_para_comparar.startswith(pergunta_para_comparar):
                # Procura pela pergunta no início da resposta (case-insensitive)
                padrao = re.compile(r'^\s*' + re.escape(pergunta_original), re.IGNORECASE)
                resposta_limpa = padrao.sub('', resposta_original).strip()

                # Remove caracteres de pontuação e espaços extras que possam ter ficado
                resposta_limpa = re.sub(r'^[:.\-\s\n]+', '', resposta_limpa)

                # Verificação adicional: se ainda começa com a pergunta (normalizada), remove
                resposta_final_para_comparar = re.sub(r'\s+', ' ', resposta_limpa.lower())
                if resposta_final_para_comparar.startswith(pergunta_para_comparar):
                    # Remove baseado no tamanho aproximado
                    resposta_limpa = resposta_limpa[len(pergunta_original):].strip()
                    resposta_limpa = re.sub(r'^[:.\-\s\n]+', '', resposta_limpa)

        # Adiciona espaçamento entre blocos (exceto o primeiro)
        if i > 0:
            html_content += '<div style="margin-top: 0.8cm;"></div>'

        html_content += f"""
        <div class="bloco-conversa">
            <div class="secao-titulo">PERGUNTA DO USUÁRIO</div>
            <div class="pergunta-texto">{_texto_para_html(pergunta_limpa)}</div>

            <div class="secao-titulo">RESPOSTA</div>
            <div class="resposta-texto">{_texto_para_html(resposta_limpa)}</div>
        """

        # Adicionar referências se houver
        if bloco["referencias"]:
            html_content += '<hr class="linha-separadora" />'
            html_content += '<div class="secao-titulo">REFERÊNCIAS CONSULTADAS</div>'
            html_content += '<table class="referencias-tabela">'
            for ref, relevancia, url in bloco["referencias"]:
                ref_escaped = html.escape(ref)
                url_normalized = (url or "").strip()
                if re.match(r"^https?://", url_normalized, flags=re.IGNORECASE):
                    url_escaped = html.escape(url_normalized, quote=True)
                    ref_html = f'<a href="{url_escaped}" class="referencia-link" target="_blank">{ref_escaped}</a>'
                else:
                    ref_html = ref_escaped
                html_content += f'<tr><td class="referencia-nome">{ref_html}</td><td class="referencia-relevancia">Relevância: {relevancia}</td></tr>'
            html_content += '</table>'

        html_content += '</div>'

    html_content += """
    </body>
    </html>
    """

    return html_content


_CONTROL_CHAR_RE = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")
_BULLET_SEQ_RE = re.compile(r"[■●▪▫•◦◾◼◻\u2022\u2023\u25A0\u25AA\u25CF\u25C6]+")


def _limpar_texto_preservando_emoji(raw_text: str) -> str:
    """Limpa texto removendo apenas bullets problemáticos, preservando emojis e formatação"""
    if not raw_text:
        return ""

    plain = html.unescape(raw_text)
    plain = _CONTROL_CHAR_RE.sub("", plain)
    plain = plain.replace("\r", "")
    plain = plain.replace("\u00a0", " ")
    plain = re.sub(r"<br\s*/?>", "\n", plain, flags=re.IGNORECASE)
    plain = re.sub(r"</p>", "\n\n", plain, flags=re.IGNORECASE)
    # Remove apenas tags HTML problemáticas, preservando <b> e </b>
    plain = re.sub(r"<(?!/?b>)[^>]+>", "", plain)
    # Remove bullets problemáticos
    plain = _BULLET_SEQ_RE.sub("", plain)
    plain = plain.replace("■", "")
    plain = plain.replace("▪", "")
    plain = plain.replace("â– ", "")
    plain = plain.replace("â€¢", "")
    plain = plain.replace("Â■", "")
    plain = plain.replace("â—", "")
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    plain = plain.strip()

    return plain


def _render_pdf(html_content: str) -> bytes:
    """Gera PDF usando Puppeteer (Node.js)"""
    backend_dir = Path(__file__).parent
    project_dir = backend_dir.parent
    reportlab_dir = backend_dir / "reportlab"

    # Criar arquivo HTML temporário
    temp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    temp_html.write(html_content)
    temp_html.close()
    temp_html_path = temp_html.name

    # Criar arquivo PDF temporário
    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_pdf.close()
    temp_pdf_path = temp_pdf.name

    try:
        puppeteer_candidates = [
            Path('/app/reportlab/node_modules/puppeteer'),
            reportlab_dir / 'node_modules' / 'puppeteer',
            Path('/app/frontend/node_modules/puppeteer'),
            project_dir / 'frontend' / 'node_modules' / 'puppeteer',
            backend_dir / 'node_modules' / 'puppeteer',
        ]
        puppeteer_path = next((str(path) for path in puppeteer_candidates if path.exists()), None)
        if not puppeteer_path:
            raise ValueError(
                'Puppeteer nao encontrado. Instale as dependencias em CORA/backend/reportlab com npm install.'
            )

        executable_path = os.getenv('PUPPETEER_EXECUTABLE_PATH', '').strip()
        if not executable_path:
            browser_candidates = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Chromium.app/Contents/MacOS/Chromium',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
            ]
            executable_path = next((path for path in browser_candidates if os.path.exists(path)), '')

        # Normalizar caminhos para evitar problemas com espaços e caracteres especiais
        temp_html_path_escaped = temp_html_path.replace('\\', '\\\\').replace("'", "\\'")
        temp_pdf_path_escaped = temp_pdf_path.replace('\\', '\\\\').replace("'", "\\'")
        puppeteer_path_escaped = puppeteer_path.replace('\\', '\\\\').replace("'", "\\'")
        executable_path_escaped = executable_path.replace('\\', '\\\\').replace("'", "\\'")
        executable_path_js = (
            f"executablePath: '{executable_path_escaped}',"
            if executable_path_escaped
            else ''
        )

        puppeteer_script = f"""
        const puppeteer = require('{puppeteer_path_escaped}');

        (async () => {{
            const browser = await puppeteer.launch({{ 
                headless: true,
                {executable_path_js}
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            }});
            const page = await browser.newPage();
            await page.goto('file://{temp_html_path_escaped}', {{ waitUntil: 'networkidle0' }});
            await page.pdf({{
                path: '{temp_pdf_path_escaped}',
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
        }})();
        """

        # Salvar script Puppeteer temporário
        temp_js = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
        temp_js.write(puppeteer_script)
        temp_js.close()

        # Executar Puppeteer
        result = subprocess.run(
            ['node', temp_js.name],
            cwd=str(reportlab_dir),
            capture_output=True,
            text=True,
            check=True
        )

        # Ler PDF gerado
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        return pdf_bytes

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao executar Puppeteer: {e.stderr}")
        raise ValueError(f"Falha ao gerar PDF: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao gerar PDF: {e}")
        raise ValueError(f"Falha ao gerar PDF: {str(e)}")
    finally:
        # Limpar arquivos temporários
        try:
            os.unlink(temp_html_path)
            os.unlink(temp_pdf_path)
            os.unlink(temp_js.name)
        except:
            pass


def _normalize_pdf_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_messages: List[Dict[str, Any]] = []

    for message in messages:
        metadata = message.get("metadata")
        normalized_messages.append(
            {
                "role": str(message.get("role") or "assistant"),
                "content": str(message.get("content") or ""),
                "metadata": metadata if isinstance(metadata, dict) else {},
            }
        )

    return normalized_messages


def _build_pdf_response(
    conversation_id: Optional[str],
    title: Optional[str],
    messages: List[Dict[str, Any]],
    owner_label: Optional[str],
) -> Response:
    normalized_messages = _normalize_pdf_messages(messages)

    if not normalized_messages:
        raise HTTPException(status_code=400, detail="Conversa sem mensagens para exportar")

    conversation = {
        "id": conversation_id or "conversa",
        "title": (title or conversation_id or "Nova conversa").strip(),
    }
    html_content = _build_conversation_html(conversation, normalized_messages, owner_label)

    try:
        pdf_bytes = _render_pdf(html_content)
    except ValueError as err:
        logger.error("❌ Erro ao gerar PDF para conversa %s: %s", conversation["id"], err)
        raise HTTPException(status_code=500, detail="Falha ao gerar PDF da conversa") from err

    filename = f'cora_conversa_{_sanitize_filename(conversation["title"])}.pdf'
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    logger.info("✅ PDF da conversa %s gerado com sucesso", conversation["id"])
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)



@app.post("/api/consulta", response_model=ConsultaResponse)
async def processar_consulta(
    consulta: ConsultaRequest,
    user: dict = Depends(verify_token)
):
    """Processa consulta jurídica (requer autenticação)"""
    agent = _require_research_agent()

    start_time = time.time()
    workflow_id = f"wf_{int(time.time())}"

    try:
        logger.info(f"🔍 Processando: {consulta.pergunta}")
        logger.info(f"📋 DEBUG - session_id: {consulta.session_id}, conversation_id: {consulta.conversation_id}")

        memory_session_id = await _resolve_memory_session_id(
            user,
            consulta.conversation_id,
            consulta.session_id,
        )
        result = await agent.process_query(consulta.pergunta, memory_session_id)

        duracao = time.time() - start_time

        # DEBUG: Log completo do resultado
        logger.info(f"🔍 DEBUG - Resultado completo do agente: {result}")
        logger.info(f"🔍 DEBUG - Tipo do resultado: {type(result)}")
        logger.info(f"🔍 DEBUG - Chaves no resultado: {result.keys() if isinstance(result, dict) else 'NÃO É DICT'}")
        logger.info(f"🔍 DEBUG - Status: {result.get('status') if isinstance(result, dict) else 'N/A'}")
        logger.info(f"🔍 DEBUG - Response presente: {'response' in result if isinstance(result, dict) else False}")
        logger.info(f"🔍 DEBUG - Response value: {result.get('response', 'CAMPO NÃO ENCONTRADO')[:200] if isinstance(result, dict) else 'N/A'}")

        # Atualiza métricas
        metrics["total_consultas"] += 1
        metrics["tempos_processamento"].append(duracao)

        # Mantém apenas últimos 100 tempos
        if len(metrics["tempos_processamento"]) > 100:
            metrics["tempos_processamento"] = metrics["tempos_processamento"][-100:]

        metrics["tempo_medio"] = sum(metrics["tempos_processamento"]) / len(metrics["tempos_processamento"])

        if isinstance(result, dict) and result.get("status") == "success":
            metrics["consultas_sucesso"] += 1
        else:
            metrics["consultas_erro"] += 1
            logger.warning(f"⚠️ Status não é 'success': {result.get('status') if isinstance(result, dict) else 'resultado não é dict'}")

        logger.info(f"✅ Consulta processada em {duracao:.2f}s")

        # Se status é error, incluir mensagem de erro nos logs
        if isinstance(result, dict) and result.get("status") == "error":
            error_msg = result.get("message", "Erro desconhecido")
            error_trace = result.get("error_trace", "")
            logger.error(f"❌ Agente retornou erro: {error_msg}")
            if error_trace:
                logger.error(f"❌ DEBUG - Traceback do agente:\n{error_trace}")

        return ConsultaResponse(
            resposta_completa=result.get("response", result.get("message", "Erro na geração da resposta")) if isinstance(result, dict) else f"Erro: resultado não é dict - {type(result)}",
            fontes=result.get("sources_found", 0) if isinstance(result, dict) else 0,
            references=result.get("references", []) if isinstance(result, dict) else [],
            workflow_id=workflow_id,
            duracao=duracao,
            timestamp=datetime.now().isoformat(),
            status=result.get("status", "error") if isinstance(result, dict) else "error"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro no processamento: {e}")
        logger.error(f"❌ DEBUG - Traceback completo:")
        logger.error(traceback.format_exc())
        metrics["total_consultas"] += 1
        metrics["consultas_erro"] += 1

        return ConsultaResponse(
            resposta_completa=f"Erro no processamento: {str(e)}",
            fontes=0,
            references=[],
            workflow_id=workflow_id,
            duracao=time.time() - start_time,
            timestamp=datetime.now().isoformat(),
            status="error"
        )

@app.post("/api/conversations/pdf")
async def export_conversation_pdf_from_payload(
    payload: ConversationPdfRequest,
    user: dict = Depends(verify_token)
):
    """Exporta PDF a partir do payload recebido do frontend autenticado."""
    conversation_id = payload.conversation_id or "conversa"
    logger.info("📄 Solicitada exportação em PDF via payload para conversa %s", conversation_id)

    return await asyncio.to_thread(
        _build_pdf_response,
        payload.conversation_id,
        payload.title,
        [message.model_dump() for message in payload.messages],
        user.get("email") or user.get("name"),
    )

@app.get("/api/conversations/{conversation_id}/pdf")
async def export_conversation_pdf(
    conversation_id: str,
    user: dict = Depends(verify_token)
):
    """Exporta uma conversa específica em PDF."""
    logger.info("📄 Solicitada exportação em PDF para conversa %s", conversation_id)

    uid = user.get("uid")
    conversation = await _firestore_get_conversation(uid, conversation_id)

    if not conversation:
        logger.warning("⚠️ Conversa %s não encontrada", conversation_id)
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    messages = await _firestore_get_messages(uid, conversation_id)
    return await asyncio.to_thread(
        _build_pdf_response,
        conversation_id,
        conversation.get("title"),
        messages,
        user.get("email") or user.get("name"),
    )

@app.get("/api/metrics")
async def get_metrics():
    """Retorna métricas do sistema"""
    return {
        "total_consultas": metrics["total_consultas"],
        "consultas_sucesso": metrics["consultas_sucesso"],
        "consultas_erro": metrics["consultas_erro"],
        "tempo_medio": round(metrics["tempo_medio"], 2),
        "taxa_sucesso": round(
            (metrics["consultas_sucesso"] / max(metrics["total_consultas"], 1)) * 100, 2
        )
    }

@app.delete("/api/session/{session_id}")
async def clear_session(
    session_id: str,
    user: dict = Depends(verify_token)
):
    """Limpa histórico de uma sessão específica (requer autenticação)"""
    agent = _require_research_agent()
    if not agent.memory_manager:
        raise HTTPException(status_code=500, detail="Memória não disponível")

    try:
        scoped_session_id = await _resolve_memory_session_id(user, session_id)
        agent.memory_manager.clear_session(scoped_session_id)
        return {"message": f"Sessão {session_id} limpa com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao limpar sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    user: dict = Depends(verify_token)
):
    """Retorna estatísticas de uma sessão (requer autenticação)"""
    agent = _require_research_agent()
    if not agent.memory_manager:
        raise HTTPException(status_code=500, detail="Memória não disponível")

    try:
        scoped_session_id = await _resolve_memory_session_id(user, session_id)
        stats = agent.memory_manager.get_session_stats(scoped_session_id)
        stats["session_id"] = session_id
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter stats da sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Verifica saúde do sistema"""
    dependency_status = _get_agent_dependency_status()
    return {
        "status": "healthy" if research_agent else "unhealthy",
        "agent_available": research_agent is not None,
        "agent_error": research_agent_error,
        "dependency_status": dependency_status,
        "assistant": ASSISTANT_NAME,
        "knowledge_namespace": KNOWLEDGE_NAMESPACE,
        "auth_provider": "firebase",
        "history_store": "firestore",
        "memory_store": "redis" if research_agent and research_agent.memory_manager else "unavailable",
        "timestamp": datetime.now().isoformat()
    }

# Configuração para servir Frontend React (Build)
# Isso deve vir DEPOIS de todas as rotas da API para não conflitar
# Tenta primeiro na raiz (estratégia de persistência), depois no local original
frontend_build_candidates = [
    BACKEND_DIR / "frontend_build",
    BACKEND_DIR / "frontend" / "build",
    BACKEND_DIR.parent / "frontend" / "build",
]
frontend_build_path = next((path for path in frontend_build_candidates if path.exists()), frontend_build_candidates[0])

# DEBUG: Listar diretórios para diagnóstico
try:
    current_dir = BACKEND_DIR
    logger.info(f"📂 Diretório atual: {current_dir}")
    logger.info(f"📂 Conteúdo de {current_dir}: {[p.name for p in current_dir.iterdir()]}")
    
    frontend_dir = current_dir / "frontend"
    if frontend_dir.exists():
        logger.info(f"📂 Conteúdo de {frontend_dir}: {[p.name for p in frontend_dir.iterdir()]}")
    else:
        logger.error(f"❌ Diretório frontend não encontrado em {frontend_dir}")
except Exception as e:
    logger.error(f"❌ Erro ao listar diretórios: {e}")

if frontend_build_path.exists():
    logger.info(f"✅ Servindo frontend estático de: {frontend_build_path}")

    def _serve_index_html() -> FileResponse:
        return FileResponse(
            frontend_build_path / "index.html",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
    
    # Monta arquivos estáticos (JS, CSS, imagens)
    # Verifica se a pasta static existe dentro do build
    static_assets_path = frontend_build_path / "static"
    if static_assets_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_assets_path)), name="static")
    
    # Rota catch-all para SPA (Single Page Application)
    # IMPORTANTE: Isso captura qualquer rota não definida anteriormente
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Se a rota começar com api/, retorna 404 pois deveria ter sido capturada antes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Endpoint da API não encontrado")
            
        # Verifica se é um arquivo existente na raiz do build (ex: favicon.ico, manifest.json)
        file_path = frontend_build_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
            
        # Se não for arquivo e não for rota de API, retorna index.html (Client-side routing)
        return _serve_index_html()

else:
    logger.warning("⚠️ Diretório de build do frontend não encontrado. Servindo apenas API.")
    
    @app.get("/")
    async def root():
        """Endpoint raiz do backend (Fallback)"""
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url:
            return RedirectResponse(url=frontend_url)
        return {
            "status": "ok",
            "assistant": ASSISTANT_NAME,
            "knowledge_namespace": KNOWLEDGE_NAMESPACE,
            "message": "C.O.R.A. API online (frontend nao detectado)",
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
