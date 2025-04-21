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


class BaseAiHandler(ABC):
    """
    This class defines the interface for an AI handler to be used by the PR Agents.
    """

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def deployment_id(self):
        pass

    @abstractmethod
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2, img_path: str = None):
        """
        This method should be implemented to return a chat completion from the AI model.
        Args:
            model (str): the name of the model to use for the chat completion
            system (str): the system message string to use for the chat completion
            user (str): the user message string to use for the chat completion
            temperature (float): the temperature to use for the chat completion
        """
        pass
