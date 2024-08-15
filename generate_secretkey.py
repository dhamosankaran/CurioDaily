import secrets

# Generate a 32-byte random string
secret_key = secrets.token_urlsafe(32)
print(f"Generated SECRET_KEY: {secret_key}")