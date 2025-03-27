import copy
from functools import partial
from jinja2 import Environment, StrictUndefined
import math
import os
import re
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import clip_tokens, get_max_tokens, load_yaml, ModelType
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider_with_context
from pr_agent.log import get_logger
from pr_agent.servers.help import HelpMessage


#Common code that can be called from similar tools:
def modify_answer_section(ai_response: str) -> str | None:
    # Gets the model's answer and relevant sources section, repacing the heading of the answer section with:
    # :bulb: Auto-generated documentation-based answer:
    """
    For example: The following input:

    ### Question: \nThe following general issue was asked by a user: Title: How does one request to re-review a PR? More Info: I cannot seem to find to do this.
    ### Answer:\nAccording to the documentation, one needs to invoke the command: /review
    #### Relevant Sources...

    Should become:

    ### :bulb: Auto-generated documentation-based answer:\n
    According to the documentation, one needs to invoke the command: /review
    #### Relevant Sources...
    """
    model_answer_and_relevant_sections_in_response \
        = extract_model_answer_and_relevant_sources(ai_response)
    if model_answer_and_relevant_sections_in_response is not None:
        cleaned_question_with_answer = "### :bulb: Auto-generated documentation-based answer:\n"
        cleaned_question_with_answer += model_answer_and_relevant_sections_in_response
        return cleaned_question_with_answer
    get_logger().warning(f"Either no answer section found, or that section is malformed: {ai_response}")
    return None

def extract_model_answer_and_relevant_sources(ai_response: str) -> str | None:
    # It is assumed that the input contains several sections with leading "### ",
    # where the answer is the last one of them having the format: "### Answer:\n"), since the model returns the answer
    # AFTER the user question. By splitting using the string: "### Answer:\n" and grabbing the last part,
    # the model answer is guaranteed to be in that last part, provided it is followed by a "#### Relevant Sources:\n\n".
    # (for more details, see here: https://github.com/Codium-ai/pr-agent-pro/blob/main/pr_agent/tools/pr_help_message.py#L173)
    """
    For example:
    ### Question: \nHow does one request to re-review a PR?\n\n
    ### Answer:\nAccording to the documentation, one needs to invoke the command: /review\n\n
    #### Relevant Sources:\n\n...

    The answer part is: "According to the documentation, one needs to invoke the command: /review\n\n"
    followed by "Relevant Sources:\n\n".
    """
    if "### Answer:\n" in ai_response:
        model_answer_and_relevant_sources_sections_in_response = ai_response.split("### Answer:\n")[-1]
        # Split such part by "Relevant Sources" section to contain only the model answer:
        if "#### Relevant Sources:\n\n" in model_answer_and_relevant_sources_sections_in_response:
            model_answer_section_in_response \
                = model_answer_and_relevant_sources_sections_in_response.split("#### Relevant Sources:\n\n")[0]
            get_logger().info(f"Found model answer: {model_answer_section_in_response}")
            return model_answer_and_relevant_sources_sections_in_response \
                if len(model_answer_section_in_response) > 0 else None
    get_logger().warning(f"Either no answer section found, or that section is malformed: {ai_response}")
    return None

def get_maximal_text_input_length_for_token_count_estimation():
    model = get_settings().config.model
    if 'claude-3-7-sonnet' in model.lower():
        return 900000 #Claude API for token estimation allows maximal text input of 900K chars
    return math.inf #Otherwise, no known limitation on input text just for token estimation

# Load documentation files to memory, decorating them with a header to mark where each file begins,
# as to help the LLM to give a better answer.
def aggregate_documentation_files_for_prompt_contents(base_path: str, doc_files: List[str]) -> Optional[str]:
    docs_prompt = ""
    for file in doc_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip files with no text content
                if not re.search(r'[a-zA-Z]', content):
                    continue
                file_path = str(file).replace(str(base_path), '')
                docs_prompt += f"\n==file name==\n\n{file_path}\n\n==file content==\n\n{content.strip()}\n=========\n\n"
        except Exception as e:
            get_logger().warning(f"Error while reading the file {file}: {e}")
            continue
    if not docs_prompt:
        get_logger().error("Couldn't find any usable documentation files. Returning None.")
        return None
    return docs_prompt

