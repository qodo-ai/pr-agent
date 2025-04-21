# Copyright (c) 2023 PR-Agent Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FILE_PATH = "pr_agent/cli_pip.py"

PR_HEADER_START_WITH = '### **User description**\nupdate cli_pip.py\n\n\n___\n\n### **PR Type**'
REVIEW_START_WITH = '## PR Reviewer Guide 🔍\n\n<table>\n<tr><td>⏱️&nbsp;<strong>Estimated effort to review</strong>:'
IMPROVE_START_WITH_REGEX_PATTERN = r'^## PR Code Suggestions ✨\n\n<!-- [a-z0-9]+ -->\n\n<table><thead><tr><td>Category</td>'

NUM_MINUTES = 5

NEW_FILE_CONTENT = """\
from pr_agent import cli
from pr_agent.config_loader import get_settings


def main():
    # Fill in the following values
    provider = "github"  # GitHub provider
    user_token = "..."  # GitHub user token
    openai_key = "ghs_afsdfasdfsdf"  # Example OpenAI key
    pr_url = "..."  # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/improve"  # Command to run (e.g. '/review', '/describe', 'improve', '/ask="What is the purpose of this PR?"')

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Run the command. Feedback will appear in GitHub PR comments
    output = cli.run_command(pr_url, command)

    print(output)

if __name__ == '__main__':
    main()
"""
