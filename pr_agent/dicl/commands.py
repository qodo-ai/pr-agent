class DICLEvolve:
    def __init__(self, pr_url: str, ai_handler=None, args: list = None):
        self.pr_url = pr_url
        self.args = args or []
        self.ai_handler = ai_handler

    async def run(self):
        print("🧬 Starting automated multi-model learning...")

        from pr_agent.git_providers import get_git_provider_with_context
        git_provider = get_git_provider_with_context(self.pr_url)
        files = git_provider.get_files()
        patches_diff = ""
        for file in files[:10]:
            patches_diff += f"\n--- {file.filename}\n{file.patch[:500]}...\n"
        from pr_agent.git_providers.git_provider import get_main_pr_language
        languages = git_provider.get_languages()
        main_language = get_main_pr_language(languages, files)
        pr_data = {
            "pr_url": self.pr_url,
            "pr_id": self.pr_url.split("/")[-1] if "/" in self.pr_url else "unknown",
            "title": git_provider.pr.title,
            "description": git_provider.get_pr_description()[0] if git_provider.get_pr_description() else "",
            "diff": patches_diff,
            "language": main_language,
            "changed_files": [f.filename for f in files][:10]
        }

        base_prompt = f"""PULL REQUEST ANALYSIS REQUEST

## Context
- **Title**: {pr_data['title']}
- **Description**: {pr_data['description']}
- **Language**: {pr_data['language']}
- **Files Modified**: {len(pr_data['changed_files'])} files

## Code Changes
```diff
{patches_diff[:3000]}
```

## Analysis Requirements

**PRIORITY ASSESSMENT AREAS:**
1. **Security**: Authentication, authorization, input validation, data exposure
2. **Correctness**: Logic errors, boundary conditions, algorithmic flaws
3. **Performance**: Scalability bottlenecks, resource utilization, query optimization
4. **Maintainability**: Code complexity, documentation, architectural consistency
5. **Reliability**: Error handling, edge cases, failure recovery mechanisms

**OUTPUT STRUCTURE:**
```
## Executive Summary
[2-3 sentence overview of change quality and risk level]

## Critical Issues (if any)
- [Issue]: [Location] - [Impact] - [Solution]

## High Priority Issues  
- [Issue]: [Location] - [Impact] - [Solution]

## Medium Priority Issues
- [Issue]: [Location] - [Impact] - [Solution]

## Recommendations
[Prioritized action items with implementation guidance]
```

**ANALYSIS GUIDELINES:**
- Reference specific files and line numbers for each issue
- Quantify business impact where possible (performance, security risk, etc.)
- Provide actionable remediation steps with code examples
- Consider the change within broader system architecture
- Focus on issues that could cause production problems

Conduct a thorough technical analysis and provide professional, constructive feedback."""

        from pr_agent.dicl.auto_learning import DualModelReviewer
        dual_reviewer = DualModelReviewer()
        final_review, insights_count = await dual_reviewer.dual_review_with_learning(pr_data, base_prompt)
        print("\n" + "="*80)
        print("🧬 DICL Multi-Model Enhanced Review")
        print("="*80)
        print(final_review)
        print("="*80)

        if insights_count > 0:
            print(f"\n🧠 Automated Learning: Generated {insights_count} new insights from model comparison")

        return f"Multi-model review completed with {insights_count} learning insights"

