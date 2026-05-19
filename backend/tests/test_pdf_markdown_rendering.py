import unittest

from main import _texto_para_html


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


if __name__ == "__main__":
    unittest.main()
