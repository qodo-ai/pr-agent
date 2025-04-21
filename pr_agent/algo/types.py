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

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EDIT_TYPE(Enum):
    ADDED = 1
    DELETED = 2
    MODIFIED = 3
    RENAMED = 4
    UNKNOWN = 5


@dataclass
class FilePatchInfo:
    base_file: str
    head_file: str
    patch: str
    filename: str
    tokens: int = -1
    edit_type: EDIT_TYPE = EDIT_TYPE.UNKNOWN
    old_filename: str = None
    num_plus_lines: int = -1
    num_minus_lines: int = -1
    language: Optional[str] = None
    ai_file_summary: str = None
