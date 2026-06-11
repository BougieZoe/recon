from openai import OpenAI

client = OpenAI(
    api_key="sk-1b8385467da1478bb26c26dab92f7e2f",
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = (
    "You are a top-tier intelligence analyst.\n"
    "You receive fragmented public data about a person.\n"
    "Output a structured intent map as JSON only — no preamble, no markdown.\n"
    "\n"
    "Required fields:\n"
    "{\n"
    '  "core_drive": "one sentence — what is this person fundamentally fighting for",\n'
    '  "recurring_signals": ["topics/words/emotions appearing 3+ times"],\n'
    '  "workarounds": ["clumsy detours they use — reveals real pain points"],\n'
    '  "direction": "where are they heading based on last 6 months of signals",\n'
    '  "contact_window": "what topic or framing would make them stop and look for 2 seconds",\n'
    '  "confidence": 0-100,\n'
    '  "data_quality": "high | medium | low"\n'
    "}"
)


def analyze_person(raw_text: str) -> dict:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is the collected public data:\n\n{raw_text[:8000]}"},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    content = response.choices[0].message.content.strip()
    import json
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "core_drive": "analysis failed — could not parse AI response",
            "recurring_signals": [],
            "workarounds": [],
            "direction": content[:500],
            "contact_window": "",
            "confidence": 0,
            "data_quality": "low",
        }
