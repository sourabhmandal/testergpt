from fastapi import BackgroundTasks
from src.github.types import GithubPRRequest
from src.github.client import github_pr_diff_content, post_pr_comments
from src.llm.service import LLMService
import logging
 
logger = logging.getLogger(__name__)
llm = LLMService()

def fresh_pr_review(payload: GithubPRRequest, background_tasks: BackgroundTasks) -> str:
    diff_url = payload.pull_request.diff_url
    if not diff_url:
        raise ValueError("Pull request diff URL not found")

    diff_data = github_pr_diff_content(diff_url)
    review_response = llm.review_code_diff(diff=diff_data)
    num_issues = len(review_response.issues)
    logger.debug(f"📝 AI review completed with {num_issues} issues found")

    background_tasks.add_task(post_pr_comments, payload, review_response)
    logger.debug(f"✅ Successfully processed PR #{payload.number}")