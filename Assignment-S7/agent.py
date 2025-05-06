import asyncio
import logging
import time
import os
import datetime
from perception import extract_perception
from memory import MemoryManager, MemoryItem
from decision import generate_plan
from action import execute_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from flask_cors import CORS
from flask import Flask, request, jsonify
import re
import requests
import example3 as e3
import shutil
import sys
import json
from pathlib import Path

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

max_steps = 3

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working."""
    print("Test endpoint called")
    return jsonify(success=True, message="API is working")

@app.route('/api/indexed_pages', methods=['GET'])
def list_indexed_pages():
    """List all pages that have been indexed in FAISS."""
    print("=== Indexed Pages Endpoint Called ===")
    print("Request method:", request.method)
    print("Request URL:", request.url)
    print("Request headers:", dict(request.headers))
    
    logging.info("Received request for indexed pages")
    try:
        # Path to the FAISS metadata file
        metadata_path = Path("faiss_index/metadata.json")
        print(f"Looking for metadata file at: {metadata_path}")
        
        if not metadata_path.exists():
            logging.warning("No metadata file found at: %s", metadata_path)
            print(f"No metadata file found at: {metadata_path}")
            return jsonify(
                success=True,
                stats={
                    "total_pages": 0,
                    "total_chunks": 0,
                    "pages": []
                }
            )
        
        # Read the metadata file
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"Successfully loaded metadata file with {len(metadata)} entries")
            logging.info("Successfully loaded metadata file with %d entries", len(metadata))
        
        # Extract unique documents and their chunk counts
        doc_stats = {}
        for item in metadata:
            doc_name = item['doc']
            if doc_name not in doc_stats:
                doc_stats[doc_name] = {
                    'filename': doc_name,
                    'chunk_count': 0,
                    'last_modified': None
                }
            doc_stats[doc_name]['chunk_count'] += 1
            
            # Try to get file modification time
            try:
                file_path = os.path.join('documents', doc_name)
                if os.path.exists(file_path):
                    doc_stats[doc_name]['last_modified'] = datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logging.warning(f"Could not get modification time for {doc_name}: {e}")
        
        # Convert to list format
        indexed_pages = list(doc_stats.values())
        total_chunks = sum(page['chunk_count'] for page in indexed_pages)
        
        print(f"Found {len(indexed_pages)} unique indexed pages with {total_chunks} total chunks")
        logging.info("Found %d unique indexed pages with %d total chunks", len(indexed_pages), total_chunks)
        
        response = jsonify(
            success=True,
            stats={
                "total_pages": len(indexed_pages),
                "total_chunks": total_chunks,
                "pages": indexed_pages
            }
        )
        print('I am going to return ----------', response)
        return response
    except Exception as e:
        logging.exception("Error listing indexed pages")
        print(f"Error listing indexed pages: {str(e)}")
        return jsonify(success=False, error=str(e))

@app.route('/log_page', methods=['POST'])
def log_page():
    """Logs a page's content by URL and stores its embeddings."""
    url = request.json.get('url')
    logging.info(f"Logging page for URL: {url}")
    try:
        # Check if URL is already indexed
        metadata_path = Path("faiss_index/metadata.json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                # Check if any document in metadata matches this URL
                url_filename = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50] + ".txt"
                if any(item['doc'] == url or item['doc'] == url_filename for item in metadata):
                    logging.info(f"URL already indexed: {url}")
                    return jsonify(success=True, message="Page already indexed", already_indexed=True)

        # If not indexed, proceed with indexing
        html = requests.get(url).text
        text = e3.clean_html(html)

        # Create a safe filename from the URL
        filename = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50] + ".txt"
        file_path = os.path.join('documents', filename)
        
        # Ensure documents directory exists
        os.makedirs('documents', exist_ok=True)
        
        # Save the cleaned content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        # Process the document to update the FAISS index
        e3.process_documents()
        
        logging.info(f"Successfully logged page: {url}")
        return jsonify(success=True, message="Page logged and indexed", already_indexed=False)
    except Exception as e:
        logging.exception("Error logging page")
        return jsonify(success=False, error=str(e))

@app.route('/summary', methods=['POST'])
def summary():
    """Generate a basic summary of the given URL content."""
    url = request.json.get('url')
    logging.info(f"Generating summary for URL: {url}")
    try:
        # Read the FAISS metadata
        metadata_path = Path("faiss_index/metadata.json")
        if not metadata_path.exists():
            logging.error("Metadata file not found at: %s", metadata_path)
            return jsonify(success=False, error="No index metadata found")
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            logging.info(f"Successfully loaded metadata with {len(metadata)} entries")
            
        # Find chunks for the given URL
        chunks = []
        # Convert URL to filename format for comparison
        url_filename = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50] + ".txt"
        logging.info(f"Looking for content with URL: {url} or filename: {url_filename}")
        
        for item in metadata:
            # Check if the document name matches either the URL or the filename
            if item['doc'] == url or item['doc'] == url_filename:
                chunks.append(item['chunk'])
                
        if not chunks:
            # Log the available documents for debugging
            available_docs = set(item['doc'] for item in metadata)
            logging.error(f"No content found. Available documents: {available_docs}")
            return jsonify(
                success=False, 
                error="No content found for the given URL",
                debug_info={
                    "requested_url": url,
                    "requested_filename": url_filename,
                    "available_documents": list(available_docs)
                }
            )
            
        # Create summary from first few chunks
        full_text = "\n".join(chunks[:10])
        logging.info(f"Created text from {len(chunks[:10])} chunks, total length: {len(full_text)}")
        
        # Create a proper query for summarization
        query = f"Please summarize the following text: {full_text}"
        logging.info("Calling main() with summarization query")
        
        try:
            summary = asyncio.run(main(query))
            logging.info(f"Received summary response: {summary[:100]}...")  # Log first 100 chars
            
            # Extract the summary from the FINAL_ANSWER format
            if summary and summary.startswith("FINAL_ANSWER:"):
                summary = summary.replace("FINAL_ANSWER:", "").strip()
                summary = summary.strip('[]')
                logging.info("Successfully processed summary")
            else:
                logging.warning(f"Unexpected summary format: {summary[:100]}...")
                
            return jsonify(success=True, summary=summary)
        except Exception as e:
            logging.exception("Error in main() execution")
            return jsonify(success=False, error=f"Error generating summary: {str(e)}")
            
    except Exception as e:
        logging.exception("Error in summary endpoint")
        return jsonify(success=False, error=str(e))
    
