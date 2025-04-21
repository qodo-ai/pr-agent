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

from pr_agent.identity_providers.identity_provider import (Eligibility,
                                                           IdentityProvider)


class DefaultIdentityProvider(IdentityProvider):
    def verify_eligibility(self, git_provider, git_provider_id, pr_url):
        return Eligibility.ELIGIBLE

    def inc_invocation_count(self, git_provider, git_provider_id):
        pass
