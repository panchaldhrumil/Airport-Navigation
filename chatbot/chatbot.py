from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage
import psycopg2
from dotenv import load_dotenv
import os 
from langsmith import traceable
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, StateGraph, END
from typing import TypedDict, Optional
from .prompts import CLASSIFIER_PROMPT
from .database.postgres.db import get_db_connection
from .database.postgres.checkpointer import get_checkpointer
import json
from langchain_ollama import ChatOllama
from chatbot.backend.transformer import translate
from langchain_core.prompts import ChatPromptTemplate
from .prompts import general_prompt





load_dotenv()

#LLM
llm = ChatOllama(model="llama3.2", temperature=0)



class AgentState(TypedDict):
    query: str
    intent: Optional[str]
    language: Optional[str]
    confidence: Optional[float]
    translated_query: Optional[str]
    response: Optional[str]


def classifier_node(state):
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content="{query}")
        ]
    )

    formatted_prompt = prompt.format_prompt(query=state["query"]).to_messages()

    response = llm(formatted_prompt)

    # Parse the response and update the state
    result = json.loads(response.content)

    return {
        **state,
        "language": result.get("language"),
        "confidence": result.get("confidence")
    }

def translate_node(state):
    translated = translate(state["query"])
    return {
        **state,
        "translated_query": translated
    }


def language_router(state):
    if state["language"] == "en" and state["confidence"] > 0.7:
        return "intent_router"
    elif state["language"] == "hi" and state["confidence"] > 0.7:
        return "translate"
    else:
        return "intent_router"


def intent_router(state):
    intent = state.get("intent")
    confidence = state.get("confidence", 0)

    # fallback safety
    if confidence < 0.6:
        return "general_handler"

    if intent == "airport":
        return "airport_handler"
    
    return "general_handler"

def general_handler(state):
    query = state.get("translated_query") or state["query"]

    chain = general_prompt | llm

    response = chain.invoke({"query": query})

    return {
        **state,
        "response": response.content
    }

def translate_node(state):
    # Use a translation API or model to translate the query to English
    translated = translate(state["query"])
    return {
        **state,
        "translated_query": translated
    }

builder = StateGraph(AgentState)

builder.add_node("classifier", classifier_node)
builder.add_node("intent_router", intent_router)
builder.add_node("translate", translate_node)
builder.add_node("airport_handler", airport_handler)
builder.add_node("general_handler", general_handler)

builder.set_entry_point("classifier")

builder.add_conditional_edges(
    "classifier",
    language_router,
    {
        "translate": "translate",
        "intent_router": "intent_router"
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

builder.add_conditional_edges(
    "classifier",
    intent_router,
    {
        "airport_handler": "airport_handler",
        "general_handler": "general_handler"
    }
)

graph = builder.compile()