#!/usr/bin/env python
import languagemodels as lm
import chromadb

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection")
collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges",
    ],
    ids=["id1", "id2"],
)
collection.query(query_texts=["pineapple"], n_results=5)
lm.config["instruct_model"] = "Qwen2.5-0.5B-Instruct"
lm.do("testing")
