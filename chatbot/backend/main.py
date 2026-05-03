from langsmith import traceable
from database.qdrant.embeddingsStore import store_airport_data
import json
from database.qdrant.retrieveEmbeddings import retrieve_embed
from dotenv import load_dotenv


@traceable(name="Airport Data Ingestion")
def ingest_airport_data(file_path: str):
    """
    Load airport dataset (JSON) and store in Qdrant
    """

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} entries")

    store_airport_data(data)

    print("Airport data successfully stored in Qdrant")


def pipeline(query : str):

    return retrieve_embed(query)

if __name__ == "__main__":
    ingest_airport_data("airport_data.json")