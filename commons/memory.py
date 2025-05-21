import chromadb
import os

chroma_client = chromadb.PersistentClient(path=os.getenv("KITTY_MEMORY_DB", "/data/memory.chroma"))
memory = chroma_client.get_or_create_collection(name="memory")
