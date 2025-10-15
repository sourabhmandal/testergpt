"""
Github related integrations
"""

import requests
from typing import Dict, Optional, Tuple
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from core.llm_client import flow_test_planner, review_pr
from core.services.github import get_pr_diff, get_pr_latest_commit_diff
from rest_framework.response import Response
from core.views.github import GithubPRChanged
from core.types import PRReviewResponse
from core.utils import (
    GITHUB_COMMIT_INLINE_COMMENT_URL_TEMPLATE,
    generate_jwt,
    get_installation_token,
)
from unidiff import PatchSet


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
    delivery = request.headers.get("X-GitHub-Delivery", "unknown")

    # handle events
    print(f"Received event={event} delivery={delivery}")
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


def post_pr_comments(payload: GithubPRChanged, review_response: PRReviewResponse):
    if not review_response.issues:
        print("No issues found in the diff, skipping comment posting")
        return

    if not payload or not payload.pull_request:
        print("Invalid payload data, cannot post comments")
        return

    try:
        # Step 1: Generate JWT
        jwt_token = generate_jwt()

        # Step 2: Exchange for installation token
        installation_id = payload.installation.id
        installation_token = get_installation_token(jwt_token, installation_id)

        # Step 3: Get the diff to understand line positions
        diff_info = _get_diff_line_mapping(payload)
        print(
            f"🔍 Parsed diff info for {len(diff_info)} files: {list(diff_info.keys())}"
        )

        # Debug: Print some line mappings
        for file_path, line_map in diff_info.items():
            if line_map:
                print(
                    f"📊 {file_path}: lines {min(line_map.keys())}-{max(line_map.keys())} available"
                )
            else:
                print(f"📊 {file_path}: no lines found in diff")

        # GitHub API endpoint
        url = GITHUB_COMMIT_INLINE_COMMENT_URL_TEMPLATE.format(
            owner=payload.repository.owner.login,
            repo=payload.repository.name,
            pull_number=payload.pull_request.number,
        )

        print(f"Calling PR Comment URL: {url}")

        headers = {
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        successful_comments = 0
        for issue in review_response.issues:
            emoji = {"error": "🚫", "warning": "⚠️", "suggestion": "💡"}.get(
                issue.type, "ℹ️"
            )
            comment_body = f"{emoji} **{issue.type.title()}** ({issue.severity} severity)\\n\\n{issue.message}"

            # Parse the line number from the issue
            try:
                line_num = (
                    int(issue.line.split("-")[0])
                    if "-" in issue.line
                    else int(issue.line)
                )
            except (ValueError, AttributeError):
                print(f"⚠️ Invalid line number format: {issue.line}, skipping comment")
                continue

            # Check if this file and line exist in the diff
            file_path = issue.file
            diff_position = _get_diff_position(diff_info, file_path, line_num)

            if diff_position is None:
                print(
                    f"⚠️ Line {line_num} in file {file_path} not found in diff, posting as general PR comment"
                )
                # Fall back to posting as a general PR comment (issue comment)
                success = _post_general_pr_comment(
                    payload, installation_token, comment_body, file_path, line_num
                )
                if success:
                    successful_comments += 1
                continue

            # Use both position and line parameters for compatibility
            api_payload = {
                "body": comment_body,
                "commit_id": payload.pull_request.head.sha,
                "path": file_path,
                "position": diff_position,
                "line": line_num,
                "side": "RIGHT",
            }

            print(
                f"📝 Posting PR comment to {file_path}:{line_num} (diff position: {diff_position})"
            )
            response = requests.post(url, json=api_payload, headers=headers)
            if response.status_code == 201:
                print(f"✅ Posted comment for {file_path}:{line_num}")
                successful_comments += 1
            else:
                print(f"❌ Failed ({response.status_code}): {response.text}")
                # Try fallback to general PR comment
                print(
                    f"🔄 Trying fallback to general PR comment for {file_path}:{line_num}"
                )
                success = _post_general_pr_comment(
                    payload, installation_token, comment_body, file_path, line_num
                )
                if success:
                    successful_comments += 1

        print(
            f"🎯 Posted {successful_comments}/{len(review_response.issues)} comments successfully"
        )

    except Exception as e:
        print(f"Error posting PR comments: {e}")
        raise


def _get_diff_line_mapping(payload: GithubPRChanged) -> Dict[str, Dict[int, int]]:
    """
    Get mapping of file line numbers to diff positions.
    Returns: {file_path: {line_number: diff_position}}
    """
    try:
        diff_url = payload.pull_request.diff_url
        response = requests.get(diff_url)
        response.raise_for_status()

        patch = PatchSet(response.text)
        line_mapping = {}

        for patched_file in patch:
            file_path = patched_file.path
            if file_path.startswith("b/"):
                file_path = file_path[2:]  # Remove 'b/' prefix

            line_mapping[file_path] = {}
            position = 0

            for hunk in patched_file:
                for line in hunk:
                    position += 1
                    # Only map lines that are additions or context (not deletions)
                    if line.line_type in ["+", " "]:
                        if line.target_line_no:
                            line_mapping[file_path][line.target_line_no] = position

        return line_mapping
    except Exception as e:
        print(f"Error parsing diff for line mapping: {e}")
        return {}


def _get_diff_position(
    diff_info: Dict[str, Dict[int, int]], file_path: str, line_num: int
) -> Optional[int]:
    """
    Get the diff position for a specific file and line number.
    Returns None if the line doesn't exist in the diff.
    """
    # Try exact file path match first
    if file_path in diff_info:
        return diff_info[file_path].get(line_num)

    # Try matching without leading path components (in case of path differences)
    for diff_file_path, line_map in diff_info.items():
        if diff_file_path.endswith(file_path) or file_path.endswith(diff_file_path):
            return line_map.get(line_num)

    return None


def _post_general_pr_comment(
    payload: GithubPRChanged,
    installation_token: str,
    comment_body: str,
    file_path: str,
    line_num: int,
) -> bool:
    """
    Post a general comment on the PR (issue comment) as fallback when review comments fail.
    """
    try:
        # URL for general PR comments (issue comments)
        url = f"https://api.github.com/repos/{payload.repository.owner.login}/{payload.repository.name}/issues/{payload.pull_request.number}/comments"

        headers = {
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Include file and line info in the comment body
        enhanced_body = (
            f"**File: `{file_path}` (around line {line_num})**\\n\\n{comment_body}"
        )

        api_payload = {"body": enhanced_body}

        print(f"📝 Posting general PR comment for {file_path}:{line_num}")
        response = requests.post(url, json=api_payload, headers=headers)

        if response.status_code == 201:
            print(f"✅ Posted general comment for {file_path}:{line_num}")
            return True
        else:
            print(
                f"❌ Failed to post general comment ({response.status_code}): {response.text}"
            )
            return False

    except Exception as e:
        print(f"❌ Error posting general PR comment: {e}")
        return False
