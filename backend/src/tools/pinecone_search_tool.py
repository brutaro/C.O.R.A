#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Ferramenta de Busca no Pinecone - Versão com Host Personalizado
Utiliza o host específico que está funcionando
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

# Carrega variáveis de ambiente do backend isolado do C.O.R.A.
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

@dataclass
class SearchResult:
    """Resultado de busca padronizado"""
    documento_id: str
    titulo: str
    conteudo: str
    score: float
    fonte: str
    metadata: Optional[Dict] = None

class PineconeSearchTool:
    """Ferramenta de busca otimizada para Pinecone usando host personalizado"""

    def __init__(self):
        # Configurar Pinecone com host personalizado
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if not pinecone_api_key:
            raise Exception("PINECONE_API_KEY não encontrada no .env")

        # Host personalizado que funciona
        self.custom_host = "agentes-juridicos-10b89ab.svc.aped-4627-b74a.pinecone.io"
        self.api_key = pinecone_api_key
        self.namespace = os.getenv('PINECONE_NAMESPACE', 'notas_conflito_interesse')

        # Configurações otimizadas
        self.config = {
            'top_k': int(os.getenv('PINECONE_TOP_K', 10)),
            'similarity_threshold': float(os.getenv('PINECONE_SIMILARITY_THRESHOLD', 0.3)),
            'final_result_count': int(os.getenv('PINECONE_FINAL_RESULT_COUNT', 10)),
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

        print(f"✅ PineconeSearchTool configurado com host personalizado: {self.custom_host}")

    def _query_pinecone_custom(self, text: str, top_k: int = 5) -> List[Dict]:
        """Executa busca textual nativa no índice integrado do Pinecone"""
        try:
            query_url = f"https://{self.custom_host}/records/namespaces/{self.namespace}/search"
            headers = {
                'Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'query': {
                    'top_k': top_k,
                    'inputs': {
                        'text': text
                    }
                },
                'fields': self.config['fields'],
            }

            response = requests.post(query_url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('result', {}).get('hits', [])
            else:
                print(f"❌ Erro na query: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"❌ Erro na query personalizada: {e}")
            return []

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[SearchResult]:
        """Executa busca textual nativa no Pinecone usando host personalizado"""
        print(f"🔍 Buscando: '{query}'")

        start_time = time.time()
        try:
            matches = self._query_pinecone_custom(query, top_k)
            search_time = time.time() - start_time

            print(f"  • Busca executada em {search_time:.3f}s")
            print(f"  • Hits brutos: {len(matches)}")

            filtered_matches = [
                match for match in matches
                if match.get('_score', 0) >= self.config['similarity_threshold']
            ]

            print(f"  • Após filtro (>={self.config['similarity_threshold']}): {len(filtered_matches)}")

            search_results = []
            for match in filtered_matches[:self.config['final_result_count']]:
                metadata = match.get('fields', {})

                search_result = SearchResult(
                    documento_id=match.get('_id', 'N/A'),
                    titulo=metadata.get('numero_nota_tecnica') or metadata.get('arquivo_original', 'N/A'),
                    conteudo=metadata.get('texto_original', '')[:2000] + '...' if len(metadata.get('texto_original', '')) > 2000 else metadata.get('texto_original', ''),
                    score=match.get('_score', 0),
                    fonte='pinecone_custom',
                    metadata={
                        'numero_processo': metadata.get('numero_processo'),
                        'objeto': metadata.get('objeto'),
                        'fonte_sei': metadata.get('fonte_sei'),
                        'referencia_cabecalho': metadata.get('referencia_cabecalho')
                    }
                )
                search_results.append(search_result)

            # Estatísticas finais
            if search_results:
                scores = [r.score for r in search_results]
                print(f"  • Resultados finais: {len(search_results)}")
                print(f"  • Score médio: {np.mean(scores):.4f}")
                print(f"  • Score range: {np.min(scores):.4f} - {np.max(scores):.4f}")
            else:
                print("  ⚠️ Nenhum resultado atende aos critérios de qualidade")

            return search_results

        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do índice usando host personalizado"""
        try:
            stats_url = f"https://{self.custom_host}/describe_index_stats"

            headers = {
                'Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(stats_url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

def test_custom_search_tool():
    """Função de teste da ferramenta personalizada"""
    print("🧪 TESTANDO FERRAMENTA DE BUSCA PERSONALIZADA")
    print("=" * 50)

    try:
        tool = PineconeSearchToolCustom()

        # Obtém estatísticas do índice
        print("\n📊 Estatísticas do índice:")
        stats = tool.get_index_stats()
        print(f"   - Total de vetores: {stats.get('totalVectorCount', 'N/A')}")
        print(f"   - Dimensões: {stats.get('dimension', 'N/A')}")

        # Testes de busca
        test_queries = [
            "licença prêmio servidor público",
            "progressão funcional DNIT",
            "indenização de campo"
        ]

        for query in test_queries:
            print(f"\n📋 TESTE: {query}")
            print("-" * 30)

            results = tool.search(query)

            if results:
                print(f"✅ Encontrados {len(results)} resultados de alta qualidade:")
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. Score: {result.score:.4f}")
                    print(f"     Título: {result.titulo}")
                    print(f"     Objeto: {result.metadata.get('objeto', 'N/A')[:60]}...")
            else:
                print("❌ Nenhum resultado encontrado")

        print(f"\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    test_custom_search_tool()
