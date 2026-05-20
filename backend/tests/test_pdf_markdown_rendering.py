import unittest

from main import _build_conversation_html, _texto_para_html


class PdfMarkdownRenderingTest(unittest.TestCase):
    def test_renders_markdown_blocks_without_raw_markers(self):
        markdown = """Com base na Nota Técnica **188/2023/SENOR/COLEG**, observe:

### Requisitos de Admissibilidade

1. Identificação do interessado;
2. Referência a objeto determinado.

> Não são apreciadas consultas em tese.

- **Informação Privilegiada:** é vedada.
"""

        rendered = _texto_para_html(markdown)

        self.assertIn("<strong>188/2023/SENOR/COLEG</strong>", rendered)
        self.assertIn("<h3>Requisitos de Admissibilidade</h3>", rendered)
        self.assertIn("<ol><li>Identificação do interessado;</li>", rendered)
        self.assertIn("<blockquote>", rendered)
        self.assertIn("<ul><li><strong>Informação Privilegiada:</strong> é vedada.</li></ul>", rendered)
        self.assertNotIn("### Requisitos", rendered)
        self.assertNotIn("**188/2023", rendered)
        self.assertNotIn("&gt; Não", rendered)

    def test_renders_markdown_tables(self):
        markdown = """| Situação | Conclusão |
|---|---|
| Caso A | Requer cautela |
"""

        rendered = _texto_para_html(markdown)

        self.assertIn('<table class="markdown-tabela">', rendered)
        self.assertIn("<th>Situação</th>", rendered)
        self.assertIn("<td>Requer cautela</td>", rendered)
        self.assertNotIn("|---|", rendered)

    def test_renders_alpha_lists_as_single_lettered_list(self):
        markdown = """a) primeira condição;
b) segunda condição;
c) terceira condição."""

        rendered = _texto_para_html(markdown)

        self.assertIn('<ol type="a">', rendered)
        self.assertEqual(rendered.count("<li>"), 3)
        self.assertNotIn("a) primeira", rendered)

    def test_pdf_template_matches_chat_list_and_reference_styling(self):
        rendered = _build_conversation_html(
            {"id": "teste", "title": "Teste"},
            [
                {"role": "user", "content": "Pergunta de teste"},
                {
                    "role": "assistant",
                    "content": "1. Primeiro ponto\n2. Segundo ponto",
                    "metadata": {
                        "references": [
                            {
                                "source": "Nota Técnica 188/2023",
                                "score": 0.87,
                                "url": "https://example.com/nota",
                                "namespace": "notas_conflito_interesse",
                            }
                        ]
                    },
                },
            ],
            "usuario@example.com",
        )

        self.assertIn(".resposta-texto li::marker", rendered)
        self.assertIn("color: #0f766e;", rendered)
        self.assertIn('<ol><li>Primeiro ponto</li>', rendered)
        self.assertIn('class="referencias-bloco"', rendered)
        self.assertIn("Namespace utilizado: notas_conflito_interesse", rendered)
        self.assertIn('class="referencia-nome"', rendered)
        self.assertIn('class="referencia-link"', rendered)
        self.assertIn("font-size: 9pt;", rendered)
        self.assertIn("font-weight: 500;", rendered)
        self.assertIn("white-space: nowrap;", rendered)
        self.assertNotIn("referencias-tabela", rendered)


if __name__ == "__main__":
    unittest.main()
