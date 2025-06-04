import json
from pathlib import Path
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
from pr_agent.git_providers import get_git_provider_with_context, GithubProvider # Assuming GithubProvider for now
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.git_patch_processing import extract_hunk_lines_from_patch
from jinja2 import Environment, StrictUndefined


class PRImpactValidator:
    def __init__(self, pr_url: str, suggestions_commit_sha: str, new_commit_sha: str):
        self.pr_url = pr_url
        self.suggestions_commit_sha = suggestions_commit_sha
        self.new_commit_sha = new_commit_sha
        self.git_provider = get_git_provider_with_context(pr_url)
        self.original_suggestions = None
        self.analysis_results = []

        # Add these lines for AI Handler initialization
        try:
            # Assuming LiteLLMAIHandler constructor takes the model name from settings
            model_name = get_settings().config.model
            self.ai_handler = LiteLLMAIHandler(model_name)
            get_logger().info(f"ImpactValidator: AI Handler initialized with model {model_name}")
        except Exception as e:
            get_logger().error(f"ImpactValidator: Failed to initialize AI Handler: {e}", exc_info=True)
            self.ai_handler = None

        self._load_original_suggestions()

    def _load_original_suggestions(self):
        try:
            pr_id_str = self.git_provider.get_pr_id()
            if not pr_id_str:
                get_logger().error("ImpactValidator: Failed to get PR ID, cannot load suggestions.")
                return

            sane_pr_id = pr_id_str.replace('/', '_')
            suggestions_file = Path(f".pr_agent_data/suggestions/{sane_pr_id}/{self.suggestions_commit_sha}.json")

            if not suggestions_file.exists():
                get_logger().error(f"ImpactValidator: Suggestions file not found: {suggestions_file}")
                return

            with open(suggestions_file, 'r') as f:
                self.original_suggestions = json.load(f)
            get_logger().info(f"ImpactValidator: Successfully loaded suggestions from {suggestions_file}")

        except FileNotFoundError:
            get_logger().error(f"ImpactValidator: Suggestions file not found at {suggestions_file}")
        except json.JSONDecodeError as e:
            get_logger().error(f"ImpactValidator: Error decoding JSON from {suggestions_file}: {e}")
        except Exception as e:
            get_logger().error(f"ImpactValidator: An unexpected error occurred while loading suggestions: {e}", exc_info=True)

    async def analyze_commit_async(self):
        if not self.original_suggestions or 'code_suggestions' not in self.original_suggestions:
            get_logger().warning("ImpactValidator: No original suggestions loaded or suggestions are malformed.")
            return []

        if not self.ai_handler:
            get_logger().error("ImpactValidator: AI Handler not initialized. Cannot perform indirect checks effectively.")
            # Decide if to proceed with direct checks only or return. For now, returning.
            return []

        get_logger().info(f"ImpactValidator: Analyzing commit {self.new_commit_sha} against suggestions from {self.suggestions_commit_sha}")

        try:
            diff_files = self.git_provider.get_diff_between_commits(self.suggestions_commit_sha, self.new_commit_sha)
            if diff_files is None:
                 get_logger().error("ImpactValidator: Failed to get diff between commits. Aborting analysis.")
                 return []
        except Exception as e:
            get_logger().error(f"ImpactValidator: Error getting diff between commits: {e}", exc_info=True)
            return []

        self.analysis_results = []
        for suggestion in self.original_suggestions['code_suggestions']:
            implemented_status = "pending"
            explanation = ""
            relevant_file_path = suggestion.get('relevant_file', '').strip()
            changed_file_info = next((df for df in diff_files if df.filename == relevant_file_path), None)
            analysed_file_found_in_diff = changed_file_info is not None

            # Direct Implementation Check
            if changed_file_info and changed_file_info.head_file is not None:
                try:
                    suggested_code_snippet = suggestion.get('improved_code', '').strip()
                    if suggested_code_snippet:
                        normalized_suggested_snippet = "\n".join(line.strip() for line in suggested_code_snippet.splitlines() if line.strip())
                        new_file_content = changed_file_info.head_file
                        normalized_new_file_content_lines = [line.strip() for line in new_file_content.splitlines() if line.strip()]
                        normalized_new_file_content_for_search = "\n".join(normalized_new_file_content_lines)

                        if normalized_suggested_snippet and normalized_suggested_snippet in normalized_new_file_content_for_search:
                            implemented_status = "direct"
                            explanation = "The suggested code snippet (or a normalized version) was found in the updated file."
                            get_logger().info(f"Direct implementation found for suggestion in {relevant_file_path}: {suggestion.get('one_sentence_summary')}")
                except Exception as e:
                    get_logger().error(f"Error during direct implementation check for {relevant_file_path}: {e}", exc_info=True)

            # Indirect Implementation Check (AI-based)
            if implemented_status == "pending" and changed_file_info and changed_file_info.patch:
                try:
                    hunk_patch, _ = extract_hunk_lines_from_patch(
                        patch=changed_file_info.patch,
                        file_name=relevant_file_path,
                        line_start=suggestion.get('relevant_lines_start', 0),
                        line_end=suggestion.get('relevant_lines_end', 0),
                        side='left'
                    )

                    if not hunk_patch.strip():
                        get_logger().warning(f"Could not extract relevant hunk for {relevant_file_path}, lines {suggestion.get('relevant_lines_start')}-{suggestion.get('relevant_lines_end')}. Skipping indirect check.")
                    else:
                        default_prompt_str = (
                            "Analyze the following code suggestion and the provided code patch (diff).\n"
                            "Determine if the *intent* of the original suggestion was implemented in the new code, even if the exact code differs.\n\n"
                            "Original Suggestion:\n"
                            "File: {{ suggestion.relevant_file }}\n"
                            "Lines: {{ suggestion.relevant_lines_start }}-{{ suggestion.relevant_lines_end }}\n"
                            "Summary: {{ suggestion.one_sentence_summary }}\n"
                            "Content: {{ suggestion.suggestion_content }}\n"
                            "Original Code Snippet (if available):\n"
                            "```\n{{ suggestion.existing_code }}\n```\n"
                            "Suggested Improvement Snippet:\n"
                            "```\n{{ suggestion.improved_code }}\n```\n\n"
                            "Code Patch (Changes made in the new commit relevant to the suggestion area):\n"
                            "```diff\n{{ patch_hunk }}\n```\n\n"
                            "Question: Was the core intent of the original suggestion addressed or implemented by the changes in the code patch?\n"
                            "Respond in JSON format with two keys: \"implemented_indirectly\" (boolean) and \"explanation\" (string, max 100 words).\n"
                            "Your explanation should briefly state how the suggestion's intent was met or why it wasn't.\n"
                            "If the suggestion was about removing or refactoring code, and the code is indeed gone or changed as intended, consider it implemented.\n"
                            "If the patch is empty or doesn't relate to the suggestion, assume not implemented."
                        )
                        prompt_template_from_config = get_settings().get("impact_validator.indirect_check_prompt", default_prompt_str)

                        environment = Environment(undefined=StrictUndefined)
                        template = environment.from_string(prompt_template_from_config)
                        rendered_prompt = template.render(suggestion=suggestion, patch_hunk=hunk_patch)

                        response_json_str, _ = await self.ai_handler.chat_completion(
                            model=get_settings().config.model,
                            temperature=0.2,
                            system="You are an AI assistant helping to determine if a code suggestion was implemented.",
                            user=rendered_prompt
                        )

                        ai_response_data = json.loads(response_json_str) # Ensure json is imported
                        if ai_response_data.get("implemented_indirectly", False):
                            implemented_status = "indirect"
                            explanation = ai_response_data.get("explanation", "AI determined the suggestion was implemented indirectly.")
                            get_logger().info(f"Indirect implementation found by AI for suggestion in {relevant_file_path}: {suggestion.get('one_sentence_summary')}")
                        else:
                            current_ai_explanation = ai_response_data.get("explanation", "AI determined the suggestion was not implemented or the changes were unrelated.")
                            explanation = current_ai_explanation if current_ai_explanation else explanation
                            get_logger().info(f"AI determined suggestion not implemented or unrelated for {relevant_file_path}: {suggestion.get('one_sentence_summary')}")

                except json.JSONDecodeError: # Ensure json is imported for this exception
                    get_logger().error(f"Failed to parse AI JSON response for indirect check on {relevant_file_path}.", exc_info=True)
                    explanation = "Error parsing AI response for indirect implementation."
                except Exception as e:
                    get_logger().error(f"Error during indirect AI check for {relevant_file_path}: {e}", exc_info=True)
                    explanation = "Error during AI-based indirect implementation check."

            self.analysis_results.append({
                "original_suggestion": suggestion,
                "implemented_status": implemented_status,
                "explanation": explanation,
                "new_commit_sha": self.new_commit_sha,
                "analysed_file_found_in_diff": analysed_file_found_in_diff
            })
            get_logger().debug(f"ImpactValidator: Processed suggestion for file '{relevant_file_path}': {suggestion.get('one_sentence_summary')}, status: {implemented_status}")

        get_logger().info(f"ImpactValidator: Analysis complete. Processed {len(self.analysis_results)} suggestions.")
        return self.analysis_results

