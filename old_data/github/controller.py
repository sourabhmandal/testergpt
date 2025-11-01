from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from core.llm_client import flow_test_planner, review_pr
from github.github_pr_manager import get_pr_diff, get_pr_latest_commit_diff
from rest_framework.response import Response
from core.types import GithubPRChanged
import logging


logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {"status": "ok"}, status=200, headers={"ngrok-skip-browser-warning": "<>"}
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def github_webhook(request):
    event = request.headers.get("X-GitHub-Event", "unknown")

    # handle events
    logger.info(f"Received event={event}")
    if event == "ping":
        return Response({"msg": "pong"}, status=200)

    # PR Opened for first time
    if event == "pull_request" and request.data.get("action") == "opened":
        try:
            payload = GithubPRChanged(**request.data)
            print(
                f"✅ Successfully parsed webhook payload for PR #{payload.number}: {payload.pull_request.title}"
            )
        except Exception as e:
            print(f"Failed to parse webhook payload: {e}")
            print(
                f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}"
            )
            return Response({"error": "Invalid payload structure"}, status=400)

        if not payload.pull_request.state == "open":
            print(f"PR #{payload.number} is not open, skipping processing")
            return Response({"msg": "PR not open, skipping"}, status=200)

        # Fetch diff
        try:
            print(f"🔍 Fetching diff content for PR #{payload.number}")
            diff_text = get_pr_diff(payload)
            print(f"📄 Retrieved diff content ({len(diff_text)} characters)")

            # ai
            print(f"🤖 Running AI review on diff...")
            review_response = review_pr(diff=diff_text)
            print(
                f"📝 AI review completed with {len(review_response.issues) if review_response.issues else 0} issues found"
            )

            post_pr_comments(payload, review_response=review_response)
            print(f"✅ Successfully processed PR #{payload.number}")
        except Exception as e:
            print(f"Error processing pull request: {e}")
            return Response({"error": "Failed to process pull request"}, status=500)
    # New commit pushed to existing PR
    elif event == "pull_request" and request.data.get("action") == "synchronize":
        try:
            print(f"🔍 Fetching diff content for PR #{payload.number}")
            diff_text = get_pr_latest_commit_diff(payload)
            print(f"📄 Retrieved diff content ({len(diff_text)} characters)")

            # ai-review
            print(f"🤖 Running AI review on diff...")
            review_response = review_pr(diff=diff_text)
            test_plan = flow_test_planner(diff=diff_text)
            print(
                f"📝 AI review completed with {len(review_response.issues) if review_response.issues else 0} issues found"
            )
            print(test_plan)
            post_pr_comments(payload, review_response=review_response)
            print(f"✅ Successfully processed PR #{payload.number}")
        except Exception as e:
            print(f"Failed to parse webhook payload: {e}")
            print(
                f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}"
            )
            return Response({"error": "Invalid payload structure"}, status=400)

        if not payload.pull_request.state == "open":
            print(f"PR #{payload.number} is not open, skipping processing")
            return Response({"msg": "PR not open, skipping"}, status=200)

        # Fetch diff
        try:
            print(f"🔍 Fetching diff content for PR #{payload.number}")
            diff_text = get_pr_latest_commit_diff(payload)
            print(f"📄 Retrieved diff content ({len(diff_text)} characters)")

            # ai
            print(f"🤖 Running AI review on diff...")
            review_response = review_pr(diff=diff_text)
            print(
                f"📝 AI review completed with {len(review_response.issues) if review_response.issues else 0} issues found"
            )

            post_pr_comments(payload, review_response=review_response)
            print(f"✅ Successfully processed PR #{payload.number}")
        except Exception as e:
            print(f"Error processing pull request: {e}")
            return Response({"error": "Failed to process pull request"}, status=500)
    return Response("", status=204)
