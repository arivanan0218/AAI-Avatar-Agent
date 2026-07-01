"""One-time script to load all domain knowledge into Pinecone."""
from dotenv import load_dotenv
load_dotenv()

import os
from pinecone import Pinecone

# Delete the old index if it exists with wrong dimensions
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
existing = {idx.name for idx in pc.list_indexes()}
if "interview-knowledge" in existing:
    print("Deleting existing index (may have wrong dimensions)...")
    pc.delete_index("interview-knowledge")
    print("Deleted.")

from rag.knowledge_base import KnowledgeBase

kb = KnowledgeBase()
for domain in ['software_engineering', 'healthcare', 'finance']:
    n = kb.load_domain(domain)
    print(f"Loaded {n} vectors for {domain}")

print("Done.")
