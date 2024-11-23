import os

from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq API client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Create a prompt for the podcast generation
content = "Generate the podcast script between 2 people. The podcast should be restricted as follows: \n"
content += "- The script dialogue should not contain the names of the speakers. \n"
content += "- The content of the podcast is Einstein's Laws of Gravity. \n"
content += "- The podcast should be interactive but informative of the topic."
content += "- The podcast should cover extensively the content of the mentioned topic. \n"

# Create chat completion for the prompt
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": content,
        }
    ],
    model="llama3-8b-8192",
)


print(chat_completion.choices[0].message.content)