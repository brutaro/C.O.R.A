# -*- coding: utf-8 -*-
"""
Módulo de Pós-processamento de Queries
======================================

Este módulo implementa o pós-processamento de queries para validar se a
expansão de termos resolveu problemas de homonímia e se os resultados
são relevantes.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import sys

# Adiciona o diretório src ao path para importar o glossário
sys.path.append(str(Path(__file__).parent.parent))

from glossary.technical_glossary import expandir_termo_ambiguo, obter_contexto_termo

# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# CLASSE PRINCIPAL DO PÓS-PROCESSAMENTO
# =============================================================================

class QueryPostprocessor:
    """
    Classe responsável pelo pós-processamento de queries para validar
    resultados e detectar se problemas de homonímia foram resolvidos.
    """

    def __init__(self):
        """Inicializa o pós-processador de queries."""
        self.logger = logging.getLogger(f"{__name__}.QueryPostprocessor")
        self.logger.info("Inicializando QueryPostprocessor")

    def analisar_resultados(self,
                           query_original: str,
                           query_expandida: str,
                           resultados_busca: List[Dict[str, Any]],
                           termos_ambiguos_detectados: List[str]) -> Dict[str, Any]:
        """
        Analisa os resultados da busca para validar se a expansão foi eficaz.

        Args:
            query_original (str): Query original do usuário
            query_expandida (str): Query expandida pelo pré-processamento
            resultados_busca (List[Dict[str, Any]]): Resultados da busca no banco
            termos_ambiguos_detectados (List[str]): Termos ambíguos detectados

        Returns:
            Dict[str, Any]: Análise dos resultados
        """
        self.logger.info(f"Analisando resultados para query: {query_original}")

        # Analisa relevância dos resultados
        relevancia = self._analisar_relevancia_resultados(
            query_original, query_expandida, resultados_busca
        )

        # Detecta se problemas de homonímia foram resolvidos
        homonímia_resolvida = self._verificar_homonímia_resolvida(
            query_original, query_expandida, resultados_busca, termos_ambiguos_detectados
        )

        # Sugere refinamentos se necessário
        sugestoes_refinamento = self._sugerir_refinamentos(
            query_original, resultados_busca, relevancia, homonímia_resolvida
        )

        # Calcula métricas de qualidade
        metricas_qualidade = self._calcular_metricas_qualidade(
            resultados_busca, relevancia, homonímia_resolvida
        )

        resultado = {
            "query_original": query_original,
            "query_expandida": query_expandida,
            "termos_ambiguos_detectados": termos_ambiguos_detectados,
            "total_resultados": len(resultados_busca),
            "relevancia_resultados": relevancia,
            "homonímia_resolvida": homonímia_resolvida,
            "sugestoes_refinamento": sugestoes_refinamento,
            "metricas_qualidade": metricas_qualidade,
            "posprocessamento_realizado": True
        }

        self.logger.info(f"Pós-processamento concluído: {len(resultados_busca)} resultados analisados")
        return resultado

    def _analisar_relevancia_resultados(self,
                                      query_original: str,
                                      query_expandida: str,
                                      resultados_busca: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa a relevância dos resultados encontrados.

        Args:
            query_original (str): Query original
            query_expandida (str): Query expandida
            resultados_busca (List[Dict[str, Any]]): Resultados da busca

        Returns:
            Dict[str, Any]: Análise de relevância
        """
        if not resultados_busca:
            return {
                "relevancia_geral": "baixa",
                "resultados_relevantes": 0,
                "resultados_parcialmente_relevantes": 0,
                "resultados_irrelevantes": 0,
                "score_medio": 0.0
            }

        # Analisa scores dos resultados
        scores = [resultado.get('score', 0.0) for resultado in resultados_busca]
        score_medio = sum(scores) / len(scores) if scores else 0.0

        # Classifica relevância baseado em scores
        resultados_relevantes = len([s for s in scores if s >= 0.7])
        resultados_parcialmente_relevantes = len([s for s in scores if 0.5 <= s < 0.7])
        resultados_irrelevantes = len([s for s in scores if s < 0.5])

        # Determina relevância geral
        if resultados_relevantes > len(resultados_busca) * 0.6:
            relevancia_geral = "alta"
        elif resultados_relevantes > len(resultados_busca) * 0.3:
            relevancia_geral = "média"
        else:
            relevancia_geral = "baixa"

        return {
            "relevancia_geral": relevancia_geral,
            "resultados_relevantes": resultados_relevantes,
            "resultados_parcialmente_relevantes": resultados_parcialmente_relevantes,
            "resultados_irrelevantes": resultados_irrelevantes,
            "score_medio": score_medio
        }

    def _verificar_homonímia_resolvida(self,
                                      query_original: str,
                                      query_expandida: str,
                                      resultados_busca: List[Dict[str, Any]],
                                      termos_ambiguos_detectados: List[str]) -> Dict[str, Any]:
        """
        Verifica se problemas de homonímia foram resolvidos.

        Args:
            query_original (str): Query original
            query_expandida (str): Query expandida
            resultados_busca (List[Dict[str, Any]]): Resultados da busca
            termos_ambiguos_detectados (List[str]): Termos ambíguos detectados

        Returns:
            Dict[str, Any]: Análise de resolução de homonímia
        """
        if not termos_ambiguos_detectados:
            return {
                "homonímia_detectada": False,
                "homonímia_resolvida": True,
                "termos_problematicos": [],
                "contexto_correto": "N/A"
            }

        # Verifica se a query foi expandida
        query_foi_expandida = query_original != query_expandida

        # Analisa contexto dos resultados
        contextos_resultados = []
        for resultado in resultados_busca:
            conteudo = resultado.get('content', '').lower()

            # Identifica contexto baseado no conteúdo
            if any(termo in conteudo for termo in ["jurídico", "legal", "processo", "decisão"]):
                contextos_resultados.append("jurídico")
            elif any(termo in conteudo for termo in ["técnico", "engenharia", "projeto", "obra"]):
                contextos_resultados.append("técnico")
            elif any(termo in conteudo for termo in ["administrativo", "servidor", "cargo", "funcionário"]):
                contextos_resultados.append("administrativo")

        # Determina contexto predominante
        if contextos_resultados:
            contexto_predominante = max(set(contextos_resultados), key=contextos_resultados.count)
        else:
            contexto_predominante = "geral"

        # Verifica se os termos ambíguos foram resolvidos corretamente
        termos_problematicos = []
        for termo in termos_ambiguos_detectados:
            contexto_termo = obter_contexto_termo(termo)
            if contexto_termo and contexto_termo != contexto_predominante:
                termos_problematicos.append({
                    "termo": termo,
                    "contexto_esperado": contexto_termo,
                    "contexto_encontrado": contexto_predominante
                })

        homonímia_resolvida = len(termos_problematicos) == 0 and query_foi_expandida

        return {
            "homonímia_detectada": len(termos_ambiguos_detectados) > 0,
            "homonímia_resolvida": homonímia_resolvida,
            "termos_problematicos": termos_problematicos,
            "contexto_correto": contexto_predominante,
            "query_expandida": query_foi_expandida
        }

    def _sugerir_refinamentos(self,
                              query_original: str,
                              resultados_busca: List[Dict[str, Any]],
                              relevancia: Dict[str, Any],
                              homonímia: Dict[str, Any]) -> List[str]:
        """
        Sugere refinamentos para melhorar os resultados.

        Args:
            query_original (str): Query original
            resultados_busca (List[Dict[str, Any]]): Resultados da busca
            relevancia (Dict[str, Any]): Análise de relevância
            homonímia (Dict[str, Any]): Análise de homonímia

        Returns:
            List[str]: Lista de sugestões de refinamento
        """
        sugestoes = []

        # Sugestões baseadas na relevância
        if relevancia["relevancia_geral"] == "baixa":
            sugestoes.append("Considerar expandir a query com termos mais específicos")
            sugestoes.append("Verificar se os termos de busca estão corretos")

        if relevancia["resultados_irrelevantes"] > len(resultados_busca) * 0.5:
            sugestoes.append("Refinar os critérios de busca para melhorar a precisão")

        # Sugestões baseadas na homonímia
        if not homonímia["homonímia_resolvida"]:
            sugestoes.append("Especificar melhor o contexto da consulta")
            sugestoes.append("Usar termos mais específicos para evitar ambiguidade")

        if homonímia["termos_problematicos"]:
            for problema in homonímia["termos_problematicos"]:
                sugestoes.append(f"Especificar contexto para '{problema['termo']}' ({problema['contexto_esperado']})")

        # Sugestões baseadas no número de resultados
        if len(resultados_busca) == 0:
            sugestoes.append("Ampliar os critérios de busca")
            sugestoes.append("Verificar se os termos estão corretos")
        elif len(resultados_busca) > 50:
            sugestoes.append("Refinar a busca para obter resultados mais específicos")

        return sugestoes

    def _calcular_metricas_qualidade(self,
                                    resultados_busca: List[Dict[str, Any]],
                                    relevancia: Dict[str, Any],
                                    homonímia: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas de qualidade dos resultados.

        Args:
            resultados_busca (List[Dict[str, Any]]): Resultados da busca
            relevancia (Dict[str, Any]): Análise de relevância
            homonímia (Dict[str, Any]): Análise de homonímia

        Returns:
            Dict[str, Any]: Métricas de qualidade
        """
        total_resultados = len(resultados_busca)

        # Calcula taxa de relevância
        taxa_relevancia = 0.0
        if total_resultados > 0:
            resultados_relevantes = relevancia["resultados_relevantes"]
            taxa_relevancia = resultados_relevantes / total_resultados

        # Calcula score de qualidade geral
        score_qualidade = 0.0

        # Fator de relevância (40% do score)
        if relevancia["relevancia_geral"] == "alta":
            score_qualidade += 0.4
        elif relevancia["relevancia_geral"] == "média":
            score_qualidade += 0.2

        # Fator de resolução de homonímia (30% do score)
        if homonímia["homonímia_resolvida"]:
            score_qualidade += 0.3

        # Fator de quantidade de resultados (30% do score)
        if 5 <= total_resultados <= 30:
            score_qualidade += 0.3
        elif 1 <= total_resultados <= 50:
            score_qualidade += 0.15

        return {
            "score_qualidade_geral": score_qualidade,
            "taxa_relevancia": taxa_relevancia,
            "score_medio_resultados": relevancia["score_medio"],
            "qualidade_classificacao": self._classificar_qualidade(score_qualidade)
        }

    def _classificar_qualidade(self, score: float) -> str:
        """
        Classifica a qualidade baseada no score.

        Args:
            score (float): Score de qualidade

        Returns:
            str: Classificação da qualidade
        """
        if score >= 0.8:
            return "excelente"
        elif score >= 0.6:
            return "boa"
        elif score >= 0.4:
            return "regular"
        else:
            return "baixa"

    def validar_posprocessamento(self, resultado: Dict[str, Any]) -> bool:
        """
        Valida se o pós-processamento foi realizado corretamente.

        Args:
            resultado (Dict[str, Any]): Resultado do pós-processamento

        Returns:
            bool: True se válido, False caso contrário
        """
        # Verifica se todos os campos obrigatórios estão presentes
        campos_obrigatorios = [
            "query_original",
            "query_expandida",
            "termos_ambiguos_detectados",
            "total_resultados",
            "relevancia_resultados",
            "homonímia_resolvida",
            "sugestoes_refinamento",
            "metricas_qualidade",
            "posprocessamento_realizado"
        ]

        for campo in campos_obrigatorios:
            if campo not in resultado:
                self.logger.error(f"Campo obrigatório ausente: {campo}")
                return False

        return True

# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def analisar_resultados_simples(query_original: str,
                               query_expandida: str,
                               resultados_busca: List[Dict[str, Any]],
                               termos_ambiguos: List[str]) -> Dict[str, Any]:
    """
    Função de conveniência para analisar resultados.

    Args:
        query_original (str): Query original
        query_expandida (str): Query expandida
        resultados_busca (List[Dict[str, Any]]): Resultados da busca
        termos_ambiguos (List[str]): Termos ambíguos detectados

    Returns:
        Dict[str, Any]: Análise dos resultados
    """
    postprocessor = QueryPostprocessor()
    return postprocessor.analisar_resultados(
        query_original, query_expandida, resultados_busca, termos_ambiguos
    )

# =============================================================================
# TESTES DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    # Configura logging para testes
    logging.basicConfig(level=logging.INFO)

    print("=== TESTES DO MÓDULO DE PÓS-PROCESSAMENTO ===")

    # Cria instância do pós-processador
    postprocessor = QueryPostprocessor()

    # Dados de teste
    query_original = "Qual o entendimento sobre custeio de ART no DNIT?"
    query_expandida = "Qual o entendimento sobre custeio de ART (Anotação de Responsabilidade Técnica) no DNIT (Departamento Nacional de Infraestrutura de Transportes)?"
    termos_ambiguos = ["ART", "DNIT"]

    # Resultados simulados
    resultados_busca = [
        {"content": "Documento sobre ART no DNIT", "score": 0.85},
        {"content": "Anotação de Responsabilidade Técnica", "score": 0.78},
        {"content": "Departamento Nacional de Infraestrutura", "score": 0.72},
        {"content": "Documento irrelevante", "score": 0.35}
    ]

    # Teste de análise
    print("\n1. Teste de análise de resultados:")
    resultado = postprocessor.analisar_resultados(
        query_original, query_expandida, resultados_busca, termos_ambiguos
    )

    print(f"   Query original: {resultado['query_original']}")
    print(f"   Query expandida: {resultado['query_expandida']}")
    print(f"   Total resultados: {resultado['total_resultados']}")
    print(f"   Relevância: {resultado['relevancia_resultados']['relevancia_geral']}")
    print(f"   Homonímia resolvida: {resultado['homonímia_resolvida']['homonímia_resolvida']}")
    print(f"   Score qualidade: {resultado['metricas_qualidade']['score_qualidade_geral']:.2f}")
    print(f"   Sugestões: {resultado['sugestoes_refinamento']}")

    # Teste de validação
    print("\n2. Teste de validação:")
    valido = postprocessor.validar_posprocessamento(resultado)
    print(f"   Resultado válido: {valido}")

    print("\n=== FIM DOS TESTES ===")
