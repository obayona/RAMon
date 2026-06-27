import os
import csv
import time
from dotenv import load_dotenv

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "ramon-products"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50
CSV_FILE = "products_processed.csv"

openai_client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating index '{PINECONE_INDEX_NAME}'...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)
    print("Index ready.")
else:
    print(f"Index '{PINECONE_INDEX_NAME}' already exists.")

index = pc.Index(PINECONE_INDEX_NAME)

def build_text(row):
    return (
        f"name: {row['name']}\n"
        f"description: {row['description']}\n"
        f"categories: {row['categories']}\n"
        f"sku: {row['sku']}\n"
        f"reviews: {row['reviews']}"
    )

def get_embeddings(texts):
    resp = openai_client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in resp.data]

print("Reading CSV...")
with open(CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=",")
    products = list(reader)

print(f"Loaded {len(products)} products.")

vectors = []
for i, row in enumerate(products):
    text = build_text(row)
    prod_id = row["id"].strip()
    metadata = {
        "name": row["name"],
        "description": row["description"],
        "categories": row["categories"],
        "sku": row["sku"],
        "url": row.get("url", ""),
        "rating": row.get("rating", ""),
    }
    vectors.append((prod_id, text, metadata))

    if len(vectors) >= BATCH_SIZE or i == len(products) - 1:
        batch_texts = [v[1] for v in vectors]
        batch_ids_and_meta = [(v[0], v[2]) for v in vectors]

        print(f"Embedding batch of {len(batch_texts)} products (product {i + 1 - len(batch_texts) + 1} to {i + 1})...")
        embeddings = get_embeddings(batch_texts)

        pinecone_vectors = [
            (pid, emb, meta)
            for (pid, meta), emb in zip(batch_ids_and_meta, embeddings)
        ]

        print("Upserting to Pinecone...")
        index.upsert(vectors=pinecone_vectors)

        vectors = []

print("Done!")
