import hmac
import hashlib
from testergpt.settings import settings
import jwt
import time
import requests

GITHUB_COMMIT_INLINE_COMMENT_URL_TEMPLATE = (
    "https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
)


def verify_signature(request_body: bytes, signature_header: str) -> bool:
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

    # Debug information
    print(f"🔐 Generating JWT for GitHub App ID: {app_id}")
    print(f"🔑 Private key length: {len(private_key) if private_key else 0} characters")
    print(
        f"🔑 Private key starts with: {private_key[:50] if private_key else 'None'}..."
    )

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
        print(f"✅ JWT generated successfully")
        return token
    except Exception as e:
        print(f"❌ Failed to generate JWT: {e}")
        raise


def get_installation_token(jwt_token: str, installation_id: int) -> str:
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    print(f"🔗 Requesting installation token from: {url}")
    print(f"📋 JWT token length: {len(jwt_token)} characters")

    try:
        resp = requests.post(url, headers=headers)
        print(f"📡 GitHub API response status: {resp.status_code}")

        if resp.status_code != 201:
            print(f"❌ Error response: {resp.text}")
            print(f"❌ Response headers: {dict(resp.headers)}")

        resp.raise_for_status()
        token_data = resp.json()
        print(f"✅ Installation token obtained successfully")
        return token_data["token"]
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error getting installation token: {e}")
        print(
            f"❌ Response content: {resp.text if 'resp' in locals() else 'No response'}"
        )
        raise
    except Exception as e:
        print(f"❌ Unexpected error getting installation token: {e}")
        raise
