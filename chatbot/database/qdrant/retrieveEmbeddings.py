from langsmith import traceable
from chatbot.database.qdrant.vectorStore import create_vector_store


@traceable(name="Retrieve Airport Data")
def retrieve_embed(query: str, filters: dict = None):
    vectorstore = create_vector_store("airport_data")

    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": filters or {}
        }
    )

    return retriever.invoke(query)