import asyncio
import copy
import re
import traceback
from datetime import datetime
from functools import partial
from typing import Dict, List

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import (add_ai_metadata_to_diff_files,
                                         get_pr_diff, get_pr_multi_diffs,
                                         retry_with_fallback_models)
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import ModelType, load_yaml
from pr_agent.beekeeper.guidelines.beekeeper_style_guidelines_fetcher import BeekeeperStyleGuidelinesFetcher
from pr_agent.beekeeper.tools.beekeeper_pr_best_practices_formatter import BeekeeperPRBestPracticesFormatter
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider_with_context
from pr_agent.git_providers.git_provider import get_main_pr_language, GitProvider
from pr_agent.log import get_logger

class BeekeeperPRBestPracticesCheck:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None,
                 ai_handler: partial[BaseAiHandler] = LiteLLMAIHandler):
        self.git_provider = get_git_provider_with_context(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        if get_settings().pr_best_practices.max_context_tokens:
            MAX_CONTEXT_TOKENS = get_settings().pr_best_practices.max_context_tokens
            if get_settings().config.max_model_tokens > MAX_CONTEXT_TOKENS:
                get_logger().info(f"Setting max_model_tokens to {MAX_CONTEXT_TOKENS} for PR best practices check")
                get_settings().config.max_model_tokens_original = get_settings().config.max_model_tokens
                get_settings().config.max_model_tokens = MAX_CONTEXT_TOKENS

        self.is_extended = self._get_is_extended(args or [])
        num_checks = int(get_settings().pr_best_practices.num_code_suggestions_per_chunk)

        self.ai_handler = ai_handler()
        self.ai_handler.main_pr_language = self.main_language
        self.patches_diff = None
        self.prediction = None
        self.pr_url = pr_url
        self.cli_mode = cli_mode
        self.pr_description, self.pr_description_files = (
            self.git_provider.get_pr_description(split_changes_walkthrough=True))
        if (self.pr_description_files and get_settings().get("config.is_auto_command", False) and
                get_settings().get("config.enable_ai_metadata", False)):
            add_ai_metadata_to_diff_files(self.git_provider, self.pr_description_files)
            get_logger().debug(f"AI metadata added to this command")
        else:
            get_settings().set("config.enable_ai_metadata", False)
            get_logger().debug(f"AI metadata is disabled for this command")

        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.pr_description,
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "diff_no_line_numbers": "",  # empty diff for initial calculation
            "num_code_suggestions": num_checks,
            "extra_instructions": get_settings().pr_best_practices.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
            "is_ai_metadata": get_settings().get("config.enable_ai_metadata", False),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "duplicate_prompt_examples": get_settings().config.get('duplicate_prompt_examples', False),
        }

        self.best_practices = self._get_best_practices()
        self.vars["best_practices"] = self.best_practices
        self.pr_best_practices_prompt_system = get_settings().beekeeper_pr_best_practices_prompt.system

        self.token_handler = TokenHandler(
            self.git_provider.pr,
            self.vars,
            self.pr_best_practices_prompt_system,
            get_settings().beekeeper_pr_best_practices_prompt.user
        )

        self.progress = "## Beekeeper PR Guidelines Check 📏\n\n"
        self.progress += """\nWork in progress ...<br>\n<img src="https://codium.ai/images/pr_agent/dual_ball_loading-crop.gif" width=48>"""
        self.progress_response = None

    def _get_best_practices(self):
        try:
            fetcher = BeekeeperStyleGuidelinesFetcher()
            # Get file extensions from the PR files
            file_paths = [f.filename for f in self.git_provider.get_files()]
            get_logger().info(f"File paths in PR: {file_paths}")

            # Fetch guidelines relevant to the PR's file types
            relevant_guidelines = fetcher.get_relevant_guidelines(file_paths)
            if not relevant_guidelines:
                get_logger().warning(f"No relevant guidelines found for PR files")
                return ''
            get_logger().info(f"Found {len(relevant_guidelines)} relevant guidelines for PR files")

            # Format the guidelines into the expected format
            formatted_guidelines =  BeekeeperPRBestPracticesFormatter().format_guidelines(relevant_guidelines)
            get_logger().debug(f"Formatted guidelines: {formatted_guidelines}")
            return formatted_guidelines
        except Exception as e:
            get_logger().error(f"Error fetching best practices, falling back to defaults: {e}")
            return ''


    async def run(self):
        try:
            if not self.git_provider.get_files():
                get_logger().info(f"PR has no files: {self.pr_url}, skipping best practices check")
                return None

            get_logger().info('Checking PR for best practices compliance...')
            relevant_configs = {'pr_best_practices': dict(get_settings().pr_best_practices),
                                'config': dict(get_settings().config)}
            get_logger().debug("Relevant configs", artifacts=relevant_configs)

            if (get_settings().config.publish_output and get_settings().config.publish_output_progress and
                    not get_settings().config.get('is_auto_command', False)):
                if self.git_provider.is_supported("gfm_markdown"):
                    self.progress_response = self.git_provider.publish_comment(self.progress)
                else:
                    self.git_provider.publish_comment("Preparing best practices check...", is_temporary=True)

            if not self.is_extended:
                data = await retry_with_fallback_models(self._prepare_prediction, model_type=ModelType.REGULAR)
            else:
                data = await retry_with_fallback_models(self._prepare_prediction_extended, model_type=ModelType.REGULAR)
            if not data:
                data = {"best_practice_checks": []}
            self.data = data

            if not data.get('best_practice_checks'):
                await self.publish_no_issues()
                return

            if get_settings().config.publish_output:
                self.git_provider.remove_initial_comment()

                pr_body = self._generate_pr_comment(data)
                get_logger().debug(f"PR output", artifact=pr_body)

                if get_settings().pr_best_practices.persistent_comment:
                    self.publish_persistent_comment_with_history(
                        self.git_provider,
                        pr_body,
                        initial_header="## Beekeeper PR Guidelines Check 📏",
                        update_header=True,
                        name="best_practices",
                        final_update_message=False,
                        max_previous_comments=get_settings().pr_best_practices.max_history_len,
                        progress_response=self.progress_response
                    )
                else:
                    if self.progress_response:
                        self.git_provider.edit_comment(self.progress_response, body=pr_body)
                    else:
                        self.git_provider.publish_comment(pr_body)
            else:
                get_logger().info('Best practices check completed, but not published.')
                pr_body = self._generate_pr_comment(data)
                get_settings().data = {"artifact": pr_body}
        except Exception as e:
            get_logger().error(f"Failed to check best practices for PR, error: {e}",
                               artifact={"traceback": traceback.format_exc()})
            if get_settings().config.publish_output:
                if self.progress_response:
                    self.progress_response.delete()
                else:
                    self.git_provider.remove_initial_comment()
                    self.git_provider.publish_comment("Failed to check best practices for PR.")

    async def publish_no_issues(self):
        pr_body = (
            "Congratulations! 🎉 Your PR is compliant with coding standards required by this repository ✅ "
            "Well done 💪"
        )
        if get_settings().config.publish_output and get_settings().config.publish_output_no_suggestions:
            get_logger().info('No best practice violations found for the PR.')
            get_logger().debug(f"PR output", artifact=pr_body)
            if self.progress_response:
                self.git_provider.edit_comment(self.progress_response, body=pr_body)
            else:
                self.git_provider.publish_comment(pr_body)
        else:
            get_settings().data = {"artifact": pr_body}

    async def _prepare_prediction(self, model: str) -> dict:
        self.patches_diff = get_pr_diff(
            self.git_provider,
            self.token_handler,
            model,
            add_line_numbers_to_hunks=True,
            disable_extra_lines=False
        )
        self.patches_diff_list = [self.patches_diff]
        self.patches_diff_no_line_number = self.remove_line_numbers([self.patches_diff])[0]

        if self.patches_diff:
            get_logger().debug(f"PR diff", artifact=self.patches_diff)
            self.prediction = await self._get_prediction(model, self.patches_diff, self.patches_diff_no_line_number)
        else:
            get_logger().warning(f"Empty PR diff")
            self.prediction = None

        return self.prediction or {"best_practice_checks": []}

    async def _get_prediction(self, model: str, patches_diff: str, patches_diff_no_line_number: str) -> dict:
        variables = copy.deepcopy(self.vars)
        variables["diff"] = patches_diff
        variables["diff_no_line_numbers"] = patches_diff_no_line_number
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(self.pr_best_practices_prompt_system).render(variables)
        user_prompt = environment.from_string(get_settings().beekeeper_pr_best_practices_prompt.user).render(variables)

        get_logger().info(f"Sending request to AI model {model} for best practices check...")
        start_time = datetime.now()
        try:
            response, _ = await self.ai_handler.chat_completion(
                model=model,
                temperature=get_settings().config.temperature,
                system=system_prompt,
                user=user_prompt
            )
            get_logger().info(f"Received AI response in {(datetime.now() - start_time).total_seconds()} seconds")
            return self._prepare_pr_best_practices(response)
        except Exception as e:
            get_logger().error(f"Error getting AI prediction: {e}")
            raise

    def _prepare_pr_best_practices(self, predictions: str) -> Dict:
        data = load_yaml(
            predictions.strip(),
            keys_fix_yaml=["relevant_file", "non_compliant_issue", "existing_code", "suggested_fix"],
            first_key="best_practice_checks",
            last_key="category"
        )
        if isinstance(data, list):
            data = {'best_practice_checks': data}
        return data

    def remove_line_numbers(self, patches_diff_list: List[str]) -> List[str]:
        try:
            patches_diff_list_no_line_numbers = []
            for patches_diff in patches_diff_list:
                patches_diff_lines = patches_diff.splitlines()
                for i, line in enumerate(patches_diff_lines):
                    if line.strip():
                        if line.isnumeric():
                            patches_diff_lines[i] = ''
                        elif line[0].isdigit():
                            for j, char in enumerate(line):
                                if not char.isdigit():
                                    patches_diff_lines[i] = line[j + 1:]
                                    break
                patches_diff_list_no_line_numbers.append('\n'.join(patches_diff_lines))
            return patches_diff_list_no_line_numbers
        except Exception as e:
            get_logger().error(f"Error removing line numbers from patches_diff_list, error: {e}")
            return patches_diff_list

    async def _prepare_prediction_extended(self, model: str) -> dict:
        self.patches_diff_list = get_pr_multi_diffs(
            self.git_provider,
            self.token_handler,
            model,
            max_calls=get_settings().pr_best_practices.max_number_of_calls
        )
        self.patches_diff_list_no_line_numbers = self.remove_line_numbers(self.patches_diff_list)

        if self.patches_diff_list:
            get_logger().info(f"Number of PR chunk calls: {len(self.patches_diff_list)}")
            get_logger().debug(f"PR diff:", artifact=self.patches_diff_list)

            if get_settings().pr_best_practices.parallel_calls:
                prediction_list = await asyncio.gather(
                    *[self._get_prediction(model, patches_diff, patches_diff_no_line_numbers)
                      for patches_diff, patches_diff_no_line_numbers in
                      zip(self.patches_diff_list, self.patches_diff_list_no_line_numbers)]
                )
            else:
                prediction_list = []
                for patches_diff, patches_diff_no_line_numbers in zip(self.patches_diff_list, self.patches_diff_list_no_line_numbers):
                    prediction = await self._get_prediction(model, patches_diff, patches_diff_no_line_numbers)
                    prediction_list.append(prediction)

            data = {"best_practice_checks": []}
            for predictions in prediction_list:
                if "best_practice_checks" in predictions:
                    data["best_practice_checks"].extend(predictions["best_practice_checks"])
            self.data = data
        else:
            get_logger().warning(f"Empty PR diff list")
            self.data = None
        return data or {"best_practice_checks": []}

    def _generate_pr_comment(self, data: Dict) -> str:
        checks = data.get('best_practice_checks', [])
        if not checks:
            return (
                "Congratulations! 🎉 Your PR is compliant with coding standards required by this repository ✅ "
                "Well done 💪"
            )
        pr_body = (
            "Your PR is not compliant with coding standards required by this repository ❌\n\n"
            "Please make adjustments to the following places:\n"
        )
        for check in checks:
            pr_body += (
                f"- **File:** `{check['relevant_file']}`\n"
                f"  **Issue:** {check['non_compliant_issue']}\n"
                f"  **Category:** {check['category']}\n"
                f"  **Current Code:**\n```python\n{check['existing_code']}\n```\n"
                f"  **Suggested Fix:**\n```python\n{check['suggested_fix']}\n```\n"
            )
        return pr_body

    def _get_is_extended(self, args: list[str]) -> bool:
        if any(["extended" in arg for arg in args]):
            get_logger().info("Extended mode is enabled by the `--extended` flag")
            return True
        if get_settings().pr_best_practices.auto_extended_mode:
            return True
        return False

    @staticmethod
    def publish_persistent_comment_with_history(git_provider: GitProvider,
                                                pr_comment: str,
                                                initial_header: str,
                                                update_header: bool = True,
                                                name='review',
                                                final_update_message=True,
                                                max_previous_comments=4,
                                                progress_response=None,
                                                only_fold=False):
        def _extract_link(comment_text: str):
            r = re.compile(r"<!--.*?-->")
            match = r.search(comment_text)
            up_to_commit_txt = ""
            if match:
                up_to_commit_txt = f" up to commit {match.group(0)[4:-3].strip()}"
            return up_to_commit_txt

        history_header = f"#### Previous checks\n"
        last_commit_num = git_provider.get_latest_commit_url().split('/')[-1][:7]
        latest_suggestion_header = f"Latest checks up to {last_commit_num}"
        latest_commit_html_comment = f"<!-- {last_commit_num} -->"
        found_comment = None

        if max_previous_comments > 0:
            try:
                prev_comments = list(git_provider.get_issue_comments())
                for comment in prev_comments:
                    if comment.body.startswith(initial_header):
                        prev_checks = comment.body
                        found_comment = comment
                        comment_url = git_provider.get_comment_url(comment)

                        if history_header.strip() not in comment.body:
                            table_index = comment.body.find("<table>")
                            if table_index == -1:
                                git_provider.edit_comment(comment, pr_comment)
                                continue
                            up_to_commit_txt = _extract_link(comment.body[:table_index])
                            prev_check_table = comment.body[
                                               table_index:comment.body.rfind("</table>") + len("</table>")]
                            tick = "✅ " if "✅" in prev_check_table else ""
                            prev_check_table = f"<details><summary>{tick}{name.capitalize()}{up_to_commit_txt}</summary>\n<br>{prev_check_table}\n\n</details>"

                            new_check_table = pr_comment.replace(initial_header, "").strip()
                            pr_comment_updated = f"{initial_header}\n{latest_commit_html_comment}\n\n"
                            pr_comment_updated += f"{latest_suggestion_header}\n{new_check_table}\n\n___\n\n"
                            pr_comment_updated += f"{history_header}{prev_check_table}\n"
                        else:
                            sections = prev_checks.split(history_header.strip())
                            latest_table = sections[0].strip()
                            prev_check_table = sections[1].replace(history_header, "").strip()

                            table_ind = latest_table.find("<table>")
                            up_to_commit_txt = _extract_link(latest_table[:table_ind])
                            latest_table = latest_table[table_ind:latest_table.rfind("</table>") + len("</table>")]
                            count = prev_checks.count(f"\n<details><summary>{name.capitalize()}")
                            count += prev_checks.count(f"\n<details><summary>✅ {name.capitalize()}")
                            if count >= max_previous_comments:
                                prev_check_table = prev_check_table[:prev_check_table.rfind(
                                    f"<details><summary>{name.capitalize()} up to commit")]

                            tick = "✅ " if "✅" in latest_table else ""
                            last_prev_table = f"\n<details><summary>{tick}{name.capitalize()}{up_to_commit_txt}</summary>\n<br>{latest_table}\n\n</details>"
                            prev_check_table = last_prev_table + "\n" + prev_check_table

                            new_check_table = pr_comment.replace(initial_header, "").strip()
                            pr_comment_updated = f"{initial_header}\n{latest_commit_html_comment}\n\n"
                            pr_comment_updated += f"{latest_suggestion_header}\n{new_check_table}\n\n___\n\n"
                            pr_comment_updated += f"{history_header}{prev_check_table}\n"

                        get_logger().info(f"Persistent mode - updating comment {comment_url} to latest {name} message")
                        if progress_response:
                            git_provider.edit_comment(progress_response, pr_comment_updated)
                            git_provider.remove_comment(comment)
                            comment = progress_response
                        else:
                            git_provider.edit_comment(comment, pr_comment_updated)
                        return comment
            except Exception as e:
                get_logger().exception(f"Failed to update persistent check, error: {e}")
