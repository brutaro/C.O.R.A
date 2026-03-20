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
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Importa gerenciador de memória Redis
sys.path.append(str(Path(__file__).parent.parent))
from memory.redis_memory import get_memory_manager

# Carrega variáveis de ambiente do backend isolado do C.O.R.A.
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

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
            'similarity_threshold': float(os.getenv('PINECONE_SIMILARITY_THRESHOLD', 0.3)),
            'final_result_count': int(os.getenv('PINECONE_FINAL_RESULT_COUNT', 10)),
            'context_excerpt_chars': int(os.getenv('PINECONE_CONTEXT_EXCERPT_CHARS', 2200)),
            'fields': [
                'numero_nota_tecnica',
                'arquivo_original',
                'texto_original',
                'numero_processo',
                'objeto',
                'fonte_sei',
                'referencia_cabecalho',
            ],
        }

        # Configurações do LLM
        self.llm_config = {
            'model': 'gemini-2.5-flash',
            'temperature': 0.2,
            'top_p': 0.7,
            'top_k': 40,
            'max_output_tokens': 8192
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
        return normalized_content[:self.pinecone_config['context_excerpt_chars']]

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

    def _merge_search_results(self, query_results: List[Tuple[str, str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
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

        return merged_results[:self.pinecone_config['final_result_count']]

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

    def _search_pinecone(self, query: str) -> List[Dict[str, Any]]:
        """Executa busca textual nativa no índice integrado do Pinecone"""
        try:
            headers = {
                'Api-Key': self.pinecone_config['api_key'],
                'Content-Type': 'application/json'
            }

            payload = {
                'query': {
                    'top_k': self.pinecone_config['top_k'],
                    'inputs': {
                        'text': query
                    }
                },
                'fields': self.pinecone_config['fields'],
            }

            url = (
                f"https://{self.pinecone_config['host']}/records/namespaces/"
                f"{self.pinecone_config['namespace']}/search"
            )
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                raise Exception(f"Erro Pinecone Search: {response.status_code} - {response.text[:300]}")

            data = response.json()
            hits = data.get('result', {}).get('hits', [])

            filtered_matches = [
                hit for hit in hits
                if hit.get('_score', 0) >= self.pinecone_config['similarity_threshold']
            ]

            final_results = filtered_matches[:self.pinecone_config['final_result_count']]

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
        """Remove markdown e normaliza o corpo da resposta gerada pelo LLM."""
        if not text:
            return text

        import strip_markdown

        # Remove tudo até "Resultado da Pesquisa" e pega só o conteúdo depois
        resultado_idx = text.find('Resultado da Pesquisa')
        if resultado_idx != -1:
            text = text[resultado_idx + len('Resultado da Pesquisa'):]

        # Remove tudo a partir de "Fontes Consultadas" ou "Principais Fontes"
        for marker in ['## Fontes Consultadas', '## Principais Fontes', 'Fontes Consultadas', 'Principais Fontes']:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]

        # Usa strip-markdown para remover toda formatação
        text = strip_markdown.strip_markdown(text)

        # Converte asteriscos em bullets
        text = re.sub(r'^\s*\*\s*', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[-+]\s*', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s*', '• ', text, flags=re.MULTILINE)

        # Remove rótulos estruturais para o backend reformatar de forma determinística
        text = re.sub(r'<\/?b>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*PERGUNTA DO USUÁRIO:\s*.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*RESPOSTA:\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)

        # Processa linha por linha para limpeza adicional
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Se a linha não está vazia
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1]:  # Se a linha está vazia e a anterior não
                cleaned_lines.append('')  # Mantém uma linha vazia

        # Junta as linhas e adiciona espaçamento duplo entre parágrafos
        text = '\n'.join(cleaned_lines)

        # Substitui quebras simples por duplas para separar parágrafos
        text = re.sub(r'\n(?!\n)', '\n\n', text)

        # Remove espaços em excesso (mais de 2 quebras de linha)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove espaços extras no início e fim
        text = text.strip()

        return text

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

            if self.memory_manager and session_id:
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
                self.logger.info(f"🔎 Busca Pinecone ({query_kind}): {retrieval_query[:220]}...")
                results = self._search_pinecone(retrieval_query)
                query_results.append((query_kind, retrieval_query, results))

            search_results = self._merge_search_results(query_results)

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

            # 6. Gera resposta com LLM
            response = self.llm_model.generate_content(prompt)
            raw_response = response.text.strip()

            # 7. Limpa resposta
            response_body = self._clean_response(raw_response)
            moderated_body = self._moderate_response_certainty(response_body, search_results)
            clean_response = self._format_final_response(query, moderated_body)

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
