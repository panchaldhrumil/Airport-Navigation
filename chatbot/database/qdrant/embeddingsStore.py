from qdrant_client.http.models import VectorParams, Distance
from langchain_core.documents import Document
from database.qdrant.vectorStore import create_vector_store, client


def create_collection_if_not_exists(collection_name):
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )


def store_airport_data(data):
    docs = []

    for item in data:
        docs.append(
            Document(
                page_content=item["text"],
                metadata=item["metadata"]
            )
        )

    create_collection_if_not_exists("airport_data")

    vectorstore = create_vector_store("airport_data")
    vectorstore.add_documents(docs)

    return vectorstore