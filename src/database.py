try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # falls back to system sqlite3 locally, e.g. on Windows where this isn't needed

import os
import json
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = "./chroma_db"
COLLECTION_NAME = "sports_history"


def get_chroma_client():
    """Initializes and returns a persistent ChromaDB client saving to disk."""
    return chromadb.PersistentClient(path=DB_PATH)


def get_embedding_function():
    """Returns ChromaDB's default local embedding function (sentence-transformers)."""
    return embedding_functions.DefaultEmbeddingFunction()


def setup_and_populate_db(json_file_path="./data/sports_facts.json"):
    """
    Reads the offline JSON facts, creates a collection, and populates it.
    Safe to call every app startup — skips re-inserting if already populated.
    """
    client = get_chroma_client()
    embedding_fn = get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )

    if collection.count() > 0:
        print(f"[INFO] Database already populated with {collection.count()} facts.")
        return collection

    if not os.path.exists(json_file_path):
        print(f"[ERROR] Raw fact data file not found at {json_file_path}")
        return collection

    with open(json_file_path, "r") as f:
        facts_list = json.load(f)

    documents = []
    metadata_list = []
    ids = []

    for idx, item in enumerate(facts_list):
        documents.append(item["fact"])
        metadata_list.append({"sport": item["sport"]})
        ids.append(f"fact_{idx}")

    collection.add(
        documents=documents,
        metadatas=metadata_list,
        ids=ids
    )
    print(f"[INFO] Successfully vectorized and stored {len(documents)} facts.")
    return collection


def query_historic_facts(sport, query_text, n_results=3):
    """
    Queries ChromaDB for historic documents relating to a sport.
    Filters results to only match the selected sport category.
    """
    client = get_chroma_client()
    embedding_fn = get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where={"sport": sport}
    )

    return results.get("documents", [[]])[0]