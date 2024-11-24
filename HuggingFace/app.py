from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import PyPDF2
import sqlite3
import os
from datetime import datetime
import requests
from typing import List
from openai import OpenAI  # Import OpenAI for Nebius integration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# app.config["SECRET_KEY"] = "your-flask-secret-key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {"pdf"}

# API Keys
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")

# API URLs
HUGGINGFACE_API_URL = (
    "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.1-70B-Instruct"
)
NEBIUS_API_URL = "https://api.studio.nebius.ai/v1/"

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize Nebius client
nebius_client = OpenAI(
    base_url=NEBIUS_API_URL,
    api_key=NEBIUS_API_KEY,
)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
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
    chunks, current_chunk, current_length = [], [], 0

    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_length = [word], word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_with_nebius(text: str) -> str:
    """Summarize text using Nebius AI Studio."""
    chunks = chunk_text(text)
    summaries = []

    for chunk in chunks:
        prompt = f"Summarize the following text: {chunk}"
        completion = nebius_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        summaries.append(completion["choices"][0]["message"]["content"])

    return " ".join(summaries)


@app.route("/")
def index():
    conn = sqlite3.connect("pdf_summaries.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, filename, summary, upload_date FROM documents ORDER BY upload_date DESC"
    )
    documents = c.fetchall()
    conn.close()
    return render_template("index.html", documents=documents)


@app.route("/upload", methods=["POST"])
def upload_file():
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
                summary = summarize_with_nebius(text)
            except Exception as e:
                flash(f"Error during summarization: {str(e)}")
                os.remove(file_path)
                return redirect(url_for("index"))

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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
