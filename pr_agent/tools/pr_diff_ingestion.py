import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider_with_context
from pr_agent.log import get_logger


@dataclass
class PRDiffData:
    """Data structure for storing PR diff information"""
    pr_url: str
    pr_id: str
    title: str
    description: str
    diff_text: str
    diff_summary: str
    changed_files: List[str]
    commit_messages: List[str]
    created_at: str
    merged_at: Optional[str]
    author: str
    language: str
    embedding_hash: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PRDiffProcessor:
    """Processes PR diffs and generates summaries for RAG storage"""
    
    def __init__(self, ai_handler: BaseAiHandler = None):
        self.ai_handler = ai_handler or LiteLLMAIHandler()
        self.logger = get_logger()
        
    def generate_diff_summary(self, diff_text: str, pr_title: str, pr_description: str) -> str:
        """Generate a descriptive summary of what the diff is supposed to do"""
        prompt = f"""
        Analyze this PR diff and provide a concise summary of what the code changes are intended to accomplish.
        Focus on the purpose and functionality, not just what files changed.
        
        PR Title: {pr_title}
        PR Description: {pr_description}
        
        Diff:
        {diff_text[:8000]}  # Limit diff size for processing
        
        Provide a 2-3 sentence summary describing:
        1. What functionality is being added/modified/fixed
        2. The main technical approach used
        3. Any important architectural or design decisions
        
        Summary:
        """
        
        try:
            import asyncio
            
            async def get_summary():
                response = await self.ai_handler.chat_completion(
                    model=get_settings().config.model,
                    temperature=0.1,
                    system="You are a senior software engineer analyzing code changes.",
                    user=prompt
                )
                # Handle different response formats
                if hasattr(response, 'choices') and response.choices:
                    return response.choices[0].message.content.strip()
                elif isinstance(response, tuple) and len(response) > 0:
                    return str(response[0]).strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()
            
            # Run the async function safely
            try:
                # Try to get existing loop
                loop = asyncio.get_running_loop()
                # If we're in an existing loop, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_summary())
                    return future.result()
            except RuntimeError:
                # No event loop running, create a new one
                return asyncio.run(get_summary())
                
        except Exception as e:
            self.logger.error(f"Failed to generate diff summary: {e}")
            return f"Code changes in PR: {pr_title}"
    
    def extract_metadata(self, git_provider) -> Dict:
        """Extract relevant metadata from PR"""
        try:
            pr = git_provider.pr
            return {
                'title': pr.title,
                'description': git_provider.get_pr_description(),
                'author': pr.user.login if hasattr(pr, 'user') else 'unknown',
                'created_at': pr.created_at.isoformat() if hasattr(pr, 'created_at') else None,
                'merged_at': pr.merged_at.isoformat() if hasattr(pr, 'merged_at') and pr.merged_at else None,
                'changed_files': [f.filename for f in pr.get_files()] if hasattr(pr, 'get_files') else [],
                'commit_messages': git_provider.get_commit_messages().split('\n') if git_provider.get_commit_messages() else []
            }
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}
    
    def process_pr_diff(self, pr_url: str) -> Optional[PRDiffData]:
        """Process a single PR and extract diff data"""
        try:
            git_provider = get_git_provider_with_context(pr_url)
            
            # Get PR diff
            from pr_agent.algo.token_handler import TokenHandler
            token_handler = TokenHandler(pr=git_provider.pr)
            
            # Get the model from settings or use default
            model = get_settings().config.model
            patches_diff = get_pr_diff(git_provider, token_handler, model)
            if not patches_diff:
                self.logger.warning(f"No diff found for PR: {pr_url}")
                return None
            
            # Extract metadata
            metadata = self.extract_metadata(git_provider)
            
            # Generate diff summary
            diff_text = str(patches_diff)
            diff_summary = self.generate_diff_summary(
                diff_text, 
                metadata.get('title', ''), 
                metadata.get('description', '')
            )
            
            # Create embedding hash for deduplication
            content_for_hash = f"{diff_text}{metadata.get('title', '')}{metadata.get('description', '')}"
            embedding_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            # Get language
            language = git_provider.get_languages()
            main_language = max(language.items(), key=lambda x: x[1])[0] if language else 'unknown'
            
            return PRDiffData(
                pr_url=pr_url,
                pr_id=f"{git_provider.repo}#{git_provider.pr_num}",
                title=metadata.get('title', ''),
                description=metadata.get('description', ''),
                diff_text=diff_text,
                diff_summary=diff_summary,
                changed_files=metadata.get('changed_files', []),
                commit_messages=metadata.get('commit_messages', []),
                created_at=metadata.get('created_at', ''),
                merged_at=metadata.get('merged_at'),
                author=metadata.get('author', ''),
                language=main_language,
                embedding_hash=embedding_hash
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process PR {pr_url}: {e}")
            return None


class PRCrawler:
    """Crawls repositories to collect PR data for ingestion"""
    
    def __init__(self):
        self.logger = get_logger()
        
    def get_recent_prs(self, repo_url: str, max_prs: int = 100, days_back: int = 30) -> List[str]:
        """Get recent merged PRs from a repository"""
        try:
            # Create a dummy PR URL to get the git provider initialized properly
            if not repo_url.endswith('/pull/1'):
                dummy_pr_url = f"{repo_url}/pull/1"
            else:
                dummy_pr_url = repo_url
            
            git_provider = get_git_provider_with_context(dummy_pr_url)
            repo = git_provider.repo_obj
            
            # Calculate date threshold
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Get recent merged PRs
            pulls = repo.get_pulls(
                state='closed',
                sort='updated',
                direction='desc'
            )
            
            pr_urls = []
            processed_count = 0
            
            # Limit the number of PRs we check to avoid processing thousands
            # Use a reasonable multiplier since not all closed PRs will be merged and in date range
            check_limit = min(max_prs * 10, 200)  # Check at most 10x what we need, capped at 200
            
            
            for pr in pulls:
                processed_count += 1
                
                # Only include merged PRs within date range
                if (pr.merged_at and 
                    pr.merged_at > since_date and 
                    pr.merged_at < datetime.now()):
                    pr_urls.append(pr.html_url)
                    
                    # Stop when we have enough PRs
                    if len(pr_urls) >= max_prs:
                        break
                
                # Stop checking after we've processed enough PRs to avoid infinite loops
                if processed_count >= check_limit:
                    break
                    
            return pr_urls
            
        except Exception as e:
            self.logger.error(f"Failed to crawl PRs from {repo_url}: {e}")
            return []
    
    def get_similar_repo_prs(self, base_repo: str, language: str, max_repos: int = 5) -> List[str]:
        """Find PRs from similar repositories based on language and topics"""
        # This would require GitHub search API or similar
        # For now, return empty list - can be extended later
        self.logger.info(f"Similar repo search not implemented yet for {base_repo}")
        return []


class PRDiffIngestionPipeline:
    """Main pipeline for ingesting PR diffs into the learning system"""
    
    def __init__(self, storage_backend='json'):
        self.processor = PRDiffProcessor()
        self.crawler = PRCrawler()
        self.storage_backend = storage_backend
        self.logger = get_logger()
        
    def ingest_repository(self, repo_url: str, max_prs: int = 100) -> List[PRDiffData]:
        """Ingest PRs from a specific repository"""
        self.logger.info(f"Starting ingestion for repository: {repo_url}")
        
        # Get PR URLs
        pr_urls = self.crawler.get_recent_prs(repo_url, max_prs)
        self.logger.info(f"Found {len(pr_urls)} PRs to process")
        
        # Process each PR
        processed_data = []
        for i, pr_url in enumerate(pr_urls):
            self.logger.info(f"Processing PR {i+1}/{len(pr_urls)}: {pr_url}")
            
            pr_data = self.processor.process_pr_diff(pr_url)
            if pr_data:
                processed_data.append(pr_data)
                
            # Rate limiting
            time.sleep(1)
            
        self.logger.info(f"Successfully processed {len(processed_data)} PRs")
        return processed_data
    
    def save_data(self, data: List[PRDiffData], output_file: str = None):
        """Save processed PR data to storage"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"pr_diff_data_{timestamp}.json"
            
        if self.storage_backend == 'json':
            with open(output_file, 'w') as f:
                json.dump([item.to_dict() for item in data], f, indent=2)
            self.logger.info(f"Saved {len(data)} PR records to {output_file}")
        
    def load_data(self, input_file: str) -> List[PRDiffData]:
        """Load processed PR data from storage"""
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            return [PRDiffData(**item) for item in data]
        except Exception as e:
            self.logger.error(f"Failed to load data from {input_file}: {e}")
            return []


def main():
    """Example usage of the ingestion pipeline"""
    pipeline = PRDiffIngestionPipeline()
    
    # Example: ingest PRs from this repository
    repo_url = "https://github.com/qodo-ai/pr-agent"
    pr_data = pipeline.ingest_repository(repo_url, max_prs=10)
    
    # Save the data
    pipeline.save_data(pr_data)
    
    print(f"Ingested {len(pr_data)} PRs")
    for pr in pr_data[:3]:  # Show first 3 as examples
        print(f"- {pr.title}")
        print(f"  Summary: {pr.diff_summary[:100]}...")
        print()


if __name__ == "__main__":
    main()