import http.client
import httplib2
import os
import random
import sys
import time
import pickle

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Explicitly tell the underlying HTTP transport library not to retry
httplib2.RETRIES = 1
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine
)

# Always retry on these HTTP error codes
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# Update this path to your client secrets file in Colab
CLIENT_SECRETS_FILE = "/content/drive/MyDrive/YouTUBE REDDIT/colab_creds.json"

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
with information from the API Console:
https://console.cloud.google.com/

For more information, see:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service():
    REDIRECT_URI = "http://localhost:8080"  # Still needed for flow configuration
    CREDENTIALS_FILE = "oauth2_credentials.pkl"  # Store credentials in a pickle file

    # Check for existing credentials
    credentials = None
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "rb") as token:
            credentials = pickle.load(token)

    # If no valid credentials, perform OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=YOUTUBE_UPLOAD_SCOPE,
                redirect_uri=REDIRECT_URI
            )
            # Manual OAuth flow for Colab
            auth_url, _ = flow.authorization_url(prompt="consent")
            print(f"Please visit this URL to authorize the application: {auth_url}")
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            credentials = flow.credentials

        # Save the credentials for future runs
        with open(CREDENTIALS_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 credentials=credentials)

def initialize_upload(youtube, options):
    tags = options.keywords.split(",") if options.keywords else None

    body = {
        "snippet": {
            "title": options.title,
            "description": options.description,
            "tags": tags,
            "categoryId": options.category
        },
        "status": {
            "privacyStatus": options.privacyStatus
        }
    }

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response and "id" in response:
                print(f"Video ID '{response['id']}' was successfully uploaded.")
                return
            else:
                raise Exception(f"Unexpected response: {response}")

        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP error {e.resp.status}: {e.content}"
            else:
                raise
        except Exception as e:
            error = f"Retriable error occurred: {e}"

        if error:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                sys.exit("Max retries reached. Upload failed.")

            sleep_seconds = random.uniform(0, 2 ** retry)
            print(f"Sleeping {sleep_seconds:.2f} seconds before retrying...")
            time.sleep(sleep_seconds)

if __name__ == "__main__":
    from argparse import ArgumentParser
    argparser = ArgumentParser()
    argparser.add_argument("--file", required=True, help="Video file to upload")
    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description", help="Video description", default="Test Description")
    argparser.add_argument("--category", default="22", help="Numeric video category")
    argparser.add_argument("--keywords", help="Video keywords, comma separated", default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default="public", help="Video privacy status")

    args = argparser.parse_args()

    if not os.path.exists(args.file):
        sys.exit("Please specify a valid file using the --file= parameter.")

    youtube = get_authenticated_service()

    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
