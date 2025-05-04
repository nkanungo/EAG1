# coding: utf-8
"""
Actions for tool selection and page logging using FastMCP.
"""

import asyncio
from fastmcp import Client
from memory import MemoryManager
from decision import generate_summary, parse_llm_json, select_tool_for_task

async def log_page_action(html: str, url: str, memory_manager: MemoryManager, mcp_server_url: str) -> dict:
    """
    List tools, use LLM to select tool, invoke tool, and process markdown.
    The LLM/tool selector should infer the user's intent based on the input (URL, file, etc.).
    """
    async with Client(mcp_server_url) as client:
        tools = await client.list_tools()
        tool_name = select_tool_for_task(tools, url)
        if not tool_name:
            return {"status": "error", "reason": "No suitable tool found by LLM."}
        result = await client.call_tool(tool_name, {"uri": url})
        markdown = extract_markdown_from_result(result)
    chunks = memory_manager.chunk_text(markdown)
    memory_manager.add_to_index(url, chunks)
    summary = generate_summary(markdown)
    return {
        "status": "indexed",
        "url": url,
        "num_chunks": len(chunks),
        "summary": summary
    }

def extract_markdown_from_result(result) -> str:
    """
    Extract markdown from result.
    """
    if isinstance(result, list) and result:
        markdown = getattr(result[0], "text", str(result[0]))
    elif hasattr(result, "text"):
        markdown = result.text
    elif isinstance(result, dict) and "text" in result:
        markdown = result["text"]
    else:
        markdown = str(result)
    return markdown

def search_action(query: str, memory_manager: MemoryManager, k: int = 5) -> dict:
    """
    Search for query in memory manager.
    """
    results = memory_manager.search(query, k)
    context = "\n\n".join([r["chunk"] for r in results])
    source_urls = list({r["url"] for r in results if "url" in r})
    llm_json = generate_summary(context, query, source_urls)
    try:
        parsed = parse_llm_json(llm_json)
        answer = parsed.get("answer", "")
        found_answer = parsed.get("found_answer", False)
        urls = parsed.get("source_urls", source_urls)
    except Exception as e:
        answer = llm_json
        found_answer = False
        urls = source_urls
    return {
        "results": results,
        "answer": answer,
        "found_answer": found_answer,
        "source_urls": urls
    }
