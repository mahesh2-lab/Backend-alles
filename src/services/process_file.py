import re
import json
import os
from typing import Any, Optional
from pdfminer.high_level import extract_text
from src.schemas.evaluation import EvaluationOut
from openai import OpenAI
from .read_prompt import read_prompt
from dotenv import load_dotenv
from src.utils.keymanager import KeyManager

load_dotenv()

# single KeyManager instance used for rotation
key_manager = KeyManager()


def generate_content(text: str, job_description: str, retries: int = 3):
    """Generate structured content for a resume using an LLM with key rotation and retries.

    - Uses `KeyManager` to rotate API keys on failures (401/429/5xx or exceptions).
    - Preserves the previous behavior of extracting a JSON block from the model response.
    """
    SYSTEM_PROMPT = read_prompt(job_description)

    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        key = key_manager.get_active_key()
        print(
            f"🗝️ Using API key: {key[:8]}... (Attempt {attempt + 1}/{retries})")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )

        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": text}]},
                ],
            )

            response_text = completion.choices[0].message.content or ""

            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(
                    r'```json\s*([\s\S]*?)\s*```', response_text)

                final_response = (
                    json.loads(json_match.group(1))
                    if json_match
                    else {"error": "No valid JSON response found", "raw": response_text}
                )

                return final_response

        except Exception as e:
            # Try to inspect attribute-based status where available
            last_exc = e
            status_code = None
            try:
                # Some OpenAI clients include a .status_code or .http_status
                status_code = getattr(e, "status_code", None) or getattr(
                    e, "http_status", None)
            except Exception:
                status_code = None

            if status_code == 401:
                key_manager.mark_key_as_failed(key)
                continue

            if status_code in (429,) or (status_code and 500 <= int(status_code) < 600):
                key_manager.mark_key_as_failed(key)
                continue

            # If we cannot determine a status code, conservatively mark the key failed for network/other errors
            key_manager.mark_key_as_failed(key)
            continue

    # If we exit the loop without returning, all retries failed
    raise RuntimeError("🚨 All API keys failed after retries.") from last_exc


def parse_resume(file_path: str, job_description: str):
    text = extract_text(file_path)
    result = generate_content(text, job_description)
    return result
