#!/usr/bin/env python3

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add pr_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from pr_agent.evaluation import KubernetesTestCases, MetricsCalculator, ErrorDetectionParser

class DICLImprovementTester:
    def __init__(self):
        pass
        
    async def test_dicl_improvement(self, test_subset_size: int = 15) -> Dict[str, Any]:
        test_cases = self._get_diverse_test_cases(test_subset_size)
        
        baseline_results = await self._evaluate_without_context(test_cases)
        baseline_report = MetricsCalculator.aggregate_results(baseline_results)
        baseline_report.model_name = "GPT-4 (No Context)"
        
        enhanced_results = await self._evaluate_with_dicl_context(test_cases)
        enhanced_report = MetricsCalculator.aggregate_results(enhanced_results)
        enhanced_report.model_name = "GPT-4 (With DICL)"
        
        improvement_analysis = self._analyze_improvement(baseline_report, enhanced_report)
        
        return improvement_analysis
    
    def _get_diverse_test_cases(self, count: int) -> List:
        all_cases = KubernetesTestCases.get_all_test_cases()
        by_category = {}
        for case in all_cases:
            for error in case.known_errors:
                category = error.category.value
                if category not in by_category:
                    by_category[category] = []
                if case not in by_category[category]:
                    by_category[category].append(case)
        
        selected_cases = []
        categories = list(by_category.keys())
        cases_per_category = max(1, count // len(categories))
        
        for category in categories:
            category_cases = by_category[category][:cases_per_category]
            selected_cases.extend(category_cases)
            if len(selected_cases) >= count:
                break
        
        return selected_cases[:count]
    
    async def _evaluate_without_context(self, test_cases: List) -> List:
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] Testing {test_case.id} (no context)")
            review_output = await self._get_basic_gpt4_review(test_case)
            detected_errors = ErrorDetectionParser.parse_review_output(review_output, "GPT-4 (No Context)")
            result = MetricsCalculator.evaluate_test_case(test_case, detected_errors, "GPT-4 (No Context)")
            results.append(result)
            print(f"    TP: {len(result.true_positives)}, FP: {len(result.false_positives)}, FN: {len(result.false_negatives)}")
        return results
    
    async def _evaluate_with_dicl_context(self, test_cases: List) -> List:
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] Testing {test_case.id} (with DICL)")
            review_output = await self._get_dicl_enhanced_review(test_case)
            detected_errors = ErrorDetectionParser.parse_review_output(review_output, "GPT-4 (With DICL)")
            result = MetricsCalculator.evaluate_test_case(test_case, detected_errors, "GPT-4 (With DICL)")
            results.append(result)
            print(f"    TP: {len(result.true_positives)}, FP: {len(result.false_positives)}, FN: {len(result.false_negatives)}")
        return results
    
    async def _get_basic_gpt4_review(self, test_case) -> str:
        from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
        
        basic_prompt = f"""URGENT: Analyze this Kubernetes configuration for CRITICAL SECURITY and RELIABILITY issues.

```yaml
{test_case.code_content}
```

🎯 MANDATORY CHECKS - Find ALL instances of:
1. **SECURITY VIOLATIONS:**
   - privileged: true (allows container escape)
   - runAsUser: 0 (root access)
   - hardcoded secrets/passwords in env vars
   - missing securityContext
   - wildcard RBAC permissions (*)

2. **RELIABILITY ISSUES:**
   - missing resource limits (memory/cpu)
   - port mismatches between service/container
   - maxUnavailable: 100% (total downtime risk)
   - missing readiness/liveness probes

3. **CONFIGURATION ERRORS:**
   - invalid field names or values
   - missing required fields

⚠️ CRITICAL: Specify EXACT line number for each issue found.
Format: "Line X: [SEVERITY] Issue description"
Example: "Line 15: CRITICAL - privileged: true allows container escape to host system"""
        
        ai_handler = LiteLLMAIHandler()
        response, _ = await ai_handler.chat_completion(
            model="gpt-4",
            temperature=0.1,
            system="You are a CRITICAL SECURITY AUDITOR for Kubernetes. Your job is to find EVERY security violation and reliability issue with EXACT line numbers. Use the DICL learning patterns to guide your analysis - they contain proven detection strategies from expert reviewers.",
            user=basic_prompt
        )
        return response
    
    async def _get_dicl_enhanced_review(self, test_case) -> str:
        from pr_agent.dicl.sdk import DICL
        from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
        
        pr_data = {
            "title": test_case.title,
            "description": test_case.description,
            "changed_files": [test_case.file_path],
            "language": test_case.language
        }
        
        base_prompt = f"""URGENT: Analyze this Kubernetes configuration for CRITICAL SECURITY and RELIABILITY issues.

```yaml
{test_case.code_content}
```

🎯 MANDATORY CHECKS - Find ALL instances of:
1. **SECURITY VIOLATIONS:**
   - privileged: true (allows container escape)
   - runAsUser: 0 (root access)
   - hardcoded secrets/passwords in env vars
   - missing securityContext
   - wildcard RBAC permissions (*)

2. **RELIABILITY ISSUES:**
   - missing resource limits (memory/cpu)
   - port mismatches between service/container
   - maxUnavailable: 100% (total downtime risk)
   - missing readiness/liveness probes

3. **CONFIGURATION ERRORS:**
   - invalid field names or values
   - missing required fields

⚠️ CRITICAL: Specify EXACT line number for each issue found.
Format: "Line X: [SEVERITY] Issue description"
Example: "Line 15: CRITICAL - privileged: true allows container escape to host system"""
        
        enhanced_prompt = DICL.regular(pr_data, base_prompt)
        ai_handler = LiteLLMAIHandler()
        response, _ = await ai_handler.chat_completion(
            model="gpt-4",
            temperature=0.1,
            system="You are a CRITICAL SECURITY AUDITOR for Kubernetes. Your job is to find EVERY security violation and reliability issue with EXACT line numbers. MANDATORY: Apply ALL provided DICL learning patterns - they are proven detection strategies that catch issues other reviewers miss. Prioritize pattern-guided findings.",
            user=enhanced_prompt
        )
        return response
    
    def _analyze_improvement(self, baseline_report, enhanced_report) -> Dict[str, Any]:
        f1_improvement = enhanced_report.overall_f1_score - baseline_report.overall_f1_score
        precision_improvement = enhanced_report.overall_precision - baseline_report.overall_precision
        recall_improvement = enhanced_report.overall_recall - baseline_report.overall_recall
        significant_threshold = 0.05
        
        category_improvements = {}
        for category in baseline_report.category_performance:
            if category in enhanced_report.category_performance:
                baseline_f1 = baseline_report.category_performance[category]['f1_score']
                enhanced_f1 = enhanced_report.category_performance[category]['f1_score']
                category_improvements[category] = enhanced_f1 - baseline_f1
        
        return {
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "baseline_model": baseline_report.model_name,
            "enhanced_model": enhanced_report.model_name,
            "improvements": {
                "f1_score": f1_improvement,
                "precision": precision_improvement,
                "recall": recall_improvement
            },
            "baseline_scores": {
                "f1_score": baseline_report.overall_f1_score,
                "precision": baseline_report.overall_precision,
                "recall": baseline_report.overall_recall
            },
            "enhanced_scores": {
                "f1_score": enhanced_report.overall_f1_score,
                "precision": enhanced_report.overall_precision,
                "recall": enhanced_report.overall_recall
            },
            "category_improvements": category_improvements,
            "significant_improvement": f1_improvement >= significant_threshold,
            "improvement_percentage": (f1_improvement / baseline_report.overall_f1_score * 100) if baseline_report.overall_f1_score > 0 else 0,
            "conclusion": self._generate_conclusion(f1_improvement, significant_threshold)
        }
    
    def _generate_conclusion(self, f1_improvement: float, threshold: float) -> str:
        if f1_improvement >= threshold:
            return f"✅ DICL significantly improves GPT-4 performance by {f1_improvement:.3f} F1 points"
        elif f1_improvement > 0:
            return f"🟡 DICL shows modest improvement of {f1_improvement:.3f} F1 points (below significance threshold)"
        elif abs(f1_improvement) < 0.01:
            return f"➖ DICL shows no meaningful change in performance ({f1_improvement:+.3f} F1 points)"
        else:
            return f"❌ DICL appears to hurt performance by {abs(f1_improvement):.3f} F1 points"
    

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test DICL Context Impact on GPT-4 Performance')
    parser.add_argument('--test-cases', type=int, default=15, help='Number of test cases to use (default: 15)')
    args = parser.parse_args()
    
    tester = DICLImprovementTester()
    print("🎯 DICL Context Impact Evaluation")
    
    start_time = time.time()
    analysis = await tester.test_dicl_improvement(args.test_cases)
    total_time = time.time() - start_time
    
    print(f"\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    print(f"⏱️  Total Test Time: {total_time:.1f} seconds")
    print(f"📊 Test Cases: {args.test_cases}")
    print()
    print(f"📈 F1 Score Improvement: {analysis['improvements']['f1_score']:+.3f}")
    print(f"📈 Precision Improvement: {analysis['improvements']['precision']:+.3f}")
    print(f"📈 Recall Improvement: {analysis['improvements']['recall']:+.3f}")
    print(f"📊 Relative Improvement: {analysis['improvement_percentage']:+.1f}%")
    print()
    print(f"🎯 {analysis['conclusion']}")
    print()
    
    print("📂 Category-wise Improvements:")
    for category, improvement in analysis['category_improvements'].items():
        status = "🟢" if improvement > 0.05 else "🔴" if improvement < -0.05 else "🟡"
        print(f"  {status} {category.replace('_', ' ').title()}: {improvement:+.3f}")

if __name__ == "__main__":
    asyncio.run(main())