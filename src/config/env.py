from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_VERSION: str
    ENVIRONMENT: str
    DATABASE_URL: str
    DEBUG: bool = False
    PORT: int = 5000
    ALLOWED_HOSTS: list[str] = ["*"]
    SECRET_KEY: str = "django-insecure-66#o%971*dr0+mh9byikg^pdb*f!+fv$$es!!iome!q@bg0f4-"
    GITHUB_SECRET: str = "ghp_YourGitHubTokenHere"
    GPT_API_KEY: str = "sk-YourAIKeyHere"
    GITHUB_APP_ID: int = 0
    GITHUB_PRIVATE_KEY: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Read GitHub private key from file if not provided in env
        if not self.GITHUB_PRIVATE_KEY:
            self.GITHUB_PRIVATE_KEY = self.read_github_private_key()

        # Validate GitHub App configuration
        self._validate_github_config()

    def _validate_github_config(self):
        """Validate GitHub App configuration"""
        issues = []

        if not self.GITHUB_APP_ID or self.GITHUB_APP_ID == 0:
            issues.append("GITHUB_APP_ID is not set or is 0")

        if not self.GITHUB_PRIVATE_KEY:
            issues.append(
                "GITHUB_PRIVATE_KEY is not available (check .env file or pemfiles/testergpt.github.pem)"
            )
        elif not self.GITHUB_PRIVATE_KEY.startswith("-----BEGIN"):
            issues.append("GITHUB_PRIVATE_KEY does not appear to be a valid PEM format")

        if not self.GITHUB_SECRET or self.GITHUB_SECRET == "ghp_YourGitHubTokenHere":
            issues.append("GITHUB_SECRET is not configured (using placeholder value)")

        if issues:
            print("⚠️  GitHub App Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")
            print("   GitHub webhook functionality may not work properly.")
        else:
            print("✅ GitHub App configuration appears valid")

    def read_github_private_key(self) -> str:
        """Read GitHub private key from file"""
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            key_file_path = Path(BASE_DIR).joinpath("pemfiles", "testergpt.github.pem")
            if key_file_path.exists():
                return key_file_path.read_text(encoding="utf-8").strip()
            else:
                print(f"Warning: GitHub private key file not found at {key_file_path}")
                return ""
        except Exception as e:
            print(f"Error reading GitHub private key: {e}")
            return ""


    class Config:
        env_file = ".env"  # Pydantic will load from .env


settings = Settings()
