import unittest

from src.agents.simple_research_agent import SimpleResearchAgent


class ContextExcerptTest(unittest.TestCase):
    def build_agent(self, context_excerpt_chars):
        agent = object.__new__(SimpleResearchAgent)
        agent.pinecone_config = {"context_excerpt_chars": context_excerpt_chars}
        return agent

    def test_zero_context_excerpt_chars_preserves_full_context(self):
        agent = self.build_agent(0)
        content = "palavra  " * 800

        excerpt = SimpleResearchAgent._select_context_excerpt(agent, content)

        self.assertEqual(excerpt, SimpleResearchAgent._normalize_whitespace(agent, content))

    def test_positive_context_excerpt_chars_limits_context(self):
        agent = self.build_agent(20)
        content = "palavra  " * 800

        excerpt = SimpleResearchAgent._select_context_excerpt(agent, content)

        self.assertEqual(len(excerpt), 20)


if __name__ == "__main__":
    unittest.main()
