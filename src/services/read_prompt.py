from pathlib import Path
from typing import Optional




def read_prompt(job_description: str) -> str:
    """Read the system PROMPT file and inject a dynamic required match threshold.

    If no threshold is provided, DEFAULT_THRESHOLD is used.
    Replaces the placeholder {{required_match_threshold}} in the prompt text.
    """
    base = Path(__file__).resolve().parent  # src/services
    prompt_path = base.parent / "utils" / "PROMPT"
    

    try:
        content = prompt_path.read_text(encoding="utf-8")
        content = content.replace(
            "{{job_description}}", job_description.strip() or "N/A"
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"PROMPT file not found at: {prompt_path}") from None
    except Exception as e:
        raise RuntimeError(
            f"Error reading PROMPT file at {prompt_path}: {e}") from e

    return content



