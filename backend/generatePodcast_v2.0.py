import os
import requests
import json
import re
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ElevenLabs API configuration
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Parameters for podcast script
topic = "Einstein's Laws of Gravity"  # Replace with your topic
length = 10  # Duration in minutes
tone = "informal"  # Adjust as needed
style = "conversational"  # Adjust as needed

# Speaker profiles
speaker_profiles = [
    {"name": "Speaker 1", "personality": "curious", "voice_id": "iP95p4xoKVk53GoZ742B"},
    {"name": "Speaker 2", "personality": "skeptical", "voice_id": "cgSgspJ2msm6clMCkdW9"}
]

# Build the prompt
prompt = f"""
Generate a detailed podcast script for a dialogue between two speakers. The script will later be used for voice cloning and converted into a podcast audio file. Ensure the script meets the following criteria:

1. Topic: The podcast should be about "{topic}" and must provide an informative yet engaging discussion of the topic.
2. Length: The script should be approximately {length} minutes long.
3. Speakers: The dialogue should alternate between two speakers:
   - Speaker 1: Has a "{speaker_profiles[0]['personality']}" personality".
   - Speaker 2: Has a "{speaker_profiles[1]['personality']}" personality".
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

# Function to generate text-to-speech audio using ElevenLabs
def generate_audio(text, voice_id, output_path):
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.9}
    }
    response = requests.post(f"{ELEVENLABS_API_URL}/{voice_id}", headers=headers, json=data)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to {output_path}")
    else:
        print(f"Error generating audio: {response.status_code}")
        print("Response:", response.text)

# Function to remove excess information from the generated JSON output
def extract_json_content(raw_content):
    """
    Extracts the JSON content from a string that may contain extra text 
    before or after the JSON block.

    Args:
        raw_content (str): The raw string containing JSON and other excess text.

    Returns:
        list or dict: The parsed JSON content, if successfully extracted and loaded.
        None: If no valid JSON content is found.
    """
    try:
        # Use a regex to find the JSON content (starts with [ and ends with ])
        json_match = re.search(r"\[.*\]", raw_content, re.DOTALL)
        if not json_match:
            print("Error: No valid JSON content found in the provided string.")
            return None
        
        # Extract the JSON string
        json_string = json_match.group(0)

        # Parse and return the JSON content
        return json_string

    except json.JSONDecodeError as e:
        print("Error: Unable to parse JSON content.")
        print("JSONDecodeError:", e)
        return None

# Prepare the request payload to Groq API
payload = {
    "model": "llama3-8b-8192",  # Replace with the appropriate model if required
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7  # Adjust creativity level if needed
}

# Post API request and poll to check for success
try:
    response = requests.post(
        GROQ_API_URL,
        json=payload,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
    )

    if response.status_code == 200:
        response_json = response.json()
        podcast_script = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        podcast_script = extract_json_content(podcast_script)
        audio_segments = []

        # Parse the JSON script
        try:
            script_lines = json.loads(podcast_script)
    
            for i, line in enumerate(script_lines):
                speaker = line.get("speaker")
                text = line.get("text")

                # Find the corresponding speaker's voice ID
                speaker_profile = next(sp for sp in speaker_profiles if sp["name"] == speaker)
                voice_id = speaker_profile["voice_id"]
                
                # Generate audio for each line
                output_file = f"backend/audio/audio_line_{i + 1}.mp3"
                generate_audio(text, voice_id, output_file)
                audio_segments.append(output_file)

            if audio_segments:
                audio_segments = [AudioSegment.from_file(file) for file in audio_segments]
                podcast = sum(audio_segments)
                podcast.export("final_podcast.mp3", format="mp3")
                print("Final podcast saved as 'final_podcast.mp3'.")
            else:
                print("No audio files were generated; skipping podcast creation.") 
         
        except json.JSONDecodeError:
            print("Error: Unable to parse the podcast script JSON.")
    else:
        print(f"Error: Received status code {response.status_code}")
        print("Response:", response.text)

except requests.exceptions.RequestException as e:
    print(f"Error: Unable to connect to Groq API. {e}")