from typing import List
from fastapi import FastAPI, Form, UploadFile, File
from data_ingetion.data import AdvancedDatabase
from data_ingetion.pre_processor import read_metadata
from generator.response import generate_response

db = AdvancedDatabase()
app = FastAPI()


@app.post("/ingest_files")
async def ingest_files(
    metadata: str = Form(...),
    group_name: str = Form(...),
    files: List[UploadFile] = File(...),
):
    """Upload and process multiple files (PDFs and DOCXs) in single endpoint inference asyncronously"""
    result = await db.ingest(files, metadata, group_name)
    return result


@app.post("/fetch_response")
async def get_response(query: str, group_name: str, include_chunks: bool = False):
    """Invoke RAG pipeline with given collection as VectorDB to retrieve context and generate context rich responses"""
    response = generate_response(query, group_name)
    if include_chunks:
        return {"llm_response": response[0], "chunks": response[1]}
    return {"llm_response": response}


@app.get("/get_metadata")
async def get_metadata():
    """Fetch Metadata of recently uploaded documents grouped by collections ie. time they were uploaded."""
    response = read_metadata()
    return {"Metadata": response}
