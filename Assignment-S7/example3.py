from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import os
import json
import faiss
import numpy as np
from pathlib import Path
import requests
from markitdown import MarkItDown
import time
from models import AddInput, AddOutput, SqrtInput, SqrtOutput, StringsToIntsInput, StringsToIntsOutput, ExpSumInput, ExpSumOutput
from PIL import Image as PILImage
from tqdm import tqdm
import hashlib
from bs4 import BeautifulSoup
from transformers import pipeline


mcp = FastMCP("Calculator")

EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40
ROOT = Path(__file__).parent.resolve()


# === Helpers ===
def clean_html(html):
    """Remove scripts and styles from HTML and return clean text."""
    soup = BeautifulSoup(html, "html.parser")
    [s.decompose() for s in soup(["script", "style"])]
    return soup.get_text(separator="\n")

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()

@mcp.tool()
def search_documents(query: str) -> list[str]:
    """Search for relevant content from uploaded documents."""
    ensure_faiss_ready()
    mcp_log("SEARCH", f"Query: {query}")
    try:
        index = faiss.read_index(str(ROOT / "faiss_index" / "index.bin"))
        metadata = json.loads((ROOT / "faiss_index" / "metadata.json").read_text())
        query_vec = get_embedding(query).reshape(1, -1)
        D, I = index.search(query_vec, k=5)
        results = []
        for idx in I[0]:
            data = metadata[idx]
            results.append(f"{data['chunk']}\n[Source: {data['doc']}, ID: {data['chunk_id']}]")
        return results
    except Exception as e:
        return [f"ERROR: Failed to search: {str(e)}"]


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

def process_documents():
    """Process documents and create FAISS index"""
    mcp_log("INFO", "Indexing documents with MarkItDown...")
    ROOT = Path(__file__).parent.resolve()
    DOC_PATH = ROOT / "documents"
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_CACHE.mkdir(exist_ok=True)
    INDEX_FILE = INDEX_CACHE / "index.bin"
    METADATA_FILE = INDEX_CACHE / "metadata.json"
    CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"

    def file_hash(path):
        return hashlib.md5(Path(path).read_bytes()).hexdigest()

    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None
    all_embeddings = []
    converter = MarkItDown()

    for file in DOC_PATH.glob("*.*"):
        fhash = file_hash(file)
        if file.name in CACHE_META and CACHE_META[file.name] == fhash:
            mcp_log("SKIP", f"Skipping unchanged file: {file.name}")
            continue

        mcp_log("PROC", f"Processing: {file.name}")
        try:
            result = converter.convert(str(file))
            markdown = result.text_content
            chunks = list(chunk_text(markdown))
            embeddings_for_file = []
            new_metadata = []
            for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {file.name}")):
                embedding = get_embedding(chunk)
                embeddings_for_file.append(embedding)
                new_metadata.append({"doc": file.name, "chunk": chunk, "chunk_id": f"{file.stem}_{i}"})
            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_file))
                metadata.extend(new_metadata)
            CACHE_META[file.name] = fhash
        except Exception as e:
            mcp_log("ERROR", f"Failed to process {file.name}: {e}")

    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        mcp_log("SUCCESS", "Saved FAISS index and metadata")
    else:
        mcp_log("WARN", "No new documents or updates to process.")

def ensure_faiss_ready():
    from pathlib import Path
    index_path = ROOT / "faiss_index" / "index.bin"
    meta_path = ROOT / "faiss_index" / "metadata.json"
    if not (index_path.exists() and meta_path.exists()):
        mcp_log("INFO", "Index not found — running process_documents()...")
        process_documents()
    else:
        mcp_log("INFO", "Index already exists. Skipping regeneration.")

# Initialize the summarization pipeline
summarizer = None