def format_markdown_q_and_a_response(question_str: str, response_str: str, relevant_sections: List[Dict[str, str]],
                                     supported_suffixes: List[str], base_url_prefix: str, base_url_suffix: str="") -> str:
    base_url_prefix = base_url_prefix.strip('/') #Sanitize base_url_prefix
    answer_str = ""
    answer_str += f"### Question: \n{question_str}\n\n"
    answer_str += f"### Answer:\n{response_str.strip()}\n\n"
    answer_str += f"#### Relevant Sources:\n\n"
    for section in relevant_sections:
        file = section.get('file_name').strip()
        ext = [suffix for suffix in supported_suffixes if file.endswith(suffix)]
        if not ext:
            get_logger().warning(f"Unsupported file extension: {file}")
            continue
        if str(section['relevant_section_header_string']).strip():
            markdown_header = format_markdown_header(section['relevant_section_header_string'])
            if base_url_prefix:
                answer_str += f"> - {base_url_prefix}/{file}{base_url_suffix}#{markdown_header}\n"
        else:
            answer_str += f"> - {base_url_prefix}/{file}{base_url_suffix}\n"
    return answer_str

def format_markdown_header(header: str) -> str:
    try:
        # First, strip common characters from both ends
        cleaned = header.strip('# 💎\n')

        # Define all characters to be removed/replaced in a single pass
        replacements = {
            "'": '',
            "`": '',
            '(': '',
            ')': '',
            ',': '',
            '.': '',
            '?': '',
            '!': '',
            ' ': '-'
        }

        # Compile regex pattern for characters to remove
        pattern = re.compile('|'.join(map(re.escape, replacements.keys())))

        # Perform replacements in a single pass and convert to lowercase
        return pattern.sub(lambda m: replacements[m.group()], cleaned).lower()
    except Exception:
        get_logger().exception(f"Error while formatting markdown header", artifacts={'header': header})
        return ""

def clean_markdown_content(content: str) -> str:
    """
    Remove hidden comments and unnecessary elements from markdown content to reduce size.

    Args:
        content: The original markdown content

    Returns:
        Cleaned markdown content
    """
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Remove frontmatter (YAML between --- or +++ delimiters)
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    content = re.sub(r'^\+\+\+\s*\n.*?\n\+\+\+\s*\n', '', content, flags=re.DOTALL)

    # Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove HTML tags that are often used for styling only
    content = re.sub(r'<div.*?>|</div>|<span.*?>|</span>', '', content, flags=re.DOTALL)

    # Remove image alt text which can be verbose
    content = re.sub(r'!\[(.*?)\]', '![]', content)

    # Remove images completely
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

    # Remove simple HTML tags but preserve content between them
    content = re.sub(r'<(?!table|tr|td|th|thead|tbody)([a-zA-Z][a-zA-Z0-9]*)[^>]*>(.*?)</\1>',
                     r'\2', content, flags=re.DOTALL)
    return content.strip()

class PredictionPreparator:
    def __init__(self, ai_handler, vars, system_prompt, user_prompt):
        self.ai_handler = ai_handler
        variables = copy.deepcopy(vars)
        environment = Environment(undefined=StrictUndefined)
        self.system_prompt = environment.from_string(system_prompt).render(variables)
        self.user_prompt = environment.from_string(user_prompt).render(variables)

    async def __call__(self, model: str) -> str:
        try:
            response, finish_reason = await self.ai_handler.chat_completion(
                model=model, temperature=get_settings().config.temperature, system=self.system_prompt, user=self.user_prompt)
            return response
        except Exception as e:
            get_logger().error(f"Error while preparing prediction: {e}")
            return ""


