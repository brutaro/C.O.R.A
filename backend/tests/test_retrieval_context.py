import unittest

from src.agents.simple_research_agent import SimpleResearchAgent


class RetrievalContextTest(unittest.TestCase):
    def build_agent(self):
        agent = object.__new__(SimpleResearchAgent)
        agent.pinecone_config = {
            "final_result_count": 10,
            "specific_note_context_top_k": 15,
            "specific_note_max_chunks": 0,
        }
        agent.llm_config = {"input_token_budget": 30000}
        return agent

    def make_result(self, chunk_number, total_chunks=18, score=0.8):
        chunk_id = f"nota:teste#chunk:{chunk_number:03d}"
        return {
            "documento_id": chunk_id,
            "titulo": "188/2023/SENOR/COLEG",
            "titulo_full": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE",
            "arquivo_original": "17_2023_50600.031460.2023.93_e.md",
            "conteudo": f"conteudo {chunk_number}",
            "chunk_number": chunk_number,
            "score": score,
            "metadata": {
                "chunk_id": chunk_id,
                "chunk_number": chunk_number,
                "total_chunks": total_chunks,
                "numero_nota_tecnica": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE",
                "arquivo_original": "17_2023_50600.031460.2023.93_e.md",
            },
        }

    def make_note_result(self, note_title, arquivo_original="nota.md"):
        return {
            "titulo": note_title.split(" - ", 1)[0],
            "titulo_full": note_title,
            "arquivo_original": arquivo_original,
            "metadata": {
                "numero_nota_tecnica": note_title,
                "arquivo_original": arquivo_original,
            },
        }

    def test_merge_respects_custom_specific_note_limit(self):
        agent = self.build_agent()
        results = [self.make_result(index, total_chunks=15) for index in range(1, 16)]

        merged = SimpleResearchAgent._merge_search_results(
            agent,
            [("original", "consulta", results)],
            result_limit=15,
        )

        self.assertEqual(len(merged), 15)

    def test_merge_keeps_general_query_default_limit(self):
        agent = self.build_agent()
        results = [self.make_result(index, total_chunks=15) for index in range(1, 16)]

        merged = SimpleResearchAgent._merge_search_results(
            agent,
            [("original", "consulta", results)],
        )

        self.assertEqual(len(merged), 10)

    def test_specific_note_results_are_sorted_by_chunk_order(self):
        agent = self.build_agent()
        unordered = [self.make_result(3), self.make_result(1), self.make_result(2)]

        ordered = SimpleResearchAgent._sort_results_by_chunk_order(agent, unordered)

        self.assertEqual([result["chunk_number"] for result in ordered], [1, 2, 3])

    def test_retrieval_diagnostics_flags_complete_specific_note(self):
        agent = self.build_agent()
        results = [self.make_result(index, total_chunks=3) for index in range(1, 4)]

        diagnostics = SimpleResearchAgent._build_retrieval_diagnostics(
            agent,
            retrieval_mode="nota_especifica",
            search_results=results,
            context_text="contexto",
            prompt="prompt",
            specific_note_target={"numero_nota_tecnica": "188/2023/SENOR/COLEG"},
        )

        self.assertTrue(diagnostics["specific_note_complete"])
        self.assertEqual(diagnostics["specific_note_total_chunks"], 3)
        self.assertEqual(diagnostics["specific_note_sent_chunks"], [1, 2, 3])

    def test_retrieval_diagnostics_flags_partial_specific_note(self):
        agent = self.build_agent()
        results = [self.make_result(index, total_chunks=4) for index in range(1, 4)]

        diagnostics = SimpleResearchAgent._build_retrieval_diagnostics(
            agent,
            retrieval_mode="nota_especifica",
            search_results=results,
            context_text="contexto",
            prompt="prompt",
            specific_note_target={"numero_nota_tecnica": "188/2023/SENOR/COLEG"},
        )

        self.assertFalse(diagnostics["specific_note_complete"])
        self.assertEqual(diagnostics["specific_note_total_chunks"], 4)

    def test_follow_up_without_scope_change_anchors_to_active_note(self):
        agent = self.build_agent()
        active_note = {
            "numero_nota_tecnica": "21/2025/SENOR/COLEG",
            "arquivo_original": "5_2025_50600.004061.2025.11_e.md",
        }

        self.assertTrue(
            SimpleResearchAgent._should_anchor_to_active_note(
                agent,
                "E qual conclusão a nota chega?",
                active_note,
            )
        )

    def test_broad_scope_change_does_not_anchor_to_active_note(self):
        agent = self.build_agent()
        active_note = {
            "numero_nota_tecnica": "21/2025/SENOR/COLEG",
            "arquivo_original": "5_2025_50600.004061.2025.11_e.md",
        }

        self.assertFalse(
            SimpleResearchAgent._should_anchor_to_active_note(
                agent,
                "Há outras notas sobre atuação como perito judicial?",
                active_note,
            )
        )

    def test_explicit_new_note_does_not_anchor_to_active_note(self):
        agent = self.build_agent()
        active_note = {
            "numero_nota_tecnica": "21/2025/SENOR/COLEG",
            "arquivo_original": "5_2025_50600.004061.2025.11_e.md",
        }

        self.assertFalse(
            SimpleResearchAgent._should_anchor_to_active_note(
                agent,
                "E a Nota Técnica 188/2023/SENOR/COLEG chegou a qual conclusão?",
                active_note,
            )
        )

    def test_non_substantive_message_does_not_anchor_to_active_note(self):
        agent = self.build_agent()
        active_note = {
            "numero_nota_tecnica": "21/2025/SENOR/COLEG",
            "arquivo_original": "5_2025_50600.004061.2025.11_e.md",
        }

        self.assertFalse(
            SimpleResearchAgent._should_anchor_to_active_note(
                agent,
                "Obrigado",
                active_note,
            )
        )

    def test_specific_note_reference_does_not_match_larger_number_prefix(self):
        agent = self.build_agent()
        note_reference = SimpleResearchAgent._extract_specific_note_reference(
            agent,
            "E o que diz especificamente a nota 2/2022/DINOR/COLEG?",
        )
        note_2 = self.make_note_result(
            "2/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE",
            "1_2022_50600.039168.2021.57_e.md",
        )
        note_102 = self.make_note_result(
            "102/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE",
            "18_2022_50600.021129.2022.84_e.md",
        )

        self.assertTrue(
            SimpleResearchAgent._result_matches_note_reference(
                agent,
                note_2,
                note_reference,
            )
        )
        self.assertFalse(
            SimpleResearchAgent._result_matches_note_reference(
                agent,
                note_102,
                note_reference,
            )
        )

    def test_specific_note_reference_still_matches_three_digit_note(self):
        agent = self.build_agent()
        note_reference = SimpleResearchAgent._extract_specific_note_reference(
            agent,
            "Explique a Nota Técnica 102/2022/DINOR/COLEG.",
        )
        note_102 = self.make_note_result(
            "102/2022/DINOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE",
            "18_2022_50600.021129.2022.84_e.md",
        )

        self.assertTrue(
            SimpleResearchAgent._result_matches_note_reference(
                agent,
                note_102,
                note_reference,
            )
        )

    def test_specific_note_context_expands_without_similarity_threshold(self):
        agent = self.build_agent()
        agent.pinecone_config["specific_note_context_top_k"] = 3
        agent.pinecone_config["specific_note_max_chunks"] = 6
        calls = []

        def fake_search_pinecone(
            query,
            top_k=None,
            final_result_count=None,
            metadata_filter=None,
            apply_similarity_threshold=True,
        ):
            calls.append(
                {
                    "top_k": top_k,
                    "final_result_count": final_result_count,
                    "metadata_filter": metadata_filter,
                    "apply_similarity_threshold": apply_similarity_threshold,
                }
            )
            return [
                self.make_result(chunk_number, total_chunks=5)
                for chunk_number in range(1, top_k + 1)
            ]

        agent._search_pinecone = fake_search_pinecone

        results, diagnostics = SimpleResearchAgent._search_specific_note_context(
            agent,
            "consulta",
            {"numero_nota_tecnica": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"},
            {"numero_nota_tecnica": {"$eq": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"}},
        )

        self.assertEqual([call["top_k"] for call in calls], [3, 5])
        self.assertFalse(calls[0]["apply_similarity_threshold"])
        self.assertFalse(calls[1]["apply_similarity_threshold"])
        self.assertEqual(len(results), 5)
        self.assertTrue(diagnostics["complete"])
        self.assertFalse(diagnostics["similarity_threshold_applied"])

    def test_specific_note_context_uses_total_chunks_when_max_is_zero(self):
        agent = self.build_agent()
        agent.pinecone_config["specific_note_context_top_k"] = 3
        agent.pinecone_config["specific_note_max_chunks"] = 0
        calls = []

        def fake_search_pinecone(
            query,
            top_k=None,
            final_result_count=None,
            metadata_filter=None,
            apply_similarity_threshold=True,
        ):
            calls.append(top_k)
            return [
                self.make_result(chunk_number, total_chunks=8)
                for chunk_number in range(1, top_k + 1)
            ]

        agent._search_pinecone = fake_search_pinecone

        results, diagnostics = SimpleResearchAgent._search_specific_note_context(
            agent,
            "consulta",
            {"numero_nota_tecnica": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"},
            {"numero_nota_tecnica": {"$eq": "188/2023/SENOR/COLEG - CGGP/CGGP/DAF/DNIT SEDE"}},
        )

        self.assertEqual(calls, [3, 8])
        self.assertEqual(len(results), 8)
        self.assertIsNone(diagnostics["max_chunks"])
        self.assertEqual(diagnostics["desired_top_k"], 8)
        self.assertTrue(diagnostics["complete"])


if __name__ == "__main__":
    unittest.main()
