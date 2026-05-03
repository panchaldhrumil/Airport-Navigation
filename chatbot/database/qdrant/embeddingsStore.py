from qdrant_client.http.models import VectorParams, Distance
from langchain_core.documents import Document
from chatbot.database.qdrant.vectorStore import create_vector_store, client


def create_collection(collection_name):
    # Always recreate for clean state (hackathon safe)
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )


def store_airport_data(data):
    docs = []

    for i, item in enumerate(data):
        metadata = item["metadata"]

        # Ensure ID exists
        metadata["id"] = metadata.get("id", f"doc_{i}")

        docs.append(
            Document(
                page_content=item["text"],
                metadata=metadata
            )
        )

    print(f"📦 Preparing {len(docs)} documents...")

    create_collection("airport_data")

    vectorstore = create_vector_store("airport_data")
    vectorstore.add_documents(docs)

    print("✅ Data successfully stored in Qdrant!")

    return vectorstore