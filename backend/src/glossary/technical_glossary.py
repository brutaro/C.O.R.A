# -*- coding: utf-8 -*-
"""
Glossário Técnico-Jurídico para Expansão de Termos Ambíguos
============================================================

Este módulo contém um glossário estruturado de termos técnicos e jurídicos
encontrados nos documentos da pasta origem, organizado para facilitar a
expansão de termos ambíguos antes das consultas ao banco de dados.
"""

# =============================================================================
# GLOSSÁRIO TÉCNICO-JURÍDICO
# =============================================================================

TECHNICAL_GLOSSARY = {
    # ========================================================================
    # TERMOS DE RESPONSABILIDADE TÉCNICA
    # ========================================================================
    "ART": {
        "expansao": "Anotação de Responsabilidade Técnica",
        "contexto": "jurídico-técnico",
        "descricao": "Documento que registra a responsabilidade técnica de profissionais habilitados em obras e serviços de engenharia",
        "legislacao": ["Lei 6.496/1977", "Resolução CONFEA 1.025/2009"],
        "variacoes": ["ART", "art", "Anotação de Responsabilidade Técnica"]
    },

    "RRT": {
        "expansao": "Registro de Responsabilidade Técnica",
        "contexto": "jurídico-técnico",
        "descricao": "Registro que documenta a responsabilidade técnica de profissionais habilitados",
        "legislacao": ["Lei 6.496/1977", "Resolução CONFEA 1.025/2009"],
        "variacoes": ["RRT", "rrt", "Registro de Responsabilidade Técnica"]
    },

    # ========================================================================
    # ÓRGÃOS E INSTITUIÇÕES
    # ========================================================================
    "DNIT": {
        "expansao": "Departamento Nacional de Infraestrutura de Transportes",
        "contexto": "administrativo",
        "descricao": "Órgão responsável pela infraestrutura de transportes no Brasil",
        "variacoes": ["DNIT", "dnit", "Departamento Nacional de Infraestrutura de Transportes"]
    },

    "CREA": {
        "expansao": "Conselho Regional de Engenharia e Agronomia",
        "contexto": "jurídico-técnico",
        "descricao": "Conselho responsável pela fiscalização do exercício profissional",
        "legislacao": ["Lei 5.194/1966"],
        "variacoes": ["CREA", "crea", "Conselho Regional de Engenharia e Agronomia"]
    },

    "CAU": {
        "expansao": "Conselho de Arquitetura e Urbanismo",
        "contexto": "jurídico-técnico",
        "descricao": "Conselho responsável pela fiscalização da arquitetura e urbanismo",
        "variacoes": ["CAU", "cau", "Conselho de Arquitetura e Urbanismo"]
    },

    "CONFEA": {
        "expansao": "Conselho Federal de Engenharia e Agronomia",
        "contexto": "jurídico-técnico",
        "descricao": "Conselho federal responsável pela regulamentação da profissão",
        "legislacao": ["Lei 5.194/1966"],
        "variacoes": ["CONFEA", "confea", "Conselho Federal de Engenharia e Agronomia"]
    },

    "AGU": {
        "expansao": "Advocacia-Geral da União",
        "contexto": "jurídico",
        "descricao": "Órgão responsável pela representação judicial da União",
        "variacoes": ["AGU", "agu", "Advocacia-Geral da União"]
    },

    # ========================================================================
    # TRIBUNALES E INSTÂNCIAS JUDICIAIS
    # ========================================================================
    "STF": {
        "expansao": "Supremo Tribunal Federal",
        "contexto": "jurídico",
        "descricao": "Corte constitucional máxima do Brasil",
        "variacoes": ["STF", "stf", "Supremo Tribunal Federal"]
    },

    "TCU": {
        "expansao": "Tribunal de Contas da União",
        "contexto": "jurídico-administrativo",
        "descricao": "Tribunal responsável pelo controle externo da administração pública",
        "variacoes": ["TCU", "tcu", "Tribunal de Contas da União"]
    },

    "TRF": {
        "expansao": "Tribunal Regional Federal",
        "contexto": "jurídico",
        "descricao": "Tribunal federal de segunda instância",
        "variacoes": ["TRF", "trf", "Tribunal Regional Federal"]
    },

    # ========================================================================
    # CARGOS E FUNÇÕES PÚBLICAS
    # ========================================================================
    "DAS": {
        "expansao": "Cargo em Comissão de Direção e Assessoramento Superior",
        "contexto": "administrativo",
        "descricao": "Cargo de direção e assessoramento superior na administração pública",
        "legislacao": ["Lei 8.112/1990"],
        "variacoes": ["DAS", "das", "Cargo em Comissão de Direção e Assessoramento Superior"]
    },

    # ========================================================================
    # TERMOS JURÍDICOS ESPECÍFICOS
    # ========================================================================
    "vacância": {
        "expansao": "vacância de cargo público",
        "contexto": "jurídico-administrativo",
        "descricao": "Situação de cargo público que está sem ocupante",
        "legislacao": ["Lei 8.112/1990"],
        "variacoes": ["vacância", "vacancia", "vacância de cargo público"]
    },

    "inacumulável": {
        "expansao": "incompatibilidade de cargos públicos",
        "contexto": "jurídico-administrativo",
        "descricao": "Situação em que não é permitida a acumulação de cargos públicos",
        "legislacao": ["Constituição Federal", "Lei 8.112/1990"],
        "variacoes": ["inacumulável", "inacumulavel", "incompatibilidade de cargos públicos"]
    },

    "estágio probatório": {
        "expansao": "período de estágio probatório",
        "contexto": "jurídico-administrativo",
        "descricao": "Período de avaliação para servidores públicos",
        "legislacao": ["Lei 8.112/1990"],
        "variacoes": ["estágio probatório", "estagio probatorio", "período de estágio probatório"]
    },

    "recondução": {
        "expansao": "recondução a cargo público",
        "contexto": "jurídico-administrativo",
        "descricao": "Renovação de nomeação para cargo público",
        "legislacao": ["Lei 8.112/1990"],
        "variacoes": ["recondução", "reconducao", "recondução a cargo público"]
    },

    "substituição": {
        "expansao": "substituição de servidor público",
        "contexto": "jurídico-administrativo",
        "descricao": "Processo de substituição de servidor público",
        "legislacao": ["Lei 8.112/1990"],
        "variacoes": ["substituição", "substituicao", "substituição de servidor público"]
    },

    # ========================================================================
    # LEGISLAÇÃO ESPECÍFICA
    # ========================================================================
    "Lei 8112": {
        "expansao": "Lei 8.112/1990 - Estatuto dos Servidores Públicos",
        "contexto": "jurídico-administrativo",
        "descricao": "Lei que regula o regime jurídico dos servidores públicos",
        "variacoes": ["Lei 8112", "Lei 8.112", "Lei 8.112/1990", "Estatuto dos Servidores Públicos"]
    },

    "Lei 6496": {
        "expansao": "Lei 6.496/1977 - Lei da ART",
        "contexto": "jurídico-técnico",
        "descricao": "Lei que regulamenta a Anotação de Responsabilidade Técnica",
        "variacoes": ["Lei 6496", "Lei 6.496", "Lei 6.496/1977", "Lei da ART"]
    },

    "Lei 5194": {
        "expansao": "Lei 5.194/1966 - Lei do Engenheiro",
        "contexto": "jurídico-técnico",
        "descricao": "Lei que regulamenta o exercício da profissão de engenheiro",
        "variacoes": ["Lei 5194", "Lei 5.194", "Lei 5.194/1966", "Lei do Engenheiro"]
    },

    "Lei 14133": {
        "expansao": "Lei 14.133/2021 - Nova Lei de Licitações",
        "contexto": "jurídico-administrativo",
        "descricao": "Lei que regulamenta licitações e contratos administrativos",
        "variacoes": ["Lei 14133", "Lei 14.133", "Lei 14.133/2021", "Nova Lei de Licitações"]
    },

    "Lei 8666": {
        "expansao": "Lei 8.666/1993 - Lei de Licitações",
        "contexto": "jurídico-administrativo",
        "descricao": "Lei que regulamenta licitações e contratos administrativos",
        "variacoes": ["Lei 8666", "Lei 8.666", "Lei 8.666/1993", "Lei de Licitações"]
    },

    "Decreto 9507": {
        "expansao": "Decreto 9.507/2018 - Terceirização",
        "contexto": "jurídico-administrativo",
        "descricao": "Decreto que regulamenta a terceirização na administração pública",
        "variacoes": ["Decreto 9507", "Decreto 9.507", "Decreto 9.507/2018", "Terceirização"]
    },

    # ========================================================================
    # RESOLUÇÕES E NORMATIVOS
    # ========================================================================
    "Resolução 1025": {
        "expansao": "Resolução CONFEA 1.025/2009",
        "contexto": "jurídico-técnico",
        "descricao": "Resolução que regulamenta a ART e RRT",
        "variacoes": ["Resolução 1025", "Resolução 1.025", "Resolução CONFEA 1.025/2009"]
    },

    "Resolução 218": {
        "expansao": "Resolução CONFEA 218/1973",
        "contexto": "jurídico-técnico",
        "descricao": "Resolução que regulamenta atividades técnicas",
        "variacoes": ["Resolução 218", "Resolução 218/73", "Resolução CONFEA 218/1973"]
    }
}

