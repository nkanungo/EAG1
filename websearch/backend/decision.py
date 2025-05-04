# coding: utf-8
"""
Decision logic for tool selection and LLM-based summarization.
"""

import os
import json
import re
import requests

def parse_llm_json(llm_json):
    """
    Remove markdown code block if present and parse JSON.
    """
    match = re.search(r'{.*}', llm_json, re.DOTALL)
    if match:
        llm_json = match.group(0)
    return json.loads(llm_json)

def generate_summary(markdown: str, query: str = None, source_urls=None) -> str:
    """
    Call Gemini-2.0-Flash to summarize or answer a question with provided context. Returns JSON format.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + api_key
    if source_urls is None:
        source_urls = []
    urls_json = json.dumps(source_urls, ensure_ascii=False)
    if query:
        prompt = (
            "You are a helpful assistant. Given the following CONTEXT from a web page, answer the user's QUESTION in your own words, providing a clear, detailed, and helpful response. Do NOT copy the context verbatim. Always respond ONLY in the following JSON format (no explanation, no markdown, no commentary):\n"
            '{"answer": "<your detailed answer here>", "found_answer": true/false, "source_urls": ' + urls_json + '}'
            f"\nCONTEXT:\n{markdown}\n\nQUESTION: {query}"
        )
    else:
        prompt = (
            "Summarize the following content in a clear and friendly manner in JSON format (do NOT copy the context, use your own words):\n"
            '{"answer": "<summary>", "found_answer": true, "source_urls": ' + urls_json + '}'
            f"\nCONTEXT:\n{markdown}"
        )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return json.dumps({"answer": f"[Gemini API error: {e}]", "found_answer": False, "source_urls": []})

def select_tool_for_task(tools, user_input):
    """
    Given a list of tools (as dicts with name/description), and a user input (could be URL, file path, text, etc.),
    use the LLM to select the best tool for the task. Returns the tool name (string) or None if not found.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + api_key
    tools_json = json.dumps([
        {"name": t.name, "description": getattr(t, 'description', '')} for t in tools
    ], ensure_ascii=False)
    prompt = (
        "You are an autonomous agent. Here is a list of available tools (with descriptions):\n"
        f"{tools_json}\n"
        f"The user provided the following input: {user_input}.\n"
        "Based on this information, which tool should be used? Respond ONLY with the tool name as a plain string."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        tool_name = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"')
        return tool_name
    except Exception as e:
        return None
