# -*- coding: utf-8 -*-
"""
Módulo de Integração do Glossário Técnico-Jurídico
==================================================

Este módulo integra o glossário técnico-jurídico ao sistema principal,
permitindo que os agentes utilizem o pré-processamento e pós-processamento
de queries para melhorar a precisão das buscas.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent))

from preprocessing.query_preprocessor import QueryPreprocessor
from postprocessing.query_postprocessor import QueryPostprocessor
from glossary.technical_glossary import expandir_termo_ambiguo, detectar_termos_ambiguos

# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# CLASSE PRINCIPAL DE INTEGRAÇÃO
# =============================================================================

class GlossaryIntegration:
    """
    Classe responsável pela integração do glossário técnico-jurídico
    ao sistema principal de agentes.
    """

    def __init__(self):
        """Inicializa a integração do glossário."""
        self.logger = logging.getLogger(f"{__name__}.GlossaryIntegration")
        self.preprocessor = QueryPreprocessor()
        self.postprocessor = QueryPostprocessor()
        self.logger.info("Inicializando GlossaryIntegration")

    def processar_query_completa(self, query_original: str) -> Dict[str, Any]:
        """
        Processa uma query completa usando pré-processamento e pós-processamento.

        Args:
            query_original (str): Query original do usuário

        Returns:
            Dict[str, Any]: Resultado completo do processamento
        """
        self.logger.info(f"Processando query completa: {query_original}")

        # Pré-processamento
        resultado_preprocessamento = self.preprocessor.preprocessar_query(query_original)

        # Valida pré-processamento
        if not self.preprocessor.validar_preprocessamento(resultado_preprocessamento):
            self.logger.error("Falha na validação do pré-processamento")
            return self._criar_resultado_erro("Falha no pré-processamento")

        # Retorna resultado do pré-processamento para uso pelos agentes
        return {
            "status": "sucesso",
            "query_original": query_original,
            "query_expandida": resultado_preprocessamento["query_expandida"],
            "termos_ambiguos_detectados": resultado_preprocessamento["termos_ambiguos_detectados"],
            "contexto_geral": resultado_preprocessamento["contexto_geral"],
            "termos_busca_otimizados": resultado_preprocessamento["termos_busca_otimizados"],
            "preprocessamento_info": resultado_preprocessamento
        }

    def analisar_resultados_busca(self,
                                 query_original: str,
                                 query_expandida: str,
                                 resultados_busca: List[Dict[str, Any]],
                                 termos_ambiguos: List[str]) -> Dict[str, Any]:
        """
        Analisa os resultados de uma busca usando pós-processamento.

        Args:
            query_original (str): Query original
            query_expandida (str): Query expandida
            resultados_busca (List[Dict[str, Any]]): Resultados da busca
            termos_ambiguos (List[str]): Termos ambíguos detectados

        Returns:
            Dict[str, Any]: Análise dos resultados
        """
        self.logger.info(f"Analisando resultados para: {query_original}")

        # Pós-processamento
        resultado_posprocessamento = self.postprocessor.analisar_resultados(
            query_original, query_expandida, resultados_busca, termos_ambiguos
        )

        # Valida pós-processamento
        if not self.postprocessor.validar_posprocessamento(resultado_posprocessamento):
            self.logger.error("Falha na validação do pós-processamento")
            return self._criar_resultado_erro("Falha no pós-processamento")

        return {
            "status": "sucesso",
            "analise_resultados": resultado_posprocessamento,
            "sugestoes_melhoria": resultado_posprocessamento["sugestoes_refinamento"],
            "qualidade_busca": resultado_posprocessamento["metricas_qualidade"]["qualidade_classificacao"]
        }

    def obter_query_para_agente(self, query_original: str, tipo_agente: str) -> Dict[str, Any]:
        """
        Obtém a query processada específica para um tipo de agente.

        Args:
            query_original (str): Query original
            tipo_agente (str): Tipo do agente (triage, precedent, research, drafting)

        Returns:
            Dict[str, Any]: Query processada para o agente
        """
        self.logger.info(f"Obtendo query para agente {tipo_agente}: {query_original}")

        # Pré-processamento básico
        resultado_preprocessamento = self.preprocessor.preprocessar_query(query_original)

        # Adapta para o tipo de agente
        query_adaptada = self._adaptar_query_para_agente(
            resultado_preprocessamento, tipo_agente
        )

        return {
            "status": "sucesso",
            "query_original": query_original,
            "query_adaptada": query_adaptada,
            "tipo_agente": tipo_agente,
            "termos_ambiguos": resultado_preprocessamento["termos_ambiguos_detectados"],
            "contexto": resultado_preprocessamento["contexto_geral"]
        }

    def _adaptar_query_para_agente(self, resultado_preprocessamento: Dict[str, Any], tipo_agente: str) -> str:
        """
        Adapta a query processada para um tipo específico de agente.

        Args:
            resultado_preprocessamento (Dict[str, Any]): Resultado do pré-processamento
            tipo_agente (str): Tipo do agente

        Returns:
            str: Query adaptada para o agente
        """
        query_expandida = resultado_preprocessamento["query_expandida"]
        contexto = resultado_preprocessamento["contexto_geral"]
        termos_ambiguos = resultado_preprocessamento["termos_ambiguos_detectados"]

        # Adaptações específicas por tipo de agente
        if tipo_agente == "triage":
            # Agente de triagem - foca em identificar se há documentos relevantes
            prefixo = "Buscar documentos sobre: "
            return prefixo + query_expandida

        elif tipo_agente == "precedent":
            # Agente de precedentes - foca em jurisprudência e decisões
            prefixo = "Buscar precedentes e jurisprudência sobre: "
            return prefixo + query_expandida

        elif tipo_agente == "research":
            # Agente de pesquisa - busca ampla de informações
            prefixo = "Pesquisar informações sobre: "
            return prefixo + query_expandida

        elif tipo_agente == "drafting":
            # Agente de redação - foca em conteúdo para elaboração de documentos
            prefixo = "Buscar conteúdo para elaboração de documento sobre: "
            return prefixo + query_expandida

        else:
            # Tipo de agente não reconhecido - retorna query expandida padrão
            return query_expandida

    def _criar_resultado_erro(self, mensagem: str) -> Dict[str, Any]:
        """
        Cria um resultado de erro padronizado.

        Args:
            mensagem (str): Mensagem de erro

        Returns:
            Dict[str, Any]: Resultado de erro
        """
        return {
            "status": "erro",
            "mensagem": mensagem,
            "query_original": "",
            "query_expandida": "",
            "termos_ambiguos_detectados": [],
            "contexto_geral": "geral",
            "termos_busca_otimizados": []
        }

    def obter_estatisticas_glossario(self) -> Dict[str, Any]:
        """
        Obtém estatísticas sobre o uso do glossário.

        Returns:
            Dict[str, Any]: Estatísticas do glossário
        """
        from glossary.technical_glossary import TECHNICAL_GLOSSARY

        total_termos = len(TECHNICAL_GLOSSARY)

        # Categoriza termos por contexto
        contextos = {}
        for termo, info in TECHNICAL_GLOSSARY.items():
            contexto = info.get("contexto", "geral")
            if contexto not in contextos:
                contextos[contexto] = 0
            contextos[contexto] += 1

        return {
            "total_termos": total_termos,
            "distribuicao_contextos": contextos,
            "categorias_disponiveis": list(contextos.keys())
        }

# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def processar_query_simples(query: str) -> Dict[str, Any]:
    """
    Função de conveniência para processar uma query.

    Args:
        query (str): Query original

    Returns:
        Dict[str, Any]: Resultado do processamento
    """
    integration = GlossaryIntegration()
    return integration.processar_query_completa(query)

def obter_query_agente_simples(query: str, tipo_agente: str) -> Dict[str, Any]:
    """
    Função de conveniência para obter query para um agente específico.

    Args:
        query (str): Query original
        tipo_agente (str): Tipo do agente

    Returns:
        Dict[str, Any]: Query processada para o agente
    """
    integration = GlossaryIntegration()
    return integration.obter_query_para_agente(query, tipo_agente)

# =============================================================================
# TESTES DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    # Configura logging para testes
    logging.basicConfig(level=logging.INFO)

    print("=== TESTES DO MÓDULO DE INTEGRAÇÃO ===")

    # Cria instância da integração
    integration = GlossaryIntegration()

    # Teste 1: Processamento completo
    print("\n1. Teste de processamento completo:")
    query_teste = "Qual o entendimento sobre custeio de ART no DNIT?"
    resultado = integration.processar_query_completa(query_teste)

    print(f"   Status: {resultado['status']}")
    print(f"   Query original: {resultado['query_original']}")
    print(f"   Query expandida: {resultado['query_expandida']}")
    print(f"   Termos ambíguos: {resultado['termos_ambiguos_detectados']}")
    print(f"   Contexto: {resultado['contexto_geral']}")

    # Teste 2: Query para agente específico
    print("\n2. Teste de query para agente específico:")
    resultado_agente = integration.obter_query_para_agente(query_teste, "precedent")

    print(f"   Status: {resultado_agente['status']}")
    print(f"   Tipo agente: {resultado_agente['tipo_agente']}")
    print(f"   Query adaptada: {resultado_agente['query_adaptada']}")

    # Teste 3: Estatísticas do glossário
    print("\n3. Teste de estatísticas do glossário:")
    estatisticas = integration.obter_estatisticas_glossario()

    print(f"   Total termos: {estatisticas['total_termos']}")
    print(f"   Distribuição contextos: {estatisticas['distribuicao_contextos']}")

    print("\n=== FIM DOS TESTES ===")
