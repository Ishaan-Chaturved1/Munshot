from __future__ import annotations

import json
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

MODEL = "llama-3.1-8b-instant"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


# -------------------------
# BUILD PROMPT
# -------------------------

def build_prompt(summary_data):
    return f"""
You are a product intelligence analyst.

Analyze this luggage market data and generate 5 sharp insights.

Each insight must:
- Be specific
- Compare brands
- Explain WHY something is happening
- Be useful for decision-making

Return ONLY JSON:

[
  {{
    "title": "...",
    "body": "..."
  }}
]

DATA:
{json.dumps(summary_data, indent=2)}
"""


# -------------------------
# GROQ CALL
# -------------------------

def generate_insights(summary_data):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": build_prompt(summary_data)}
        ],
        "temperature": 0.4
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        result = res.json()

        content = result["choices"][0]["message"]["content"]

        # clean formatting
        content = content.strip()
        if "```" in content:
            content = content.split("```")[-1]

        return json.loads(content)

    except Exception as e:
        print("LLM error:", e)
        return []


# -------------------------
# MAIN
# -------------------------

def main():
    summary_file = DATA_DIR / "brand_summary.json"

    if not summary_file.exists():
        print("Run transform script first!")
        return

    summaries = json.loads(summary_file.read_text())

    insights = generate_insights(summaries)

    output_file = DATA_DIR / "agent_insights.json"
    output_file.write_text(json.dumps(insights, indent=2))

    print("✅ Agent insights generated!")


if __name__ == "__main__":
    main()