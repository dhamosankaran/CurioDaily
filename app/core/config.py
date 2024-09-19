import logging
from typing import List, Union, Any, Optional, Dict
from pydantic import AnyHttpUrl, PostgresDsn, Field, field_validator, SecretStr, computed_field
from pydantic_settings import BaseSettings
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secrets() -> Optional[dict[str, str]]:
    if os.getenv('GOOGLE_CLOUD_PROJECT'):
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')

        secrets = {}
        secret_ids = ['NEWS_API_KEY', 'OPENAI_API_KEY', 'DATABASE_URL', 'SECRET_KEY',
                      'POSTGRES_SERVER', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB',
                      'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
        
        for secret_id in secret_ids:
            try:
                name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secrets[secret_id] = response.payload.data.decode("UTF-8")
            except NotFound:
                logger.warning(f"Secret {secret_id} not found in GCP Secret Manager.")
            except Exception as e:
                logger.error(f"Error retrieving secret {secret_id}: {e}")
        
        return secrets
    else:
        return None

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CurioDaily"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
         "http://localhost",
         "http://localhost:8080",
         "https://localhost:8443",
         "https://autonomous-newsletter-457954888435.us-central1.run.app"
     ]

    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    ENVIRONMENT: str = Field(default="development")

    POSTGRES_SERVER: str = "host.docker.internal"
    POSTGRES_USER: str = "ainewsletteruser"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "autonomous_newsletter"
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = "postgresql://ainewsletteruser:pwd@localhost:5432/autonomous_newsletter"

    SENDER_EMAIL: str = Field(default="example@example.com")
    SENDER_PASSWORD: str = Field(default="")
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    RECIPIENT_EMAIL: str = Field(default="dhamuksy@hotmail.com")

    OPENAI_API_KEY: SecretStr = Field(default=SecretStr(""))
    NEWS_API_KEY: SecretStr = Field(default=SecretStr(""))
    SECRET_KEY: SecretStr = Field(default=SecretStr(""))

    # Change this to a regular field without leading underscore
    base_url: str = Field(default="https://localhost:8443")

    @computed_field
    @property
    def postgres_server(self) -> str:
        if self.ENVIRONMENT == "development":
            return self.POSTGRES_SERVER
        elif self.ENVIRONMENT == "production":
            return os.getenv("POSTGRES_SERVER", self.POSTGRES_SERVER)
        return "host.docker.internal"

    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("postgres_server", info.data.get("POSTGRES_SERVER")),
            port=int(info.data.get("POSTGRES_PORT", 5432)),
            path=f"/{info.data.get('POSTGRES_DB') or ''}",
        )

    @computed_field
    @property
    def PROTOCOL(self) -> str:
        return "https" if self.ENVIRONMENT == "production" else "http"

    @computed_field
    @property
    def BASE_URL(self) -> str:
        if self.ENVIRONMENT == "production":
            return "https://autonomous-newsletter-457954888435.us-central1.run.app"
        elif self.ENVIRONMENT == "development":
            return self.base_url
        else:
            return "http://host.docker.internal"

        

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    @classmethod
    def from_gcp_secrets(cls) -> 'Settings':
        secrets = get_secrets()
        if secrets:
            return cls(**secrets)
        return cls()

def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return Settings.from_gcp_secrets()
    return Settings()

settings = get_settings()

logger.info("Settings loaded:")
for field, value in settings.model_dump().items():
    if isinstance(value, SecretStr):
        logger.info(f"{field}: [REDACTED]")
    else:
        logger.info(f"{field}: {value}")