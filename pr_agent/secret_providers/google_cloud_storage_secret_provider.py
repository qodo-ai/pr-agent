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

import ujson
from google.cloud import storage

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
from pr_agent.secret_providers.secret_provider import SecretProvider


class GoogleCloudStorageSecretProvider(SecretProvider):
    def __init__(self):
        try:
            self.client = storage.Client.from_service_account_info(ujson.loads(get_settings().google_cloud_storage.
                                                                               service_account))
            self.bucket_name = get_settings().google_cloud_storage.bucket_name
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            get_logger().error(f"Failed to initialize Google Cloud Storage Secret Provider: {e}")
            raise e

    def get_secret(self, secret_name: str) -> str:
        try:
            blob = self.bucket.blob(secret_name)
            return blob.download_as_string()
        except Exception as e:
            get_logger().warning(f"Failed to get secret {secret_name} from Google Cloud Storage: {e}")
            return ""

    def store_secret(self, secret_name: str, secret_value: str):
        try:
            blob = self.bucket.blob(secret_name)
            blob.upload_from_string(secret_value)
        except Exception as e:
            get_logger().error(f"Failed to store secret {secret_name} in Google Cloud Storage: {e}")
            raise e
