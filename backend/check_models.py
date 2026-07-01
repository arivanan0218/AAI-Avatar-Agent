"""Diagnostic: verify the OpenAI API key and test embedding."""
from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
print(f"API key loaded: {'YES' if api_key else 'NO — check backend/.env'}")
if not api_key:
    raise SystemExit(1)
print(f"API key prefix: {api_key[:8]}...")
print()

client = OpenAI(api_key=api_key)

# List a few available models
print("=== Sample of available models ===")
try:
    for m in list(client.models.list())[:10]:
        print(f"  {m.id}")
except Exception as e:
    print(f"  Could not list models: {e}")
print()

# Try each candidate embedding model
candidates = ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]
for model in candidates:
    try:
        result = client.embeddings.create(model=model, input="hello world")
        dim = len(result.data[0].embedding)
        print(f"SUCCESS with model='{model}', dim={dim}")
        break
    except Exception as e:
        print(f"FAIL    with model='{model}': {e}")
