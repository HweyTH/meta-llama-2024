import requests
import os
import urllib.parse
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the path of the PDF files
src_file = "test.pdf"

# Playnote URL
url = "https://api.play.ai/api/v1/playnotes"

# Retrieve API key and User ID from environment variables
api_key = os.getenv("PLAYDIALOG_API_KEY")
user_id = os.getenv("PLAYDIALOG_USER_ID")

# Set up headers with authorization details
headers = {
    'AUTHORIZATION': api_key,
    'X-USER-ID': user_id,
    'accept': 'application/json'
}

# Configure the request parameters
files = {
    'sourceFileUrl': (None, src_file),
    'synthesisStyle': (None, 'podcast'),
    'voice1': (None, 's3://voice-cloning-zero-shot/baf1ef41-36b6-428c-9bdf-50ba54682bd8/original/manifest.json'),
    'voice1Name': (None, 'Angelo'),
    'voice2': (None, 's3://voice-cloning-zero-shot/e040bd1b-f190-4bdb-83f0-75ef85b18f84/original/manifest.json'),
    'voice2Name': (None, 'Deedee'),
}

# Send the POST request
response = requests.post(url, headers=headers, files=files)

# Initialize PlayNoteID
playNoteId = ''

# Check the response
if response.status_code == 201:
    print("Request sent successfully!")
    playNoteId = response.json().get('id')
    print(f"Generated PlayNote ID: {playNoteId}")
else:
    print(f"Failed to generate PlayNote: {response.text}")

if (playNoteId != ''):
    # Double-encode the PlayNote ID for the URL
    double_encoded_id = urllib.parse.quote(playNoteId, safe='')

    # Construct the final URL to check the status
    status_url = f"https://api.play.ai/api/v1/playnotes/{double_encoded_id}"

    # Poll for completion
    while True:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            playnote_data = response.json()
            status = playnote_data['status']
            if status == 'completed':
                print("PlayNote generation complete!")
                print("Audio URL:", playnote_data['audioUrl'])
                break
            elif status == 'generating':
                print("Please wait, your PlayNote is still generating...")
                time.sleep(10)  # Wait for 2 minute before polling again
            else:
                print("PlayNote creation failed, please try again.")
                break
        else:
            print(f"Error polling for PlayNote status: {response.text}")
            break
else:
    print('Error while generating a podcast with the current file')


