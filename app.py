import os
import uuid
import asyncio
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import edge_tts

app = Flask(__name__)
CORS(app)  # allow requests from your WordPress site

AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# A curated list of good multi-language voices (you can expand this)
VOICE_LIST = [
    {"id": "en-US-AriaNeural", "label": "English (US) - Aria - Female"},
    {"id": "en-US-GuyNeural", "label": "English (US) - Guy - Male"},
    {"id": "en-GB-SoniaNeural", "label": "English (UK) - Sonia - Female"},
    {"id": "en-GB-RyanNeural", "label": "English (UK) - Ryan - Male"},
    {"id": "ur-PK-UzmaNeural", "label": "Urdu (Pakistan) - Uzma - Female"},
    {"id": "ur-PK-AsadNeural", "label": "Urdu (Pakistan) - Asad - Male"},
    {"id": "ur-IN-GulNeural", "label": "Urdu (India) - Gul - Female"},
    {"id": "hi-IN-SwaraNeural", "label": "Hindi (India) - Swara - Female"},
    {"id": "hi-IN-MadhurNeural", "label": "Hindi (India) - Madhur - Male"},
    {"id": "ar-SA-ZariyahNeural", "label": "Arabic (Saudi) - Zariyah - Female"},
    {"id": "ar-SA-HamedNeural", "label": "Arabic (Saudi) - Hamed - Male"},
    {"id": "fr-FR-DeniseNeural", "label": "French - Denise - Female"},
    {"id": "es-ES-ElviraNeural", "label": "Spanish - Elvira - Female"},
    {"id": "de-DE-KatjaNeural", "label": "German - Katja - Female"},
]


@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify(VOICE_LIST)


@app.route("/api/generate", methods=["POST"])
def generate_audio():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    voice = data.get("voice") or "en-US-AriaNeural"
    rate = data.get("rate", "+0%")     # e.g. "+20%" or "-10%"
    pitch = data.get("pitch", "+0Hz")  # e.g. "+5Hz" or "-5Hz"

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text too long (max 5000 characters)"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    async def synthesize():
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)

    try:
        asyncio.run(synthesize())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"audio_url": f"/api/audio/{filename}"})


@app.route("/api/audio/<filename>", methods=["GET"])
def get_audio(filename):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Voice Generator API is running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
