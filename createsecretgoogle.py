import os
from google.cloud import secretmanager
from dotenv import load_dotenv

def create_secret(project_id, secret_id, secret_value):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"

    # Create the secret
    secret = client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        }
    )

    # Add the secret version
    version = client.add_secret_version(
        request={
            "parent": secret.name,
            "payload": {"data": secret_value.encode("UTF-8")},
        }
    )

    print(f"Created secret {secret_id} in {project_id}")

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Get the Google Cloud project ID
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")

    # Iterate through all environment variables
    for key, value in os.environ.items():
        # Skip the GOOGLE_CLOUD_PROJECT variable
        if key != "GOOGLE_CLOUD_PROJECT":
            try:
                create_secret(project_id, key, value)
            except Exception as e:
                print(f"Error creating secret for {key}: {str(e)}")

if __name__ == "__main__":
    main()