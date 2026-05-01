from __future__ import annotations

import json
import requests
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------
# LOAD ENV
# -------------------------

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

MODEL = "llama-3.1-8b-instant"

# -------------------------
# PATHS
# -------------------------

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"

# -------------------------
# PROMPT
# -------------------------

def build_prompt(review: str) -> str:
    return f"""
Analyze this review and return ONLY JSON:

{{
  "sentiment": number (0-100),
  "aspect": one of [wheels, handle, material, zipper, size, durability, value],
  "theme": short phrase (2-4 words),
  "polarity": positive or negative
}}

Review:
"{review}"
"""

# -------------------------
# FALLBACK
# -------------------------

def fallback():
    return {
        "sentiment": 60,
        "aspect": "value",
        "theme": "general feedback",
        "polarity": "positive"
    }

# -------------------------
# GROQ API CALL (RATE LIMIT SAFE)
# -------------------------

def analyze_review(review: str):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": build_prompt(review)}],
        "temperature": 0.2,
    }

    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=payload)
            result = res.json()

            # Handle rate limit
            if "error" in result:
                print("⏳ Rate limit hit, retrying...")
                time.sleep(3)
                continue

            if "choices" not in result:
                print("⚠️ Unexpected response:", result)
                return fallback()

            content = result["choices"][0]["message"]["content"].strip()

            # Clean markdown
            if "```" in content:
                content = content.split("```")[-1]

            return json.loads(content)

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(2)

    return fallback()

# -------------------------
# MAIN PIPELINE
# -------------------------

def main():
    DATA_DIR.mkdir(exist_ok=True)

    input_file = RAW_DIR / "amazon_reviews.json"

    if not input_file.exists():
        print("⚠️ Run review generator first!")
        return

    reviews_raw = json.loads(input_file.read_text())

    # 🔥 LIMIT REVIEWS (prevents rate limit)
    reviews_raw = reviews_raw[:50]

    enriched_reviews = []

    for idx, r in enumerate(reviews_raw):
        print(f"Processing {idx+1}/{len(reviews_raw)}")

        review_text = r.get("review_text", "")[:500]

        analysis = analyze_review(review_text)

        enriched_reviews.append({
            "review_id": f"R-{idx+1:04d}",
            "product_id": r.get("product_id"),
            "brand": r.get("brand"),
            "rating": r.get("rating"),
            "review_text": review_text,
            "sentiment": analysis.get("sentiment", 60),
            "aspect": analysis.get("aspect", "value"),
            "theme": analysis.get("theme", "general"),
            "polarity": analysis.get("polarity", "positive"),
        })

        # 🔥 SAFE DELAY (avoid rate limit)
        time.sleep(2.5)

    output_file = DATA_DIR / "reviews.json"
    output_file.write_text(json.dumps(enriched_reviews, indent=2))

    print(f"\n✅ Saved {len(enriched_reviews)} enriched reviews to {output_file}")

# -------------------------
# START
# -------------------------

if __name__ == "__main__":
    main()