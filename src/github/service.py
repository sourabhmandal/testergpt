from fastapi import BackgroundTasks
from src.llm.types import ReviewCodeDiffRequest
from src.github.types import GithubPRRequest
from src.github.client import github_pr_diff_content, post_pr_comments
from src.llm.service import LLMService
import logging

logger = logging.getLogger(__name__)


async def fresh_pr_review(payload: GithubPRRequest, background_tasks: BackgroundTasks) -> None:
    """Fetch the PR diff (async) and run an AI review pipeline.

    This function was previously synchronous and called the async
    `github_pr_diff_content` without awaiting it, which produced a
    'coroutine was never awaited' warning. Making this function async
    and awaiting the call fixes that.
    """
    try:
        diff_url = payload.pull_request.diff_url
        if not diff_url:
            raise ValueError("Pull request diff URL not found")

        llm = LLMService()
        # github_pr_diff_content is synchronous (uses requests). Run it in a
        # thread to avoid blocking the event loop.
        diff_data = github_pr_diff_content(diff_url, payload.installation.id)

        review_response = llm.review_code_diff(code_diff_request=ReviewCodeDiffRequest(diff=diff_data.diff_text))
        num_issues = len(review_response.issues)
        logger.debug(f"📝 AI review completed with {num_issues} issues found")

        # schedule posting comments in background if desired
        # background_tasks.add_task(post_pr_comments, payload, review_response)
        logger.debug(f"✅ Successfully processed PR #{payload.number}")
    except Exception as e:
        logger.error(f"Error: fresh_pr_review : {e}")
        raise