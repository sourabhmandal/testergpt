from fastapi import APIRouter, Request, Response, BackgroundTasks
import logging
from src.github.types import GithubPRRequest
from src.github.service import fresh_pr_review

github_router = APIRouter(prefix="/github", tags=["GitHub"])
logger = logging.getLogger("github")

@github_router.get("/webhook")
async def github_webhook(req: Request):
    return Response(status_code=200, content="GitHub Webhook Endpoint is live")


@github_router.post("/webhook")
async def github_webhook(req: Request, background_tasks: BackgroundTasks):
    event = req.headers.get("X-GitHub-Event", "unknown")
    logger.info(f"Received event={event}")

    if event == "ping":
        return Response({"msg": "pong"}, status_code=200)

    # PR Opened for first time
    if event == "pull_request":
        try:
            payload = GithubPRRequest(**req.data)
            if not payload.pull_request.state == "open":
                print(f"PR #{payload.number} is not open, skipping processing")
                return Response({"msg": "PR not open, skipping"}, status_code=200)

            if req.data.get("action") in ["opened", "synchronize"]:
                fresh_pr_review(payload, background_tasks)

            # elif req.data.get("action") == "synchronize":
            #     try:
            #         print(f"🔍 Fetching diff content for PR #{payload.number}")
            #         diff_text = get_pr_latest_commit_diff(payload)
            #         print(f"📄 Retrieved diff content ({len(diff_text)} characters)")

            #         # ai-review
            #         print(f"🤖 Running AI review on diff...")
            #         review_response = review_pr(diff=diff_text)
            #         test_plan = flow_test_planner(diff=diff_text)
            #         print(
            #             f"📝 AI review completed with {len(review_response.issues) if review_response.issues else 0} issues found"
            #         )
            #         print(test_plan)
            #         post_pr_comments(payload, review_response=review_response)
            #         print(f"✅ Successfully processed PR #{payload.number}")
            #     except Exception as e:
            #         print(f"Failed to parse webhook payload: {e}")
            #         print(
            #             f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}"
            #         )
            #         return Response({"error": "Invalid payload structure"}, status=400)

            #     if not payload.pull_request.state == "open":
            #         print(f"PR #{payload.number} is not open, skipping processing")
            #         return Response({"msg": "PR not open, skipping"}, status=200)

            #     # Fetch diff
            #     try:
            #         print(f"🔍 Fetching diff content for PR #{payload.number}")
            #         diff_text = get_pr_latest_commit_diff(payload)
            #         print(f"📄 Retrieved diff content ({len(diff_text)} characters)")

            #         # ai
            #         print(f"🤖 Running AI review on diff...")
            #         review_response = review_pr(diff=diff_text)
            #         print(
            #             f"📝 AI review completed with {len(review_response.issues) if review_response.issues else 0} issues found"
            #         )

            #         post_pr_comments(payload, review_response=review_response)
            #         print(f"✅ Successfully processed PR #{payload.number}")
        
        except Exception as e:
            print(f"Error processing pull request: {e}")
            return Response({"error": "Failed to process pull request"}, status_code=500)
    return Response("", status_code=204)
