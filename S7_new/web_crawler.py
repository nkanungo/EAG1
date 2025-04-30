import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Set, Optional
import time
from pathlib import Path
import json
import hashlib
from tqdm import tqdm
import faiss
import numpy as np
from markitdown import MarkItDown
from google.generativeai import GenerativeModel
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

class WebCrawler:
    def __init__(self, start_url: str, max_pages: int = 10, max_depth: int = 2):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.pages_processed = 0
        self.converter = MarkItDown()
        self.index_cache = Path("faiss_index")
        self.index_cache.mkdir(exist_ok=True)
        self.index_file = self.index_cache / "index.bin"
        self.metadata_file = self.index_cache / "metadata.json"
        self.cache_file = self.index_cache / "url_index_cache.json"

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be crawled"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_page_content(self, url: str) -> Optional[str]:
        """Fetch and parse webpage content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_text(self, html: str) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_links(self, html: str, base_url: str) -> List[str]:
        """Extract all valid links from a page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            absolute_url = urljoin(base_url, href)
            if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                links.append(absolute_url)
        
        return links

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 <= chunk_size:
                current_chunk.append(word)
                current_size += len(word) + 1
            else:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini"""
        try:
            response = model.generate_content(
                contents=f"Generate a dense vector embedding for this text: {text}"
            )
            # Parse the response to get the embedding
            # This is a placeholder - you'll need to adjust based on Gemini's actual response format
            return [float(x) for x in response.text.strip().split(',')]
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0.0] * 768  # Default embedding size

    def process_url(self, url: str, depth: int = 0):
        """Process a single URL and its content"""
        if depth > self.max_depth or self.pages_processed >= self.max_pages:
            return

        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        print(f"Processing: {url} (depth {depth})")

        html = self.get_page_content(url)
        if not html:
            return

        text = self.extract_text(html)
        if not text:
            return

        # Process the text
        try:
            result = self.converter.convert(text)
            markdown = result.text_content
            chunks = list(self.chunk_text(markdown))
            
            # Load existing index and metadata
            cache_meta = json.loads(self.cache_file.read_text()) if self.cache_file.exists() else {}
            metadata = json.loads(self.metadata_file.read_text()) if self.metadata_file.exists() else []
            index = faiss.read_index(str(self.index_file)) if self.index_file.exists() else None
            
            # Generate embeddings and update index
            embeddings_for_page = []
            new_metadata = []
            
            for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {url}")):
                embedding = self.get_embedding(chunk)
                embeddings_for_page.append(embedding)
                new_metadata.append({
                    "url": url,
                    "chunk": chunk,
                    "chunk_id": f"{hashlib.md5(url.encode()).hexdigest()}_{i}"
                })

            if embeddings_for_page:
                if index is None:
                    dim = len(embeddings_for_page[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_page))
                metadata.extend(new_metadata)
            
            # Update cache and save
            cache_meta[url] = hashlib.md5(text.encode()).hexdigest()
            self.cache_file.write_text(json.dumps(cache_meta, indent=2))
            self.metadata_file.write_text(json.dumps(metadata, indent=2))
            
            if index and index.ntotal > 0:
                faiss.write_index(index, str(self.index_file))
            
            self.pages_processed += 1

            # Get links and process them
            if depth < self.max_depth:
                links = self.get_links(html, url)
                for link in links:
                    if self.pages_processed >= self.max_pages:
                        break
                    time.sleep(1)  # Be nice to servers
                    self.process_url(link, depth + 1)

        except Exception as e:
            print(f"Error processing {url}: {e}")

    def crawl(self):
        """Start the crawling process"""
        self.process_url(self.start_url)
        print(f"Crawling completed. Processed {self.pages_processed} pages.") 