from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import traceback

from .schemas import TextChatRequest, ChatResponse, AudioChatResponse
from chatbot.chatbot import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # allow all origins during development
    allow_credentials=False,       # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)



# =========================
# TEXT ENDPOINT
# =========================
@app.post("/chat/text", response_model=ChatResponse)
def chat_text(req: TextChatRequest):
    try:
        state = {
            "query": req.query,
            "intent": None,
            "language": None,
            "confidence": None,
            "translated_query": None,
            "response": None,
            "audio_path": None
        }

        result = graph.invoke(state)

        return ChatResponse(
            session_id=req.session_id,
            response=result["response"],
            intent=result.get("intent"),
            language=result.get("language")
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# AUDIO ENDPOINT
# =========================
@app.post("/chat/audio", response_model=AudioChatResponse)
async def chat_audio(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    tmp_path = None
    try:
        # ✅ Save uploaded audio to a temp file
        suffix = os.path.splitext(file.filename)[-1] or ".ogg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        state = {
            "query": "",
            "intent": None,
            "language": None,
            "confidence": None,
            "translated_query": None,
            "response": None,
            "audio_path": tmp_path   # ✅ graph handles transcription internally
        }

        result = graph.invoke(state)

        return AudioChatResponse(
            session_id=session_id,
            response=result["response"],
            intent=result.get("intent"),
            language=result.get("language"),
            transcribed_text=result.get("translated_query")  # English text from Whisper
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # ✅ Always clean up temp audio file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}