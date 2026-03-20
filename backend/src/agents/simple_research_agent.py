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
from typing import Dict, List, Any, Optional
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

        self.memory_config = {
            'max_messages': int(os.getenv('REDIS_CONTEXT_MAX_MESSAGES', 3)),
            'retrieval_user_turns': int(os.getenv('REDIS_RETRIEVAL_USER_TURNS', 2)),
        }

        # Inicializa componentes
        self._init_gemini()
        self._load_prompt_template()

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

            self.logger.info(f"✅ Gemini inicializado: {self.llm_config['model']}")

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Gemini: {e}")
            raise

    def _load_prompt_template(self):
        """Carrega template de prompt do arquivo"""
        try:
            template_path = Path(__file__).parent.parent.parent / "prompts" / "research_agent_template.txt"
            with open(template_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
            self.logger.info("✅ Template de prompt carregado")
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar template: {e}")
            # Template de fallback
            self.prompt_template = """Você é um especialista jurídico. Responda à pergunta: "{query}"

DOCUMENTOS: {context_text}

RESPOSTA:"""

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
        """Remove markdown e formata texto usando strip-markdown"""
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

        # Adiciona negrito aos títulos específicos
        text = re.sub(r'PERGUNTA DO USUÁRIO:', '<b>PERGUNTA DO USUÁRIO:</b>', text)
        text = re.sub(r'RESPOSTA:', '<b>RESPOSTA:</b>', text)

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

    async def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Processa uma consulta jurídica com contexto de memória"""
        start_time = time.time()

        try:
            self.logger.info(f"🔍 Processando consulta: {query}")

            # 1. Recupera contexto de memória se disponível
            memory_context = ""
            use_memory_context = bool(session_id and self._should_use_memory_context(query))
            if self.memory_manager and session_id and use_memory_context:
                memory_context = self.memory_manager.get_conversation_context(
                    session_id,
                    max_messages=self.memory_config['max_messages']
                )
                if memory_context:
                    self.logger.info(f"📖 Contexto de memória recuperado para sessão: {session_id}")
            elif session_id:
                self.logger.info("🧠 Memória Redis ignorada: pergunta tratada como consulta nova")

            # 2. Busca no Pinecone
            retrieval_query = self._normalize_whitespace(query)
            search_results = []

            if memory_context:
                retrieval_query = self._build_retrieval_query(query, memory_context)
                self.logger.info(f"🔎 Consulta expandida para busca: {retrieval_query[:220]}...")
                search_results = self._search_pinecone(retrieval_query)

            if not search_results:
                if memory_context:
                    self.logger.info("🔁 Fallback para busca com query bruta")
                search_results = self._search_pinecone(query)

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
            if memory_context:
                enhanced_query = self.memory_manager.format_context_for_prompt(memory_context, query)

            # 5. Gera prompt
            prompt = self.prompt_template.format(
                query=enhanced_query,
                context_text=context_text
            )

            # 6. Gera resposta com LLM
            response = self.llm_model.generate_content(prompt)
            raw_response = response.text.strip()

            # 7. Limpa resposta
            clean_response = self._clean_response(raw_response)

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
                'raw_search_results': search_results
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
