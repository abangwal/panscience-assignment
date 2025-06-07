import chromadb
from uuid import uuid4

from .pre_processor import full_processor

from typing import List
from fastapi import UploadFile

DB_NAME = "chromadb"


class AdvancedDatabase:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=DB_NAME)

    async def ingest(self, files: List[UploadFile], user_metadata, collection_name):
        chunks, metadata, embeddings = await full_processor(
            files, user_metadata, collection_name
        )

        collection = self.client.create_collection(name=collection_name)

        collection.add(
            ids=[str(uuid4()) for _ in range(len(chunks))],
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadata,
        )

        return {"chunks_added": len(chunks), "collection_name": collection_name}

    def get_context(self, embedding: List[float], group_name: str):
        collection = self.client.get_collection(name=group_name)

        response = collection.query(
            query_embeddings=embedding, n_results=5, include=["documents"]
        )

        return response["documents"][0]
