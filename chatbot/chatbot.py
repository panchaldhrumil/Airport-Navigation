from dotenv import load_dotenv
import json
import os
import traceback
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from chatbot.prompts import CLASSIFIER_PROMPT, general_prompt, AIRPORT_SYSTEM_PROMPT
from chatbot.backend.transformer import translate_to_english, translate_to_hindi, detect_language
from chatbot.database.qdrant.retrieveEmbeddings import retrieve_embed
from langsmith import traceable
from chatbot.backend.main import pipeline, transcribe_audio

load_dotenv()

print("Tracing:", os.getenv("LANGSMITH_TRACING"))
print("API Key Exists:", os.getenv("LANGSMITH_API_KEY") is not None)

# =========================
# LLM
# =========================
llm = ChatOllama(model="llama3.2", temperature=0)


# =========================
# STATE
# =========================
class AgentState(TypedDict):
    query: str
    intent: Optional[str]
    language: Optional[str]
    confidence: Optional[float]
    translated_query: Optional[str]
    response: Optional[str]
    audio_path: Optional[str]


# =========================
# AUDIO TRANSCRIPTION NODE
# =========================
@traceable(name="Audio Transcription")
def audio_node(state):
    """
    If audio_path is present in state, transcribe it
    and inject transcribed text into state["query"].
    """
    audio_path = state.get("audio_path")

    if not audio_path:
        return state

    print(f"🎙️ Transcribing audio: {audio_path}")

    try:
        transcribed_text = transcribe_audio(audio_path)
    except Exception as e:
        print(f"❌ transcribe_audio FAILED: {e}")
        traceback.print_exc()
        raise

    print(f"📝 Transcribed: {transcribed_text}")

    return {
        **state,
        "query": transcribed_text,
        "audio_path": None
    }


# =========================
# CLASSIFIER NODE
# =========================
@traceable(name="Intent and Language Classification")
def classifier_node(state):
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CLASSIFIER_PROMPT),
            ("human", "{query}")
        ])

        chain = prompt | llm

        lang = detect_language(state["query"])
        detected_lang = "hi" if lang == "hindi" else "en"

        query_for_classification = (
            translate_to_english(state["query"]) if lang == "hindi" else state["query"]
        )

        response = chain.invoke({"query": query_for_classification})

        try:
            result = json.loads(response.content)
        except Exception as parse_err:
            print(f"⚠️ JSON parse failed in classifier: {parse_err}")
            result = {
                "intent": "general",
                "language": detected_lang,
                "confidence": 0.5
            }

        return {
            **state,
            "intent": result.get("intent"),
            "language": detected_lang,
            "confidence": result.get("confidence"),
            "translated_query": query_for_classification
        }

    except Exception as e:
        print(f"❌ classifier_node FAILED: {e}")
        traceback.print_exc()
        raise


# =========================
# TRANSLATE NODE
# =========================
@traceable(name="Translation to English")
def translate_node(state):
    try:
        if state.get("translated_query"):
            return state

        translated = translate_to_english(state["query"])
        return {
            **state,
            "translated_query": translated
        }

    except Exception as e:
        print(f"❌ translate_node FAILED: {e}")
        traceback.print_exc()
        raise


# =========================
# ROUTERS
# =========================
def audio_router(state):
    if state.get("audio_path"):
        return "audio_node"
    return "classifier"


def intent_router(state):
    intent = state.get("intent")
    confidence = state.get("confidence", 0)

    if confidence < 0.6:
        return "general_handler"

    if intent == "airport":
        return "airport_handler"

    return "general_handler"


def classifier_router(state):
    if state["language"] != "en" and state["confidence"] > 0.7:
        return "translate"
    return intent_router(state)


