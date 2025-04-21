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

import json
import os

from pr_agent.algo.utils import get_settings, github_action_output


class TestGitHubOutput:
    def test_github_action_output_enabled(self, monkeypatch, tmp_path):
        get_settings().set('GITHUB_ACTION_CONFIG.ENABLE_OUTPUT', True)
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'

        github_action_output(output_data, key_name)

        with open(str(tmp_path / 'output'), 'r') as f:
            env_value = f.read()

        actual_key = env_value.split('=')[0]
        actual_data = json.loads(env_value.split('=')[1])

        assert actual_key == key_name
        assert actual_data == output_data[key_name]

    def test_github_action_output_disabled(self, monkeypatch, tmp_path):
        get_settings().set('GITHUB_ACTION_CONFIG.ENABLE_OUTPUT', False)
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'

        github_action_output(output_data, key_name)

        assert not os.path.exists(str(tmp_path / 'output'))

    def test_github_action_output_notset(self, monkeypatch, tmp_path):
        # not set config
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'

        github_action_output(output_data, key_name)

        assert not os.path.exists(str(tmp_path / 'output'))

    def test_github_action_output_error_case(self, monkeypatch, tmp_path):
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = None # invalid data
        key_name = 'key1'

        github_action_output(output_data, key_name)

        assert not os.path.exists(str(tmp_path / 'output'))