@app.route('/user_query', methods=['POST'])
def user_query():
    """Answer user query using vector search."""
    query = request.json.get('query')
    logging.info(f"Received user query: {query}")
    try:
        result = asyncio.run(main(query))
        # Extract the actual answer from the FINAL_ANSWER format
        if result and result.startswith("FINAL_ANSWER:"):
            answer = result.replace("FINAL_ANSWER:", "").strip()
            # Remove the square brackets if present
            answer = answer.strip('[]')
            print('I am going to return ********', answer)
            return jsonify(success=True, answer=answer, found_answer=True)
        else:
            return jsonify(success=True, answer=result, found_answer=True)
    except Exception as e:
        logging.exception("Error processing query")
        return jsonify(success=False, error=str(e), found_answer=False)

async def main(user_input: str):
    try:
        print("[agent] Starting agent...")
        print(f"[agent] Current working directory: {os.getcwd()}")
        
        server_params = StdioServerParameters(
            command="python",
            args=["example3.py"],
            cwd="C:/Users/shivs/Downloads/Assignment-S7"
        )

        try:
            async with stdio_client(server_params) as (read, write):
                print("Connection established, creating session...")
                try:
                    async with ClientSession(read, write) as session:
                        print("[agent] Session created, initializing...")
 
                        try:
                            await session.initialize()
                            print("[agent] MCP session initialized")

                            # Your reasoning, planning, perception etc. would go here
                            tools = await session.list_tools()
                            print("Available tools:", [t.name for t in tools.tools])

                            # Get available tools
                            print("Requesting tool list...")
                            tools_result = await session.list_tools()
                            tools = tools_result.tools
                            tool_descriptions = "\n".join(
                                f"- {tool.name}: {getattr(tool, 'description', 'No description')}" 
                                for tool in tools
                            )

                            log("agent", f"{len(tools)} tools loaded")

                            memory = MemoryManager()
                            session_id = f"session-{int(time.time())}"
                            query = user_input  # Store original intent
                            step = 0
                            final_result = None

                            while step < max_steps:
                                log("loop", f"Step {step + 1} started")

                                perception = extract_perception(user_input)
                                log("perception", f"Intent: {perception.intent}, Tool hint: {perception.tool_hint}")

                                retrieved = memory.retrieve(query=user_input, top_k=3, session_filter=session_id)
                                log("memory", f"Retrieved {len(retrieved)} relevant memories")

                                plan = generate_plan(perception, retrieved, tool_descriptions=tool_descriptions)
                                log("plan", f"Plan generated: {plan}")

                                if plan.startswith("FINAL_ANSWER:"):
                                    log("agent", f"✅ FINAL RESULT: {plan}")
                                    final_result = plan
                                    break

                                try:
                                    result = await execute_tool(session, tools, plan)
                                    log("tool", f"{result.tool_name} returned: {result.result}")

                                    memory.add(MemoryItem(
                                        text=f"Tool call: {result.tool_name} with {result.arguments}, got: {result.result}",
                                        type="tool_output",
                                        tool_name=result.tool_name,
                                        user_query=user_input,
                                        tags=[result.tool_name],
                                        session_id=session_id
                                    ))

                                    user_input = f"Original task: {query}\nPrevious output: {result.result}\nWhat should I do next?"

                                except Exception as e:
                                    log("error", f"Tool execution failed: {e}")
                                    final_result = f"FINAL_ANSWER: [Error: {str(e)}]"
                                    break

                                step += 1
                        except Exception as e:
                            print(f"[agent] Session initialization error: {str(e)}")
                            final_result = f"FINAL_ANSWER: [Error: {str(e)}]"
                except Exception as e:
                    print(f"[agent] Session creation error: {str(e)}")
                    final_result = f"FINAL_ANSWER: [Error: {str(e)}]"
        except Exception as e:
            print(f"[agent] Connection error: {str(e)}")
            final_result = f"FINAL_ANSWER: [Error: {str(e)}]"
    except Exception as e:
        print(f"[agent] Overall error: {str(e)}")
        final_result = f"FINAL_ANSWER: [Error: {str(e)}]"

    log("agent", "Agent session complete.")
    return final_result or "FINAL_ANSWER: [No result generated]"

# if __name__ == "__main__":
#     query = input("🧑 What do you want to solve today? → ")
#     asyncio.run(main(query))

if __name__ == '__main__':
    logging.info("Starting Flask app on port 8000")
    app.run(debug=True, port=8000)


# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?