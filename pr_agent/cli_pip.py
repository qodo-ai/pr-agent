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

from pr_agent import cli
from pr_agent.config_loader import get_settings


def main():
    # Fill in the following values
    provider = "github"  # GitHub provider
    user_token = "..."  # GitHub user token
    openai_key = "..."  # OpenAI key
    pr_url = "..."  # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/review"  # Command to run (e.g. '/review', '/describe', '/ask="What is the purpose of this PR?"')

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Run the command. Feedback will appear in GitHub PR comments
    cli.run_command(pr_url, command)


if __name__ == '__main__':
    main()