def initialize_summarizer():
    global summarizer
    try:
        mcp_log("INFO", "Loading summarization model...")
        # Try to use a smaller model first
        try:
            summarizer = pipeline("summarization", 
                                model="facebook/bart-base",  # Using smaller model
                                device=-1,  # Use CPU
                                model_kwargs={"low_cpu_mem_usage": True})
            mcp_log("SUCCESS", "Summarization model (bart-base) loaded successfully")
        except Exception as e:
            mcp_log("WARN", f"Failed to load bart-base, trying bart-large-cnn: {str(e)}")
            summarizer = pipeline("summarization", 
                                model="facebook/bart-large-cnn", 
                                device=-1,  # Use CPU
                                model_kwargs={"low_cpu_mem_usage": True})
            mcp_log("SUCCESS", "Summarization model (bart-large-cnn) loaded successfully")
        return True
    except Exception as e:
        mcp_log("ERROR", f"Failed to load any summarization model: {str(e)}")
        return False

@mcp.tool()
def summarize_text(text: str, max_length: int = 150, min_length: int = 30) -> str:
    """Summarize the given text using a pre-trained model."""
    global summarizer
    
    try:
        # Try to initialize the model if it's not loaded
        if summarizer is None:
            mcp_log("INFO", "Summarizer not initialized, attempting to load...")
            if not initialize_summarizer():
                mcp_log("ERROR", "Failed to initialize summarizer")
                return "Error: Failed to load summarization model"
        
        mcp_log("SUMMARIZE", f"Starting summarization of text length {len(text)}")
        
        # Validate input
        if not isinstance(text, str):
            mcp_log("ERROR", f"Invalid input type: {type(text)}")
            return "Error: Input must be a string"
            
        if not text.strip():
            mcp_log("ERROR", "Empty text provided")
            return "Error: Empty text provided for summarization"
        
        # Truncate text if it's too long
        original_length = len(text.split())
        if original_length > 1000:
            text = " ".join(text.split()[:1000])
            mcp_log("WARN", f"Text truncated from {original_length} to 1000 words")
        
        mcp_log("INFO", "Calling summarizer pipeline...")
        summary = summarizer(text, 
                           max_length=max_length, 
                           min_length=min_length, 
                           do_sample=False,
                           truncation=True)
        
        if not summary:
            mcp_log("ERROR", "Summarizer returned empty result")
            return "Error: Failed to generate summary - empty result"
            
        if not isinstance(summary, list) or not summary:
            mcp_log("ERROR", f"Unexpected summary format: {type(summary)}")
            return "Error: Unexpected summary format"
            
        if not summary[0].get('summary_text'):
            mcp_log("ERROR", "No summary_text in result")
            return "Error: No summary text generated"
            
        result = summary[0]['summary_text']
        mcp_log("SUCCESS", f"Successfully generated summary of length {len(result)}")
        return result
        
    except Exception as e:
        mcp_log("ERROR", f"Summarization failed with error: {str(e)}")
        import traceback
        mcp_log("ERROR", f"Traceback: {traceback.format_exc()}")
        return f"Error summarizing text: {str(e)}"

if __name__ == "__main__":
    print("STARTING THE SERVER AT AMAZING LOCATION")
    
    try:
        # Initialize the summarization model first
        if not initialize_summarizer():
            mcp_log("WARN", "Continuing without summarization model")
        
        # Ensure FAISS index is ready before starting server
        mcp_log("INFO", "Checking FAISS index...")
        ensure_faiss_ready()
        mcp_log("SUCCESS", "FAISS index check complete")
        
        if len(sys.argv) > 1 and sys.argv[1] == "dev":
            mcp.run() # Run without transport for dev server
        else:
            # Start the server in a separate thread
            import threading
            server_thread = threading.Thread(target=lambda: mcp.run(transport="stdio"))
            server_thread.daemon = True
            server_thread.start()
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Process documents after server is running
            process_documents()
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
    except Exception as e:
        mcp_log("ERROR", f"Failed to start server: {str(e)}")
        sys.exit(1)
