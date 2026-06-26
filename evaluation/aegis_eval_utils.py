import re
import json
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
PHASE_OUTPUTS = ROOT / "phase_outputs"
PHASE_OUTPUTS.mkdir(exist_ok=True)

GPT4O_MINI_INPUT_PER_1M = 0.15
GPT4O_MINI_OUTPUT_PER_1M = 0.60


def estimate_tokens(text):
    return max(1, int(len(str(text or "")) / 4))


def estimate_openai_cost(prompt_text, output_text):
    input_tokens = estimate_tokens(prompt_text)
    output_tokens = estimate_tokens(output_text)

    cost = (
        (input_tokens / 1_000_000) * GPT4O_MINI_INPUT_PER_1M
        + (output_tokens / 1_000_000) * GPT4O_MINI_OUTPUT_PER_1M
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
    }


def normalize(text):
    return re.sub(r"[^a-z0-9 ]+", " ", str(text).lower()).strip()


def rca_match_score(expected, predicted):
    e = normalize(expected)
    p = normalize(predicted)

    if not e or not p:
        return 0.0

    if e in p or p in e:
        return 1.0

    e_tokens = set(e.split())
    p_tokens = set(p.split())

    overlap = len(e_tokens & p_tokens) / max(1, len(e_tokens))
    fuzzy = SequenceMatcher(None, e, p).ratio()

    return round(max(overlap, fuzzy), 3)


def is_correct(expected, predicted, threshold=0.55):
    return int(rca_match_score(expected, predicted) >= threshold)


def get_text_from_result(result):
    if isinstance(result, dict):
        for key in ["probable_root_cause", "root_cause", "rca", "analysis", "answer"]:
            if key in result and result[key]:
                return str(result[key])
        return json.dumps(result, default=str)
    return str(result)


def get_confidence(result):
    if isinstance(result, dict):
        value = result.get("confidence") or result.get("rca_confidence") or 0.75
        try:
            if isinstance(value, str) and "%" in value:
                return float(value.replace("%", "")) / 100
            return float(value)
        except Exception:
            return 0.75
    return 0.70


def security_score(phase):
    if phase == "phase3":
        return 7
    return 10


def retrieval_precision(retrieved_items, expected_root_cause):
    if not retrieved_items:
        return 0.0

    expected = normalize(expected_root_cause)
    hits = 0

    for item in retrieved_items:
        text = normalize(json.dumps(item, default=str))
        if any(token in text for token in expected.split()):
            hits += 1

    return round(hits / len(retrieved_items), 3)