# Example usage (for testing purposes, will be removed or commented out)
if __name__ == '__main__':
    # This part is for illustration and won't be part of the actual tool file submitted
    # Mocking necessary components for a local test run

    # Create dummy suggestions file
    dummy_pr_id = "myuser_myrepo/1"
    dummy_sane_pr_id = "myuser_myrepo_1"
    dummy_suggestions_commit = "abcdef1234567890"
    dummy_new_commit = "fedcba0987654321"

    suggestions_dir = Path(f".pr_agent_data/suggestions/{dummy_sane_pr_id}")
    suggestions_dir.mkdir(parents=True, exist_ok=True)
    dummy_suggestions_file = suggestions_dir / f"{dummy_suggestions_commit}.json"

    dummy_data = {
        "code_suggestions": [
            {
                "one_sentence_summary": "Use a more efficient loop",
                "label": "Performance",
                "relevant_file": "src/main.py",
                "relevant_lines_start": 10,
                "relevant_lines_end": 15,
                "suggestion_content": "The current loop can be optimized.",
                "existing_code": "for i in range(n):\n  print(i)",
                "improved_code": "for i in range(n):\n  pass # Optimized"
            }
        ]
    }
    with open(dummy_suggestions_file, 'w') as f:
        json.dump(dummy_data, f)

    # Mock Git Provider (very basic)
    class MockGitProvider:
        def get_pr_id(self):
            return dummy_pr_id
        def get_diff_between_commits(self, old_sha, new_sha): # Placeholder
            get_logger().info(f"MockGitProvider: get_diff_between_commits({old_sha}, {new_sha}) called")
            return []

    # Replace actual provider with mock for local test
    original_get_provider = get_git_provider_with_context
    get_git_provider_with_context = lambda url: MockGitProvider()

    print(f"Attempting to initialize PRImpactValidator with PR URL: any_url, suggestions_commit_sha: {dummy_suggestions_commit}, new_commit_sha: {dummy_new_commit}")
    validator = PRImpactValidator("any_url", dummy_suggestions_commit, dummy_new_commit)
    if validator.original_suggestions:
        print("Validator initialized, original suggestions loaded.")
        results = validator.analyze_commit()
        print(f"Analysis results: {results}")
    else:
        print("Validator initialization failed or no suggestions loaded.")

    # Clean up dummy file
    # dummy_suggestions_file.unlink() # Comment out if you want to inspect the file

    # Restore original provider
    get_git_provider_with_context = original_get_provider
