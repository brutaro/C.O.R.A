#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Agente de Pesquisa Jurídica Simplificado
Versão otimizada sem orquestrador - conexão direta ao FastAPI
"""

import os
import time
import logging
import requests
import sys
import re
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Importa gerenciador de memória Redis
sys.path.append(str(Path(__file__).parent.parent))
from formatting.chat_formatter import apply_chat_formatting
from memory.redis_memory import get_memory_manager

# Carrega variáveis de ambiente do backend isolado do C.O.R.A.
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

DEFAULT_GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')

NOTE_REFERENCE_WITH_PREFIX_RE = re.compile(
    r'\bnota(?:\s+t[eé]cnica)?\s*(?:n[ºo°.]?\s*)?'
    r'(?P<number>\d{1,4})\s*/\s*(?P<year>(?:19|20)\d{2})'
    r'(?:\s*/\s*(?P<org>[A-Za-zÇç]{2,}(?:\s*/\s*[A-Za-zÇç]{2,}){0,4}))?',
    re.IGNORECASE,
)
NOTE_REFERENCE_BARE_RE = re.compile(
    r'\b(?P<number>\d{1,4})\s*/\s*(?P<year>(?:19|20)\d{2})'
    r'\s*/\s*(?P<org>[A-Za-zÇç]{2,}(?:\s*/\s*[A-Za-zÇç]{2,}){1,4})\b',
    re.IGNORECASE,
)

class SimpleResearchAgent:
    """Agente de pesquisa jurídica simplificado e otimizado"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Configurações do Pinecone
        self.pinecone_config = {
            'api_key': os.getenv('PINECONE_API_KEY'),
            'host': 'agentes-juridicos-10b89ab.svc.aped-4627-b74a.pinecone.io',
            'namespace': os.getenv('PINECONE_NAMESPACE', 'notas_conflito_interesse'),
            'top_k': int(os.getenv('PINECONE_TOP_K', 10)),
            'specific_note_lookup_top_k': int(os.getenv('PINECONE_SPECIFIC_NOTE_LOOKUP_TOP_K', 20)),
            'specific_note_context_top_k': int(os.getenv('PINECONE_SPECIFIC_NOTE_CONTEXT_TOP_K', 15)),
            'specific_note_max_chunks': int(os.getenv('PINECONE_SPECIFIC_NOTE_MAX_CHUNKS', 0)),
            'similarity_threshold': float(os.getenv('PINECONE_SIMILARITY_THRESHOLD', 0.3)),
            'final_result_count': int(os.getenv('PINECONE_FINAL_RESULT_COUNT', 10)),
            'context_excerpt_chars': int(os.getenv('PINECONE_CONTEXT_EXCERPT_CHARS', 0)),
            'fields': [
                'numero_nota_tecnica',
                'arquivo_original',
                'texto_original',
                'document_id',
                'document_business_id',
                'chunk_id',
                'chunk_number',
                'total_chunks',
                'chunk_token_count',
                'numero_processo',
                'objeto',
                'fonte_sei',
                'referencia_cabecalho',
                'section_title',
                'section_path',
            ],
        }

        # Configurações do LLM
        self.llm_config = {
            'model': DEFAULT_GEMINI_MODEL,
            'temperature': 0.2,
            'top_p': 0.7,
            'top_k': 40,
            'max_output_tokens': 8192,
            'input_token_budget': int(os.getenv('GEMINI_INPUT_TOKEN_BUDGET', 30000)),
        }

        self.query_rewriter_config = {
            'temperature': 0.0,
            'top_p': 0.1,
            'top_k': 20,
            'max_output_tokens': 1024,
        }

        self.memory_config = {
            'max_messages': int(os.getenv('REDIS_CONTEXT_MAX_MESSAGES', 3)),
            'retrieval_user_turns': int(os.getenv('REDIS_RETRIEVAL_USER_TURNS', 2)),
        }

        # Inicializa componentes
        self._init_gemini()
        self._load_prompt_templates()

        # Inicializa gerenciador de memória Redis
        try:
            self.memory_manager = get_memory_manager()
            if self.memory_manager.test_connection():
                self.logger.info("✅ Memória Redis inicializada")
            else:
                self.logger.warning("⚠️ Memória Redis não disponível")
                self.memory_manager = None
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar memória Redis: {e}")
            self.memory_manager = None

        self.logger.info("✅ SimpleResearchAgent inicializado com sucesso")

    def _normalize_whitespace(self, text: str) -> str:
        """Normaliza espaços e quebras para facilitar parsing jurídico."""
        return re.sub(r'\s+', ' ', text or '').strip()

    def _select_context_excerpt(self, content: str, query: Optional[str] = None) -> str:
        """Seleciona um trecho simples e neutro do contexto recuperado."""
        if not content:
            return ""

        normalized_content = self._normalize_whitespace(content)
        max_chars = self.pinecone_config['context_excerpt_chars']
        if max_chars <= 0:
            return normalized_content

        return normalized_content[:max_chars]

    def _short_source_title(self, source_title: str) -> str:
        """Reduz o identificador da nota ao bloco principal antes do orgao emissor."""
        normalized_title = self._normalize_whitespace(source_title)
        if not normalized_title:
            return ""
        return normalized_title.split(' - ')[0].strip()

    def _build_reference_label(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Monta rotulos de exibicao para contexto e referencias finais."""
        full_title = self._normalize_whitespace(
            metadata.get('numero_nota_tecnica') or metadata.get('arquivo_original') or ''
        )
        short_title = self._short_source_title(full_title)
        file_name = self._normalize_whitespace(metadata.get('arquivo_original', ''))

        if short_title and file_name:
            reference_label = f"{short_title} | {file_name}"
        else:
            reference_label = short_title or file_name or full_title

        return {
            'full_title': full_title,
            'short_title': short_title or file_name or full_title,
            'reference_label': reference_label,
            'file_name': file_name,
        }

    def _should_use_memory_context(self, query: str) -> bool:
        """Usa memória apenas quando a pergunta indicar continuação da conversa."""
        normalized_query = self._normalize_whitespace(query).lower()
        if not normalized_query:
            return False

        follow_up_phrases = (
            'com base nisso',
            'sobre isso',
            'ainda sobre isso',
            'nesse caso',
            'neste caso',
            'desse caso',
            'dessa situação',
            'nessa situação',
            'neste cenário',
            'na resposta anterior',
            'na resposta acima',
            'que você mencionou',
            'que foi dito',
            'que foi informado',
            'esse entendimento',
            'essa resposta',
            'esse artigo',
            'esses incisos',
            'essas hipóteses',
        )
        if any(phrase in normalized_query for phrase in follow_up_phrases):
            return True

        follow_up_tokens = {
            'isso', 'isto', 'aquilo', 'esse', 'essa', 'esses', 'essas',
            'desse', 'dessa', 'nesse', 'nessa', 'neste', 'nesta',
            'anterior', 'acima',
        }
        query_tokens = set(re.findall(r'\b\w+\b', normalized_query))
        return bool(query_tokens & follow_up_tokens)

    def _query_changes_document_scope(self, query: str) -> bool:
        """Identifica sinais de que o usuario saiu da nota ativa para uma busca ampla."""
        normalized_query = self._normalize_whitespace(query).lower()
        if not normalized_query:
            return False

        scope_shift_patterns = (
            r'\boutras?\s+notas?\b',
            r'\bdemais\s+notas?\b',
            r'\bnotas?\s+semelhantes\b',
            r'\bnotas?\s+relacionadas\b',
            r'\bcompare\b',
            r'\bcomparar\b',
            r'\bcomparação\b',
            r'\bcomparativo\b',
            r'\bem\s+geral\b',
            r'\bno\s+geral\b',
            r'\bentendimento\s+geral\b',
            r'\bentendimento\s+do\s+dnit\b',
            r'\bo\s+dnit\s+costuma\b',
            r'\bprecedentes?\b',
            r'\btodas?\s+as\s+notas?\b',
            r'\bbase\s+inteira\b',
            r'\bcorpus\b',
        )
        return any(re.search(pattern, normalized_query) for pattern in scope_shift_patterns)

    def _should_anchor_to_active_note(
        self,
        query: str,
        active_note_target: Optional[Dict[str, Any]],
    ) -> bool:
        """Mantem follow-ups na nota ativa salvo mudança clara de escopo."""
        if not active_note_target:
            return False

        normalized_query = self._normalize_whitespace(query).lower()
        non_substantive_patterns = (
            r'^(ok|certo|beleza|perfeito|obrigad[oa]|valeu|entendi)[.!?]*$',
            r'^(bom dia|boa tarde|boa noite|olá|ola|oi)[.!?]*$',
        )
        if any(re.search(pattern, normalized_query) for pattern in non_substantive_patterns):
            return False

        if self._extract_specific_note_reference(query):
            return False

        return not self._query_changes_document_scope(query)

    def _clip_text(self, text: str, max_chars: int) -> str:
        """Limita trechos longos sem quebrar totalmente a legibilidade."""
        normalized_text = self._normalize_whitespace(text)
        if len(normalized_text) <= max_chars:
            return normalized_text
        return normalized_text[: max_chars - 3].rstrip() + "..."

    def _format_messages_for_rewriter(self, conversation_messages: List[Dict[str, Any]]) -> str:
        """Serializa o histórico recente em turnos numerados para o classificador/rewriter."""
        if not conversation_messages:
            return ""

        turn_blocks = []
        for message in conversation_messages:
            turn_index = message.get('turn_index')
            user_message = self._clip_text(message.get('user_message', ''), 900)
            assistant_response = self._clip_text(message.get('assistant_response', ''), 1400)
            turn_blocks.append(
                f"""TURNO {turn_index}
USUARIO: {user_message}
ASSISTENTE: {assistant_response}"""
            )

        return "\n\n".join(turn_blocks)

    def _format_selected_memory_context(self, conversation_messages: List[Dict[str, Any]], relevant_turns: List[int]) -> str:
        """Monta apenas o contexto realmente relevante para o prompt final."""
        if not conversation_messages:
            return ""

        if relevant_turns:
            relevant_turn_set = set(relevant_turns)
            selected_messages = [
                message for message in conversation_messages
                if message.get('turn_index') in relevant_turn_set
            ]
        else:
            selected_messages = conversation_messages[-1:]

        context_parts = []
        for message in selected_messages:
            context_parts.append(f"Usuário: {self._normalize_whitespace(message.get('user_message', ''))}")
            context_parts.append(f"Assistente: {self._clip_text(message.get('assistant_response', ''), 1800)}")

        return "\n".join(part for part in context_parts if part.strip())

    def _extract_json_payload(self, text: str) -> str:
        """Extrai o objeto JSON principal da resposta do rewriter."""
        if not text:
            return ""

        fenced_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, flags=re.DOTALL)
        if fenced_match:
            return fenced_match.group(1).strip()

        object_match = re.search(r'(\{.*\})', text, flags=re.DOTALL)
        if object_match:
            return object_match.group(1).strip()

        return text.strip()

    def _normalize_context_anchor(self, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normaliza a âncora semântica produzida pelo rewriter."""
        payload = payload or {}

        def _normalize_list(values: Any) -> List[str]:
            if not isinstance(values, list):
                return []
            normalized_values = []
            for value in values:
                normalized_value = self._normalize_whitespace(str(value))
                if normalized_value and normalized_value not in normalized_values:
                    normalized_values.append(normalized_value)
            return normalized_values

        return {
            'tema_central': self._normalize_whitespace(payload.get('tema_central', '')),
            'tipo_de_risco': self._normalize_whitespace(payload.get('tipo_de_risco', '')),
            'acao_perguntada': self._normalize_whitespace(payload.get('acao_perguntada', '')),
            'entes_relevantes': _normalize_list(payload.get('entes_relevantes', [])),
            'restricoes_relevantes': _normalize_list(payload.get('restricoes_relevantes', [])),
        }

    def _build_anchor_query(self, context_anchor: Dict[str, Any]) -> str:
        """Converte a âncora semântica em consulta auxiliar sem mencionar artigos."""
        if not context_anchor:
            return ""

        parts = [
            context_anchor.get('tema_central', ''),
            context_anchor.get('tipo_de_risco', ''),
            context_anchor.get('acao_perguntada', ''),
            " ".join(context_anchor.get('entes_relevantes', [])),
            " ".join(context_anchor.get('restricoes_relevantes', [])),
        ]
        unique_parts = []
        seen_parts = set()
        for part in parts:
            normalized_part = self._normalize_whitespace(part)
            lower_part = normalized_part.lower()
            if normalized_part and lower_part not in seen_parts:
                unique_parts.append(normalized_part)
                seen_parts.add(lower_part)

        return " ".join(unique_parts)

    def _heuristic_query_rewrite(self, query: str, conversation_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback seguro quando a reescrita estruturada falha."""
        normalized_query = self._normalize_whitespace(query)
        recent_user_queries = [
            self._normalize_whitespace(message.get('user_message', ''))
            for message in conversation_messages[-self.memory_config['retrieval_user_turns']:]
            if self._normalize_whitespace(message.get('user_message', ''))
        ]

        heuristic_follow_up = self._should_use_memory_context(query)
        rewritten_query = normalized_query
        relevant_turns: List[int] = []

        if heuristic_follow_up and recent_user_queries:
            context_seed = " ".join(recent_user_queries)
            rewritten_query = f"{context_seed}. {normalized_query}".strip()
            relevant_turns = [
                int(message.get('turn_index'))
                for message in conversation_messages[-self.memory_config['retrieval_user_turns']:]
                if message.get('turn_index') is not None
            ]

        return {
            'is_follow_up': heuristic_follow_up,
            'confidence': 0.35 if heuristic_follow_up else 0.9,
            'needs_clarification': False,
            'rewritten_query': rewritten_query,
            'relevant_turns': relevant_turns,
            'context_anchor': {
                'tema_central': normalized_query if heuristic_follow_up else '',
                'tipo_de_risco': '',
                'acao_perguntada': normalized_query,
                'entes_relevantes': [],
                'restricoes_relevantes': [],
            },
            'notes': 'heuristic_fallback',
            'source': 'heuristic_fallback',
        }

    def _parse_query_rewrite_result(self, raw_text: str, query: str, max_turns: int) -> Dict[str, Any]:
        """Normaliza a saída JSON do rewriter."""
        normalized_query = self._normalize_whitespace(query)
        default_result = {
            'is_follow_up': False,
            'confidence': 0.0,
            'needs_clarification': False,
            'rewritten_query': normalized_query,
            'relevant_turns': [],
            'context_anchor': self._normalize_context_anchor({}),
            'notes': '',
            'source': 'model',
        }

        payload_text = self._extract_json_payload(raw_text)
        if not payload_text:
            return default_result

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            self.logger.warning(f"⚠️ Falha ao parsear JSON do query rewriter: {exc}")
            return default_result

        is_follow_up = bool(payload.get('is_follow_up', False))
        needs_clarification = bool(payload.get('needs_clarification', False))

        try:
            confidence = float(payload.get('confidence', 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(confidence, 1.0))

        rewritten_query = self._normalize_whitespace(payload.get('rewritten_query', normalized_query))
        if not rewritten_query:
            rewritten_query = normalized_query

        relevant_turns = []
        for turn in payload.get('relevant_turns', []):
            try:
                turn_int = int(turn)
            except (TypeError, ValueError):
                continue
            if 1 <= turn_int <= max_turns and turn_int not in relevant_turns:
                relevant_turns.append(turn_int)

        notes = self._normalize_whitespace(payload.get('notes', ''))
        context_anchor = self._normalize_context_anchor(payload.get('context_anchor'))

        if not is_follow_up:
            rewritten_query = normalized_query
            relevant_turns = []
            context_anchor = self._normalize_context_anchor({})

        return {
            'is_follow_up': is_follow_up,
            'confidence': confidence,
            'needs_clarification': needs_clarification,
            'rewritten_query': rewritten_query,
            'relevant_turns': relevant_turns,
            'context_anchor': context_anchor,
            'notes': notes,
            'source': 'model',
        }

    def _rewrite_query_with_context(self, query: str, conversation_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classifica follow-up e reescreve a consulta em formato autônomo."""
        if not conversation_messages:
            return self._heuristic_query_rewrite(query, conversation_messages)

        history_text = self._format_messages_for_rewriter(conversation_messages)
        prompt = self.query_rewriter_template.format(
            conversation_history=history_text,
            query=self._normalize_whitespace(query),
        )

        try:
            response = self.query_rewriter_model.generate_content(prompt)
            raw_text = getattr(response, 'text', '') or ''
            result = self._parse_query_rewrite_result(raw_text, query, len(conversation_messages))

            if not result['is_follow_up'] and self._should_use_memory_context(query):
                fallback = self._heuristic_query_rewrite(query, conversation_messages)
                if fallback['is_follow_up']:
                    return fallback

            return result
        except Exception as exc:
            self.logger.warning(f"⚠️ Query rewriter falhou, usando fallback heurístico: {exc}")
            return self._heuristic_query_rewrite(query, conversation_messages)

    def _extract_recent_user_queries(self, memory_context: str, max_queries: Optional[int] = None) -> List[str]:
        """Extrai as ultimas perguntas do usuario do contexto Redis para enriquecer a busca."""
        if not memory_context:
            return []

        limit = max_queries or self.memory_config['retrieval_user_turns']
        user_queries = []

        for line in memory_context.splitlines():
            if line.startswith('Usuário:'):
                user_query = self._normalize_whitespace(line.replace('Usuário:', '', 1))
                if user_query:
                    user_queries.append(user_query)

        return user_queries[-limit:] if limit > 0 else user_queries

    def _build_retrieval_query(self, query: str, memory_context: str) -> str:
        """Monta uma consulta expandida para o Pinecone em perguntas de follow-up."""
        normalized_query = self._normalize_whitespace(query)
        if not memory_context:
            return normalized_query

        recent_user_queries = self._extract_recent_user_queries(memory_context)
        if not recent_user_queries:
            return normalized_query

        unique_parts = []
        seen_parts = set()

        for part in recent_user_queries + [normalized_query]:
            normalized_part = self._normalize_whitespace(part)
            lower_part = normalized_part.lower()
            if normalized_part and lower_part not in seen_parts:
                unique_parts.append(normalized_part)
                seen_parts.add(lower_part)

        return " Contexto anterior relevante: " + " ".join(unique_parts)

    def _clean_note_org_path(self, org_path: Optional[str]) -> str:
        if not org_path:
            return ""
        cleaned = re.sub(r'\s*/\s*', '/', org_path.strip())
        cleaned = re.sub(r'[^A-Za-zÇç/]', '', cleaned)
        return cleaned.strip('/').upper()

    def _extract_specific_note_reference(self, query: str) -> Optional[Dict[str, str]]:
        """Extrai referência explícita a uma nota técnica, sem confundir com leis/artigos."""
        if not query:
            return None

        match = NOTE_REFERENCE_WITH_PREFIX_RE.search(query) or NOTE_REFERENCE_BARE_RE.search(query)
        if not match:
            return None

        raw_number = match.group('number')
        try:
            number = str(int(raw_number))
        except (TypeError, ValueError):
            number = raw_number

        year = match.group('year')
        org_path = self._clean_note_org_path(match.groupdict().get('org'))
        base_identifier = f"{number}/{year}"
        canonical_identifier = f"{base_identifier}/{org_path}" if org_path else base_identifier

        return {
            'number': number,
            'year': year,
            'org_path': org_path,
            'base_identifier': base_identifier,
            'canonical_identifier': canonical_identifier,
        }

    def _normalize_note_identifier_text(self, value: str) -> str:
        normalized = self._normalize_whitespace(value).upper()
        return re.sub(r'\s*/\s*', '/', normalized)

    def _note_identifier_in_text(self, identifier: str, text: str) -> bool:
        normalized_identifier = self._normalize_note_identifier_text(identifier)
        normalized_text = self._normalize_note_identifier_text(text)
        if not normalized_identifier:
            return False

        return re.search(
            rf'(?<!\d){re.escape(normalized_identifier)}(?!\d)',
            normalized_text,
        ) is not None

    def _result_matches_note_reference(self, result: Dict[str, Any], note_reference: Dict[str, str]) -> bool:
        metadata = result.get('metadata') or {}
        title = (
            metadata.get('numero_nota_tecnica')
            or result.get('titulo_full')
            or result.get('titulo')
            or ''
        )
        normalized_title = self._normalize_note_identifier_text(title)
        canonical = self._normalize_note_identifier_text(note_reference['canonical_identifier'])
        base = self._normalize_note_identifier_text(note_reference['base_identifier'])

        if note_reference.get('org_path'):
            return self._note_identifier_in_text(canonical, normalized_title)

        return self._note_identifier_in_text(base, normalized_title)

    def _filter_results_by_note_reference(
        self,
        results: List[Dict[str, Any]],
        note_reference: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        return [
            result for result in results
            if self._result_matches_note_reference(result, note_reference)
        ]

    def _build_specific_note_lookup_query(self, query: str, note_reference: Dict[str, str]) -> str:
        return self._normalize_whitespace(
            f"Nota Técnica {note_reference['canonical_identifier']} {query}"
        )

    def _build_active_note_follow_up_query(self, query: str, target: Dict[str, Any]) -> str:
        note_title = (
            target.get('numero_nota_tecnica')
            or target.get('reference_label')
            or target.get('arquivo_original')
            or ''
        )
        return self._normalize_whitespace(f"Nota Técnica {note_title} {query}")

    def _build_specific_note_target(self, result: Dict[str, Any]) -> Dict[str, str]:
        metadata = result.get('metadata') or {}
        return {
            'arquivo_original': metadata.get('arquivo_original') or result.get('arquivo_original') or '',
            'numero_nota_tecnica': metadata.get('numero_nota_tecnica') or result.get('titulo_full') or '',
            'document_id': metadata.get('document_id') or '',
            'document_business_id': metadata.get('document_business_id') or '',
            'reference_label': result.get('reference_label') or result.get('titulo') or '',
        }

    def _build_specific_note_metadata_filter(self, target: Dict[str, str]) -> Optional[Dict[str, Any]]:
        if target.get('numero_nota_tecnica'):
            return {'numero_nota_tecnica': {'$eq': target['numero_nota_tecnica']}}
        if target.get('arquivo_original'):
            return {'arquivo_original': {'$eq': target['arquivo_original']}}
        return None

    def _result_matches_specific_note_target(
        self,
        result: Dict[str, Any],
        target: Optional[Dict[str, str]],
    ) -> bool:
        if not target:
            return True

        metadata = result.get('metadata') or {}
        target_document_id = target.get('document_id')
        if target_document_id and metadata.get('document_id') == target_document_id:
            return True

        target_business_id = target.get('document_business_id')
        if target_business_id and metadata.get('document_business_id') == target_business_id:
            return True

        target_file = target.get('arquivo_original')
        if target_file and (metadata.get('arquivo_original') or result.get('arquivo_original')) == target_file:
            return True

        target_title = target.get('numero_nota_tecnica')
        if target_title and (metadata.get('numero_nota_tecnica') or result.get('titulo_full')) == target_title:
            return True

        return False

    def _filter_results_by_specific_note_target(
        self,
        results: List[Dict[str, Any]],
        target: Optional[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        return [
            result for result in results
            if self._result_matches_specific_note_target(result, target)
        ]

    def _dedupe_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[str, Dict[str, Any]] = {}
        for result in results:
            key = result.get('documento_id') or (
                f"{result.get('titulo_full', result.get('titulo', ''))}|{result.get('arquivo_original', '')}"
            )
            existing = deduped.get(key)
            if not existing or result.get('score', 0.0) > existing.get('score', 0.0):
                deduped[key] = result

        return list(deduped.values())

    def _chunk_number_for_result(self, result: Dict[str, Any]) -> Optional[int]:
        metadata = result.get('metadata') or {}
        for value in (metadata.get('chunk_number'), result.get('chunk_number')):
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

        chunk_id = metadata.get('chunk_id') or result.get('documento_id') or ''
        match = re.search(r'#chunk:(\d+)', str(chunk_id))
        if match:
            return int(match.group(1))

        return None

    def _total_chunks_from_results(self, results: List[Dict[str, Any]]) -> Optional[int]:
        totals = []
        for result in results:
            metadata = result.get('metadata') or {}
            try:
                total = int(metadata.get('total_chunks') or 0)
            except (TypeError, ValueError):
                continue
            if total > 0:
                totals.append(total)

        return max(totals) if totals else None

    def _sort_results_by_chunk_order(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            results,
            key=lambda result: (
                self._chunk_number_for_result(result) is None,
                self._chunk_number_for_result(result) or 0,
                -(result.get('score') or 0.0),
            ),
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimativa conservadora e barata para telemetria e protecao de custo."""
        return max(1, math.ceil(len(text or '') / 4))

    def _build_retrieval_diagnostics(
        self,
        *,
        retrieval_mode: str,
        search_results: List[Dict[str, Any]],
        context_text: str,
        prompt: str,
        specific_note_target: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        total_chunks = self._total_chunks_from_results(search_results)
        sent_chunk_numbers = [
            chunk_number for chunk_number in (
                self._chunk_number_for_result(result) for result in search_results
            )
            if chunk_number is not None
        ]
        prompt_tokens_estimated = self._estimate_tokens(prompt)

        return {
            'retrieval_mode': retrieval_mode,
            'results_sent': len(search_results),
            'context_chars': len(context_text),
            'prompt_chars': len(prompt),
            'prompt_tokens_estimated': prompt_tokens_estimated,
            'input_token_budget': self.llm_config['input_token_budget'],
            'within_token_budget': prompt_tokens_estimated <= self.llm_config['input_token_budget'],
            'specific_note_target': specific_note_target,
            'specific_note_total_chunks': total_chunks,
            'specific_note_sent_chunks': sent_chunk_numbers,
            'specific_note_complete': (
                bool(total_chunks)
                and len(set(sent_chunk_numbers)) >= total_chunks
            ) if specific_note_target else None,
        }

    def _search_specific_note_context(
        self,
        query: str,
        target: Dict[str, str],
        metadata_filter: Optional[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        configured_top_k = self.pinecone_config['specific_note_context_top_k']
        configured_max_chunks = self.pinecone_config['specific_note_max_chunks']
        max_chunks = (
            None
            if configured_max_chunks <= 0
            else max(configured_top_k, configured_max_chunks)
        )
        initial_top_k = configured_top_k if max_chunks is None else min(configured_top_k, max_chunks)

        results = self._search_pinecone(
            query,
            top_k=initial_top_k,
            final_result_count=initial_top_k,
            metadata_filter=metadata_filter,
            apply_similarity_threshold=False,
        )
        results = self._filter_results_by_specific_note_target(results, target)
        total_chunks = self._total_chunks_from_results(results)

        desired_top_k = initial_top_k
        if total_chunks and total_chunks > len(self._dedupe_results(results)):
            desired_top_k = total_chunks if max_chunks is None else min(total_chunks, max_chunks)

        expanded = False
        if desired_top_k > initial_top_k:
            expanded_results = self._search_pinecone(
                query,
                top_k=desired_top_k,
                final_result_count=desired_top_k,
                metadata_filter=metadata_filter,
                apply_similarity_threshold=False,
            )
            expanded_results = self._filter_results_by_specific_note_target(expanded_results, target)
            if expanded_results:
                results = expanded_results
                expanded = True

        results = self._sort_results_by_chunk_order(self._dedupe_results(results))
        total_chunks = self._total_chunks_from_results(results)
        sent_chunks = [
            chunk_number for chunk_number in (
                self._chunk_number_for_result(result) for result in results
            )
            if chunk_number is not None
        ]

        diagnostics = {
            'initial_top_k': initial_top_k,
            'desired_top_k': desired_top_k,
            'expanded': expanded,
            'max_chunks': max_chunks,
            'similarity_threshold_applied': False,
            'total_chunks': total_chunks,
            'sent_chunks': sent_chunks,
            'complete': bool(total_chunks) and len(set(sent_chunks)) >= total_chunks,
        }

        return results, diagnostics

    def _merge_search_results(
        self,
        query_results: List[Tuple[str, str, List[Dict[str, Any]]]],
        result_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Combina resultados da query original e da query reescrita."""
        merged: Dict[str, Dict[str, Any]] = {}

        for query_kind, query_text, results in query_results:
            for rank, result in enumerate(results, start=1):
                merge_key = result.get('documento_id') or (
                    f"{result.get('titulo_full', result.get('titulo', ''))}|{result.get('arquivo_original', '')}"
                )
                existing = merged.get(merge_key)
                reciprocal_rank = 1.0 / (60 + rank)

                if not existing:
                    result_copy = dict(result)
                    result_copy['score'] = result.get('score', 0.0)
                    result_copy['retrieval_sources'] = [query_kind]
                    result_copy['matched_queries'] = [self._clip_text(query_text, 220)]
                    result_copy['merge_score'] = result_copy['score'] + reciprocal_rank
                    merged[merge_key] = result_copy
                    continue

                existing['score'] = max(existing.get('score', 0.0), result.get('score', 0.0))
                if query_kind not in existing['retrieval_sources']:
                    existing['retrieval_sources'].append(query_kind)
                clipped_query = self._clip_text(query_text, 220)
                if clipped_query not in existing['matched_queries']:
                    existing['matched_queries'].append(clipped_query)
                existing['merge_score'] = existing.get('merge_score', existing['score']) + reciprocal_rank + 0.02

        merged_results = sorted(
            merged.values(),
            key=lambda item: (item.get('merge_score', item.get('score', 0.0)), item.get('score', 0.0)),
            reverse=True,
        )

        limit = result_limit or self.pinecone_config['final_result_count']
        return merged_results[:limit]

    def _init_gemini(self):
        """Inicializa Gemini apenas para geração de resposta"""
        try:
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise Exception("GEMINI_API_KEY não encontrada")

            self.gemini_api_key = api_key
            genai.configure(api_key=api_key)

            # Configuração do LLM
            generation_config = {
                "temperature": self.llm_config['temperature'],
                "top_p": self.llm_config['top_p'],
                "top_k": self.llm_config['top_k'],
                "max_output_tokens": self.llm_config['max_output_tokens']
            }

            self.llm_model = genai.GenerativeModel(
                self.llm_config['model'],
                generation_config=generation_config
            )

            query_rewriter_generation_config = {
                "temperature": self.query_rewriter_config['temperature'],
                "top_p": self.query_rewriter_config['top_p'],
                "top_k": self.query_rewriter_config['top_k'],
                "max_output_tokens": self.query_rewriter_config['max_output_tokens'],
            }

            self.query_rewriter_model = genai.GenerativeModel(
                self.llm_config['model'],
                generation_config=query_rewriter_generation_config
            )

            self.logger.info(f"✅ Gemini inicializado: {self.llm_config['model']}")

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Gemini: {e}")
            raise

    def _load_prompt_templates(self):
        """Carrega templates de prompt do arquivo"""
        try:
            prompts_dir = Path(__file__).parent.parent.parent / "prompts"

            with open(prompts_dir / "research_agent_template.txt", 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()

            with open(prompts_dir / "query_rewriter_template.txt", 'r', encoding='utf-8') as f:
                self.query_rewriter_template = f.read()

            self.logger.info("✅ Templates de prompt carregados")
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar templates: {e}")
            self.prompt_template = """Você é um especialista jurídico. Responda à pergunta: "{query}"

DOCUMENTOS: {context_text}

RESPOSTA:"""
            self.query_rewriter_template = """Retorne apenas JSON com os campos is_follow_up, confidence, needs_clarification, rewritten_query, relevant_turns, context_anchor e notes.

HISTÓRICO RECENTE:
{conversation_history}

PERGUNTA ATUAL:
{query}
"""

    def _search_pinecone(
        self,
        query: str,
        top_k: Optional[int] = None,
        final_result_count: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        apply_similarity_threshold: bool = True,
    ) -> List[Dict[str, Any]]:
        """Executa busca textual nativa no índice integrado do Pinecone"""
        try:
            headers = {
                'Api-Key': self.pinecone_config['api_key'],
                'Content-Type': 'application/json'
            }

            payload = {
                'query': {
                    'top_k': top_k or self.pinecone_config['top_k'],
                    'inputs': {
                        'text': query
                    }
                },
                'fields': self.pinecone_config['fields'],
            }
            if metadata_filter:
                payload['query']['filter'] = metadata_filter

            url = (
                f"https://{self.pinecone_config['host']}/records/namespaces/"
                f"{self.pinecone_config['namespace']}/search"
            )
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                if metadata_filter:
                    self.logger.warning(
                        "Filtro Pinecone rejeitado (%s). Repetindo busca sem filtro e aplicando defesa local.",
                        response.status_code,
                    )
                    payload['query'].pop('filter', None)
                    response = requests.post(url, json=payload, headers=headers, timeout=30)

                if response.status_code != 200:
                    raise Exception(f"Erro Pinecone Search: {response.status_code} - {response.text[:300]}")

            data = response.json()
            hits = data.get('result', {}).get('hits', [])

            if apply_similarity_threshold:
                filtered_matches = [
                    hit for hit in hits
                    if hit.get('_score', 0) >= self.pinecone_config['similarity_threshold']
                ]
            else:
                filtered_matches = hits

            result_limit = final_result_count or self.pinecone_config['final_result_count']
            final_results = filtered_matches[:result_limit]

            formatted_results = []
            for hit in final_results:
                metadata = hit.get('fields', {})
                labels = self._build_reference_label(metadata)
                formatted_results.append({
                    'documento_id': hit.get('_id', ''),
                    'titulo': labels['short_title'],
                    'titulo_full': labels['full_title'],
                    'reference_label': labels['reference_label'],
                    'arquivo_original': labels['file_name'],
                    'conteudo': metadata.get('texto_original', ''),
                    'chunk_number': metadata.get('chunk_number'),
                    'total_chunks': metadata.get('total_chunks'),
                    'score': hit.get('_score', 0),
                    'metadata': metadata
                })

            if formatted_results:
                first_result = formatted_results[0]
                self.logger.info(f"Primeiro resultado - Título: {first_result['titulo'][:50]}...")
                self.logger.info(f"Primeiro resultado - Conteúdo: {len(first_result['conteudo'])} chars")

            return formatted_results

        except Exception as e:
            self.logger.error(f"Erro na busca Pinecone: {e}")
            return []

    def _format_context(self, search_results: List[Dict[str, Any]], query: Optional[str] = None) -> str:
        """Formata resultados para o contexto do LLM"""
        context_parts = []

        for result in search_results:
            excerpt = self._select_context_excerpt(result.get('conteudo', ''))
            context_parts.append(f"""
{result['titulo']}:
Conteúdo: {excerpt}
Score: {result['score']:.3f}
""")

        return '\n'.join(context_parts)

    def _clean_response(self, text: str) -> str:
        """Remove apenas envelopes indesejados e preserva o Markdown da LLM."""
        if not text:
            return text

        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove tudo até "Resultado da Pesquisa" e pega só o conteúdo depois
        resultado_idx = text.find('Resultado da Pesquisa')
        if resultado_idx != -1:
            text = text[resultado_idx + len('Resultado da Pesquisa'):]

        # Remove tudo a partir de "Fontes Consultadas" ou "Principais Fontes"
        sources_match = re.search(
            r'(?im)^\s*(?:#{1,3}\s*)?(?:Fontes Consultadas|Principais Fontes)\b.*$',
            text,
        )
        if sources_match:
            text = text[:sources_match.start()]

        # Remove rótulos estruturais, preservando listas, tabelas, citações e blocos Markdown.
        text = re.sub(
            r'(?im)^\s*(?:<b>)?\s*PERGUNTA DO USU[ÁA]RIO:\s*(?:</b>)?.*$',
            '',
            text,
        )
        text = re.sub(
            r'(?im)^\s*(?:<b>)?\s*RESPOSTA:\s*(?:</b>)?\s*',
            '',
            text,
        )

        # Limpa apenas excesso de espaços finais e linhas vazias, sem achatar Markdown.
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]

        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _context_supports_strong_claims(self, search_results: List[Dict[str, Any]]) -> bool:
        """Verifica se o contexto traz suporte textual para afirmações categóricas."""
        combined_content = self._normalize_whitespace(
            " ".join(result.get('conteudo', '') for result in search_results)
        ).lower()

        strong_support_markers = (
            'é suficiente',
            'ser suficiente',
            'basta',
            'afasta o risco',
            'elimina o risco',
            'restrição absoluta',
        )
        return any(marker in combined_content for marker in strong_support_markers)

    def _moderate_response_certainty(self, response_body: str, search_results: List[Dict[str, Any]]) -> str:
        """Suaviza conclusões absolutas quando o contexto só sustenta mitigação ou condicionamento."""
        if not response_body:
            return response_body

        if self._context_supports_strong_claims(search_results):
            return response_body

        softened_body = response_body
        replacements = [
            (r'(?i)\bcostuma ser suficiente\b', 'costuma ser medida mitigatória relevante, mas a suficiência depende do caso concreto'),
            (r'(?i)\bé suficiente\b', 'pode ser suficiente, a depender do caso concreto'),
            (r'(?i)\bbasta\b', 'pode bastar em alguns casos'),
            (r'(?i)\bresolve\b', 'pode contribuir para mitigar'),
            (r'(?i)\bafasta o risco\b', 'pode mitigar o risco'),
            (r'(?i)\belimina o risco\b', 'pode reduzir o risco'),
        ]

        for pattern, replacement in replacements:
            softened_body = re.sub(pattern, replacement, softened_body)

        if softened_body != response_body:
            softened_body = re.sub(
                r'^\s*Sim,\s+',
                'Os documentos indicam que ',
                softened_body,
                count=1,
                flags=re.IGNORECASE,
            )

        return softened_body.strip()

    def _format_final_response(self, query: str, response_body: str) -> str:
        """Monta a resposta final em formato determinístico para o frontend."""
        normalized_query = self._normalize_whitespace(query)
        normalized_body = (response_body or '').strip()

        return (
            f"<b>PERGUNTA DO USUÁRIO:</b> {normalized_query}\n\n"
            f"<b>RESPOSTA:</b>\n\n"
            f"{normalized_body}"
        ).strip()

    async def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Processa uma consulta jurídica com contexto de memória"""
        start_time = time.time()

        try:
            self.logger.info(f"🔍 Processando consulta: {query}")

            # 1. Recupera histórico estruturado e decide se há follow-up
            conversation_messages: List[Dict[str, Any]] = []
            query_rewrite = {
                'is_follow_up': False,
                'confidence': 0.0,
                'needs_clarification': False,
                'rewritten_query': self._normalize_whitespace(query),
                'relevant_turns': [],
                'context_anchor': self._normalize_context_anchor({}),
                'notes': '',
                'source': 'default',
            }
            selected_memory_context = ""
            specific_note_reference = self._extract_specific_note_reference(query)
            specific_note_candidates: List[Dict[str, Any]] = []
            specific_note_target: Optional[Dict[str, str]] = None
            specific_note_filter: Optional[Dict[str, Any]] = None
            retrieval_mode = 'pergunta_ampla'
            specific_note_retrieval_diagnostics: Dict[str, Any] = {}
            active_note_target: Optional[Dict[str, Any]] = None

            if specific_note_reference:
                self.logger.info(
                    "🎯 Consulta com nota específica detectada: %s",
                    specific_note_reference['canonical_identifier'],
                )
            elif self.memory_manager and session_id:
                conversation_messages = self.memory_manager.get_conversation_messages(
                    session_id,
                    max_messages=self.memory_config['max_messages']
                )
                if conversation_messages:
                    query_rewrite = self._rewrite_query_with_context(query, conversation_messages)
                    self.logger.info(
                        "🧠 Query rewrite | follow_up=%s confidence=%.2f turns=%s source=%s rewritten=%s",
                        query_rewrite['is_follow_up'],
                        query_rewrite['confidence'],
                        query_rewrite['relevant_turns'],
                        query_rewrite['source'],
                        query_rewrite['rewritten_query'][:240],
                    )

                    if query_rewrite['is_follow_up'] and not query_rewrite.get('needs_clarification'):
                        selected_memory_context = self._format_selected_memory_context(
                            conversation_messages,
                            query_rewrite.get('relevant_turns', [])
                        )
                else:
                    self.logger.info("📭 Sessão sem histórico Redis útil para contextualização")

                if hasattr(self.memory_manager, 'get_active_note_target'):
                    active_note_target = self.memory_manager.get_active_note_target(session_id)
                    if active_note_target:
                        self.logger.info(
                            "🎯 Nota ativa recuperada: titulo=%s arquivo=%s",
                            active_note_target.get('numero_nota_tecnica') or 'indisponivel',
                            active_note_target.get('arquivo_original') or 'indisponivel',
                        )

            if (
                not specific_note_reference
                and self._should_anchor_to_active_note(query, active_note_target)
            ):
                retrieval_mode = 'same_note_follow_up'
                specific_note_target = active_note_target
                specific_note_filter = self._build_specific_note_metadata_filter(specific_note_target)
                self.logger.info(
                    "🎯 Follow-up ancorado na nota ativa: titulo=%s arquivo=%s",
                    specific_note_target.get('numero_nota_tecnica') or 'indisponivel',
                    specific_note_target.get('arquivo_original') or 'indisponivel',
                )

            if specific_note_reference:
                retrieval_mode = 'nota_especifica'
                lookup_query = self._build_specific_note_lookup_query(query, specific_note_reference)
                lookup_results = self._search_pinecone(
                    lookup_query,
                    top_k=self.pinecone_config['specific_note_lookup_top_k'],
                    final_result_count=self.pinecone_config['specific_note_lookup_top_k'],
                )
                specific_note_candidates = self._filter_results_by_note_reference(
                    lookup_results,
                    specific_note_reference,
                )

                if not specific_note_candidates:
                    return {
                        'status': 'no_results',
                        'message': (
                            f"Não encontrei a nota {specific_note_reference['canonical_identifier']} "
                            f"no namespace {self.pinecone_config['namespace']}."
                        ),
                        'sources_found': 0,
                        'processing_time': time.time() - start_time
                    }

                specific_note_target = self._build_specific_note_target(specific_note_candidates[0])
                specific_note_filter = self._build_specific_note_metadata_filter(specific_note_target)
                self.logger.info(
                    "🎯 Nota específica resolvida: titulo=%s arquivo=%s",
                    specific_note_target.get('numero_nota_tecnica') or specific_note_reference['canonical_identifier'],
                    specific_note_target.get('arquivo_original') or 'indisponivel',
                )

            # 2. Busca no Pinecone com query original e, quando aplicável, query reescrita
            retrieval_queries: List[Tuple[str, str]] = [('original', self._normalize_whitespace(query))]

            rewritten_query = query_rewrite.get('rewritten_query', self._normalize_whitespace(query))
            if (
                query_rewrite.get('is_follow_up')
                and not query_rewrite.get('needs_clarification')
                and rewritten_query
                and rewritten_query.lower() != self._normalize_whitespace(query).lower()
            ):
                retrieval_queries.append(('rewritten', rewritten_query))

            anchor_query = self._build_anchor_query(query_rewrite.get('context_anchor', {}))
            if (
                query_rewrite.get('is_follow_up')
                and not query_rewrite.get('needs_clarification')
                and anchor_query
                and all(anchor_query.lower() != existing_query.lower() for _, existing_query in retrieval_queries)
            ):
                retrieval_queries.append(('semantic_anchor', anchor_query))

            query_results: List[Tuple[str, str, List[Dict[str, Any]]]] = []
            for query_kind, retrieval_query in retrieval_queries:
                effective_retrieval_query = retrieval_query
                if retrieval_mode == 'same_note_follow_up' and specific_note_target:
                    effective_retrieval_query = self._build_active_note_follow_up_query(
                        retrieval_query,
                        specific_note_target,
                    )

                self.logger.info(f"🔎 Busca Pinecone ({query_kind}): {effective_retrieval_query[:220]}...")
                if specific_note_target:
                    results, specific_note_retrieval_diagnostics = self._search_specific_note_context(
                        effective_retrieval_query,
                        specific_note_target,
                        specific_note_filter,
                    )
                else:
                    results = self._search_pinecone(
                        effective_retrieval_query,
                        metadata_filter=specific_note_filter,
                    )
                query_results.append((query_kind, effective_retrieval_query, results))

            result_limit = (
                specific_note_retrieval_diagnostics.get('desired_top_k')
                if specific_note_target
                else None
            )
            search_results = self._merge_search_results(query_results, result_limit=result_limit)
            if specific_note_target:
                search_results = self._sort_results_by_chunk_order(
                    self._filter_results_by_specific_note_target(search_results, specific_note_target)
                )

            if (
                not search_results
                and query_rewrite.get('is_follow_up')
                and selected_memory_context
            ):
                legacy_query = self._build_retrieval_query(query, selected_memory_context)
                self.logger.info(f"🔁 Fallback legado de recuperação contextual: {legacy_query[:220]}...")
                legacy_results = self._search_pinecone(legacy_query)
                search_results = self._merge_search_results(
                    query_results + [('legacy_context', legacy_query, legacy_results)]
                )

            if specific_note_target and not search_results and specific_note_candidates:
                self.logger.info("🎯 Usando candidatos da etapa de resolução da nota específica como fallback")
                search_results = specific_note_candidates[:self.pinecone_config['specific_note_context_top_k']]

            if not search_results:
                return {
                    'status': 'no_results',
                    'message': 'Nenhum documento relevante encontrado',
                    'sources_found': 0,
                    'processing_time': time.time() - start_time
                }

            # 3. Formata contexto
            context_text = self._format_context(search_results, query)

            # 4. Prepara query com contexto de memória
            enhanced_query = query
            if selected_memory_context:
                enhanced_query = self.memory_manager.format_context_for_prompt(selected_memory_context, query)

            # 5. Gera prompt
            prompt = self.prompt_template.format(
                query=enhanced_query,
                context_text=context_text
            )
            retrieval_diagnostics = self._build_retrieval_diagnostics(
                retrieval_mode=retrieval_mode,
                search_results=search_results,
                context_text=context_text,
                prompt=prompt,
                specific_note_target=specific_note_target,
            )
            if specific_note_retrieval_diagnostics:
                retrieval_diagnostics['specific_note_retrieval'] = specific_note_retrieval_diagnostics

            self.logger.info(
                "📏 Recuperação CORA | mode=%s results=%s context_chars=%s prompt_tokens_est=%s budget=%s within_budget=%s",
                retrieval_diagnostics['retrieval_mode'],
                retrieval_diagnostics['results_sent'],
                retrieval_diagnostics['context_chars'],
                retrieval_diagnostics['prompt_tokens_estimated'],
                retrieval_diagnostics['input_token_budget'],
                retrieval_diagnostics['within_token_budget'],
            )
            if specific_note_target:
                self.logger.info(
                    "🎯 Nota específica | complete=%s chunks=%s/%s expanded=%s",
                    retrieval_diagnostics.get('specific_note_complete'),
                    len(set(retrieval_diagnostics.get('specific_note_sent_chunks') or [])),
                    retrieval_diagnostics.get('specific_note_total_chunks') or 'desconhecido',
                    specific_note_retrieval_diagnostics.get('expanded'),
                )

            # 6. Gera resposta com LLM
            response = self.llm_model.generate_content(prompt)
            raw_response = response.text.strip()

            # 7. Limpa resposta
            response_body = self._clean_response(raw_response)
            moderated_body = self._moderate_response_certainty(response_body, search_results)
            formatted_body = apply_chat_formatting(moderated_body, logger=self.logger)
            clean_response = self._format_final_response(query, formatted_body)

            # 8. Extrai referências únicas
            references = []
            seen_sources = set()

            for result in search_results:
                source = result.get('reference_label') or result['titulo'] or result['documento_id']
                dedupe_key = (
                    result.get('titulo_full') or result['titulo'] or result['documento_id'],
                    result.get('arquivo_original', '')
                )
                if dedupe_key not in seen_sources:
                    # Extrai metadados
                    metadata = result.get('metadata', {})
                    
                    ref_data = {
                        'source': source,
                        'source_short': result.get('titulo') or result['documento_id'],
                        'source_full': result.get('titulo_full') or result.get('titulo') or result['documento_id'],
                        'source_file': result.get('arquivo_original', ''),
                        'score': result['score'],
                        'namespace': self.pinecone_config['namespace'],
                    }
                    
                    # Adiciona URL se existir
                    if metadata.get('url'):
                        ref_data['url'] = metadata['url']
                        
                    references.append(ref_data)
                    seen_sources.add(dedupe_key)

            # Ordena por score
            references.sort(key=lambda x: x['score'], reverse=True)

            processing_time = time.time() - start_time

            # 7. Armazena conversa na memória Redis se disponível
            if self.memory_manager and session_id:
                try:
                    self.memory_manager.store_conversation(
                        session_id=session_id,
                        user_message=query,
                        assistant_response=clean_response
                    )
                    if (
                        specific_note_target
                        and retrieval_mode in {'nota_especifica', 'same_note_follow_up'}
                        and hasattr(self.memory_manager, 'store_active_note_target')
                    ):
                        self.memory_manager.store_active_note_target(session_id, specific_note_target)
                    elif (
                        retrieval_mode == 'pergunta_ampla'
                        and active_note_target
                        and hasattr(self.memory_manager, 'clear_active_note_target')
                    ):
                        self.memory_manager.clear_active_note_target(session_id)
                    self.logger.info(f"💾 Conversa armazenada para sessão: {session_id}")
                except Exception as e:
                    self.logger.error(f"❌ Erro ao armazenar conversa: {e}")

            return {
                'status': 'success',
                'response': clean_response,
                'sources_found': len(search_results),
                'references': references,
                'processing_time': processing_time,
                'raw_search_results': search_results,
                'query_rewrite': query_rewrite,
                'retrieval_diagnostics': retrieval_diagnostics,
                'retrieval_queries': [
                    {'kind': query_kind, 'query': retrieval_query}
                    for query_kind, retrieval_query in retrieval_queries
                ],
            }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.logger.error(f"❌ Erro no processamento: {e}")
            self.logger.error(f"❌ DEBUG - Traceback completo:")
            self.logger.error(error_trace)
            return {
                'status': 'error',
                'message': str(e),
                'error_trace': error_trace,
                'sources_found': 0,
                'processing_time': time.time() - start_time
            }
