from typing import Dict, Any

class DICL:
    @staticmethod
    def ingest(repo_url: str, max_prs: int = 10) -> Dict[str, Any]:
        try:
            from pr_agent.tools.pr_diff_ingestion import PRDiffIngestionPipeline
            from pr_agent.algo.rag_handler import HybridSearchRAG
            
            pipeline = PRDiffIngestionPipeline()
            pr_data = pipeline.ingest_repository(repo_url, max_prs)
            
            rag = HybridSearchRAG("pinecone")
            rag.add_pr_diffs(pr_data)
            
            return {"ingested": len(pr_data), "status": "success"}
        except Exception as e:
            return {"ingested": 0, "status": "error", "message": str(e)}
    
    @staticmethod
    def evolve(pr_data: Dict[str, Any], base_prompt: str) -> str:
        return DICL.regular(pr_data, base_prompt)
    
    @staticmethod
    def regular(pr_data: Dict[str, Any], base_prompt: str) -> str:
        try:
            from pr_agent.algo.rag_handler import HybridSearchRAG
            
            rag = HybridSearchRAG("pinecone")
            
            title = pr_data.get("title", "")
            description = pr_data.get("description", "")
            diff_text = pr_data.get("diff", "")
            language = pr_data.get("language", "")
            
            context = rag.get_context_for_pr_analysis(title, description, diff_text, language)
            enhanced_prompt = base_prompt
            
            if context.similar_diffs:
                enhanced_prompt = rag.enhance_prompt_with_context(base_prompt, context)
            
            insights = rag.get_relevant_learning_insights(f"{title} {description}", max_insights=3)
            
            if insights:
                learning_section = f"\\n\\n## Learning Context ({len(insights)} patterns):\\n"
                for insight in insights:
                    if isinstance(insight, dict) and 'insight' in insight:
                        learning_section += f"- {insight['insight'][:100]}...\\n"
                    elif isinstance(insight, str):
                        learning_section += f"- {insight[:100]}...\\n"
                enhanced_prompt += learning_section
            
            return enhanced_prompt
        except Exception as e:
            print(f"❌ DICL Error: {e}")
            return base_prompt