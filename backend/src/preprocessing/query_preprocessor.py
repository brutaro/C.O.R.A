# -*- coding: utf-8 -*-
"""
Módulo de Pré-processamento de Queries
======================================

Este módulo implementa o pré-processamento de queries usando o glossário
técnico-jurídico para expandir termos ambíguos antes das consultas ao banco
de dados.
"""

import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys

# Adiciona o diretório src ao path para importar o glossário
sys.path.append(str(Path(__file__).parent.parent))

from glossary.technical_glossary import (
    expandir_termo_ambiguo,
    detectar_termos_ambiguos,
    expandir_query,
    obter_contexto_termo
)

# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# CLASSE PRINCIPAL DO PRÉ-PROCESSAMENTO
# =============================================================================

class QueryPreprocessor:
    """
    Classe responsável pelo pré-processamento de queries usando o glossário
    técnico-jurídico para expandir termos ambíguos.
    """

    def __init__(self):
        """Inicializa o pré-processador de queries."""
        self.logger = logging.getLogger(f"{__name__}.QueryPreprocessor")
        self.logger.info("Inicializando QueryPreprocessor")

    def preprocessar_query(self, query_original: str) -> Dict[str, any]:
        """
        Pré-processa uma query expandindo termos ambíguos.

        Args:
            query_original (str): Query original do usuário

        Returns:
            Dict[str, any]: Dicionário com informações do pré-processamento
        """
        self.logger.info(f"Pré-processando query: {query_original}")

        # Detecta termos ambíguos
        termos_ambiguos = detectar_termos_ambiguos(query_original)

        # Expande a query
        query_expandida = expandir_query(query_original)

        # Analisa o contexto geral da query
        contexto_geral = self._analisar_contexto_query(query_original, termos_ambiguos)

        # Gera termos de busca otimizados
        termos_busca = self._gerar_termos_busca(query_expandida, termos_ambiguos)

        resultado = {
            "query_original": query_original,
            "query_expandida": query_expandida,
            "termos_ambiguos_detectados": termos_ambiguos,
            "contexto_geral": contexto_geral,
            "termos_busca_otimizados": termos_busca,
            "preprocessamento_realizado": True
        }

        self.logger.info(f"Pré-processamento concluído: {len(termos_ambiguos)} termos expandidos")
        return resultado

    def _analisar_contexto_query(self, query: str, termos_ambiguos: List[str]) -> str:
        """
        Analisa o contexto geral da query baseado nos termos encontrados.

        Args:
            query (str): Query original
            termos_ambiguos (List[str]): Lista de termos ambíguos detectados

        Returns:
            str: Contexto geral da query
        """
        contextos = []

        # Analisa contexto de cada termo ambíguo
        for termo in termos_ambiguos:
            contexto = obter_contexto_termo(termo)
            if contexto and contexto not in contextos:
                contextos.append(contexto)

        # Analisa palavras-chave na query
        palavras_chave = query.lower().split()

        # Identifica contexto por palavras-chave
        if any(palavra in palavras_chave for palavra in ["precedente", "jurisprudência", "decisão", "acórdão"]):
            contextos.append("jurídico")

        if any(palavra in palavras_chave for palavra in ["técnico", "engenharia", "projeto", "obra"]):
            contextos.append("técnico")

        if any(palavra in palavras_chave for palavra in ["servidor", "cargo", "funcionário", "administração"]):
            contextos.append("administrativo")

        # Remove duplicatas e ordena
        contextos = list(set(contextos))
        contextos.sort()

        return "-".join(contextos) if contextos else "geral"

    def _gerar_termos_busca(self, query_expandida: str, termos_ambiguos: List[str]) -> List[str]:
        """
        Gera termos de busca otimizados para consulta no banco de dados.

        Args:
            query_expandida (str): Query já expandida
            termos_ambiguos (List[str]): Lista de termos ambíguos detectados

        Returns:
            List[str]: Lista de termos de busca otimizados
        """
        termos_busca = []

        # Adiciona a query expandida completa
        termos_busca.append(query_expandida)

        # Adiciona expansões individuais dos termos ambíguos
        for termo in termos_ambiguos:
            expansao = expandir_termo_ambiguo(termo)
            if expansao:
                termos_busca.append(expansao["expansao"])

        # Adiciona variações dos termos
        for termo in termos_ambiguos:
            expansao = expandir_termo_ambiguo(termo)
            if expansao and "variacoes" in expansao:
                termos_busca.extend(expansao["variacoes"])

        # Remove duplicatas e limpa
        termos_busca = list(set(termos_busca))
        termos_busca = [termo.strip() for termo in termos_busca if termo.strip()]

        return termos_busca

    def validar_preprocessamento(self, resultado: Dict[str, any]) -> bool:
        """
        Valida se o pré-processamento foi realizado corretamente.

        Args:
            resultado (Dict[str, any]): Resultado do pré-processamento

        Returns:
            bool: True se válido, False caso contrário
        """
        # Verifica se todos os campos obrigatórios estão presentes
        campos_obrigatorios = [
            "query_original",
            "query_expandida",
            "termos_ambiguos_detectados",
            "contexto_geral",
            "termos_busca_otimizados",
            "preprocessamento_realizado"
        ]

        for campo in campos_obrigatorios:
            if campo not in resultado:
                self.logger.error(f"Campo obrigatório ausente: {campo}")
                return False

        # Verifica se a query expandida é diferente da original (se houve expansão)
        if resultado["query_original"] == resultado["query_expandida"]:
            self.logger.warning("Query não foi expandida - pode não ter termos ambíguos")

        # Verifica se há termos de busca
        if not resultado["termos_busca_otimizados"]:
            self.logger.error("Nenhum termo de busca gerado")
            return False

        return True

# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def preprocessar_query_simples(query: str) -> Dict[str, any]:
    """
    Função de conveniência para pré-processar uma query.

    Args:
        query (str): Query original

    Returns:
        Dict[str, any]: Resultado do pré-processamento
    """
    preprocessor = QueryPreprocessor()
    return preprocessor.preprocessar_query(query)

# =============================================================================
# TESTES DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    # Configura logging para testes
    logging.basicConfig(level=logging.INFO)

    print("=== TESTES DO MÓDULO DE PRÉ-PROCESSAMENTO ===")

    # Cria instância do pré-processador
    preprocessor = QueryPreprocessor()

    # Teste 1: Query com termos ambíguos
    print("\n1. Teste com query contendo termos ambíguos:")
    query_teste1 = "Qual o entendimento sobre custeio de ART no DNIT?"
    resultado1 = preprocessor.preprocessar_query(query_teste1)

    print(f"   Query original: {resultado1['query_original']}")
    print(f"   Query expandida: {resultado1['query_expandida']}")
    print(f"   Termos ambíguos: {resultado1['termos_ambiguos_detectados']}")
    print(f"   Contexto: {resultado1['contexto_geral']}")
    print(f"   Termos de busca: {resultado1['termos_busca_otimizados'][:3]}...")

    # Teste 2: Query sem termos ambíguos
    print("\n2. Teste com query sem termos ambíguos:")
    query_teste2 = "Como funciona o processo de licitação?"
    resultado2 = preprocessor.preprocessar_query(query_teste2)

    print(f"   Query original: {resultado2['query_original']}")
    print(f"   Query expandida: {resultado2['query_expandida']}")
    print(f"   Termos ambíguos: {resultado2['termos_ambiguos_detectados']}")
    print(f"   Contexto: {resultado2['contexto_geral']}")

    # Teste 3: Validação
    print("\n3. Teste de validação:")
    valido1 = preprocessor.validar_preprocessamento(resultado1)
    valido2 = preprocessor.validar_preprocessamento(resultado2)

    print(f"   Resultado 1 válido: {valido1}")
    print(f"   Resultado 2 válido: {valido2}")

    print("\n=== FIM DOS TESTES ===")
