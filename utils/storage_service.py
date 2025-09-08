# src/utils/storage_service.py
import boto3
import os
from  botocore.exceptions import NoCredentialsError, ClientError

# --- Configuration is loaded at the module level ---
SPACES_KEY = os.getenv("DO_SPACES_KEY")
SPACES_SECRET = os.getenv("DO_SPACES_SECRET")
SPACES_NAME = os.getenv("DO_SPACES_NAME")
SPACES_REGION = os.getenv("DO_SPACES_REGION")
SPACES_ENDPOINT_URL = os.getenv("DO_SPACES_ENDPOINT_URL")

# --- A private, global variable to hold the client instance (Singleton) ---
_client = None

def get_client():
    """
    Creates and returns a boto3 client for DigitalOcean Spaces.
    Uses a singleton pattern to ensure only one client is created per session.
    This is "lazy loaded" - it only connects when first called.
    """
    global _client
    if _client is None:
        print("   - Creating new S3 client for Spaces...")
        if not all([SPACES_KEY, SPACES_SECRET, SPACES_NAME, SPACES_REGION, SPACES_ENDPOINT_URL]):
            print("   - ❌ Critical Error: Missing one or more DigitalOcean Spaces environment variables.")
            # We don't raise an exception here, so the app can start, but functions will fail gracefully.
            return None
        
        session = boto3.session.Session()
        _client = session.client('s3',
                                region_name=SPACES_REGION,
                                endpoint_url=SPACES_ENDPOINT_URL,
                                aws_access_key_id=SPACES_KEY,
                                aws_secret_access_key=SPACES_SECRET)
        print("   - ✅ S3 Client created successfully.")
    return _client

def upload_file(file_path, object_name):
    """Upload a file to the configured Spaces bucket."""
    client = get_client()
    if not client: return None
    
    try:
        client.upload_file(file_path, SPACES_NAME, object_name)
        print(f"   - ✅ File '{object_name}' uploaded successfully to Spaces.")
        return f"{SPACES_ENDPOINT_URL}/{SPACES_NAME}/{object_name}"
    except FileNotFoundError:
        print(f"   - ❌ The file to upload was not found at '{file_path}'.")
        return None
    except NoCredentialsError:
        print("   - ❌ Credentials not available for Spaces authentication.")
        return None
    except Exception as e:
        print(f"   - ❌ An unexpected error occurred during upload: {e}")
        return None

def get_file_content(object_name):
    """Retrieve the content of a file from  Spaces."""
    client = get_client()
    if not client: return None
    
    try:
        response = client.get_object(Bucket=SPACES_NAME, Key=object_name)
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"   - ℹ️  Info: File '{object_name}' not found in Spaces.")
        else:
            print(f"   - ❌ A client error occurred while retrieving file: {e}")
        return None
    except Exception as e:
        print(f"   - ❌ Could not retrieve file '{object_name}': {e}")
        return None
