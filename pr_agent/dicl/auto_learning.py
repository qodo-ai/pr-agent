from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ModelComparison:
    gpt4_review: str
    o3_review: str
    differences: List[str]
    unique_to_gpt4: List[str]
    unique_to_o3: List[str]
    agreement_score: float
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class AutoLearningEngine:
    def __init__(self):
        from pr_agent.log import get_logger
        self.logger = get_logger()
    
    def compare_models(self, gpt4_review: str, o3_review: str) -> ModelComparison:
        gpt4_issues = self._extract_issues(gpt4_review)
        o3_issues = self._extract_issues(o3_review)
        unique_to_gpt4 = [issue for issue in gpt4_issues if not self._similar_issue_exists(issue, o3_issues)]
        unique_to_o3 = [issue for issue in o3_issues if not self._similar_issue_exists(issue, gpt4_issues)]
        common_issues = len(gpt4_issues) + len(o3_issues) - len(unique_to_gpt4) - len(unique_to_o3)
        total_issues = len(gpt4_issues) + len(o3_issues)
        
        # Fix agreement score calculation to be between 0 and 1
        if total_issues == 0:
            agreement_score = 1.0  # No issues found by either model = perfect agreement
        else:
            agreement_score = min(1.0, (2 * common_issues) / total_issues)
        
        differences = unique_to_gpt4 + unique_to_o3
        
        return ModelComparison(
            gpt4_review=gpt4_review,
            o3_review=o3_review,
            differences=differences,
            unique_to_gpt4=unique_to_gpt4,
            unique_to_o3=unique_to_o3,
            agreement_score=agreement_score
        )
    
    def _extract_issues(self, review_text: str) -> List[str]:
        issues = []
        lines = review_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in [
                'issue:', 'problem:', 'concern:', 'warning:', 'error:', 
                'missing:', 'should:', 'consider:', 'recommend:', 'fix:'
            ]):
                if len(line) > 10:
                    issues.append(line[:200])
                    
        return issues
    
    def _similar_issue_exists(self, issue: str, issue_list: List[str]) -> bool:
        issue_lower = issue.lower()
        key_words = [word for word in issue_lower.split() if len(word) > 3]
        
        for existing_issue in issue_list:
            existing_lower = existing_issue.lower()
            overlap = sum(1 for word in key_words if word in existing_lower)
            if overlap >= 2:
                return True
        return False
    
    def generate_learning_insights(self, comparison: ModelComparison, pr_context: Dict[str, Any]) -> List[str]:
        """Use LLM judge to compare reviews and generate insights"""
        
        # Skip if no reviews to compare
        if not comparison.gpt4_review or not comparison.o3_review:
            return []
        
        try:
            import asyncio
            
            # Handle event loop properly
            try:
                loop = asyncio.get_running_loop()
                # Create a new task in the existing loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._generate_insights_with_judge(comparison, pr_context))
                    insights = future.result(timeout=30)
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                insights = asyncio.run(self._generate_insights_with_judge(comparison, pr_context))
                
            self.logger.info(f"LLM Judge generated {len(insights)} learning insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"LLM Judge failed: {e}")
            return []
    
    async def _generate_insights_with_judge(self, comparison: ModelComparison, pr_context: Dict[str, Any]) -> List[str]:
        """Use LLM to judge differences and generate insights"""
        
        from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
        
        judge_prompt = f"""Compare these two code reviews and extract learning insights about what each model specializes in detecting.

## Context
- **Language**: {pr_context.get('language', 'unknown')}
- **Files**: {', '.join(pr_context.get('changed_files', [])[:3])}

## GPT-4 Review:
{comparison.gpt4_review[:2000]}

## O3 Review:
{comparison.o3_review[:2000]}

## Task
Analyze what each model uniquely caught or emphasized. Generate 2-4 specific learning insights that capture:

1. **Technical Specializations**: What types of issues does each model excel at finding?
2. **Specific Examples**: File-level insights with clear impact (like "O3 detected test coverage gap in test/e2e/dra/dra.go:921 affecting ResourceClaim validation")
3. **Actionable Patterns**: When to prioritize which model for similar code changes

Format each insight as a complete, standalone learning point. Focus on substantial differences, not minor style variations.

Output format: One insight per line, no prefixes or numbering."""

        ai_handler = LiteLLMAIHandler()
        response, _ = await ai_handler.chat_completion(
            model="gpt-4o-mini",
            temperature=0.1,
            system="""You are an expert code review analyst. Your job is to identify what each AI model specializes in detecting by comparing their reviews.

Focus on:
- **Substantial technical differences** (not style preferences)
- **File-specific insights** with concrete examples
- **Actionable specialization patterns** for future reviews

Generate insights that would help choose the right model for specific types of code changes.

Keep insights concise but technically specific. Each insight should be valuable for improving future code reviews.""",
            user=judge_prompt
        )
        
        # Parse insights from response
        insights = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if len(line) > 40:  # Only substantial insights
                insights.append(f"JUDGE_INSIGHT: {line}")
        
        return insights
    
    
    def store_learning_insights(self, insights: List[str], pr_context: Dict[str, Any]) -> bool:
        try:
            from pr_agent.algo.rag_handler import HybridSearchRAG
            
            rag = HybridSearchRAG("pinecone")
            stored_count = 0
            
            for insight in insights:
                success = rag.add_learning_insight(
                    insight_text=insight,
                    pr_id=pr_context.get("pr_id", "auto_learning"),
                    agreement_score=0.8,
                    metadata={
                        "learning_type": "automated_comparison",
                        "timestamp": datetime.now().isoformat(),
                        "pr_language": pr_context.get("language", "unknown"),
                        "pr_files": pr_context.get("changed_files", [])[:10],
                        "automated": True
                    }
                )
                if success:
                    stored_count += 1
            
            self.logger.info(f"Stored {stored_count}/{len(insights)} automated learning insights")
            return stored_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to store automated learning: {e}")
            return False

class DualModelReviewer:
    def __init__(self):
        self.learning_engine = AutoLearningEngine()
        from pr_agent.log import get_logger
        self.logger = get_logger()
    
    async def dual_review_with_learning(self, pr_data: Dict[str, Any], base_prompt: str) -> Tuple[str, int]:
        try:
            gpt4_review = await self._get_gpt4_review(pr_data, base_prompt)
            o3_review = await self._get_o3_review(pr_data, base_prompt)
            comparison = self.learning_engine.compare_models(gpt4_review, o3_review)
            insights = self.learning_engine.generate_learning_insights(comparison, pr_data)
            stored = self.learning_engine.store_learning_insights(insights, pr_data)
            final_review = self._synthesize_reviews(gpt4_review, o3_review, comparison)
            
            self.logger.info(f"Dual model review completed. Agreement: {comparison.agreement_score:.2f}, Insights: {len(insights)}")
            
            return final_review, len(insights)
            
        except Exception as e:
            self.logger.error(f"Dual model review failed: {e}")
            return base_prompt, 0
    
    async def _get_gpt4_review(self, pr_data: Dict[str, Any], prompt: str) -> str:
        try:
            from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
            
            ai_handler = LiteLLMAIHandler()
            response, _ = await ai_handler.chat_completion(
                model="gpt-4",
                temperature=0.1,
                system="""You are a senior software engineer and code review expert with 15+ years of experience. Your role is to conduct thorough, constructive code reviews.

ANALYSIS FRAMEWORK:
1. Security vulnerabilities and potential exploits
2. Performance bottlenecks and optimization opportunities  
3. Code maintainability and technical debt
4. Best practices adherence (language-specific patterns)
5. Error handling and edge case coverage
6. Testing gaps and quality assurance concerns

OUTPUT REQUIREMENTS:
- Structure findings with clear severity levels (Critical/High/Medium/Low)
- Provide specific file:line references for each issue
- Include actionable remediation steps with code examples where helpful
- Prioritize issues by business impact and implementation effort
- Use concise, professional language focused on improvement

Focus on substantial issues that impact code quality, security, or maintainability. Avoid nitpicking style preferences unless they affect readability.""",
                user=prompt
            )
            return response
        except Exception as e:
            self.logger.error(f"GPT-4 review failed: {e}")
            return "GPT-4 review unavailable"
    
    async def _get_o3_review(self, pr_data: Dict[str, Any], prompt: str) -> str:
        try:
            from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
            
            ai_handler = LiteLLMAIHandler()
            response, _ = await ai_handler.chat_completion(
                model="o3-mini",
                temperature=0.05,
                system="""
You are an elite code auditor with deep expertise in software architecture and security. Your specialty is detecting subtle, hard-to-find issues that other reviewers miss.

PRIMARY FOCUS AREAS:
1. Logic flaws and algorithmic correctness
2. Race conditions and concurrency issues
3. Memory leaks and resource management
4. Input validation and injection vulnerabilities
5. Business logic violations and edge cases
6. API design inconsistencies and breaking changes

REVIEW METHODOLOGY:
- Trace data flow through the entire change
- Analyze interaction patterns between modified components  
- Identify assumptions that may not hold in production
- Consider failure modes and recovery scenarios
- Evaluate scalability implications of design decisions

OUTPUT FORMAT:
- Lead with the most critical findings
- Use evidence-based reasoning for each concern
- Specify exact locations using file:line notation
- Suggest concrete solutions, not just problems
- Classify issues by risk level (Critical/High/Medium/Low)

Your unique value is catching issues that automated tools and standard reviews miss through deep reasoning and system-level thinking.""",
                user=prompt
            )
            return response
        except Exception as e:
            self.logger.error(f"O3 review failed: {e}")
            return "O3 review unavailable"
    
    def _synthesize_reviews(self, gpt4_review: str, o3_review: str, comparison: ModelComparison) -> str:
        if comparison.agreement_score > 0.8:
            return gpt4_review if len(gpt4_review) > len(o3_review) else o3_review
        combined = f"## 🧬 DICL Enhanced Review (Multi-Model Analysis)\n\n"
        
        if gpt4_review and "unavailable" not in gpt4_review:
            combined += f"### 🔍 Primary Analysis (GPT-4):\n{gpt4_review}\n\n"
        
        if comparison.unique_to_o3:
            combined += f"### 🎯 Specialized Insights (O3):\n"
            for insight in comparison.unique_to_o3[:10]:
                combined += f"- {insight}\n"
        
        combined += f"\n### 📊 Model Consensus Analysis\n"
        combined += f"- **Agreement Score**: {comparison.agreement_score:.2f}/1.0\n"
        combined += f"- **Unique GPT-4 Findings**: {len(comparison.unique_to_gpt4)}\n"
        combined += f"- **Unique O3 Findings**: {len(comparison.unique_to_o3)}\n"
        combined += f"- **Analysis Quality**: {'High consensus' if comparison.agreement_score >= 0.8 else 'Multi-perspective analysis required'}\n"
        
        return combined