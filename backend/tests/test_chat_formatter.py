import os
import re
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from src.formatting.chat_formatter import (
    apply_chat_formatting,
    format_for_chat,
    is_chat_formatting_enabled,
)


def visual_markdown_to_plain(text):
    text = re.sub(r"(?m)^\s*(?:[-*+]\s+|>\s+|\d+\.\s+|[a-z]\)\s+)", "", text)
    return re.sub(r"\s+", " ", text).strip()


class ChatFormatterTest(unittest.TestCase):
    def test_returns_string(self):
        self.assertIsInstance(format_for_chat("Resposta objetiva."), str)

    def test_empty_answer_returns_empty_answer(self):
        self.assertEqual(format_for_chat(""), "")

    def test_technical_content_is_not_removed(self):
        original = "A resposta deve preservar a fundamentacao tecnica e a selecao de fontes do RAG."
        formatted = format_for_chat(original)
        self.assertIn("fundamentacao tecnica", formatted)
        self.assertIn("selecao de fontes", formatted)

    def test_citations_are_not_removed(self):
        original = "A conclusao consta da nota 188/2023/SENOR/COLEG e deve ser preservada."
        formatted = format_for_chat(original)
        self.assertIn("188/2023/SENOR/COLEG", formatted)

    def test_legal_articles_items_and_numbers_are_preserved(self):
        original = (
            "Art. 5o Configura conflito de interesses: I - divulgar informacao privilegiada; "
            "II - exercer atividade privada incompatível. O prazo e de 15 dias."
        )
        formatted = format_for_chat(original)
        for token in ["Art. 5o", "I -", "II -", "15 dias"]:
            self.assertIn(token, formatted)

    def test_dates_percentages_and_values_are_preserved(self):
        original = "Em 15/05/2026, o indice foi de 85% e o valor estimado foi de R$ 1.250,00."
        formatted = format_for_chat(original)
        for token in ["15/05/2026", "85%", "R$ 1.250,00"]:
            self.assertIn(token, formatted)

    def test_does_not_make_answer_shorter(self):
        original = (
            "A funcao deve preservar conteudo tecnico, citacoes, ressalvas e fundamentos. "
            "Tambem deve melhorar apenas a apresentacao visual da resposta final."
        )
        formatted = format_for_chat(original)
        self.assertGreaterEqual(len(formatted), len(original))

    def test_quoted_passages_are_preserved(self):
        original = 'A nota afirma que "nao ha conflito de interesses" desde que cumpridas as condicoes.'
        formatted = format_for_chat(original)
        self.assertIn('"nao ha conflito de interesses"', formatted)

    def test_code_blocks_are_preserved(self):
        original = "Use o exemplo:\n\n```python\nprint('ok')\n```\n\nDepois valide."
        formatted = format_for_chat(original)
        self.assertIn("```python\nprint('ok')\n```", formatted)

    def test_improves_clear_semicolon_enumeration(self):
        original = "A funcao pode melhorar: quebras de paragrafo; listas; subtitulos; espacamento."
        formatted = format_for_chat(original)
        self.assertIn("- quebras de paragrafo;", formatted)
        self.assertIn("- espacamento.", formatted)
        self.assertEqual(visual_markdown_to_plain(formatted), original)

    def test_preserves_conjunctions_and_punctuation_in_lists(self):
        original = "A funcao pode melhorar: paragrafo; lista; e espacamento."
        formatted = format_for_chat(original)
        self.assertIn("- e espacamento.", formatted)
        self.assertEqual(visual_markdown_to_plain(formatted), original)

    def test_trailing_observation_after_list_is_not_last_item(self):
        original = (
            "Ela nao deve interferir em: recuperacao; selecao de fontes; raciocinio; validacao. "
            "Caso a resposta contenha citacoes, elas devem ser preservadas."
        )
        formatted = format_for_chat(original)
        self.assertIn("- validacao.", formatted)
        self.assertIn("> Caso a resposta contenha citacoes", formatted)
        self.assertEqual(visual_markdown_to_plain(formatted), original)

    def test_ordered_sequence_does_not_invent_introductory_words(self):
        original = (
            "Primeiro identifique onde a resposta final e montada. "
            "Depois crie uma funcao isolada de formatacao. "
            "Em seguida aplique essa funcao antes do envio ao usuario. "
            "Por fim, crie testes."
        )
        formatted = format_for_chat(original)
        self.assertNotIn("Sequencia", formatted)
        self.assertEqual(visual_markdown_to_plain(formatted), original)

    def test_does_not_create_titles_in_short_answers(self):
        formatted = format_for_chat("Resposta curta e direta.")
        self.assertNotIn("##", formatted)

    def test_feature_flag_disabled(self):
        original = "A funcao pode melhorar: paragrafo; lista; espacamento."
        self.assertEqual(apply_chat_formatting(original, enabled=False), original)

    def test_feature_flag_enabled(self):
        original = "A funcao pode melhorar: paragrafo; lista; espacamento."
        formatted = apply_chat_formatting(original, enabled=True)
        self.assertIn("- paragrafo;", formatted)

    def test_feature_flag_env_true(self):
        with patch.dict(os.environ, {"ENABLE_CHAT_FORMATTING": "true"}):
            self.assertTrue(is_chat_formatting_enabled())

    def test_formatter_error_falls_back_to_original(self):
        original = "Resposta original."

        def broken_formatter(_answer):
            raise RuntimeError("boom")

        self.assertEqual(
            apply_chat_formatting(
                original,
                enabled=True,
                formatter=broken_formatter,
                logger=Mock(),
            ),
            original,
        )


if __name__ == "__main__":
    unittest.main()
