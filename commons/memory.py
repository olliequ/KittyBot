import chromadb

chroma_client = chromadb.PersistentClient(path="./memory.chroma")
memory = chroma_client.get_or_create_collection(name="memory")
