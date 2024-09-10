import os
from google.cloud import secretmanager
from pydantic import BaseModel, SecretStr
from typing import Dict, Any

class SecretTest(BaseModel):
    secret_value: SecretStr

def get_secret(project_id: str, secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        return f"Error accessing secret: {str(e)}"

def test_gcp_secrets():
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("GOOGLE_CLOUD_PROJECT environment variable is not set.")
        return

    secret_ids = [
        'NEWS_API_KEY',
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'SECRET_KEY',
        'POSTGRES_SERVER',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB',
        'SENDER_EMAIL',
        'SENDER_PASSWORD',
        'RECIPIENT_EMAIL'
    ]

    results: Dict[str, Any] = {}

    for secret_id in secret_ids:
        secret_value = get_secret(project_id, secret_id)
        try:
            SecretTest(secret_value=secret_value)
            results[secret_id] = "Valid"
        except Exception as e:
            results[secret_id] = f"Invalid: {str(e)}"

    print("\nGCP Secret Manager Test Results:")
    print("================================")
    for secret_id, result in results.items():
        print(f"{secret_id}: {result}")

if __name__ == "__main__":
    test_gcp_secrets()