class PRHelpDocs(object):
    def __init__(self, ctx_url, ai_handler:partial[BaseAiHandler,] = LiteLLMAIHandler, args: Tuple[str]=None, return_as_string: bool=False):
        self.ctx_url = ctx_url
        self.question = args[0] if args else None
        self.return_as_string = return_as_string
        self.repo_url_given_explicitly = True
        self.repo_url = get_settings().get('PR_HELP_DOCS.REPO_URL', '')
        self.repo_desired_branch = get_settings().get('PR_HELP_DOCS.REPO_DEFAULT_BRANCH', 'main') #Ignored if self.repo_url is empty
        self.include_root_readme_file = not(get_settings()['PR_HELP_DOCS.EXCLUDE_ROOT_README'])
        self.supported_doc_exts = get_settings()['PR_HELP_DOCS.SUPPORTED_DOC_EXTS']
        self.docs_path = get_settings()['PR_HELP_DOCS.DOCS_PATH']

        retrieved_settings = [self.include_root_readme_file, self.supported_doc_exts, self.docs_path]
        if any([setting is None for setting in retrieved_settings]):
            raise Exception(f"One of the settings is invalid: {retrieved_settings}")

        self.git_provider = get_git_provider_with_context(ctx_url)
        if not self.git_provider:
            raise Exception(f"No git provider found at {ctx_url}")
        if not self.repo_url:
            self.repo_url_given_explicitly = False
            get_logger().debug(f"No explicit repo url provided, deducing it from type: {self.git_provider.__class__.__name__} "
                              f"context url: {self.ctx_url}")
            self.repo_url = self.git_provider.get_git_repo_url(self.ctx_url)
            if not self.repo_url:
                raise Exception(f"Unable to deduce repo url from type: {self.git_provider.__class__.__name__} url: {self.ctx_url}")
            get_logger().debug(f"deduced repo url: {self.repo_url}")
            self.repo_desired_branch = None #Inferred from the repo provider.

        self.ai_handler = ai_handler()
        self.vars = {
            "docs_url": self.repo_url,
            "question": self.question,
            "snippets": "",
        }
        self.token_handler = TokenHandler(None,
                                              self.vars,
                                              get_settings().pr_help_docs_prompts.system,
                                              get_settings().pr_help_docs_prompts.user)

    async def run(self):
        if not self.question:
            get_logger().warning('No question provided. Will do nothing.')
            return None

        try:
            # Clone the repository and gather relevant documentation files.
            docs_prompt = None
            with TemporaryDirectory() as tmp_dir:
                get_logger().debug(f"About to clone repository: {self.repo_url} to temporary directory: {tmp_dir}...")
                returned_cloned_repo_root = self.git_provider.clone(self.repo_url, tmp_dir, remove_dest_folder=False)
                if not returned_cloned_repo_root:
                    raise Exception(f"Failed to clone {self.repo_url} to {tmp_dir}")

                get_logger().debug(f"About to gather relevant documentation files...")
                doc_files = []
                if self.include_root_readme_file:
                    for root, _, files in os.walk(returned_cloned_repo_root.path):
                        # Only look at files in the root directory, not subdirectories
                        if root == returned_cloned_repo_root.path:
                            for file in files:
                                if file.lower().startswith("readme."):
                                    doc_files.append(os.path.join(root, file))
                abs_docs_path = os.path.join(returned_cloned_repo_root.path, self.docs_path)
                if os.path.exists(abs_docs_path):
                    doc_files.extend(self._find_all_document_files_matching_exts(abs_docs_path,
                                                                                 ignore_readme=(self.docs_path=='.')))
                    if not doc_files:
                        get_logger().warning(f"No documentation files found matching file extensions: "
                                             f"{self.supported_doc_exts} under repo: {self.repo_url} path: {self.docs_path}")
                        return None

                get_logger().info(f'Answering a question inside context {self.ctx_url} for repo: {self.repo_url}'
                                  f' using the following documentation files: ', artifacts={'doc_files': doc_files})

                docs_prompt = aggregate_documentation_files_for_prompt_contents(returned_cloned_repo_root.path, doc_files)
            if not docs_prompt:
                get_logger().warning(f"Error reading one of the documentation files. Returning with no result...")
                return None
            docs_prompt_to_send_to_model = docs_prompt

            # Estimate how many tokens will be needed. Trim in case of exceeding limit.
            # Firstly, check if text needs to be trimmed, as some models fail to return the estimated token count if the input text is too long.
            max_allowed_txt_input = get_maximal_text_input_length_for_token_count_estimation()
            if len(docs_prompt_to_send_to_model) >= max_allowed_txt_input:
                get_logger().warning(f"Text length: {len(docs_prompt_to_send_to_model)} exceeds the current returned limit of {max_allowed_txt_input} just for token count estimation. Trimming the text...")
                docs_prompt_to_send_to_model = docs_prompt_to_send_to_model[:max_allowed_txt_input]
            # Then, count the tokens in the prompt. If the count exceeds the limit, trim the text.
            token_count = self.token_handler.count_tokens(docs_prompt_to_send_to_model, force_accurate=True)
            get_logger().debug(f"Estimated token count of documentation to send to model: {token_count}")
            model = get_settings().config.model
            if model in MAX_TOKENS:
                max_tokens_full = MAX_TOKENS[model] # note - here we take the actual max tokens, without any reductions. we do aim to get the full documentation website in the prompt
            else:
                max_tokens_full = get_max_tokens(model)
            delta_output = 5000 #Elbow room to reduce chance of exceeding token limit or model paying less attention to prompt guidelines.
            if token_count > max_tokens_full - delta_output:
                docs_prompt_to_send_to_model = clean_markdown_content(docs_prompt_to_send_to_model) #Reduce unnecessary text/images/etc.
                get_logger().info(f"Token count {token_count} exceeds the limit {max_tokens_full - delta_output}. Attempting to clip text to fit within the limit...")
                docs_prompt_to_send_to_model = clip_tokens(docs_prompt_to_send_to_model, max_tokens_full - delta_output,
                                                           num_input_tokens=token_count)
            self.vars['snippets'] = docs_prompt_to_send_to_model.strip()

            # Run the AI model and extract sections from its response
            response = await retry_with_fallback_models(PredictionPreparator(self.ai_handler, self.vars,
                                                                             get_settings().pr_help_docs_prompts.system,
                                                                             get_settings().pr_help_docs_prompts.user),
                                                        model_type=ModelType.REGULAR)
            response_yaml = load_yaml(response)
            if not response_yaml:
                get_logger().exception("Failed to parse the AI response.", artifacts={'response': response})
                raise Exception(f"Failed to parse the AI response.")
            response_str = response_yaml.get('response')
            relevant_sections = response_yaml.get('relevant_sections')
            if not response_str or not relevant_sections:
                get_logger().exception("Failed to extract response/relevant sections.",
                                       artifacts={'response_str': response_str, 'relevant_sections': relevant_sections})
                raise Exception(f"Failed to extract response/relevant sections.")

            # Format the response as markdown
            canonical_url_prefix, canonical_url_suffix = self.git_provider.get_canonical_url_parts(repo_git_url=self.repo_url if self.repo_url_given_explicitly else None,
                                                                                                   desired_branch=self.repo_desired_branch)
            answer_str = format_markdown_q_and_a_response(self.question, response_str, relevant_sections, self.supported_doc_exts, canonical_url_prefix, canonical_url_suffix)
            if answer_str:
                #Remove the question phrase and replace with light bulb and a heading mentioning this is an automated answer:
                answer_str = modify_answer_section(answer_str)
            # For PR help docs, we return the answer string instead of publishing it
            if answer_str and self.return_as_string:
                if int(response_yaml.get('question_is_relevant', '1')) == 0:
                    get_logger().warning(f"Chat help docs answer would be ignored due to an invalid question.",
                                         artifacts={'answer_str': answer_str})
                    return ""
                get_logger().info(f"Chat help docs answer", artifacts={'answer_str': answer_str})
                return answer_str

            # Publish the answer
            if not answer_str or int(response_yaml.get('question_is_relevant', '1')) == 0:
                get_logger().info(f"No answer found")
                return ""

            if self.git_provider.is_supported("gfm_markdown") and get_settings().pr_help_docs.enable_help_text:
                answer_str += "<hr>\n\n<details> <summary><strong>💡 Tool usage guide:</strong></summary><hr> \n\n"
                answer_str += HelpMessage.get_help_docs_usage_guide()
                answer_str += "\n</details>\n"

            if get_settings().config.publish_output:
                self.git_provider.publish_comment(answer_str)
            else:
                get_logger().info("Answer:", artifacts={'answer_str': answer_str})

        except:
            get_logger().exception('failed to provide answer to given user question as a result of a thrown exception (see above)')


    def _find_all_document_files_matching_exts(self, abs_docs_path: str, ignore_readme=False) -> List[str]:
        matching_files = []

        # Ensure extensions don't have leading dots and are lowercase
        dotless_extensions = [ext.lower().lstrip('.') for ext in self.supported_doc_exts]

        # Walk through directory and subdirectories
        for root, _, files in os.walk(abs_docs_path):
            for file in files:
                if ignore_readme and root == abs_docs_path and file.lower() in [f"readme.{ext}" for ext in dotless_extensions]:
                    continue
                # Check if file has one of the specified extensions
                if any(file.lower().endswith(f'.{ext}') for ext in dotless_extensions):
                    matching_files.append(os.path.join(root, file))
        return matching_files
