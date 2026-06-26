import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"

def call_ollama(prompt: str, model: str = DEFAULT_MODEL, temperature: float = 0.1) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return "OLLAMA_NOT_AVAILABLE: " + str(e)

def extract_json_safely(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except Exception:
        return None
    return None
