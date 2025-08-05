import asyncio
import traceback
from functools import partial
from typing import List, Dict, Any

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger


class PRReviewSummary:
    """
    PR이 close되거나 merge될 때 리뷰와 코멘트들을 종합하여 총평을 제공하는 클래스입니다.
    """

    def __init__(self, pr_url: str, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        """
        PRReviewSummary 객체를 초기화합니다.

        Args:
            pr_url (str): 총평을 생성할 PR의 URL
            args (list, optional): 추가 인자 목록. 기본값은 None.
            ai_handler (BaseAiHandler): 리뷰 총평 생성에 사용할 AI 핸들러. 기본값은 LiteLLMAIHandler.
        """
        self.git_provider = get_git_provider()(pr_url)
        self.args = args
        self.ai_handler = ai_handler()
        self.pr_url = pr_url

    async def run(self):
        """
        PR 리뷰 총평을 실행하는 메인 메소드입니다.
        """
        try:
            get_logger().info('PR 리뷰 총평 생성을 시작합니다...')
            
            # PR 정보 수집
            pr_info = self._collect_pr_info()
            
            # 리뷰와 코멘트 수집
            reviews_and_comments = self._collect_reviews_and_comments()
            
            # 총평 생성
            summary = await self._generate_review_summary(pr_info, reviews_and_comments)
            
            # 총평 게시
            if summary:
                await self._publish_summary(summary)
                get_logger().info('PR 리뷰 총평이 성공적으로 생성되고 게시되었습니다.')
            else:
                get_logger().warning('총평 생성에 실패했습니다.')
                
        except Exception as e:
            get_logger().error(f"PR 리뷰 총평 생성 중 오류 발생: {e}")
            get_logger().debug(traceback.format_exc())

    def _collect_pr_info(self) -> Dict[str, Any]:
        """
        PR의 기본 정보를 수집합니다.
        
        Returns:
            Dict[str, Any]: PR 정보 딕셔너리
        """
        try:
            # 기본 PR 정보 수집
            title = self.git_provider.get_title() if hasattr(self.git_provider, 'get_title') else 'Unknown'
            description = self.git_provider.get_pr_description_full() if hasattr(self.git_provider, 'get_pr_description_full') else 'Unknown'
            
            # 작성자 정보 처리 (GitHub의 경우)
            author = 'Unknown'
            if hasattr(self.git_provider.pr, 'user') and self.git_provider.pr.user:
                author = getattr(self.git_provider.pr.user, 'login', 'Unknown')
            
            # PR 상태 정보
            state = getattr(self.git_provider.pr, 'state', 'Unknown')
            merged = getattr(self.git_provider.pr, 'merged', False)
            
            # 변경 통계
            files_changed = len(self.git_provider.get_files()) if hasattr(self.git_provider, 'get_files') else 0
            additions = getattr(self.git_provider.pr, 'additions', 0)
            deletions = getattr(self.git_provider.pr, 'deletions', 0)
            commits = getattr(self.git_provider.pr, 'commits', 0)
            
            pr_info = {
                'title': title,
                'description': description,
                'author': author,
                'state': state,
                'merged': merged,
                'files_changed': files_changed,
                'additions': additions,
                'deletions': deletions,
                'commits': commits,
            }
            
            # Diff 정보 추가
            try:
                diff_files = self.git_provider.get_diff_files()
                pr_info['diff_summary'] = self._create_diff_summary(diff_files)
            except Exception as e:
                get_logger().warning(f"Diff 정보 수집 실패: {e}")
                pr_info['diff_summary'] = "Diff 정보를 가져올 수 없습니다."
            
            return pr_info
            
        except Exception as e:
            get_logger().error(f"PR 정보 수집 중 오류: {e}")
            return {
                'title': 'Unknown',
                'description': 'Unknown',
                'author': 'Unknown',
                'state': 'Unknown',
                'merged': False,
                'files_changed': 0,
                'additions': 0,
                'deletions': 0,
                'commits': 0,
                'diff_summary': 'PR 정보를 가져올 수 없습니다.'
            }

    def _create_diff_summary(self, diff_files) -> str:
        """
        Diff 파일들로부터 간단한 요약을 생성합니다.
        """
        if not diff_files:
            return "변경된 파일이 없습니다."
        
        summary_lines = []
        for file_info in diff_files[:10]:  # 최대 10개 파일만
            file_path = getattr(file_info, 'filename', 'Unknown file')
            summary_lines.append(f"- {file_path}")
        
        if len(diff_files) > 10:
            summary_lines.append(f"... 그리고 {len(diff_files) - 10}개의 파일이 더 있습니다.")
        
        return "\n".join(summary_lines)

    def _collect_reviews_and_comments(self) -> Dict[str, List[str]]:
        """
        PR의 모든 리뷰와 코멘트를 수집합니다.
        
        Returns:
            Dict[str, List[str]]: 리뷰와 코멘트 목록
        """
        reviews_and_comments = {
            'issue_comments': [],
            'review_comments': [],
            'inline_comments': []
        }
        
        try:
            # Issue 코멘트 수집 (일반 PR 코멘트)
            if self.git_provider.is_supported('get_issue_comments'):
                issue_comments = self.git_provider.get_issue_comments()
                for comment in issue_comments:
                    if hasattr(comment, 'body') and comment.body:
                        # PR-Agent가 생성한 코멘트는 제외
                        if not self._is_pr_agent_comment(comment.body):
                            user = 'Unknown'
                            if hasattr(comment, 'user') and comment.user:
                                user = getattr(comment.user, 'login', 'Unknown')
                            reviews_and_comments['issue_comments'].append(f"{user}: {comment.body}")
            
            # PR 리뷰 코멘트 수집 (GitHub의 경우)
            if hasattr(self.git_provider, 'pr') and hasattr(self.git_provider.pr, 'get_reviews'):
                try:
                    reviews = self.git_provider.pr.get_reviews()
                    for review in reviews:
                        if review.body and not self._is_pr_agent_comment(review.body):
                            user = review.user.login if review.user else 'Unknown'
                            state = review.state
                            reviews_and_comments['review_comments'].append(f"{user} ({state}): {review.body}")
                except Exception as e:
                    get_logger().debug(f"리뷰 코멘트 수집 실패: {e}")
            
            # 인라인 코멘트 수집
            try:
                if hasattr(self.git_provider, 'pr') and hasattr(self.git_provider.pr, 'get_review_comments'):
                    inline_comments = self.git_provider.pr.get_review_comments()
                    for comment in inline_comments:
                        if comment.body and not self._is_pr_agent_comment(comment.body):
                            user = comment.user.login if comment.user else 'Unknown'
                            path = comment.path if comment.path else 'Unknown file'
                            line = comment.line if comment.line else 'Unknown line'
                            reviews_and_comments['inline_comments'].append(f"{user} (파일: {path}, 라인: {line}): {comment.body}")
            except Exception as e:
                get_logger().debug(f"인라인 코멘트 수집 실패: {e}")
                
        except Exception as e:
            get_logger().error(f"리뷰와 코멘트 수집 중 오류: {e}")
        
        return reviews_and_comments

    def _is_pr_agent_comment(self, comment_body: str) -> bool:
        """
        PR-Agent가 생성한 코멘트인지 확인합니다.
        """
        pr_agent_markers = [
            "## PR Reviewer Guide",
            "## PR Description",
            "## Code Suggestions",
            "PR-Agent",
            "## Changelog",
            "## Summary"
        ]
        return any(marker in comment_body for marker in pr_agent_markers)

    async def _generate_review_summary(self, pr_info: Dict[str, Any], 
                                     reviews_and_comments: Dict[str, List[str]]) -> str:
        """
        AI를 사용하여 리뷰 총평을 생성합니다.
        """
        try:
            # 프롬프트 템플릿 로드 - 임시로 하드코딩된 프롬프트 사용
            environment = Environment(undefined=StrictUndefined)
            settings = get_settings()
            
            # 템플릿에 데이터 주입
            pr_info_str = self._format_pr_info(pr_info)
            comments_str = self._format_comments(reviews_and_comments)
            system_prompt = environment.from_string(get_settings().pr_review_summary_prompt.system).render()

            user_prompt = environment.from_string(get_settings().pr_review_summary_prompt.user).render(
                pr_info=pr_info_str,
                comments=comments_str
            )
            
            # AI 호출
            model = settings.config.model
            response, finish_reason = await self.ai_handler.chat_completion(
                model=model,
                system=system_prompt,
                user=user_prompt,
                temperature=settings.config.temperature
            )
            
            return response
            
        except Exception as e:
            get_logger().error(f"총평 생성 중 오류: {e}")
            return None

    def _format_pr_info(self, pr_info: Dict[str, Any]) -> str:
        """
        PR 정보를 포맷팅합니다.
        """
        return f"""
**PR 정보:**
- 제목: {pr_info['title']}
- 작성자: {pr_info['author']}
- 상태: {pr_info['state']} (병합됨: {pr_info['merged']})
- 변경된 파일 수: {pr_info['files_changed']}
- 추가된 라인: {pr_info['additions']}
- 삭제된 라인: {pr_info['deletions']}
- 커밋 수: {pr_info['commits']}

**설명:**
{pr_info['description']}

**변경된 파일들:**
{pr_info['diff_summary']}
"""

    def _format_comments(self, reviews_and_comments: Dict[str, List[str]]) -> str:
        """
        리뷰와 코멘트를 포맷팅합니다.
        """
        formatted = []
        
        if reviews_and_comments['issue_comments']:
            formatted.append("**일반 코멘트:**")
            for comment in reviews_and_comments['issue_comments']:
                formatted.append(f"- {comment}")
            formatted.append("")
        
        if reviews_and_comments['review_comments']:
            formatted.append("**리뷰 코멘트:**")
            for comment in reviews_and_comments['review_comments']:
                formatted.append(f"- {comment}")
            formatted.append("")
        
        if reviews_and_comments['inline_comments']:
            formatted.append("**인라인 코멘트:**")
            for comment in reviews_and_comments['inline_comments']:
                formatted.append(f"- {comment}")
            formatted.append("")
        
        if not any(reviews_and_comments.values()):
            formatted.append("**코멘트나 리뷰가 없습니다.**")
        
        return "\n".join(formatted)

    async def _publish_summary(self, summary: str):
        """
        생성된 총평을 PR에 게시합니다.
        """
        try:
            # 총평 헤더 추가
            header = "## 📋 PR 리뷰 총평\n\n"
            footer = "\n\n---\n*이 총평은 PR-Agent에 의해 자동으로 생성되었습니다.*"
            
            full_summary = header + summary + footer
            
            # 코멘트 게시
            self.git_provider.publish_comment(full_summary)
            get_logger().info("PR 리뷰 총평이 성공적으로 게시되었습니다.")
            
        except Exception as e:
            get_logger().error(f"총평 게시 중 오류: {e}")
