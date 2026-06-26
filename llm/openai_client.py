import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.1,
        )
        return response.output_text.strip()
    except Exception as e:
        return "OPENAI_NOT_AVAILABLE: " + str(e)


def extract_json_safely(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except Exception:
        return None
    return None