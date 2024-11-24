from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import PyPDF2
import sqlite3
import os
from datetime import datetime
import requests
from typing import List
from dotenv import load_dotenv  # Added for better env variable handling
from flask import send_from_directory
import subprocess

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "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"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {"pdf"}

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Print API key status for debugging (remove in production)
print(f"API Key status: {'Configured' if GROQ_API_KEY else 'Not configured'}")
print(f"API Key value (first 5 chars): {GROQ_API_KEY[:5] if GROQ_API_KEY else 'None'}")

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
     # Delete the existing database file to reset the documents
    if os.path.exists("pdf_summaries.db"):
        os.remove("pdf_summaries.db")

    conn = sqlite3.connect("pdf_summaries.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def chunk_text(text: str, chunk_size: int = 8000) -> List[str]:
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def verify_api_key():
    """Verify if the API key is valid by making a small test request"""
    if not GROQ_API_KEY:
        return False, "API key is not set"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    test_payload = {
        "messages": [{"role": "user", "content": "test"}],
        "model": "llama3-70b-8192",
        "max_tokens": 1,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=test_payload)
        response.raise_for_status()
        return True, "API key is valid"
    except requests.exceptions.RequestException as e:
        return False, f"API key verification failed: {str(e)}"


def summarize_with_groq(text: str) -> str:
    """Summarize text using Groq API."""
    # Verify API key before proceeding
    is_valid, message = verify_api_key()
    if not is_valid:
        raise ValueError(message)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    chunks = chunk_text(text)
    summaries = []

    for chunk in chunks:
        prompt = f"""Please provide a concise summary of the following text. Focus on the main points and key information:

{chunk}

Provide the summary in a clear, professional style."""

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional document summarizer. Provide clear, accurate, and concise summaries.",
                },
                {"role": "user", "content": prompt},
            ],
            "model": "llama3-70b-8192",
            "temperature": 0.3,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"]
            summaries.append(summary)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Groq API: {str(e)}")

    if len(summaries) > 1:
        combined_summary = "\n\n".join(summaries)

        if len(combined_summary) > 4000:
            final_summary_prompt = f"""Please provide a unified summary of these related text segments:

{combined_summary}

Create a coherent, flowing summary that captures the main points from all segments."""

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional document summarizer. Provide clear, accurate, and concise summaries.",
                    },
                    {"role": "user", "content": final_summary_prompt},
                ],
                "model": "llama3-70b-8192",
                "temperature": 0.3,
                "max_tokens": 1000,
            }

            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        return combined_summary

    return summaries[0]

def extract_topic(text: str) -> str:
    """Extracts the topic of the text. Defaults to the first sentence."""
    try:
        # Assuming the topic is the first line or sentence
        lines = text.splitlines()
        topic = lines[0] if lines else "Unknown Topic"
        return topic.strip()
    except Exception as e:
        print(f"Error extracting topic: {str(e)}")
        return "Unknown Topic"
    
def generate_podcast_for_uploaded_document(filename):
    """Trigger the podcast generation after document is processed."""
    conn = sqlite3.connect("pdf_summaries.db")
    c = conn.cursor()
    c.execute("SELECT id, summary FROM documents WHERE filename = ?", (filename,))
    document = c.fetchone()
    conn.close()

    if document:
        summary = document[1]

        try:
            # Run the external script to generate the podcast with the document summary
            result = subprocess.run(
                ["python3", "backend/generatePodcast_v2.0.py", summary],
                text=True,
                capture_output=True,
                check=True
            )
            print("Podcast generation successful:", result.stdout)  # Optionally log output
        except subprocess.CalledProcessError as e:
            print(f"Error generating podcast: {e.stderr}")
            raise Exception(f"Podcast generation failed: {str(e)}")

    else:
        raise ValueError("Document not found for podcast generation.")

@app.route("/")
def index():
    # Verify API key status
    api_status, api_message = verify_api_key()

    conn = sqlite3.connect("pdf_summaries.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, filename, summary, upload_date FROM documents ORDER BY upload_date DESC"
    )
    documents = c.fetchall()
    conn.close()

    return render_template(
        "index.html",
        documents=documents,
        api_status=api_status,
        api_message=api_message,
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    # Verify API key first
    api_status, api_message = verify_api_key()
    if not api_status:
        flash(f"API Configuration Error: {api_message}")
        return redirect(url_for("index"))

    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            text = extract_text_from_pdf(file_path)

            try:
                summary = summarize_with_groq(text)
            except Exception as e:
                flash(f"Error during summarization: {str(e)}")
                os.remove(file_path)
                return redirect(url_for("index"))

            # Insert data into the database, including the topic
            conn = sqlite3.connect("pdf_summaries.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO documents (filename, original_text, summary)
                VALUES (?, ?, ?)
                """,
                (filename, text, summary),
            )
            conn.commit()
            conn.close()

            os.remove(file_path)

            flash("File successfully processed and summarized")

            # Call the function to generate podcast after the upload and processing
            try:
                # Now call the generate_podcast function or the subprocess
                generate_podcast_for_uploaded_document(filename)
            except Exception as e:
                flash(f"Error generating podcast: {str(e)}")

        except Exception as e:
            flash(f"Error processing file: {str(e)}")
    else:
        flash("Allowed file type is PDF")

    return redirect(url_for("index"))


@app.route("/document/<int:id>")
def view_document(id):
    conn = sqlite3.connect("pdf_summaries.db")
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id = ?", (id,))
    document = c.fetchone()
    conn.close()

    if document is None:
        flash("Document not found")
        return redirect(url_for("index"))
    return render_template("document.html", document=document)


@app.route('/audio/final_podcast')
def serve_audio():
    return send_from_directory('backend/audio', 'final_podcast.mp3')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
