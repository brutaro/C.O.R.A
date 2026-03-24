#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Módulo de Memória Redis para Follow-up
Gerencia contexto de conversação usando Redis
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError, ResponseError
import json
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def _normalize_env_scalar(value: Optional[str], key_name: str) -> Optional[str]:
    if value is None:
        return None

    normalized = str(value).strip()
    prefix = f"{key_name}="
    if normalized.startswith(prefix):
        return normalized[len(prefix):].strip()

    return normalized


def _parse_env_int(key_name: str, default: int) -> int:
    raw_value = os.getenv(key_name)
    if raw_value in {None, ""}:
        return default

    normalized = _normalize_env_scalar(raw_value, key_name)
    try:
        return int(normalized)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Variavel {key_name} invalida: esperado inteiro, recebido {raw_value!r}"
        ) from exc

class RedisMemoryManager:
    """Gerenciador de memória Redis para contexto de conversação"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Configurações Redis
        self.redis_config = {
            'host': os.getenv('REDIS_HOST'),
            'port': _parse_env_int('REDIS_PORT', 6379),
            'password': os.getenv('REDIS_PASSWORD'),
            'db': _parse_env_int('REDIS_DB', 0),
            'decode_responses': True,
            # Configurações de produção seguindo melhores práticas
            'socket_connect_timeout': 10,  # Timeout para conexão
            'socket_timeout': 5,           # Timeout para comandos
            'health_check_interval': 30,    # Health check a cada 30s
            'retry': Retry(ExponentialBackoff(), 3),  # 3 tentativas com backoff exponencial
            'retry_on_error': [ConnectionError, TimeoutError, ResponseError]
        }

        # Valida configurações
        if not all([self.redis_config['host'], self.redis_config['password']]):
            raise ValueError("Configurações Redis incompletas no .env")

        # Inicializa cliente Redis com connection pool
        try:
            self.redis_client = redis.Redis(**self.redis_config)
            # Testa conexão na inicialização
            self.redis_client.ping()
            self.logger.info("✅ Redis Memory Manager inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Redis: {e}")
            raise

        # Prefixo para chaves
        self.key_prefix = "ia-jur:session"

    def test_connection(self) -> bool:
        """Testa conexão com Redis"""
        try:
            self.redis_client.ping()
            self.logger.info("✅ Conexão Redis OK")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro conexão Redis: {e}")
            return False

    def store_conversation(self, session_id: str, user_message: str, assistant_response: str) -> None:
        """Armazena uma troca de mensagens na sessão"""
        try:
            # Cria chave única para esta mensagem
            message_id = f"{int(datetime.now().timestamp() * 1000)}"
            key = f"{self.key_prefix}:{session_id}:{message_id}"

            # Dados da mensagem
            message_data = {
                'user_message': user_message,
                'assistant_response': assistant_response,
                'timestamp': datetime.now().isoformat(),
                'message_id': message_id
            }

            # Armazena no Redis com pipeline para melhor performance
            pipe = self.redis_client.pipeline()
            pipe.hset(key, mapping=message_data)
            pipe.expire(key, 86400)  # TTL de 24 horas
            pipe.execute()

            self.logger.info(f"💾 Conversa armazenada para sessão: {session_id}")

        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"❌ Erro de conexão ao armazenar conversa: {e}")
            raise
        except ResponseError as e:
            self.logger.error(f"❌ Erro de resposta Redis ao armazenar conversa: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao armazenar conversa: {e}")
            raise

    def get_conversation_context(self, session_id: str, max_messages: int = 3) -> str:
        """Recupera contexto da conversação para follow-up"""
        try:
            messages = self.get_conversation_messages(session_id, max_messages=max_messages)
            if not messages:
                return ""

            context_parts = []
            for message in messages:
                context_parts.append(f"Usuário: {message['user_message']}")
                context_parts.append(f"Assistente: {message['assistant_response']}")

            context = "\n".join(context_parts)
            self.logger.info(f"📖 Contexto recuperado para sessão: {session_id}")
            return context

        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"❌ Erro de conexão ao recuperar contexto: {e}")
            return ""
        except ResponseError as e:
            self.logger.error(f"❌ Erro de resposta Redis ao recuperar contexto: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao recuperar contexto: {e}")
            return ""

    def get_conversation_messages(self, session_id: str, max_messages: int = 3) -> List[Dict[str, str]]:
        """Recupera mensagens estruturadas da sessão para tarefas de contextualização."""
        try:
            pattern = f"{self.key_prefix}:{session_id}:*"
            keys = []

            for key in self.redis_client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if not keys:
                return []

            keys.sort(key=lambda x: int(x.split(':')[-1]))
            recent_keys = keys[-max_messages:] if len(keys) > max_messages else keys

            pipe = self.redis_client.pipeline()
            for key in recent_keys:
                pipe.hgetall(key)
            results = pipe.execute()

            messages: List[Dict[str, str]] = []
            for index, result in enumerate(results, start=1):
                if not result:
                    continue
                messages.append({
                    'turn_index': index,
                    'user_message': result.get('user_message', ''),
                    'assistant_response': result.get('assistant_response', ''),
                    'timestamp': result.get('timestamp', ''),
                    'message_id': result.get('message_id', ''),
                })

            self.logger.info(f"📚 Mensagens estruturadas recuperadas para sessão: {session_id}")
            return messages

        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"❌ Erro de conexão ao recuperar mensagens estruturadas: {e}")
            return []
        except ResponseError as e:
            self.logger.error(f"❌ Erro de resposta Redis ao recuperar mensagens estruturadas: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao recuperar mensagens estruturadas: {e}")
            return []

    def clear_session(self, session_id: str) -> None:
        """Limpa histórico de uma sessão específica"""
        try:
            pattern = f"{self.key_prefix}:{session_id}:*"
            keys = []

            # Usa SCAN para melhor performance em vez de KEYS
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                # Usa pipeline para deletar múltiplas chaves de uma vez
                pipe = self.redis_client.pipeline()
                for key in keys:
                    pipe.delete(key)
                pipe.execute()
                self.logger.info(f"🗑️ Sessão limpa: {session_id} ({len(keys)} mensagens)")
            else:
                self.logger.info(f"📭 Sessão não encontrada: {session_id}")

        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"❌ Erro de conexão ao limpar sessão: {e}")
            raise
        except ResponseError as e:
            self.logger.error(f"❌ Erro de resposta Redis ao limpar sessão: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao limpar sessão: {e}")
            raise

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Retorna estatísticas da sessão"""
        try:
            pattern = f"{self.key_prefix}:{session_id}:*"
            keys = []

            # Usa SCAN para contar chaves
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                keys.append(key)

            return {
                'session_id': session_id,
                'message_count': len(keys),
                'last_activity': datetime.now().isoformat(),
                'status': 'active' if keys else 'empty'
            }
        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"❌ Erro de conexão ao obter stats da sessão: {e}")
            return {
                'session_id': session_id,
                'message_count': 0,
                'last_activity': None,
                'status': 'error'
            }
        except ResponseError as e:
            self.logger.error(f"❌ Erro de resposta Redis ao obter stats da sessão: {e}")
            return {
                'session_id': session_id,
                'message_count': 0,
                'last_activity': None,
                'status': 'error'
            }
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado ao obter stats da sessão: {e}")
            return {
                'session_id': session_id,
                'message_count': 0,
                'last_activity': None,
                'status': 'error'
            }

    def format_context_for_prompt(self, context: str, current_query: str) -> str:
        """Formata contexto para incluir no prompt do LLM"""
        if not context:
            return current_query

        formatted_context = f"""
CONTEXTO DA CONVERSAÇÃO ANTERIOR:
{context}

PERGUNTA ATUAL:
{current_query}

INSTRUÇÕES:
- Considere o contexto da conversa anterior
- Responda à pergunta atual considerando o histórico
- Mantenha coerência com as respostas anteriores
- Se a pergunta atual não se relaciona com o contexto, responda normalmente
"""
        return formatted_context

# Instância global do gerenciador de memória
memory_manager = None

def get_memory_manager() -> RedisMemoryManager:
    """Retorna instância singleton do gerenciador de memória"""
    global memory_manager
    if memory_manager is None:
        memory_manager = RedisMemoryManager()
    return memory_manager
