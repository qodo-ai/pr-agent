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

from pr_agent.config_loader import get_settings


def get_secret_provider():
    if not get_settings().get("CONFIG.SECRET_PROVIDER"):
        return None

    provider_id = get_settings().config.secret_provider
    if provider_id == 'google_cloud_storage':
        try:
            from pr_agent.secret_providers.google_cloud_storage_secret_provider import \
                GoogleCloudStorageSecretProvider
            return GoogleCloudStorageSecretProvider()
        except Exception as e:
            raise ValueError(f"Failed to initialize google_cloud_storage secret provider {provider_id}") from e
    else:
        raise ValueError("Unknown SECRET_PROVIDER")
