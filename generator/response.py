from openai import OpenAI
from typing import List
import os

from .prompts import SYS_PROMPT
from data_ingetion.data import AdvancedDatabase

api_key = (
    os.getenv("TOGETHER_API")
    or "0d1849365485f54f5deb32458276cb348948608da5a89dad0efc780c2d356916"
)
client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
EMBEDDING_MODEL = "togethercomputer/m2-bert-80M-2k-retrieval"


def generate_response(query: str, group_name: str, return_chunks: bool = True):
    db = AdvancedDatabase()
    query_embedding = get_embedding(query)
    context = db.get_context(query_embedding, group_name)
    response = llm_response(context, query)
    if return_chunks:
        return (response, context)
    return response


def llm_response(context: List[str], user_query: str, history={}, stream: bool = False):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[
            {
                "role": "system",
                "content": SYS_PROMPT,
            },
            *history,
            {
                "role": "user",
                "content": f"Query : {user_query} \n\n Context: {context}",
            },
        ],
        stream=False,
    )

    # Feature to add streaming response
    # if stream:
    #    for chunk in response:
    #        yield chunk.choices[0].delta.content or ""
    # else:
    return response.choices[0].message.content


def get_embedding(query: str):
    response = client.embeddings.create(input=query, model=EMBEDDING_MODEL)
    embeddings = response.data[0].embedding
    return embeddings
