import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq API configuration
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("Error: GROQ_API_KEY not found in environment variables.")
    exit(1)

# Parameters for podcast script
topic = "Einstein's Laws of Gravity"  # Replace with your topic
length = 10  # Duration in minutes
tone = "informal"  # Adjust as needed
style = "conversational"  # Adjust as needed

# Speaker profiles
speaker_profiles = [
    {"name": "Speaker 1", "personality": "curious", "expertise": "physics"},
    {"name": "Speaker 2", "personality": "skeptical", "expertise": "philosophy"}
]

# Build the prompt
prompt = f"""
Generate a detailed podcast script for a dialogue between two speakers. The script will later be used for voice cloning and converted into a podcast audio file. Ensure the script meets the following criteria:

1. Topic: The podcast should be about "{topic}" and must provide an informative yet engaging discussion of the topic.
2. Length: The script should be approximately {length} minutes long.
3. Speakers: The dialogue should alternate between two speakers:
   - Speaker 1: Has a "{speaker_profiles[0]['personality']}" personality and expertise in "{speaker_profiles[0]['expertise']}".
   - Speaker 2: Has a "{speaker_profiles[1]['personality']}" personality and expertise in "{speaker_profiles[1]['expertise']}".
4. Tone and Style: Use an "{tone}" tone and a "{style}" style to make the content accessible and engaging.
5. Restrictions:
   - Avoid including the names of the speakers in the script.
   - Do not introduce or conclude the podcast explicitly (e.g., no “Welcome to the show!”).
   - Keep the dialogue focused entirely on the topic.
   - Ensure the interaction is natural and feels like a genuine conversation.
6. Structure: The dialogue should:
   - Introduce the topic naturally through the conversation.
   - Cover key concepts, theories, or ideas comprehensively.
   - Include a balance of facts, examples, and analogies to explain complex ideas.
   - Feature occasional light humor or curiosity to maintain listener engagement.

Format the script as a JSON object, where each line of dialogue is represented as an array of objects with the following structure:

[
  {{"speaker": "Speaker 1", "text": "Opening line or question."}},
  {{"speaker": "Speaker 2", "text": "Response or follow-up."}}
]

The output should strictly follow this format, as it will be programmatically processed for voice cloning. Ensure there are no formatting errors.
"""

# Prepare the request payload
payload = {
    "model": "llama3-8b-8192",  # Replace with the appropriate model if required
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7  # Adjust creativity level if needed
}

# Make the API request
try:
    response = requests.post(
        API_URL,
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    # Check for successful response
    if response.status_code == 200:
        response_json = response.json()
        podcast_script = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        print(podcast_script)

        # Save the script to a file (optional)
        # with open("podcast_script.json", "w") as file:
        #     file.write(podcast_script)
    else:
        print(f"Error: Received status code {response.status_code}")
        print("Response:", response.text)

except requests.exceptions.RequestException as e:
    print(f"Error: Unable to connect to Groq API. {e}")
