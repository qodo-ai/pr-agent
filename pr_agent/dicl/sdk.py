from typing import Dict, Any

class DICL:
    @staticmethod
    def evolve(pr_data: Dict[str, Any], base_prompt: str) -> str:
        """Enhanced review with automated multi-model learning"""
        try:
            from pr_agent.dicl.auto_learning import DualModelReviewer
            import asyncio
            
            dual_reviewer = DualModelReviewer()
            enhanced_review, insights_count = asyncio.run(
                dual_reviewer.dual_review_with_learning(pr_data, base_prompt)
            )

            if insights_count > 0:
                print(f"🧠 Automated learning: Generated {insights_count} new insights from model comparison")

            return enhanced_review
        except Exception as e:
            print(f"❌ Auto-learning error: {e}")
            return DICL.regular(pr_data, base_prompt)

    @staticmethod
    def regular(pr_data: Dict[str, Any], base_prompt: str) -> str:
        try:
            from pr_agent.algo.rag_handler import HybridSearchRAG
            rag = HybridSearchRAG("pinecone")
            title = pr_data.get("title", "")
            description = pr_data.get("description", "")
            enhanced_prompt = base_prompt
            insights = rag.get_relevant_learning_insights(f"{title} {description}", max_insights=10)

            if insights:
                learning_section = f"\\n\\n## 🧠 DICL Learning Context ({len(insights)} patterns):\\n"
                learning_section += f"**Applied Learning Insights from Previous Reviews:**\\n"
                for i, insight in enumerate(insights, 1):
                    if isinstance(insight, dict) and 'insight' in insight:
                        learning_section += f"{i}. {insight['insight'][:150]}...\\n"
                    elif isinstance(insight, str):
                        learning_section += f"{i}. {insight[:150]}...\\n"
                learning_section += f"\\n**Integration Instructions:** Apply these learned patterns to enhance review quality and catch similar issues.\\n"
                enhanced_prompt += learning_section

            return enhanced_prompt
        except Exception as e:
            print(f"❌ DICL Error: {e}")
            return base_prompt
