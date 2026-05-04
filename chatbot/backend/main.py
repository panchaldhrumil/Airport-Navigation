from langsmith import traceable
from chatbot.database.qdrant.embeddingsStore import store_airport_data
import json
from chatbot.database.qdrant.retrieveEmbeddings import retrieve_embed
from dotenv import load_dotenv
from chatbot.backend.process_audio import addToChunk

load_dotenv()


# =========================
# AIRPORT DATA INGESTION
# =========================
@traceable(name="Airport Data Ingestion")
def ingest_airport_data(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Loaded {len(data)} entries")
    store_airport_data(data)
    print("✅ Airport data successfully stored in Qdrant")


# =========================
# AUDIO TRANSCRIPTION
# =========================
def transcribe_audio(audio_path: str) -> dict:  # ✅ return type changed to dict
    """
    Takes an audio file path, transcribes + translates to English via Whisper,
    and returns both the transcribed text and the detected original language.
    """
    print(f"🎙️ Transcribing: {audio_path}")
    result = addToChunk(audio_path)

    transcribed_text = result["text"]
    detected_language = result["detected_language"]  # ✅ extract language

    print(f"📝 Transcribed text: {transcribed_text}")
    print(f"🌐 Detected language: {detected_language}")

    return {
        "text": transcribed_text,
        "language": detected_language  # ✅ return to caller
    }


# =========================
# RAG PIPELINE
# =========================
def pipeline(query: str) -> list:
    """
    Takes a plain text query,
    retrieves relevant docs from Qdrant,
    and returns them.
    """
    return retrieve_embed(query)


# =========================
# MAIN ENTRY (for testing)
# =========================
def main(isaudio: bool, audio_path: str = None, query: str = None):
    """
    isaudio=True  → transcribe audio file → run pipeline
    isaudio=False → use query directly   → run pipeline
    """
    if isaudio:
        if not audio_path:
            raise ValueError("❌ audio_path must be provided when isaudio=True")
        final_query = transcribe_audio(audio_path)
    else:
        if not query:
            raise ValueError("❌ query must be provided when isaudio=False")
        final_query = query

    print(f"🔍 Running pipeline for: {final_query}")
    pipeline_result = pipeline(final_query)
    return pipeline_result


# =========================
# TEST BLOCK
# =========================
if __name__ == "__main__":
    # ✅ Test with audio
    audio_path = r"F:\Projects\AI Airport\chatbot\backend\WhatsApp Ptt 2026-05-04 at 12.05.17 AM.ogg"
    print("=== Audio Test ===")
    print(main(isaudio=True, audio_path=audio_path))

    # ✅ Test with text
    print("\n=== Text Test ===")
    print(main(isaudio=False, query="Where is McDonald's?"))