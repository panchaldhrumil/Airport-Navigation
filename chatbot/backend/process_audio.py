import whisper
import warnings
import gc
import torch
from langsmith import traceable

# Load once at module level
_whisper_model = whisper.load_model("base", device="cpu")

@traceable(name="Audio to Text")
def addToChunk(audio_path: str, language: str = None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # suppress CPU/FP16 warnings
        
        result = _whisper_model.transcribe(
            audio=audio_path,
            task="translate",
            language=language
        )

    # ✅ Free memory after transcription so Ollama has room
    gc.collect()
    torch.cuda.empty_cache()

    return {
        "source": audio_path,
        "text": result["text"].strip(),
        "detected_language": result["language"]  # ✅ "hi", "en", "gu" etc.
    }