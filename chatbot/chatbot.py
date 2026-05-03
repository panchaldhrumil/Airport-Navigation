from dotenv import load_dotenv
import json
import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama  # ✅ fixed deprecation
from langchain_core.prompts import ChatPromptTemplate
from chatbot.prompts import CLASSIFIER_PROMPT, general_prompt, AIRPORT_SYSTEM_PROMPT
from chatbot.backend.transformer import translate_to_english, translate_to_hindi
from chatbot.database.qdrant.retrieveEmbeddings import retrieve_embed
from langsmith import traceable

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
    response: Optional[str]  # ✅ plain string, not add_messages


# =========================
# CLASSIFIER NODE
# =========================
@traceable(name="Intent and Language Classification")
def classifier_node(state):
    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFIER_PROMPT),
        ("human", "{query}")
    ])

    chain = prompt | llm
    response = chain.invoke({"query": state["query"]})

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "intent": "general",
            "language": "en",
            "confidence": 0.5
        }

    return {
        **state,
        "intent": result.get("intent"),
        "language": result.get("language"),
        "confidence": result.get("confidence")
    }


# =========================
# TRANSLATE NODE
# =========================
@traceable(name="Translation to English")
def translate_node(state):
    translated = translate_to_english(state["query"])
    return {
        **state,
        "translated_query": translated
    }


# =========================
# ROUTERS
# =========================
def intent_router(state):
    intent = state.get("intent")
    confidence = state.get("confidence", 0)

    if confidence < 0.6:
        return "general_handler"

    if intent == "airport":
        return "airport_handler"

    return "general_handler"


def classifier_router(state):
    """
    Single router from classifier:
    - If non-English + confident → translate first
    - Else → route by intent directly
    """
    if state["language"] != "en" and state["confidence"] > 0.7:
        return "translate"

    return intent_router(state)


# =========================
# HANDLERS
# =========================
@traceable(name="General Query Handler")
def general_handler(state):
    query = state.get("translated_query") or state["query"]
    chain = general_prompt | llm
    response = chain.invoke({"query": query})
    return {
        **state,
        "response": response.content  # ✅ plain string
    }


@traceable(name="Airport Query Handler")
def airport_pipeline_node(state):
    original_query = state["query"]
    user_lang = state.get("language", "en")

    # STEP 1: Translate if needed
    if user_lang != "en":
        translated_query = translate_to_english(original_query)
    else:
        translated_query = original_query

    # STEP 2: RAG Retrieval
    docs = retrieve_embed(translated_query)

    # STEP 3: LLM Response (English)
    response = llm.invoke([
        {"role": "system", "content": AIRPORT_SYSTEM_PROMPT},
        {"role": "user", "content": f"""
User query: {translated_query}
Retrieved docs: {docs}

Explain the best option clearly to the user.
"""}
    ])

    english_response = response.content

    # STEP 4: Translate back if needed
    if user_lang == "hi":
        final_response = translate_to_hindi(english_response)
    else:
        final_response = english_response

    return {
        **state,
        "translated_query": translated_query,
        "response": final_response  # ✅ plain string, no list wrapper
    }


# =========================
# GRAPH
# =========================
builder = StateGraph(AgentState)

# =========================
# NODES
# =========================
builder.add_node("classifier", classifier_node)
builder.add_node("translate", translate_node)
builder.add_node("airport_handler", airport_pipeline_node)
builder.add_node("general_handler", general_handler)

# =========================
# ENTRY POINT
# =========================
builder.set_entry_point("classifier")

# =========================
# ROUTING FROM CLASSIFIER
# =========================
builder.add_conditional_edges(
    "classifier",
    classifier_router,
    {
        "translate": "translate",
        "airport_handler": "airport_handler",
        "general_handler": "general_handler"
    }
)

# =========================
# ROUTING AFTER TRANSLATION
# =========================
builder.add_conditional_edges(
    "translate",
    intent_router,
    {
        "airport_handler": "airport_handler",
        "general_handler": "general_handler"
    }
)

# =========================
# TERMINAL EDGES
# =========================
builder.add_edge("airport_handler", END)
builder.add_edge("general_handler", END)

# =========================
# COMPILE GRAPH
# =========================
graph = builder.compile()


# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    print("🚀 Chatbot started (type 'exit' to quit)\n")

    while True:
        user_query = input("👤 You: ").strip()

        if not user_query:
            continue

        if user_query.lower() in ["exit", "quit"]:
            print("👋 Exiting chatbot...")
            break

        # Initial state
        state = {
            "query": user_query,
            "intent": None,
            "language": None,
            "confidence": None,
            "translated_query": None,
            "response": None  # ✅ None is valid for Optional[str]
        }

        try:
            result = graph.invoke(state)
            print("\n🤖 Bot:", result["response"])
        except Exception as e:
            print(f"\n❌ Error: {e}")

        print("-" * 50)