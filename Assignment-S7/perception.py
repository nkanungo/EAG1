from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

load_dotenv()

# Configure the API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class PerceptionResult(BaseModel):
    user_input: str
    intent: Optional[str] = None  # Make intent optional with default None
    entities: List[str] = []
    tool_hint: Optional[str] = None


def extract_perception(user_input: str) -> PerceptionResult:
    """Extracts intent, entities, and tool hints using LLM"""

    try:
        # For summarization requests, set a default intent
        if user_input.lower().startswith("please summarize"):
            return PerceptionResult(
                user_input=user_input,
                intent="summarize",
                entities=[],
                tool_hint="summarize_text"
            )

        prompt = f"""
You are an AI that extracts structured facts from user input.

Input: "{user_input}"

Return the response as a Python dictionary with keys:
- intent: (brief phrase about what the user wants)
- entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"])
- tool_hint: (name of the MCP tool that might be useful, if any)

Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. Ensure `entities` is a list of strings, not a dictionary.
    """

        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        raw = response.text.strip()
        log("perception", f"LLM output: {raw}")

        # Strip Markdown backticks if present
        clean = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()

        try:
            parsed = eval(clean)
        except Exception as e:
            log("perception", f"⚠️ Failed to parse cleaned output: {e}")
            # Return a default perception result if parsing fails
            return PerceptionResult(user_input=user_input)

        # Fix common issues
        if isinstance(parsed.get("entities"), dict):
            parsed["entities"] = list(parsed["entities"].values())

        return PerceptionResult(user_input=user_input, **parsed)

    except Exception as e:
        log("perception", f"⚠️ Extraction failed: {e}")
        # Return a default perception result if extraction fails
        return PerceptionResult(user_input=user_input)
