import os
import logging  # Import logging module
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import chromadb
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm
import shutil  # For deleting directories

db_port = 8003
db_log_dir = '/teamspace/studios/this_studio/log'
db_log_filename = 'db_log.log'

# Set up logging configuration
os.makedirs(db_log_dir, exist_ok=True)  # Create directory if it doesn't exist
logging.basicConfig(
    filename=db_log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextData(BaseModel):
    text: str

class UploadDataFrame(BaseModel):
    dataframe: List[str]
    collection_name: str

class UpsertData(BaseModel):
    q_a: str
    collection_name: str

class SimilaritySearchData(BaseModel):
    query: str
    collection_name: str
    k: Optional[int] = 5  # Default value is 5 if not provided

def initialize_databases():
    """Initialize all databases on first run of the FastAPI server."""
    try:
        create_db_def("rag")
        logging.info("Databases initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing databases: {str(e)}")
        print(f"Error initializing databases: {str(e)}")



def clear_chroma_directory():
    """Delete the 'chroma' directory if it exists."""
    chroma_dir = "./chroma"
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
        logging.info(f"Deleted '{chroma_dir}' directory.")


def create_collection_if_not_exists(client, collection_name, embedding_function):
    """Create a collection if it does not already exist."""
    try:
        if collection_name not in client.list_collections():
            collection = client.create_collection(name=collection_name)
            logging.info(f"Collection '{collection_name}' created successfully.")
            return collection
        else:
            raise Exception(f"Collection '{collection_name}' already exists")
    except Exception as e:
        logging.error(f"Error in creating collection '{collection_name}': {str(e)}")
        raise


def db_def(collection_name, ids, doc, client=None, embedding_function=None):
    if client is None:
        client = chromadb.PersistentClient()

    if embedding_function is None:
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create collection if not exists
    create_collection_if_not_exists(client, collection_name, embedding_function)
    
    collection = client.get_collection(name=collection_name)
    doc_texts = [d.page_content for d in doc]
    collection.add(ids=ids, documents=doc_texts)

    langchain_chroma = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding_function,
    )

    logging.info(f"Database '{collection_name}' created with {len(ids)} documents.")
    return langchain_chroma


def db_def_pair(collection_name, ids, doc, client=None, embedding_function=None):
    if client is None:
        client = chromadb.PersistentClient()

    if embedding_function is None:
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create collection if not exists
    create_collection_if_not_exists(client, collection_name, embedding_function)
    
    collection = client.get_collection(name=collection_name)
    collection.add(ids=ids, documents=doc)

    langchain_chroma = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding_function,
    )

    logging.info(f"Database pair '{collection_name}' created with {len(ids)} documents.")
    return langchain_chroma

@app.on_event("startup")
async def on_startup():
    """Startup event to initialize databases."""
    clear_chroma_directory()
    initialize_databases()

@app.post("/db_def")
def create_db_def(collection_name: str):
    try:
        client = chromadb.PersistentClient()
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        loader = TextLoader("rto_dataset.txt")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
        chunked_docs = text_splitter.split_documents(docs)

        ids = [str(i) for i in range(1, len(chunked_docs) + 1)]
        db = db_def(collection_name, ids, chunked_docs, client, embedding_function)
        logging.info(f"Database '{collection_name}' created successfully.")
        return {"status": "success", "message": "Database created successfully."}
    except Exception as e:
        logging.error(f"Error creating database '{collection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

################# FOR CSV HANDLING ####################
# @app.post("/db_def_pair")
# def create_db_def_pair(collection_name: str):
#     try:
#         client = chromadb.PersistentClient()
#         embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
#         doc = ["hey"]
#         ids = ["1"]
#         db = db_def_pair(collection_name, ids, doc, client, embedding_function)
#         logging.info(f"Database pair '{collection_name}' created successfully.")
#         return {"status": "success", "message": "Database pair created successfully."}
#     except Exception as e:
#         logging.error(f"Error creating database pair '{collection_name}': {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/upload")
# def upload(data: UploadDataFrame):
#     try:
#         client = chromadb.PersistentClient()
#         embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

#         collection = client.get_collection(name=data.collection_name)
#         for i in tqdm(range(len(data.dataframe))):
#             collection.add(ids=[str(collection.count() + 1)], documents=[data.dataframe[i]])

#         logging.info(f"Data uploaded successfully to collection '{data.collection_name}'.")
#         return {"status": "success", "message": "Data uploaded successfully."}
#     except Exception as e:
#         logging.error(f"Error uploading data to collection '{data.collection_name}': {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/upsert")
def upsert(data: UpsertData):
    try:
        client = chromadb.PersistentClient()
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        collection = client.get_collection(name=data.collection_name)
        collection.add(ids=[str(collection.count() + 1)], documents=[data.q_a])
        logging.info(f"Data upserted to collection '{data.collection_name}'.")
        return {"status": "success", "message": "Data upserted successfully."}
    except Exception as e:
        logging.error(f"Error upserting data to collection '{data.collection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    try:
        # Read uploaded file and append its content to test.txt
        file_content = await file.read()
        with open("/teamspace/studios/this_studio/data/rto_dataset.txt", "a") as f:
            f.write(file_content.decode())

        # Delete the 'chroma' directory to reset the databases
        clear_chroma_directory()

        # Reload the database after appending the new content
        loader = TextLoader("/teamspace/studios/this_studio/data/rto_dataset.txt")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
        chunked_docs = text_splitter.split_documents(docs)

        # Redefine databases
        initialize_databases()

        logging.info("File uploaded and database redefined successfully.")
        return {"status": "success", "message": "File uploaded and database redefined successfully."}
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similarity_search")
def similarity_search(data: SimilaritySearchData):
    try:
        client = chromadb.PersistentClient()
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        # Access the specified collection
        langchain_chroma = Chroma(
            client=client,
            collection_name=data.collection_name,
            embedding_function=embedding_function,
        )

        # Perform similarity search
        doc_results = langchain_chroma.similarity_search_with_score(data.query, k=data.k)
        matched_info = ' '.join(item[0].page_content for item in doc_results)

        logging.info(f"Similarity search performed on collection '{data.collection_name}' with query: {data.query}")
        return {"status": "success", "matched_info": matched_info}
    except Exception as e:
        logging.error(f"Error performing similarity search on collection '{data.collection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=db_port)