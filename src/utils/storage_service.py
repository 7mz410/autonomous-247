# src/utils/storage_service.py
import boto3
import os
from botocore.exceptions import NoCredentialsError

# --- Load Credentials from Environment ---
SPACES_KEY = os.getenv("DO_SPACES_KEY")
SPACES_SECRET = os.getenv("DO_SPACES_SECRET")
SPACES_NAME = os.getenv("DO_SPACES_NAME")
SPACES_REGION = os.getenv("DO_SPACES_REGION")
SPACES_ENDPOINT_URL = os.getenv("DO_SPACES_ENDPOINT_URL")

session = boto3.session.Session()
client = session.client('s3',
                        region_name=SPACES_REGION,
                        endpoint_url=SPACES_ENDPOINT_URL,
                        aws_access_key_id=SPACES_KEY,
                        aws_secret_access_key=SPACES_SECRET)

def upload_file(file_path, object_name):
    """Upload a file to a Spaces bucket"""
    try:
        client.upload_file(file_path, SPACES_NAME, object_name)
        print(f"   - ✅ File '{object_name}' uploaded successfully to Spaces.")
        # We will return the public URL for now, but a CDN is better for production
        return f"{SPACES_ENDPOINT_URL}/{SPACES_NAME}/{object_name}"
    except FileNotFoundError:
        print(f"   - ❌ The file '{file_path}' was not found.")
        return None
    except NoCredentialsError:
        print("   - ❌ Credentials not available for Spaces.")
        return None

def get_file_content(object_name):
    """Retrieve the content of a file from Spaces"""
    try:
        response = client.get_object(Bucket=SPACES_NAME, Key=object_name)
        return response['Body'].read()
    except Exception as e:
        print(f"   - ❌ Could not retrieve file '{object_name}': {e}")
        return None
