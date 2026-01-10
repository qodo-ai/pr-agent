import time
from enum import Enum
import re
from typing import List
from urllib.parse import urlparse

import openai
from pydantic import BaseModel, Field

from pr_agent.algo.ticket_utils import find_jira_keys
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider_with_context
from pr_agent.issue_providers import get_issue_provider, resolve_issue_provider_name
from pr_agent.log import get_logger
from pr_agent.tools.embedding_client import EmbeddingClient

DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"


class PRSimilarIssue:
    def __init__(self, issue_url: str, ai_handler, args: list = None):
        self.issue_url = issue_url
        self.resource_url = issue_url.split('=')[-1] if issue_url else ""
        self.provider_name = get_settings().config.git_provider
        self.issue_provider_name = resolve_issue_provider_name(
            get_settings().get("CONFIG.ISSUE_PROVIDER", "auto"),
            self.provider_name,
        )
        self.supported = self.provider_name in ("github", "gitlab")
        self.git_provider = get_git_provider_with_context(self.resource_url)
        if not self.supported:
            return

        self.cli_mode = get_settings().CONFIG.CLI_MODE
        self.max_issues_to_scan = get_settings().pr_similar_issue.max_issues_to_scan
        self.token_handler = TokenHandler()
        self.embedding_model = get_settings().pr_similar_issue.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
        self.embedding_base_url = get_settings().pr_similar_issue.get("embedding_base_url", "")
        self.embedding_api_key = get_settings().pr_similar_issue.get("embedding_api_key", "")
        self.embedding_dim = get_settings().pr_similar_issue.get("embedding_dim", 1536)
        self.embedding_max_tokens = get_settings().pr_similar_issue.get("embedding_max_tokens", 8000)
        self.embedding_client = None
        if self.embedding_base_url:
            self.embedding_client = EmbeddingClient(
                self.embedding_base_url,
                self.embedding_model,
                api_key=self.embedding_api_key or None,
            )
        self.repo_obj = None
        self.issue_iid = None
        self.project_path = None
        self.issue_context = False
        self.output_target = None
        self.issue_provider = None
        self.jira_keys = []
        if self.provider_name == "github":
            repo_name_for_index = self._init_github_context()
        else:
            repo_name_for_index = self._init_gitlab_context()

        repo_name_for_index = repo_name_for_index.lower().replace('/', '-').replace('_/', '-')
        if self.issue_provider_name == "jira":
            repo_name_for_index = f"{repo_name_for_index}-jira"
        self.repo_name_for_index = repo_name_for_index
        self.issue_provider = get_issue_provider(
            self.issue_provider_name,
            git_provider=self.git_provider,
            repo_obj=self.repo_obj,
            project_path=self.project_path,
        )
        index_name = self.index_name = "codium-ai-pr-agent-issues"

        if get_settings().pr_similar_issue.vectordb == "pinecone":
            try:
                import pandas as pd
                import pinecone
                from pinecone_datasets import Dataset, DatasetMetadata
            except:
                raise Exception("Please install 'pinecone' and 'pinecone_datasets' to use pinecone as vectordb")
            # assuming pinecone api key and environment are set in secrets file
            try:
                api_key = get_settings().pinecone.api_key
                environment = get_settings().pinecone.environment
            except Exception:
                if not self.cli_mode:
                    try:
                        if self.provider_name == "github":
                            _, issue_number = self.git_provider._parse_issue_url(self.resource_url)
                            issue_main = self._get_issue_by_number(issue_number)
                        elif self.issue_context and self.issue_provider_name != "jira":
                            issue_main = self._get_issue_by_number(self.issue_iid)
                        else:
                            issue_main = self.git_provider.mr
                        self._publish_output(issue_main, "Please set pinecone api key and environment in secrets file")
                    except Exception:
                        get_logger().warning("Failed to publish pinecone credential message.")
                raise Exception("Please set pinecone api key and environment in secrets file")

            # check if index exists, and if repo is already indexed
            run_from_scratch = False
            if run_from_scratch:  # for debugging
                pinecone.init(api_key=api_key, environment=environment)
                if index_name in pinecone.list_indexes():
                    get_logger().info('Removing index...')
                    pinecone.delete_index(index_name)
                    get_logger().info('Done')

            upsert = True
            pinecone.init(api_key=api_key, environment=environment)
            if not index_name in pinecone.list_indexes():
                run_from_scratch = True
                upsert = False
            else:
                if get_settings().pr_similar_issue.force_update_dataset:
                    upsert = True
                else:
                    pinecone_index = pinecone.Index(index_name=index_name)
                    res = pinecone_index.fetch([f"example_issue_{repo_name_for_index}"]).to_dict()
                    if res["vectors"]:
                        upsert = False

            if run_from_scratch or upsert:  # index the entire repo
                get_logger().info('Indexing the entire repo...')

                get_logger().info('Getting issues...')
                issues = list(self._iter_issues())
                get_logger().info('Done')
                self._update_index_with_issues(issues, repo_name_for_index, upsert=upsert)
            else:  # update index if needed
                pinecone_index = pinecone.Index(index_name=index_name)
                issues_to_update = []
                issues_paginated_list = self._iter_issues()
                counter = 1
                for issue in issues_paginated_list:
                    if getattr(issue, "pull_request", None):
                        continue
                    issue_str, comments, number = self._process_issue(issue)
                    issue_key = f"issue_{number}"
                    id = issue_key + "." + "issue"
                    res = pinecone_index.fetch([id]).to_dict()
                    is_new_issue = True
                    for vector in res["vectors"].values():
                        if vector['metadata']['repo'] == repo_name_for_index:
                            is_new_issue = False
                            break
                    if is_new_issue:
                        counter += 1
                        issues_to_update.append(issue)
                    else:
                        break

                if issues_to_update:
                    get_logger().info(f'Updating index with {counter} new issues...')
                    self._update_index_with_issues(issues_to_update, repo_name_for_index, upsert=True)
                else:
                    get_logger().info('No new issues to update')

        elif get_settings().pr_similar_issue.vectordb == "lancedb":
            try:
                import lancedb  # import lancedb only if needed
            except:
                raise Exception("Please install lancedb to use lancedb as vectordb")
            self.db = lancedb.connect(get_settings().lancedb.uri)
            self.table = None

            run_from_scratch = False
            if run_from_scratch:  # for debugging
                if index_name in self.db.table_names():
                    get_logger().info('Removing Table...')
                    self.db.drop_table(index_name)
                    get_logger().info('Done')

            ingest = True
            if index_name not in self.db.table_names():
                run_from_scratch = True
                ingest = False
            else:
                if get_settings().pr_similar_issue.force_update_dataset:
                    ingest = True
                else:
                    self.table = self.db[index_name]
                    res = self.table.search().limit(len(self.table)).where(f"id='example_issue_{repo_name_for_index}'").to_list()
                    get_logger().info("result: ", res)
                    if res[0].get("vector"):
                        ingest = False

            if run_from_scratch or ingest:  # indexing the entire repo
                get_logger().info('Indexing the entire repo...')

                get_logger().info('Getting issues...')
                issues = list(self._iter_issues())
                get_logger().info('Done')

                self._update_table_with_issues(issues, repo_name_for_index, ingest=ingest)
            else:  # update table if needed
                issues_to_update = []
                issues_paginated_list = self._iter_issues()
                counter = 1
                for issue in issues_paginated_list:
                    if getattr(issue, "pull_request", None):
                        continue
                    issue_str, comments, number = self._process_issue(issue)
                    issue_key = f"issue_{number}"
                    issue_id = issue_key + "." + "issue"
                    res = self.table.search().limit(len(self.table)).where(f"id='{issue_id}'").to_list()
                    is_new_issue = True
                    for r in res:
                        if r['metadata']['repo'] == repo_name_for_index:
                            is_new_issue = False
                            break
                    if is_new_issue:
                        counter += 1
                        issues_to_update.append(issue)
                    else:
                        break

                if issues_to_update:
                    get_logger().info(f'Updating index with {counter} new issues...')
                    self._update_table_with_issues(issues_to_update, repo_name_for_index, ingest=True)
                else:
                    get_logger().info('No new issues to update')

        elif get_settings().pr_similar_issue.vectordb == "qdrant":
            try:
                import qdrant_client
                from qdrant_client.models import (Distance, FieldCondition,
                                                  Filter, MatchValue,
                                                  PointStruct, VectorParams)
            except Exception:
                raise Exception("Please install qdrant-client to use qdrant as vectordb")

            api_key = get_settings().get("QDRANT.API_KEY", None)
            url = get_settings().get("QDRANT.URL", None)
            if not url:
                if not self.cli_mode:
                    try:
                        if self.provider_name == "github":
                            _, issue_number = self.git_provider._parse_issue_url(self.resource_url)
                            issue_main = self._get_issue_by_number(issue_number)
                        elif self.issue_context and self.issue_provider_name != "jira":
                            issue_main = self._get_issue_by_number(self.issue_iid)
                        else:
                            issue_main = self.git_provider.mr
                        self._publish_output(issue_main, "Please set qdrant url in secrets file")
                    except Exception:
                        get_logger().warning("Failed to publish qdrant credential message.")
                raise Exception("Please set qdrant url in secrets file")

            self.qdrant = qdrant_client.QdrantClient(url=url, api_key=api_key)

            run_from_scratch = False
            ingest = True

            if not self.qdrant.collection_exists(collection_name=self.index_name):
                run_from_scratch = True
                ingest = False
                self.qdrant.create_collection(
                    collection_name=self.index_name,
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                )
            else:
                existing_dim = self._get_qdrant_vector_size()
                if existing_dim and existing_dim != self.embedding_dim:
                    if get_settings().pr_similar_issue.force_update_dataset:
                        get_logger().warning(
                            "Qdrant collection dimension mismatch (existing=%s, expected=%s); recreating.",
                            existing_dim,
                            self.embedding_dim,
                        )
                        self.qdrant.delete_collection(self.index_name)
                        self.qdrant.create_collection(
                            collection_name=self.index_name,
                            vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                        )
                        run_from_scratch = True
                        ingest = False
                    else:
                        raise Exception(
                            f"Qdrant collection '{self.index_name}' has dimension {existing_dim}, "
                            f"expected {self.embedding_dim}. Set pr_similar_issue.force_update_dataset=true to rebuild."
                        )
                elif get_settings().pr_similar_issue.force_update_dataset:
                    ingest = True
                else:
                    response = self.qdrant.count(
                        collection_name=self.index_name,
                        count_filter=Filter(must=[
                            FieldCondition(key="metadata.repo", match=MatchValue(value=repo_name_for_index)),
                            FieldCondition(key="id", match=MatchValue(value=f"example_issue_{repo_name_for_index}")),
                        ]),
                    )
                    ingest = True if response.count == 0 else False

            if run_from_scratch or ingest:
                get_logger().info('Indexing the entire repo...')
                get_logger().info('Getting issues...')
                issues = list(self._iter_issues())
                get_logger().info('Done')
                self._update_qdrant_with_issues(issues, repo_name_for_index, ingest=ingest)
            else:
                issues_to_update = []
                issues_paginated_list = self._iter_issues()
                counter = 1
                for issue in issues_paginated_list:
                    if getattr(issue, "pull_request", None):
                        continue
                    issue_str, comments, number = self._process_issue(issue)
                    issue_key = f"issue_{number}"
                    point_id = issue_key + "." + "issue"
                    response = self.qdrant.count(
                        collection_name=self.index_name,
                        count_filter=Filter(must=[
                            FieldCondition(key="id", match=MatchValue(value=point_id)),
                            FieldCondition(key="metadata.repo", match=MatchValue(value=repo_name_for_index)),
                        ]),
                    )
                    if response.count == 0:
                        counter += 1
                        issues_to_update.append(issue)
                    else:
                        break

                if issues_to_update:
                    get_logger().info(f'Updating index with {counter} new issues...')
                    self._update_qdrant_with_issues(issues_to_update, repo_name_for_index, ingest=True)
                else:
                    get_logger().info('No new issues to update')


    async def run(self):
        if not self.supported:
            message = "The /similar_issue tool is currently supported only for GitHub and GitLab."
            if get_settings().config.publish_output and hasattr(self.git_provider, "publish_comment"):
                try:
                    self.git_provider.publish_comment(message)
                except Exception:
                    get_logger().warning("Failed to publish unsupported-provider message.")
            return ""

        original_issue_number = None
        get_logger().info('Preparing query...')
        if self.issue_provider_name == "jira" and self.jira_keys:
            issue_texts = []
            for key in self.jira_keys:
                issue = self._get_issue_by_number(key)
                if not issue:
                    continue
                issue_str, _, _ = self._process_issue(issue)
                issue_texts.append(issue_str)
            if issue_texts:
                original_issue_number = str(self.jira_keys[0])
                query_text = "\n\n".join(issue_texts)
                issue_main = self.git_provider.mr
            else:
                issue_main = self.git_provider.mr
                query_text = self._build_query_from_mr(issue_main)
        elif self.provider_name == "github":
            _, original_issue_number = self.git_provider._parse_issue_url(self.resource_url)
            issue_main = self._get_issue_by_number(original_issue_number)
            issue_str, _, _ = self._process_issue(issue_main)
            query_text = issue_str
        else:
            if self.issue_context:
                issue_main = self._get_issue_by_number(self.issue_iid)
                issue_str, _, original_issue_number = self._process_issue(issue_main)
                query_text = issue_str
            else:
                issue_main = self.git_provider.mr
                query_text = self._build_query_from_mr(issue_main)
        get_logger().info('Done')

        get_logger().info('Querying...')
        embeds = self._embed_texts([query_text])

        relevant_issues_number_list = []
        relevant_comment_number_list = []
        score_list = []

        if get_settings().pr_similar_issue.vectordb == "pinecone":
            pinecone_index = pinecone.Index(index_name=self.index_name)
            res = pinecone_index.query(embeds[0],
                                    top_k=5,
                                    filter={"repo": self.repo_name_for_index},
                                    include_metadata=True).to_dict()

            for r in res['matches']:
                # skip example issue
                if 'example_issue_' in r["id"]:
                    continue

                issue_number = r["id"].split(".", 1)[0].split("_", 1)[-1]
                if not issue_number:
                    get_logger().debug(f"Failed to parse issue number from {r['id']}")
                    continue

                if original_issue_number and str(original_issue_number) == str(issue_number):
                    continue
                if issue_number not in relevant_issues_number_list:
                    relevant_issues_number_list.append(issue_number)
                if 'comment' in r["id"]:
                    relevant_comment_number_list.append(int(r["id"].split('.')[1].split('_')[-1]))
                else:
                    relevant_comment_number_list.append(-1)
                score_list.append(str("{:.2f}".format(r['score'])))
            get_logger().info('Done')

        elif get_settings().pr_similar_issue.vectordb == "lancedb":
            res = self.table.search(embeds[0]).where(f"metadata.repo='{self.repo_name_for_index}'", prefilter=True).to_list()

            for r in res:
                # skip example issue
                if 'example_issue_' in r["id"]:
                    continue

                issue_number = r["id"].split(".", 1)[0].split("_", 1)[-1]
                if not issue_number:
                    get_logger().debug(f"Failed to parse issue number from {r['id']}")
                    continue

                if original_issue_number and str(original_issue_number) == str(issue_number):
                    continue
                if issue_number not in relevant_issues_number_list:
                    relevant_issues_number_list.append(issue_number)

                if 'comment' in r["id"]:
                    relevant_comment_number_list.append(int(r["id"].split('.')[1].split('_')[-1]))
                else:
                    relevant_comment_number_list.append(-1)
                score_list.append(str("{:.2f}".format(1-r['_distance'])))
            get_logger().info('Done')

        elif get_settings().pr_similar_issue.vectordb == "qdrant":
            from qdrant_client.models import FieldCondition, Filter, MatchValue
            res = self.qdrant.search(
                collection_name=self.index_name,
                query_vector=embeds[0],
                limit=5,
                query_filter=Filter(must=[FieldCondition(key="metadata.repo", match=MatchValue(value=self.repo_name_for_index))]),
                with_payload=True,
            )

            for r in res:
                rid = r.payload.get("id", "")
                if 'example_issue_' in rid:
                    continue
                issue_number = rid.split(".", 1)[0].split("_", 1)[-1]
                if not issue_number:
                    get_logger().debug(f"Failed to parse issue number from {rid}")
                    continue
                if original_issue_number and str(original_issue_number) == str(issue_number):
                    continue
                if issue_number not in relevant_issues_number_list:
                    relevant_issues_number_list.append(issue_number)
                if 'comment' in rid:
                    relevant_comment_number_list.append(int(rid.split('.')[1].split('_')[-1]))
                else:
                    relevant_comment_number_list.append(-1)
                score_list.append(str("{:.2f}".format(r.score)))
            get_logger().info('Done')

        get_logger().info('Publishing response...')
        similar_issues_str = "### Similar Issues\n___\n\n"

        for i, issue_number_similar in enumerate(relevant_issues_number_list):
            issue = self._get_issue_by_number(issue_number_similar)
            title = self._get_issue_title(issue)
            url = getattr(issue, "html_url", None) or getattr(issue, "web_url", None)
            if relevant_comment_number_list[i] != -1:
                url = self._get_issue_comment_url(issue, relevant_comment_number_list[i])
            similar_issues_str += f"{i + 1}. **[{title}]({url})** (score={score_list[i]})\n\n"
        if get_settings().config.publish_output:
            target = self.output_target or issue_main
            self._publish_output(target, similar_issues_str)
        get_logger().info(similar_issues_str)
        get_logger().info('Done')

    def _embed_texts(self, list_to_encode: list[str]) -> list[list[float]]:
        if not list_to_encode:
            return []

        if self.embedding_client:
            return self.embedding_client.embed(list_to_encode)

        openai.api_key = get_settings().openai.key
        res = openai.Embedding.create(input=list_to_encode, engine=self.embedding_model)
        return [record['embedding'] for record in res['data']]

    def _embed_texts_with_fallback(self, list_to_encode: list[str]) -> list[list[float]]:
        try:
            return self._embed_texts(list_to_encode)
        except Exception:
            get_logger().error('Failed to embed entire list, embedding one by one...')
            embeds = []
            for text in list_to_encode:
                try:
                    embeds.append(self._embed_texts([text])[0])
                except Exception:
                    embeds.append([0] * self.embedding_dim)
            return embeds

    def _get_qdrant_vector_size(self) -> int | None:
        try:
            info = self.qdrant.get_collection(self.index_name)
            vectors = info.config.params.vectors
            if hasattr(vectors, "size"):
                return vectors.size
            if isinstance(vectors, dict):
                if "size" in vectors:
                    return vectors.get("size")
                default_vec = vectors.get("default")
                if hasattr(default_vec, "size"):
                    return default_vec.size
        except Exception:
            return None
        return None

    def _process_issue(self, issue):
        header = self._get_issue_title(issue)
        body = self._get_issue_body(issue)
        number = self._get_issue_number(issue)
        if get_settings().pr_similar_issue.skip_comments:
            comments = []
        else:
            comments = self._get_issue_comments(issue)
        issue_str = f"Issue Header: \"{header}\"\n\nIssue Body:\n{body}"
        return issue_str, comments, number

    def _iter_issues(self):
        return self.issue_provider.list_issues(self.project_path, state="all")

    def _get_issue_by_number(self, issue_number):
        return self.issue_provider.get_issue(issue_number, self.project_path)

    def _publish_output(self, target, message: str):
        if self.provider_name == "github":
            return target.create_comment(message)
        return target.notes.create({"body": message})

    def _is_issue_url(self, url: str) -> bool:
        try:
            path = urlparse(url).path
        except Exception:
            return False
        return "/issues/" in path

    def _build_query_from_mr(self, mr) -> str:
        title = getattr(mr, "title", "") or ""
        description = getattr(mr, "description", "") or ""
        if description:
            return f"MR Title: \"{title}\"\n\nMR Description:\n{description}"
        return f"MR Title: \"{title}\""

    def _extract_jira_keys_from_mr(self, mr) -> list:
        title = getattr(mr, "title", "") or ""
        description = getattr(mr, "description", "") or ""
        branch_name = ""
        commit_messages = ""
        try:
            branch_name = self.git_provider.get_pr_branch() or ""
        except Exception:
            branch_name = ""
        try:
            commit_messages = self.git_provider.get_commit_messages() or ""
        except Exception:
            commit_messages = ""
        text = "\n".join([title, description, branch_name, commit_messages])
        return find_jira_keys(text)

    def _extract_issue_iid_from_text(self, text: str):
        if not text:
            return None
        match = re.search(r"#(\d+)", text)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _get_issue_title(self, issue) -> str:
        return getattr(issue, "title", "") or ""

    def _get_issue_body(self, issue) -> str:
        body = getattr(issue, "body", None)
        if body is None:
            body = getattr(issue, "description", "")
        return body or ""

    def _get_issue_number(self, issue) -> int:
        for attr in ("iid", "number", "id", "key"):
            value = getattr(issue, attr, None)
            if value is not None:
                if isinstance(value, int):
                    return value
                value_str = str(value)
                if value_str.isdigit():
                    return int(value_str)
                return value_str
        raise ValueError("Issue number is missing")

    def _init_github_context(self) -> str:
        repo_name, _ = self.git_provider._parse_issue_url(self.resource_url)
        self.git_provider.repo = repo_name
        self.repo_obj = self.git_provider.github_client.get_repo(repo_name)
        self.git_provider.repo_obj = self.repo_obj
        return self.repo_obj.full_name

    def _init_gitlab_context(self) -> str:
        # Issue URL path (non-Jira) – treat it as issue context
        if self.issue_provider_name != "jira" and self._is_issue_url(self.resource_url):
            self.issue_context = True
            self.project_path, self.issue_iid = self.git_provider._parse_issue_url(self.resource_url)
            self.repo_obj = self.git_provider._get_project(self.project_path)
            if self.repo_obj is None:
                raise Exception(f"GitLab project not found: {self.project_path}")
            self.git_provider.id_project = self.project_path
            self.git_provider.repo_obj = self.repo_obj
            return getattr(self.repo_obj, "path_with_namespace", self.project_path)

        # MR context is required from here on
        if not getattr(self.git_provider, "mr", None):
            raise Exception("GitLab merge request context is required for /similar_issue")

        self.issue_context = False
        self.output_target = self.git_provider.mr
        self.project_path = self.git_provider.id_project
        self.repo_obj = self.git_provider.gl.projects.get(self.project_path)
        self.git_provider.repo_obj = self.repo_obj

        if self.issue_provider_name == "jira":
            self.jira_keys = find_jira_keys(self.resource_url)
            if not self.jira_keys:
                self.jira_keys = self._extract_jira_keys_from_mr(self.git_provider.mr)
            if self.jira_keys:
                self.issue_context = True
                self.issue_iid = self.jira_keys[0]
                return getattr(self.repo_obj, "path_with_namespace", self.project_path)

        issue_iid = self._extract_issue_iid_from_text(self._build_query_from_mr(self.git_provider.mr))
        if issue_iid:
            try:
                self._get_issue_by_number(issue_iid)
                self.issue_context = True
                self.issue_iid = issue_iid
            except Exception as exc:
                get_logger().debug(
                    "Issue reference not found or inaccessible; falling back to MR context.",
                    artifact={"error": str(exc)},
                )
        return getattr(self.repo_obj, "path_with_namespace", self.project_path)

    def _get_issue_username(self, issue) -> str:
        user = getattr(issue, "user", None)
        if user and getattr(user, "login", None):
            return user.login
        author = getattr(issue, "author", None)
        if isinstance(author, dict):
            return author.get("username") or author.get("name") or "@unknown"
        if author and getattr(author, "username", None):
            return author.username
        return "@unknown"

    def _get_issue_comments(self, issue):
        comments = getattr(issue, "comments", None)
        if comments is not None:
            return comments
        return self.issue_provider.get_issue_comments(issue)

    def _get_issue_comment_url(self, issue, comment_index: int) -> str:
        comments = self._get_issue_comments(issue)
        if comment_index < 0 or comment_index >= len(comments):
            return getattr(issue, "web_url", None) or getattr(issue, "html_url", None) or ""
        comment = comments[comment_index]
        comment_url = getattr(comment, "html_url", None) or getattr(comment, "web_url", None) or getattr(comment, "url", None)
        if comment_url:
            return comment_url
        issue_url = getattr(issue, "web_url", None) or getattr(issue, "html_url", None) or ""
        return issue_url

    def _update_index_with_issues(self, issues_list, repo_name_for_index, upsert=False):
        get_logger().info('Processing issues...')
        corpus = Corpus()
        example_issue_record = Record(
            id=f"example_issue_{repo_name_for_index}",
            text="example_issue",
            metadata=Metadata(repo=repo_name_for_index)
        )
        corpus.append(example_issue_record)

        counter = 0
        for issue in issues_list:
            if getattr(issue, "pull_request", None):
                continue

            counter += 1
            if counter % 100 == 0:
                get_logger().info(f"Scanned {counter} issues")
            if counter >= self.max_issues_to_scan:
                get_logger().info(f"Scanned {self.max_issues_to_scan} issues, stopping")
                break

            issue_str, comments, number = self._process_issue(issue)
            issue_key = f"issue_{number}"
            username = self._get_issue_username(issue)
            created_at = str(issue.created_at)
            if len(issue_str) < 8000 or \
                    self.token_handler.count_tokens(issue_str) < self.embedding_max_tokens:  # fast reject first
                issue_record = Record(
                    id=issue_key + "." + "issue",
                    text=issue_str,
                    metadata=Metadata(repo=repo_name_for_index,
                                      username=username,
                                      created_at=created_at,
                                      level=IssueLevel.ISSUE)
                )
                corpus.append(issue_record)
                if comments:
                    for j, comment in enumerate(comments):
                        comment_body = comment.body
                        num_words_comment = len(comment_body.split())
                        if num_words_comment < 10 or not isinstance(comment_body, str):
                            continue

                        if len(comment_body) < 8000 or \
                                self.token_handler.count_tokens(comment_body) < self.embedding_max_tokens:
                            comment_record = Record(
                                id=issue_key + ".comment_" + str(j + 1),
                                text=comment_body,
                                metadata=Metadata(repo=repo_name_for_index,
                                                  username=username,  # use issue username for all comments
                                                  created_at=created_at,
                                                  level=IssueLevel.COMMENT)
                            )
                            corpus.append(comment_record)
        df = pd.DataFrame(corpus.dict()["documents"])
        get_logger().info('Done')

        get_logger().info('Embedding...')
        list_to_encode = list(df["text"].values)
        embeds = self._embed_texts_with_fallback(list_to_encode)
        df["values"] = embeds
        meta = DatasetMetadata.empty()
        meta.dense_model.dimension = len(embeds[0])
        ds = Dataset.from_pandas(df, meta)
        get_logger().info('Done')

        api_key = get_settings().pinecone.api_key
        environment = get_settings().pinecone.environment
        if not upsert:
            get_logger().info('Creating index from scratch...')
            ds.to_pinecone_index(self.index_name, api_key=api_key, environment=environment)
            time.sleep(15)  # wait for pinecone to finalize indexing before querying
        else:
            get_logger().info('Upserting index...')
            namespace = ""
            batch_size: int = 100
            concurrency: int = 10
            pinecone.init(api_key=api_key, environment=environment)
            ds._upsert_to_index(self.index_name, namespace, batch_size, concurrency)
            time.sleep(5)  # wait for pinecone to finalize upserting before querying
        get_logger().info('Done')

    def _update_table_with_issues(self, issues_list, repo_name_for_index, ingest=False):
        get_logger().info('Processing issues...')

        corpus = Corpus()
        example_issue_record = Record(
            id=f"example_issue_{repo_name_for_index}",
            text="example_issue",
            metadata=Metadata(repo=repo_name_for_index)
        )
        corpus.append(example_issue_record)

        counter = 0
        for issue in issues_list:
            if getattr(issue, "pull_request", None):
                continue

            counter += 1
            if counter % 100 == 0:
                get_logger().info(f"Scanned {counter} issues")
            if counter >= self.max_issues_to_scan:
                get_logger().info(f"Scanned {self.max_issues_to_scan} issues, stopping")
                break

            issue_str, comments, number = self._process_issue(issue)
            issue_key = f"issue_{number}"
            username = self._get_issue_username(issue)
            created_at = str(issue.created_at)
            if len(issue_str) < 8000 or \
                    self.token_handler.count_tokens(issue_str) < self.embedding_max_tokens:  # fast reject first
                issue_record = Record(
                    id=issue_key + "." + "issue",
                    text=issue_str,
                    metadata=Metadata(repo=repo_name_for_index,
                                        username=username,
                                        created_at=created_at,
                                        level=IssueLevel.ISSUE)
                )
                corpus.append(issue_record)
                if comments:
                    for j, comment in enumerate(comments):
                        comment_body = comment.body
                        num_words_comment = len(comment_body.split())
                        if num_words_comment < 10 or not isinstance(comment_body, str):
                            continue

                        if len(comment_body) < 8000 or \
                                self.token_handler.count_tokens(comment_body) < self.embedding_max_tokens:
                            comment_record = Record(
                                id=issue_key + ".comment_" + str(j + 1),
                                text=comment_body,
                                metadata=Metadata(repo=repo_name_for_index,
                                                    username=username,  # use issue username for all comments
                                                    created_at=created_at,
                                                    level=IssueLevel.COMMENT)
                            )
                            corpus.append(comment_record)
        df = pd.DataFrame(corpus.dict()["documents"])
        get_logger().info('Done')

        get_logger().info('Embedding...')
        list_to_encode = list(df["text"].values)
        embeds = self._embed_texts_with_fallback(list_to_encode)
        df["vector"] = embeds
        get_logger().info('Done')

        if not ingest:
            get_logger().info('Creating table from scratch...')
            self.table = self.db.create_table(self.index_name, data=df, mode="overwrite")
            time.sleep(15)
        else:
            get_logger().info('Ingesting in Table...')
            if self.index_name not in self.db.table_names():
                self.table.add(df)
            else:
                get_logger().info(f"Table {self.index_name} doesn't exists!")
            time.sleep(5)
        get_logger().info('Done')


    def _update_qdrant_with_issues(self, issues_list, repo_name_for_index, ingest=False):
        try:
            import uuid

            from qdrant_client.models import PointStruct
        except Exception:
            raise

        get_logger().info('Processing issues...')
        corpus = Corpus()
        example_issue_record = Record(
            id=f"example_issue_{repo_name_for_index}",
            text="example_issue",
            metadata=Metadata(repo=repo_name_for_index)
        )
        corpus.append(example_issue_record)

        counter = 0
        for issue in issues_list:
            if getattr(issue, "pull_request", None):
                continue

            counter += 1
            if counter % 100 == 0:
                get_logger().info(f"Scanned {counter} issues")
            if counter >= self.max_issues_to_scan:
                get_logger().info(f"Scanned {self.max_issues_to_scan} issues, stopping")
                break

            issue_str, comments, number = self._process_issue(issue)
            issue_key = f"issue_{number}"
            username = self._get_issue_username(issue)
            created_at = str(issue.created_at)
            if len(issue_str) < 8000 or \
                    self.token_handler.count_tokens(issue_str) < self.embedding_max_tokens:
                issue_record = Record(
                    id=issue_key + "." + "issue",
                    text=issue_str,
                    metadata=Metadata(repo=repo_name_for_index,
                                      username=username,
                                      created_at=created_at,
                                      level=IssueLevel.ISSUE)
                )
                corpus.append(issue_record)
                if comments:
                    for j, comment in enumerate(comments):
                        comment_body = comment.body
                        num_words_comment = len(comment_body.split())
                        if num_words_comment < 10 or not isinstance(comment_body, str):
                            continue

                        if len(comment_body) < 8000 or \
                                self.token_handler.count_tokens(comment_body) < self.embedding_max_tokens:
                            comment_record = Record(
                                id=issue_key + ".comment_" + str(j + 1),
                                text=comment_body,
                                metadata=Metadata(repo=repo_name_for_index,
                                                  username=username,
                                                  created_at=created_at,
                                                  level=IssueLevel.COMMENT)
                            )
                            corpus.append(comment_record)

        documents = corpus.dict()["documents"]
        get_logger().info('Done')

        get_logger().info('Embedding...')
        list_to_encode = [doc["text"] for doc in documents]
        embeds = self._embed_texts_with_fallback(list_to_encode)
        for doc, vector in zip(documents, embeds):
            doc["vector"] = vector
        get_logger().info('Done')

        get_logger().info('Upserting into Qdrant...')
        points = []
        for row in documents:
            points.append(
                PointStruct(id=uuid.uuid5(uuid.NAMESPACE_DNS, row["id"]).hex, vector=row["vector"], payload={"id": row["id"], "text": row["text"], "metadata": row["metadata"]})
            )
        self.qdrant.upsert(collection_name=self.index_name, points=points)
        get_logger().info('Done')


class IssueLevel(str, Enum):
    ISSUE = "issue"
    COMMENT = "comment"


class Metadata(BaseModel):
    repo: str
    username: str = Field(default="@codium")
    created_at: str = Field(default="01-01-1970 00:00:00.00000")
    level: IssueLevel = Field(default=IssueLevel.ISSUE)

    class Config:
        use_enum_values = True


class Record(BaseModel):
    id: str
    text: str
    metadata: Metadata


class Corpus(BaseModel):
    documents: List[Record] = Field(default=[])

    def append(self, r: Record):
        self.documents.append(r)
