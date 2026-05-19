import unittest

from src.agents.simple_research_agent import SimpleResearchAgent


class ResponseCleaningTest(unittest.TestCase):
    def clean(self, text):
        return SimpleResearchAgent._clean_response(object(), text)

    def test_preserves_markdown_lists_tables_and_quotes(self):
        original = """<b>PERGUNTA DO USUÁRIO:</b> teste

<b>RESPOSTA:</b>
## Bloco principal

1. Primeiro ponto.
2. Segundo ponto:
   a) alternativa interna;
   b) segunda alternativa.

| Situação | Conclusão |
|---|---|
| Caso A | Requer cautela |

> Ressalva importante.

## Fontes Consultadas
- fonte removida
"""

        cleaned = self.clean(original)

        self.assertIn("## Bloco principal", cleaned)
        self.assertIn("1. Primeiro ponto.", cleaned)
        self.assertIn("a) alternativa interna;", cleaned)
        self.assertIn("| Situação | Conclusão |", cleaned)
        self.assertIn("> Ressalva importante.", cleaned)
        self.assertNotIn("PERGUNTA DO USUÁRIO", cleaned)
        self.assertNotIn("Fontes Consultadas", cleaned)

    def test_does_not_convert_numbered_lists_to_bullets(self):
        cleaned = self.clean("1. Etapa inicial.\n2. Etapa final.")

        self.assertIn("1. Etapa inicial.", cleaned)
        self.assertIn("2. Etapa final.", cleaned)
        self.assertNotIn("•", cleaned)


if __name__ == "__main__":
    unittest.main()
