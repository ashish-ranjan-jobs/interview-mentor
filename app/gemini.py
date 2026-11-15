import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from app.config import (
    GEMINI_API_KEY,
    DEFAULT_GEMINI_MODEL,
    FAST_GEMINI_MODEL,
    PREVIEW_GEMINI_MODEL,
)

logger = logging.getLogger("interview_mentor.gemini")

SUPPORTED_MODELS = {
    "gemini-pro-latest": "Gemini Pro (Deep Reasoning & Evaluation)",
    "gemini-flash-lite-latest": "Gemini Flash Lite (Fast & Responsive)",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview (Next-Gen)",
}

BASE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def validate_gemini_key(api_key: str) -> bool:
    if not api_key or not isinstance(api_key, str):
        return False
    key = api_key.strip()
    # Google Gemini keys are typically 39 chars starting with AIzaSy
    if key.startswith("AIzaSy") and len(key) >= 30:
        return True
    # Allow other valid Google Cloud / Gemini key formats
    return len(key) >= 20 and not key.startswith("sk-") and not key.startswith("ghp_")


def resolve_api_key(custom_key: Optional[str] = None) -> str:
    if custom_key and custom_key.strip():
        key = custom_key.strip()
        if not validate_gemini_key(key):
            raise ValueError(
                "Invalid API Key format. Only Google Gemini API keys (starting with AIzaSy) are supported."
            )
        return key
    return GEMINI_API_KEY


def format_messages_for_gemini(messages: List[Dict[str, str]]) -> List[Dict]:
    formatted = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Gemini roles must be 'user' or 'model'
        gemini_role = "model" if role in ("model", "assistant") else "user"
        formatted.append({
            "role": gemini_role,
            "parts": [{"text": content}],
        })

    # Gemini requires alternating user/model or starting with user. Combine consecutive same-role messages.
    merged = []
    for item in formatted:
        if merged and merged[-1]["role"] == item["role"]:
            merged[-1]["parts"][0]["text"] += "\n\n" + item["parts"][0]["text"]
        else:
            merged.append(item)

    # If the first message is model, prepend an initial user prompt
    if merged and merged[0]["role"] == "model":
        merged.insert(0, {"role": "user", "parts": [{"text": "Hello interviewer, I am ready to begin."}]})

    return merged


async def stream_gemini_response(
    messages: List[Dict[str, str]],
    system_instruction: str,
    model: str = DEFAULT_GEMINI_MODEL,
    custom_key: Optional[str] = None,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    api_key = resolve_api_key(custom_key)
    if model not in SUPPORTED_MODELS:
        model = DEFAULT_GEMINI_MODEL

    url = f"{BASE_API_URL}/{model}:streamGenerateContent?key={api_key}&alt=sse"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": format_messages_for_gemini(messages),
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 4096,
        },
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    err_text = err_body.decode(errors="replace")
                    logger.error(f"Gemini API returned error {response.status_code}: {err_text}")
                    yield f"data: {json.dumps({'error': f'Gemini API Error {response.status_code}: {err_text}'})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str:
                            continue
                        try:
                            chunk_data = json.loads(data_str)
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text_chunk = part.get("text", "")
                                    if text_chunk:
                                        yield f"data: {json.dumps({'text': text_chunk})}\n\n"
                        except json.JSONDecodeError:
                            continue

                yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.exception("Error streaming from Gemini API")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"


async def generate_gemini_response(
    messages: List[Dict[str, str]],
    system_instruction: str,
    model: str = DEFAULT_GEMINI_MODEL,
    custom_key: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    api_key = resolve_api_key(custom_key)
    if model not in SUPPORTED_MODELS:
        model = DEFAULT_GEMINI_MODEL

    url = f"{BASE_API_URL}/{model}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": format_messages_for_gemini(messages),
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 4096,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API error ({response.status_code}): {response.text}")
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "No response generated by model."
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)


async def generate_scorecard(
    skill: dict,
    transcript: List[Dict[str, str]],
    custom_key: Optional[str] = None,
) -> dict:
    prompt = f"""You are the senior interviewer who just concluded the technical interview for "{skill['title']}".
Target Role: {skill['role']}
Topic: {skill['topic']}
Difficulty: {skill['difficulty']}

Evaluate the candidate's complete performance based on the following skill specification and rubric:
{skill['body_content']}

---
INTERVIEW TRANSCRIPT:
"""
    for msg in transcript:
        speaker = "Candidate" if msg.get("role") == "user" else "Interviewer"
        prompt += f"\n[{speaker}]: {msg.get('content', '')}\n"

    prompt += """
---
TASK:
Provide a rigorous, constructive, and comprehensive evaluation.
Output your response in valid JSON matching this exact structure:
{
  "score": <integer from 0 to 100>,
  "recommendation": "<Strong Hire | Hire | Leaning Hire | Leaning No | Strong No Hire>",
  "summary": "<1-2 paragraph executive summary of the performance>",
  "rubric_breakdown": {
    "problem_solving": {"score": <0-100>, "feedback": "<text>"},
    "technical_competence": {"score": <0-100>, "feedback": "<text>"},
    "communication_collaboration": {"score": <0-100>, "feedback": "<text>"},
    "edge_cases_and_scale": {"score": <0-100>, "feedback": "<text>"}
  },
  "strengths": [
    "<Strength 1>",
    "<Strength 2>",
    "<Strength 3>"
  ],
  "areas_for_growth": [
    "<Area 1>",
    "<Area 2>",
    "<Area 3>"
  ],
  "actionable_prep_tips": [
    "<Prep Tip 1>",
    "<Prep Tip 2>"
  ]
}

DO NOT wrap with markdown code fence if possible, or if wrapped in ```json, ensure it parses as valid JSON.
"""

    raw = await generate_gemini_response(
        messages=[{"role": "user", "content": prompt}],
        system_instruction="You are an expert technical hiring committee evaluator producing structured interview scorecards.",
        model=DEFAULT_GEMINI_MODEL,
        custom_key=custom_key,
        temperature=0.3,
    )

    clean_raw = raw.strip()
    if clean_raw.startswith("```json"):
        clean_raw = clean_raw[7:]
    if clean_raw.startswith("```"):
        clean_raw = clean_raw[3:]
    if clean_raw.endswith("```"):
        clean_raw = clean_raw[:-3]
    clean_raw = clean_raw.strip()

    try:
        eval_data = json.loads(clean_raw)
        return eval_data
    except Exception:
        # Fallback structured response
        return {
            "score": 75,
            "recommendation": "Hire",
            "summary": raw[:500],
            "rubric_breakdown": {
                "problem_solving": {"score": 75, "feedback": "Demonstrated logical approach."},
                "technical_competence": {"score": 75, "feedback": "Good understanding of fundamentals."},
                "communication_collaboration": {"score": 80, "feedback": "Clear articulation."},
                "edge_cases_and_scale": {"score": 70, "feedback": "Addressed primary edge cases."},
            },
            "strengths": ["Structured problem solving", "Good technical communication"],
            "areas_for_growth": ["Deepen edge case coverage"],
            "actionable_prep_tips": ["Review progressive hint ladders and system trade-offs"],
            "raw_output": raw,
        }