# =============================================================================
# FUNÇÕES DE EXPANSÃO
# =============================================================================

def expandir_termo_ambiguo(termo: str) -> dict:
    """
    Expande um termo ambíguo usando o glossário técnico-jurídico.

    Args:
        termo (str): Termo a ser expandido

    Returns:
        dict: Dicionário com informações do termo expandido ou None se não encontrado
    """
    termo_upper = termo.upper()
    termo_lower = termo.lower()

    # Busca direta no glossário
    if termo_upper in TECHNICAL_GLOSSARY:
        return TECHNICAL_GLOSSARY[termo_upper]
    elif termo_lower in TECHNICAL_GLOSSARY:
        return TECHNICAL_GLOSSARY[termo_lower]

    # Busca por variações
    for key, value in TECHNICAL_GLOSSARY.items():
        if termo in value.get("variacoes", []):
            return value

    return None

def detectar_termos_ambiguos(texto: str) -> list:
    """
    Detecta termos ambíguos em um texto.

    Args:
        texto (str): Texto para análise

    Returns:
        list: Lista de termos ambíguos encontrados
    """
    termos_encontrados = []
    palavras = texto.split()

    for palavra in palavras:
        # Remove pontuação
        palavra_limpa = palavra.strip(".,;:!?()[]{}")

        # Verifica se é um termo ambíguo
        if expandir_termo_ambiguo(palavra_limpa):
            termos_encontrados.append(palavra_limpa)

    return list(set(termos_encontrados))

