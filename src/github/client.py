import requests
import hmac
import hashlib
import jwt
import time
import requests
from src.config.env import settings
from http import HTTPMethod
import logging

from src.github.types import GithubPRRequest, GithubPrDiffResponse, PRReviewResponse

logger = logging.getLogger(__name__)

# ------------------------- GITHUB API ----------------------------- #
def github_pr_diff_content(payload__pull_request__diff_url: str, installation_id: int) -> GithubPrDiffResponse:
    """Fetch PR diff content synchronously using requests.

    This function is intentionally synchronous because it uses the
    `requests` library. Callers that run inside an async event loop
    should execute this in a thread (e.g. via asyncio.to_thread).
    """
    response = call_github_api(payload__pull_request__diff_url, HTTPMethod.GET, installation_id=installation_id)
    if not response.text:
        logger.warning("Received empty diff text from GitHub")

    return GithubPrDiffResponse(diff_text=response.text)

def post_pr_comments(payload: GithubPRRequest, review_response: PRReviewResponse):
    if not review_response.issues:
        logger.debug("No issues found in the diff, skipping comment posting")
        return
    diff_info = _get_diff_line_mapping(payload)
    logger.debug(f"🔍 Parsed diff info for {diff_info}")

    for file_path, line_map in diff_info.items():
        if line_map:
            logger.debug(
                f"📊 {file_path}: lines {min(line_map.keys())}-{max(line_map.keys())} available"
            )
        else:
            logger.debug(f"📊 {file_path}: no lines found in diff")

    successful_comments = 0
    for issue in review_response.issues:
        emoji = {"error": "🚫", "warning": "⚠️", "suggestion": "💡"}.get(
            issue.type, "ℹ️"
        )
        comment_body = f"""{emoji} **{issue.type.title()}** ({issue.severity} severity)
        
        {issue.message}"""

        # Parse the line number from the issue
        try:
            line_num = (
                int(issue.line.split("-")[0])
                if "-" in issue.line
                else int(issue.line)
            )
        except (ValueError, AttributeError):
            logger.debug(f"⚠️ Invalid line number format: {issue.line}, skipping comment")
            continue

        # Check if this file and line exist in the diff
        file_path = issue.file
        diff_position = _get_diff_position(diff_info, file_path, line_num)

        if diff_position is None:
            logger.debug(
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

        logger.debug(
            f"📝 Posting PR comment to {file_path}:{line_num} (diff position: {diff_position})"
        )
        response = requests.post(url, json=api_payload, headers=headers)
        if response.status_code == 201:
            logger.debug(f"✅ Posted comment for {file_path}:{line_num}")
            successful_comments += 1
        else:
            logger.debug(f"❌ Failed ({response.status_code}): {response.text}")
            # Try fallback to general PR comment
            logger.debug(
                f"🔄 Trying fallback to general PR comment for {file_path}:{line_num}"
            )
            success = _post_general_pr_comment(
                payload, installation_token, comment_body, file_path, line_num
            )
            if success:
                successful_comments += 1

    logger.debug(
        f"🎯 Posted {successful_comments}/{len(review_response.issues)} comments successfully"
    )

# ----------------------- AUTH UTILITIES -------------------------- #

def call_github_api(url: str, method: HTTPMethod, installation_id: int, data: dict = None) -> requests.Response:
    try:
        jwt_token = generate_jwt()
        installation_token = get_installation_token(jwt_token, installation_id)
        headers = {
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        match method:
            case HTTPMethod.GET:
                resp = requests.get(url, headers=headers)
            case HTTPMethod.POST:
                resp = requests.post(url, headers=headers, json=data)

        resp.raise_for_status()
        return resp
    except Exception as e:
        logger.error(f"Error calling GitHub API: {e}")
        raise

def _verify_signature(request_body: bytes, signature_header: str) -> bool:
    """
    Verifies X-Hub-Signature-256 header using HMAC SHA256.
    signature_header example: "sha256=abcdef..."
    """
    if not signature_header:
        return False

    # For development/testing - if secret is the default placeholder, allow all requests
    if settings.GITHUB_SECRET == "ghp_YourGitHubTokenHere":
        print(
            "WARNING: Using placeholder GitHub secret - webhook signature verification disabled for development"
        )
        return True

    try:
        sha_name, signature = signature_header.split("=", 1)
    except ValueError:
        return False

    if sha_name != "sha256":
        return False

    # Convert secret to bytes if it's a string
    secret_key = (
        settings.GITHUB_SECRET.encode("utf-8")
        if isinstance(settings.GITHUB_SECRET, str)
        else settings.GITHUB_SECRET
    )
    mac = hmac.new(secret_key, msg=request_body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    # use hmac.compare_digest to avoid timing attacks
    return hmac.compare_digest(expected, signature)

def generate_jwt() -> str:
    now = int(time.time())
    app_id, private_key = settings.GITHUB_APP_ID, settings.GITHUB_PRIVATE_KEY

    if not app_id or app_id == 0:
        raise ValueError("GitHub App ID is not configured")

    if not private_key:
        raise ValueError("GitHub Private Key is not configured")

    payload = {
        "iat": now - 60,  # issued at
        "exp": now + (10 * 60),  # JWT valid for 10 minutes
        "iss": str(app_id),  # GitHub App ID (ensure it's a string)
    }

    try:
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return token
    except Exception as e:
        print(f"Failed to generate JWT: {e}")
        raise

def get_installation_token(jwt_token: str, installation_id: int) -> str:
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        resp = requests.post(url, headers=headers)
        if resp.status_code != 201:
            print(f"❌ Error response: {resp.text}")

        resp.raise_for_status()
        token_data = resp.json()
        return token_data["token"]
    except Exception as e:
        print(f"❌ error getting installation token: {e}")
        raise
