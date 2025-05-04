import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import pickle

CHUNK_SIZE = 1000  # tokens
MODEL_NAME = "all-MiniLM-L6-v2"
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss.index")
CHUNKS_PATH = os.path.join(os.path.dirname(__file__), "chunks.pkl")

class MemoryManager:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
        self.chunks = []  # List[Dict]: {"url", "chunk", "embedding", "position"}
        self._load_index()

    def chunk_text(self, text: str) -> List[str]:
        # Simple chunking by character count (since tokenization is model-dependent)
        return [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

    def embed(self, text: str) -> np.ndarray:
        # SentenceTransformer handles batching and tokenization internally
        embedding = self.model.encode(text)
        return embedding

    def add_to_index(self, url: str, chunks: List[str]):
        # Remove existing chunks and embeddings for this URL (re-index/update)
        old_indices = [i for i, c in enumerate(self.chunks) if c["url"] == url]
        if old_indices:
            # Remove from FAISS index and chunks (rebuild index)
            keep_indices = [i for i in range(len(self.chunks)) if i not in old_indices]
            if keep_indices:
                kept_embs = np.array([self.chunks[i]["embedding"] for i in keep_indices]).astype('float32')
                self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
                self.index.add(kept_embs)
                self.chunks = [self.chunks[i] for i in keep_indices]
            else:
                self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
                self.chunks = []
        # Add new chunks
        for idx, chunk in enumerate(chunks):
            emb = self.embed(chunk)
            self.index.add(np.array([emb]).astype('float32'))
            self.chunks.append({"url": url, "chunk": chunk, "embedding": emb, "position": idx})
        self._save_index()

    def search(self, query: str, k: int = 5):
        q_emb = self.embed(query)
        D, I = self.index.search(np.array([q_emb]).astype('float32'), k)
        results = []
        for i in I[0]:
            if 0 <= i < len(self.chunks):
                chunk = self.chunks[i].copy()
                if "embedding" in chunk:
                    del chunk["embedding"]
                results.append(chunk)
        return results

    def _save_index(self):
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

    def _load_index(self):
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self.index = faiss.read_index(FAISS_INDEX_PATH)
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)