def expandir_query(query: str) -> str:
    """
    Expande uma query substituindo termos ambíguos por suas versões completas.

    Args:
        query (str): Query original

    Returns:
        str: Query expandida
    """
    query_expandida = query

    # Detecta termos ambíguos
    termos_ambiguos = detectar_termos_ambiguos(query)

    # Expande cada termo encontrado
    for termo in termos_ambiguos:
        expansao = expandir_termo_ambiguo(termo)
        if expansao:
            # Substitui o termo pela expansão
            query_expandida = query_expandida.replace(
                termo,
                f"{termo} ({expansao['expansao']})"
            )

    return query_expandida

def obter_contexto_termo(termo: str) -> str:
    """
    Obtém o contexto de um termo técnico.

    Args:
        termo (str): Termo a ser analisado

    Returns:
        str: Contexto do termo (jurídico, técnico, administrativo, etc.)
    """
    expansao = expandir_termo_ambiguo(termo)
    if expansao:
        return expansao.get("contexto", "geral")
    return "geral"

# =============================================================================
# TESTES DO GLOSSÁRIO
# =============================================================================

if __name__ == "__main__":
    # Testes de expansão
    print("=== TESTES DO GLOSSÁRIO TÉCNICO-JURÍDICO ===")

    # Teste 1: Expansão de ART
    print("\n1. Teste de expansão de 'ART':")
    resultado = expandir_termo_ambiguo("ART")
    if resultado:
        print(f"   Termo: ART")
        print(f"   Expansão: {resultado['expansao']}")
        print(f"   Contexto: {resultado['contexto']}")
        print(f"   Descrição: {resultado['descricao']}")

    # Teste 2: Detecção de termos ambíguos
    print("\n2. Teste de detecção em texto:")
    texto_teste = "Qual o entendimento sobre custeio de ART no DNIT?"
    termos = detectar_termos_ambiguos(texto_teste)
    print(f"   Texto: {texto_teste}")
    print(f"   Termos ambíguos encontrados: {termos}")

    # Teste 3: Expansão de query
    print("\n3. Teste de expansão de query:")
    query_teste = "Existe algum precedente similar sobre ART/RRT no DNIT?"
    query_expandida = expandir_query(query_teste)
    print(f"   Query original: {query_teste}")
    print(f"   Query expandida: {query_expandida}")

    print("\n=== FIM DOS TESTES ===")
