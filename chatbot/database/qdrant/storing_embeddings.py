import os
import json
from chatbot.database.qdrant.embeddingsStore import store_airport_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "airport_rag_dataset.json")

with open(file_path, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

store_airport_data(data)