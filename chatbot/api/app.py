from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest
from chatbot import graph
from backend.status import redis_client

app = FastAPI()


def ai_stream(query: str, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = {
        "query": query
    }

    for message, metadata in graph.stream(
        state,
        config=config,
        stream_mode="messages"
    ):
        if message.__class__.__name__ == "AIMessageChunk":
            if message.content:
                yield message.content + " "


@app.post("/chat")
def chat(req: ChatRequest):
    return StreamingResponse(
        ai_stream(req.query, req.thread_id),
        media_type="text/plain"
    )


# Single clean status endpoint
@app.get("/status/{thread_id}")
def get_status(thread_id: str):
    try:
        status = redis_client.get(thread_id)

        if not status:
            raise HTTPException(
                status_code=404,
                detail="invalid_thread_id"
            )

        return {"status": status}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"redis_error: {str(e)}"
        )