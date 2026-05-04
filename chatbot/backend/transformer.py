import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from dotenv import load_dotenv
import os
import re

# =========================
# LOAD ENV
# =========================
load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

if not HF_TOKEN:
    raise ValueError("❌ HUGGINGFACE_API_KEY not found in .env")

print("✅ Token loaded:", HF_TOKEN[:10], "...")

# =========================
# DEVICE
# ✅ Force CPU for ALL translation models
# so they don't compete with Ollama for VRAM
# =========================
DEVICE = "cpu"
print("🚀 Translation models using device: CPU")

# =========================
# MODEL NAMES
# =========================
EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"  # English → Hindi
INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"  # Hindi → English

# =========================
# LOAD EN → INDIC
# =========================
print("⏳ Loading EN→Indic tokenizer...")
en_indic_tokenizer = AutoTokenizer.from_pretrained(
    EN_INDIC_MODEL, trust_remote_code=True, token=HF_TOKEN
)
print("⏳ Loading EN→Indic model...")
en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(
    EN_INDIC_MODEL, trust_remote_code=True, token=HF_TOKEN
).to(DEVICE)  # ✅ CPU
print("✅ EN→Indic model loaded!")

# =========================
# LOAD INDIC → EN
# =========================
print("⏳ Loading Indic→EN tokenizer...")
indic_en_tokenizer = AutoTokenizer.from_pretrained(
    INDIC_EN_MODEL, trust_remote_code=True, token=HF_TOKEN
)
print("⏳ Loading Indic→EN model...")
indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(
    INDIC_EN_MODEL, trust_remote_code=True, token=HF_TOKEN
).to(DEVICE)  # ✅ CPU
print("✅ Indic→EN model loaded!\n")


# =========================
# LANGUAGE DETECTION
# =========================
def detect_language(text: str) -> str:
    """
    Returns:
      'hindi'   — Devanagari script
      'english' — English or anything else (including Hinglish)
    """
    if not text or not isinstance(text, str):
        return "english"

    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_chars = len(text.replace(" ", ""))

    if total_chars == 0:
        return "english"

    devanagari_ratio = devanagari_chars / total_chars

    if devanagari_ratio > 0.3:
        return "hindi"

    return "english"


# =========================
# TRANSLATE FUNCTIONS
# =========================
def translate_to_english(text: str) -> str:
    """Hindi (Devanagari) → English. Returns as-is if already English/Hinglish."""
    if not text or not isinstance(text, str):
        return text

    if detect_language(text) == "english":
        return text  # Already English or Hinglish — return as-is

    input_text = f"hin_Deva eng_Latn {text}"

    # ✅ inputs go to same device as model (CPU)
    inputs = indic_en_tokenizer(input_text, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = indic_en_model.generate(**inputs, max_length=256)

    return indic_en_tokenizer.decode(outputs[0], skip_special_tokens=True)


def translate_to_hindi(text: str) -> str:
    """English → Hindi (Devanagari)"""
    if not text or not isinstance(text, str):
        return text

    input_text = f"eng_Latn hin_Deva {text}"

    # ✅ inputs go to same device as model (CPU)
    inputs = en_indic_tokenizer(input_text, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = en_indic_model.generate(**inputs, max_length=256)

    return en_indic_tokenizer.decode(outputs[0], skip_special_tokens=True)


# =========================
# TEST BLOCK
# =========================
if __name__ == "__main__":

    print("=" * 50)
    print("🧪 RUNNING TRANSFORMER TESTS")
    print("=" * 50)

    hindi_inputs = [
        "मुझे गेट A2 जाना है",
        "Gate A2 kaha hai?",     # Hinglish — returned as-is
        "मुझे खाना चाहिए",
        "Coffee shop kaha hai?",  # Hinglish — returned as-is
        "",
        "12345",
        None,
    ]

    english_inputs = [
        "Where is Gate A2?",
        "I need food.",
        "Where is the coffee shop?",
    ]

    print("\n--- Hindi → English ---")
    for i, text in enumerate(hindi_inputs, 1):
        print(f"\nTest {i} | INPUT  : {text}")
        print(f"         | LANG   : {detect_language(text) if text and isinstance(text, str) else 'N/A'}")
        try:
            print(f"         | OUTPUT : {translate_to_english(text)}")
        except Exception as e:
            print(f"         | ERROR  : {e}")

    print("\n--- English → Hindi ---")
    for i, text in enumerate(english_inputs, 1):
        print(f"\nTest {i} | INPUT  : {text}")
        try:
            print(f"         | OUTPUT : {translate_to_hindi(text)}")
        except Exception as e:
            print(f"         | ERROR  : {e}")