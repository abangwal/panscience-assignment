from docx import Document
from pypdf import PdfReader
import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import sqlite3
import json

import os
from io import BytesIO

from typing import List
from fastapi import UploadFile

splitter = RecursiveCharacterTextSplitter(chunk_size=225, chunk_overlap=64)
EMBEDDING_MODEL = "togethercomputer/m2-bert-80M-2k-retrieval"
api_key = (
    os.getenv("TOGETHER_API")
    or "0d1849365485f54f5deb32458276cb348948608da5a89dad0efc780c2d356916"
)
ai_client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

# Setup/Initiate SQLite database for metadata store
conn = sqlite3.connect("metadata.db")
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS metadata_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_dict TEXT NOT NULL
)
"""
)
conn.commit()


async def full_processor(files: List[UploadFile], user_tags: str, collection_name: str):
    user_metadata = {"tags": user_tags}

    file_names = [str(file.filename) for file in files]
    file_types = [name.split(".")[-1] for name in file_names]

    processed_docs = await processor(files, file_types)

    chunks, metadata = create_chunks(processed_docs, file_names, user_metadata)

    response = ai_client.embeddings.create(input=chunks, model=EMBEDDING_MODEL)
    embeddings = [item.embedding for item in response.data]

    write_metadata(file_names, file_types, user_tags, len(chunks), collection_name)

    return (chunks, metadata, embeddings)


async def processor(files: List[UploadFile], file_types: List[str]) -> List[str]:
    processed_docs = []
    for idx, file_type in enumerate(file_types):
        if file_type == "pdf":
            processed_docs.append(await process_pdf(files[idx]))
        elif file_type == "docx":
            processed_docs.append(await process_docx(files[idx]))

    return processed_docs


async def process_pdf(file: UploadFile) -> str:
    data = await file.read()
    doc = PdfReader(BytesIO(data))

    text = ""
    for page in doc.pages:
        text += page.extract_text() or ""

    return text


async def process_docx(file: UploadFile) -> str:
    data = await file.read()
    doc = Document(BytesIO(data))

    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"

    return text


def create_chunks(docs: List[str], file_names: List[str], user_metadata):
    all_chunks = []
    all_metadata = []

    dateTime = datetime.datetime.now().strftime("%d/%m/%y-%I")

    for idx, doc in enumerate(docs):
        chunks = splitter.split_text(doc)
        all_chunks += chunks
        metadata = {
            "file_name": file_names[idx],
            "timestamp": dateTime,
            **user_metadata,
        }
        all_metadata += [metadata] * len(chunks)

    return all_chunks, all_metadata


def write_metadata(file_names, file_types, user_tags, total_chunks, collection_name):

    time = datetime.datetime.now().strftime("%d/%m/%y-%I")
    pdf, docx, unsupported = 0, 0, 0
    for i in file_types:
        if i == "pdf":
            pdf += 1
        elif i == "docx":
            docx += 1
        else:
            unsupported += 1

    metadata = {
        "Collection": collection_name,
        "FileName": file_names,
        "TotalPDF": pdf,
        "TotalDocx": docx,
        "Unsupported": unsupported,
        "CustomTag": user_tags,
        "TotalChunks": total_chunks,
        "Time": time,
    }
    cursor.execute(
        "INSERT INTO metadata_store (meta_dict) VALUES (?)", (json.dumps(metadata),)
    )
    conn.commit()


def read_metadata():

    cursor.execute("SELECT meta_dict FROM metadata_store")
    rows = cursor.fetchall()

    data = []
    for row in rows:
        meta = json.loads(row[0])
        data.append(meta)

    return data
