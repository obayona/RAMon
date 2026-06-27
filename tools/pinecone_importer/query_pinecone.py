import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("ramon-products")

query = "IP Camara"
resp = openai_client.embeddings.create(input=query, model="text-embedding-3-small")
embedding = resp.data[0].embedding

results = index.query(vector=embedding, top_k=3, include_metadata=True)

for i, match in enumerate(results.matches, 1):
    print(f"\n--- Result {i} (score: {match.score:.4f}) ---")
    for k, v in match.metadata.items():
        print(f"{k}: {v[:200] if isinstance(v, str) else v}")
