from pydantic_settings import BaseSettings
from typing import List, Union, Any
from pydantic import AnyHttpUrl, PostgresDsn, validator, SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "CurioDaily"
    BACKEND_CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Union[PostgresDsn, str, None] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Union[str, None], values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        ).unicode_string()  # Convert to string

    OPENAI_API_KEY: SecretStr
    NEWS_API_KEY: SecretStr
    SECRET_KEY: SecretStr

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Debugging: Print out the settings (be careful with sensitive information)
print("Settings loaded:")
for field, value in settings.dict().items():
    if isinstance(value, SecretStr):
        print(f"{field}: [REDACTED]")
    else:
        print(f"{field}: {value}")