# coding: utf-8
"""
Main Flask agent application for vector store assistant.
"""

import os
import faiss
import numpy as np
import requests as req
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel
from memory import MemoryManager
from decision import generate_summary, parse_llm_json, select_tool_for_task
from action import log_page_action, search_action, extract_markdown_from_result
from fastmcp import Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Explicitly load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
# Configure CORS to allow requests from Chrome extension
CORS(app, resources={
    r"/*": {
        "origins": ["chrome-extension://*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize memory manager (handles embeddings and FAISS)
memory_manager = MemoryManager()

class URLRequest(BaseModel):
    """URLRequest model for URL requests."""
    url: str

class DeletePageRequest(BaseModel):
    """DeletePageRequest model for deleting pages."""
    url: str

class SearchRequest(BaseModel):
    """SearchRequest model for search queries."""
    query: str
    k: int = 5

class SummaryRequest(BaseModel):
    """SummaryRequest model for summary requests."""
    url: str

async def extract_markdown(url: str) -> str:
    """
    Extract markdown from a URL using the MCP server.
    """
    async with Client("http://127.0.0.1:3001/sse") as client:
        tools = await client.list_tools()
        tool_name = select_tool_for_task(tools, url)
        if not tool_name:
            raise ValueError("No suitable tool found for URL")
        result = await client.call_tool(tool_name, {"uri": url})
        return extract_markdown_from_result(result)

@app.route("/log_page", methods=["POST"])
def log_page():
    """
    Log a page and its HTML content.

    Returns:
    The result of logging the page action.
    """
    start_time = datetime.now()
    try:
        data = request.get_json()
        url = data["url"]
        logger.info(f"Logging page request received for URL: {url}")
        
        html = data.get("html")
        if not html:
            logger.info(f"HTML not provided, fetching from URL: {url}")
            resp = req.get(url)
            resp.raise_for_status()
            html = resp.text
            logger.info(f"Successfully fetched HTML from URL: {url}")
        
        logger.info(f"Processing page with memory manager")
        result = asyncio.run(log_page_action(html, url, memory_manager, "http://127.0.0.1:3001/sse"))
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Page logging completed for {url}. Duration: {duration:.2f}s. Chunks: {result.get('num_chunks', 0)}")
        
        return jsonify(result)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Error logging page {url}: {str(e)}. Duration: {duration:.2f}s")
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route("/user_query", methods=["POST"])
def user_query():
    """
    Handle a user query.

    Returns:
    The result of the search action.
    """
    data = request.get_json()
    request_model = SearchRequest(**data)
    return jsonify(search_action(request_model.query, memory_manager, request_model.k))

@app.route("/summary", methods=["POST"])
def summary():
    """
    Generate a summary for a given URL.

    Returns:
    The generated summary for the URL.
    """
    data = request.get_json()
    request_model = SummaryRequest(**data)
    url = request_model.url
    # Find all chunks for the url
    chunks = [c["chunk"] for c in memory_manager.chunks if c["url"] == url]
    if not chunks:
        return jsonify({"error": "No content found for this URL. Please index it first."})
    context = "\n\n".join(chunks)
    summary_text = generate_summary(context)
    return jsonify({"url": url, "summary": summary_text})

@app.route("/search", methods=["POST"])
def search():
    """
    Handle a search query.

    Returns:
    The result of the search action.
    """
    start_time = datetime.now()
    try:
        data = request.get_json()
        request_model = SearchRequest(**data)
        query = request_model.query
        k = request_model.k
        
        logger.info(f"Search request received. Query: '{query}', k: {k}")
        
        result = search_action(query, memory_manager, k)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Search completed. Query: '{query}'. Duration: {duration:.2f}s. Found answer: {result.get('found_answer', False)}")
        logger.debug(f"Search results: {result}")
        
        return jsonify(result)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Error processing search query '{query}': {str(e)}. Duration: {duration:.2f}s")
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route("/convert", methods=["POST"])
def convert_url_to_markdown():
    """
    Convert a URL to Markdown.

    Returns:
    The Markdown content for the URL.
    """
    data = request.get_json()
    request_model = URLRequest(**data)
    markdown = asyncio.run(extract_markdown(request_model.url))
    return jsonify({"markdown": markdown})

@app.route("/list_pages", methods=["GET"])
def list_pages():
    """
    List all unique URLs indexed.

    Returns:
    A list of unique URLs.
    """
    # Return unique URLs indexed
    urls = list({c["url"] for c in memory_manager.chunks})
    return jsonify({"urls": urls})

@app.route("/delete_page", methods=["POST"])
def delete_page():
    """
    Delete a page and its associated chunks.

    Returns:
    The result of deleting the page.
    """
    data = request.get_json()
    request_model = DeletePageRequest(**data)
    url = request_model.url
    # Remove all chunks for this URL and rebuild index
    old_indices = [i for i, c in enumerate(memory_manager.chunks) if c["url"] == url]
    if not old_indices:
        return jsonify({"status": "not_found", "url": url})
    keep_indices = [i for i in range(len(memory_manager.chunks)) if i not in old_indices]
    if keep_indices:
        kept_embs = [memory_manager.chunks[i]["embedding"] for i in keep_indices]
        memory_manager.index = faiss.IndexFlatL2(memory_manager.model.get_sentence_embedding_dimension())
        if kept_embs:
            memory_manager.index.add(np.array(kept_embs).astype('float32'))
        memory_manager.chunks = [memory_manager.chunks[i] for i in keep_indices]
    else:
        memory_manager.index = faiss.IndexFlatL2(memory_manager.model.get_sentence_embedding_dimension())
        memory_manager.chunks = []
    memory_manager._save_index()
    return jsonify({"status": "deleted", "url": url})

@app.route("/health", methods=["GET"])
def health():
    """
    Check the health of the application.

    Returns:
    The health status of the application.
    """
    # Check if embedding model and FAISS index are loaded
    try:
        dim = memory_manager.model.get_sentence_embedding_dimension()
        num_vecs = memory_manager.index.ntotal
        return jsonify({"status": "ok", "embedding_model_dim": dim, "faiss_vectors": num_vecs})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)})

@app.route("/faiss_stats", methods=["GET"])
def faiss_stats():
    """
    Get FAISS statistics.

    Returns:
    FAISS statistics.
    """
    try:
        dim = memory_manager.model.get_sentence_embedding_dimension()
        num_vecs = memory_manager.index.ntotal
        return jsonify({
            "faiss_vectors": num_vecs,
            "embedding_dim": dim,
            "num_chunks": len(memory_manager.chunks),
            "faiss_index_type": type(memory_manager.index).__name__
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
