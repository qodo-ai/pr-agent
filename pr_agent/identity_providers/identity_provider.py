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

from abc import ABC, abstractmethod
from enum import Enum


class Eligibility(Enum):
    NOT_ELIGIBLE = 0
    ELIGIBLE = 1
    TRIAL = 2


class IdentityProvider(ABC):
    @abstractmethod
    def verify_eligibility(self, git_provider, git_provier_id, pr_url):
        pass

    @abstractmethod
    def inc_invocation_count(self, git_provider, git_provider_id):
        pass
