import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai

from chatbot_config import CHATBOT_TITLE, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


@app.get("/")
def index():
    return render_template("index.html", chatbot_title=CHATBOT_TITLE)


@app.post("/chat")
def chat():
    if client is None:
        return jsonify({"error": "Gemini API key is not configured."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a question."}), 400

    contents = []

    if isinstance(history, list):
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            text = str(item.get("text", "")).strip()

            if role in {"user", "model"} and text:
                contents.append({
                    "role": role,
                    "parts": [{"text": text}],
                })

    contents.append({
        "role": "user",
        "parts": [{"text": message}],
    })

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.25,
                "max_output_tokens": 1400,
            },
        )

        answer = (response.text or "").strip()

        if not answer:
            return jsonify({"error": "The model returned an empty response."}), 502

        return jsonify({"answer": answer})

    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "Unable to generate a response right now. Please try again."
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