# =========================
# HANDLERS
# =========================
@traceable(name="General Query Handler")
def general_handler(state):
    try:
        query = state.get("translated_query") or state["query"]
        chain = general_prompt | llm
        response = chain.invoke({"query": query})
        return {
            **state,
            "response": response.content
        }

    except Exception as e:
        print(f"❌ general_handler FAILED: {e}")
        traceback.print_exc()
        raise


@traceable(name="Airport Query Handler")
def airport_pipeline_node(state):
    try:
        user_lang = state.get("language", "en")
        translated_query = state.get("translated_query") or state["query"]

        # RAG Retrieval
        docs = pipeline(translated_query)

        # LLM Response
        response = llm.invoke([
            {"role": "system", "content": AIRPORT_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
User query: {translated_query}
Retrieved docs: {docs}

Explain the best option clearly to the user.
"""}
        ])

        english_response = response.content

        if user_lang == "hi":
            final_response = translate_to_hindi(english_response)
        else:
            final_response = english_response

        return {
            **state,
            "translated_query": translated_query,
            "response": final_response
        }

    except Exception as e:
        print(f"❌ airport_pipeline_node FAILED: {e}")
        traceback.print_exc()
        raise


# =========================
# GRAPH
# =========================
builder = StateGraph(AgentState)

# =========================
# NODES
# =========================
builder.add_node("audio_node", audio_node)
builder.add_node("classifier", classifier_node)
builder.add_node("translate", translate_node)
builder.add_node("airport_handler", airport_pipeline_node)
builder.add_node("general_handler", general_handler)

# =========================
# ENTRY POINT
# =========================
builder.set_entry_point("entry")
builder.add_node("entry", lambda state: state)

builder.add_conditional_edges(
    "entry",
    audio_router,
    {
        "audio_node": "audio_node",
        "classifier": "classifier"
    }
)

builder.add_edge("audio_node", "classifier")

builder.add_conditional_edges(
    "classifier",
    classifier_router,
    {
        "translate": "translate",
        "airport_handler": "airport_handler",
        "general_handler": "general_handler"
    }
)

builder.add_conditional_edges(
    "translate",
    intent_router,
    {
        "airport_handler": "airport_handler",
        "general_handler": "general_handler"
    }
)

builder.add_edge("airport_handler", END)
builder.add_edge("general_handler", END)

# =========================
# COMPILE
# =========================
graph = builder.compile()


# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    AUDIO_PATH = r"F:\Projects\AI Airport\chatbot\backend\WhatsApp Ptt 2026-05-04 at 12.05.17 AM.ogg"

    # ✅ Isolated transcription test BEFORE starting the graph loop
    print("🧪 Testing transcribe_audio directly...")
    try:
        test_result = transcribe_audio(AUDIO_PATH)
        print(f"✅ Transcription test passed: {test_result}")
    except Exception as e:
        print(f"❌ Transcription test FAILED: {e}")
        traceback.print_exc()
        print("⚠️  Fix transcribe_audio before continuing. Exiting.")
        exit(1)

    print("\n🚀 Chatbot started (type 'exit' to quit)")
    print("💡 Type your message OR press Enter on empty line to use audio\n")

    while True:
        user_input = input("👤 You (text or press Enter for audio): ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Exiting chatbot...")
            break

        if not user_input:
            if not os.path.exists(AUDIO_PATH):
                print(f"❌ Audio file not found at: {AUDIO_PATH}")
                continue

            print(f"📁 Using audio: {AUDIO_PATH}")
            state = {
                "query": "",
                "intent": None,
                "language": None,
                "confidence": None,
                "translated_query": None,
                "response": None,
                "audio_path": AUDIO_PATH
            }

        else:
            state = {
                "query": user_input,
                "intent": None,
                "language": None,
                "confidence": None,
                "translated_query": None,
                "response": None,
                "audio_path": None
            }

        try:
            result = graph.invoke(state)
            print("\n🤖 Bot:", result["response"])
        except Exception as e:
            print(f"\n❌ Graph invocation FAILED: {e}")
            traceback.print_exc()

        print("-" * 50)