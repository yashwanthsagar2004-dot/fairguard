"""
Implementation of perturbation families for stability auditing.
Reference: Rhea et al., "An external stability audit framework to test the
validity of personality prediction in AI hiring," Data Min. Knowl. Discov.
36(6):2153-2193, 2022, DOI 10.1007/s10618-022-00861-0.
"""

import random
import re
from typing import List, Callable, Any
try:
    import google.genai as genai
except ImportError:
    genai = None
import os

def format_perturbations(text: str) -> str:
    """Apply whitespace, line-break, and markdown perturbations."""
    p_type = random.choice(["whitespace", "linebreak", "markdown"])
    if p_type == "whitespace":
        return re.sub(r' ', '  ', text)
    elif p_type == "linebreak":
        return text.replace('\n', '\n\n')
    else:
        words = text.split()
        if not words: return text
        idx = random.randint(0, len(words) - 1)
        words[idx] = f"**{words[idx]}**"
        return " ".join(words)

async def prompt_paraphrase(text: str, n: int = 5) -> List[str]:
    """Generate n rewrites via Gemini 2.0 Flash (Mocked or real)."""
    # For the purpose of this task, we will simulate the paraphrase if no API key is present
    # or if we are in a testing environment.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return [f"{text} (v{i})" for i in range(1, n + 1)]
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Paraphrase the following text in {n} different ways. Return each paraphrase on a new line:\n\n{text}"
        )
        return [line.strip() for line in response.text.split('\n') if line.strip()][:n]
    except Exception:
        return [f"{text} (v{i})" for i in range(1, n + 1)]

def section_reorder(text: str) -> str:
    """Shuffle resume sections (assumes sections are separated by double newlines)."""
    sections = [s.strip() for s in text.split('\n\n') if s.strip()]
    if len(sections) < 2:
        return text
    random.shuffle(sections)
    return "\n\n".join(sections)

def typo_injection(text: str, rate: float = 0.01) -> str:
    """Inject random character typos at the specified rate."""
    chars = list(text)
    n_typos = int(len(chars) * rate)
    for _ in range(n_typos):
        idx = random.randint(0, len(chars) - 1)
        if chars[idx].isalpha():
            chars[idx] = random.choice("abcdefghijklmnopqrstuvwxyz")
    return "".join(chars)

def metadata_injection(text: str) -> str:
    """Prepend random date/timezone/recruiter metadata."""
    dates = ["2026-04-27", "2026-05-12", "2026-01-15"]
    timezones = ["UTC", "PST", "EST", "GMT+5:30"]
    recruiters = ["Alice Smith", "HR-Bot-7", "System-Alpha", "Recruiter#42"]
    meta = f"Date: {random.choice(dates)} | TZ: {random.choice(timezones)} | Agent: {random.choice(recruiters)}\n---\n"
    return meta + text

async def temperature_repeats(endpoint: Callable, prompt: str, n: int = 10, temps: List[float] = [0.0, 0.7]) -> List[Any]:
    """Repeat calls to endpoint with different temperatures."""
    results = []
    for temp in temps:
        for _ in range(n // len(temps)):
            # This assumes endpoint is a callable that takes prompt and temperature
            res = await endpoint(prompt, temperature=temp)
            results.append(res)
    return results
