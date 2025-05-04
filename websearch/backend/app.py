import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import requests
import hashlib
import os
import json
import numpy as np

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# === In-memory storage ===
index = faiss.IndexFlatL2(384)  # For model 'all-MiniLM-L6-v2'
page_data = {}  # URL -> list of (chunk, vector)
url_map = {}    # URL -> [chunk indices in index]

# === Load embedding model ===
model = SentenceTransformer('all-MiniLM-L6-v2')

# === Helpers ===
def clean_html(html):
    """Remove scripts and styles from HTML and return clean text."""
    soup = BeautifulSoup(html, "html.parser")
    [s.decompose() for s in soup(["script", "style"])]
    return soup.get_text(separator="\n")

def split_chunks(text, max_words=100):
    """Split text into chunks of max_words length."""
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def embed_chunks(chunks):
    """Generate embeddings for each chunk."""
    return model.encode(chunks, show_progress_bar=False)

# === Routes ===
@app.route('/health')
def health():
    """Check server health."""
    logging.info("Health check requested.")
    return jsonify(status='ok')

@app.route('/log_page', methods=['POST'])
def log_page():
    """Logs a page's content by URL and stores its embeddings."""
    url = request.json.get('url')
    logging.info(f"Logging page for URL: {url}")
    try:
        html = requests.get(url).text
        text = clean_html(html)
        chunks = split_chunks(text)
        vectors = embed_chunks(chunks)
        index.add(vectors)

        # Store metadata
        ids = list(range(index.ntotal - len(chunks), index.ntotal))
        page_data[url] = list(zip(chunks, vectors.tolist()))
        url_map[url] = ids

        logging.info(f"Successfully logged page: {url}")
        return jsonify(success=True, message="Page logged.")
    except Exception as e:
        logging.exception("Error logging page")
        return jsonify(success=False, error=str(e))

@app.route('/summary', methods=['POST'])
def summary():
    """Generate a basic summary of the given URL content."""
    url = request.json.get('url')
    logging.info(f"Generating summary for URL: {url}")
    try:
        chunks = [chunk for chunk, _ in page_data.get(url, [])]
        full_text = "\n".join(chunks[:10])
        summary = "Summary:\n" + full_text[:1000]  # Simulated summary
        return jsonify(summary=summary)
    except Exception as e:
        logging.exception("Error generating summary")
        return jsonify(error=str(e))

@app.route('/user_query', methods=['POST'])
def user_query():
    """Answer user query using vector search."""
    query = request.json.get('query')
    k = request.json.get('k', 5)
    logging.info(f"Received user query: {query}")
    try:
        q_vector = model.encode([query])
        D, I = index.search(q_vector, k)

        matched_chunks = []
        source_urls = []
        for i in I[0]:
            for url, ids in url_map.items():
                if i in ids:
                    chunk_text = page_data[url][ids.index(i)][0]
                    matched_chunks.append(chunk_text)
                    source_urls.append(url)
                    break

        answer = "\n\n".join(matched_chunks)
        return jsonify(answer=answer, found_answer=True, source_urls=list(set(source_urls)))
    except Exception as e:
        logging.exception("Error processing user query")
        return jsonify(error=str(e), found_answer=False)

@app.route('/list_pages', methods=['GET'])
def list_pages():
    """List all URLs that have been indexed."""
    logging.info("Listing indexed pages.")
    return jsonify(urls=list(page_data.keys()))

@app.route('/delete_page', methods=['POST'])
def delete_page():
    """Delete an indexed page and rebuild the FAISS index."""
    url = request.json.get('url')
    logging.info(f"Request to delete page: {url}")
    if url in url_map:
        try:
            # Rebuild index without deleted vectors
            keep_chunks = []
            for u, chunks in page_data.items():
                if u != url:
                    keep_chunks.extend([v for _, v in chunks])

            global index
            index = faiss.IndexFlatL2(384)
            index.add(np.array(keep_chunks).astype('float32'))

            # Update metadata
            del page_data[url]
            del url_map[url]
            url_map.clear()
            offset = 0
            for u, chunks in page_data.items():
                ids = list(range(offset, offset + len(chunks)))
                url_map[u] = ids
                offset += len(chunks)

            logging.info(f"Successfully deleted and rebuilt index excluding: {url}")
            return jsonify(success=True)
        except Exception as e:
            logging.exception("Error deleting page")
            return jsonify(success=False, error=str(e))
    return jsonify(success=False, error="URL not found")

@app.route('/faiss_stats', methods=['GET'])
def faiss_stats():
    """Return statistics about the FAISS index."""
    logging.info("Returning FAISS stats.")
    return jsonify(
        num_chunks=index.ntotal,
        embedding_dim=index.d,
        faiss_index_type=str(type(index).__name__)
    )

if __name__ == '__main__':
    logging.info("Starting Flask app on port 8000")
    app.run(debug=True, port=8000)