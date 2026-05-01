from __future__ import annotations

import json
import random
from collections import defaultdict, Counter
from pathlib import Path

# Project paths
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"


def clamp(value, low, high):
    """Keep value within range"""
    return max(low, min(high, value))


def generate_sentiment_from_rating(rating: float) -> int:
    """
    Convert rating (1–5) → sentiment (0–100)

    Simple mapping:
    5⭐ → ~90+
    4⭐ → ~75
    3⭐ → ~60
    2⭐ → ~40
    1⭐ → ~20
    """
    base = (rating / 5) * 100
    noise = random.randint(-8, 8)  # small variation
    return int(clamp(base + noise, 10, 95))


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # Load raw data
    products_raw = json.loads((RAW_DIR / "amazon_products_seed.json").read_text())
    reviews_raw = json.loads((RAW_DIR / "amazon_reviews.json").read_text())

    products = []
    reviews = []

    # Map URL → product_id (important for linking reviews)
    url_to_id = {}

    # -------------------------
    # STEP 1: TRANSFORM PRODUCTS
    # -------------------------
    for idx, p in enumerate(products_raw):
        product_id = f"P-{idx+1:03d}"

        price = p.get("price") or random.randint(3000, 8000)

        # Fake list price (since not scraped)
        list_price = int(price * random.uniform(1.2, 1.6))
        discount = int(((list_price - price) / list_price) * 100)

        rating = p.get("rating") or round(random.uniform(3.8, 4.5), 1)

        sentiment = generate_sentiment_from_rating(rating)

        product = {
            "product_id": product_id,
            "brand": p.get("brand"),
            "title": p.get("title"),
            "category": "Luggage",  # placeholder
            "size": random.choice(["55 cm", "65 cm", "75 cm"]),
            "price": price,
            "list_price": list_price,
            "discount_pct": discount,
            "rating": rating,
            "review_count": p.get("review_count") or 0,
            "sentiment": sentiment,
            "positioning": "Amazon marketplace brand",
            "top_pros": [],
            "top_cons": [],
            "amazon_url": p.get("amazon_url"),
        }

        products.append(product)
        url_to_id[p.get("amazon_url")] = product_id

    # -------------------------
    # STEP 2: TRANSFORM REVIEWS
    # -------------------------
    ASPECTS = ["wheels", "handle", "material", "zipper", "size", "durability", "value"]

    for r in reviews_raw:
        product_id = r.get("product_id")

        if not product_id:
            continue

        rating = r.get("rating", 4)
        sentiment = generate_sentiment_from_rating(rating)

        polarity = "positive" if sentiment >= 65 else "negative"

        review = {
            "review_id": f"{product_id}-{random.randint(1000,9999)}",
            "product_id": product_id,
            "brand": r.get("brand"),
            "rating": rating,
            "sentiment": sentiment,
            "aspect": random.choice(ASPECTS),  # simple aspect tagging
            "theme": extract_theme(r.get("review_text")),
            "polarity": polarity,
            "review_text": r.get("review_text"),
        }

        reviews.append(review)

    # -------------------------
    # STEP 3: GENERATE BRAND SUMMARY
    # -------------------------
    by_brand = defaultdict(list)
    reviews_by_brand = defaultdict(list)

    for p in products:
        by_brand[p["brand"]].append(p)

    for r in reviews:
        reviews_by_brand[r["brand"]].append(r)

    summaries = []

    for brand, rows in by_brand.items():
        brand_reviews = reviews_by_brand[brand]

        avg_price = round(sum(p["price"] for p in rows) / len(rows))
        avg_discount = round(sum(p["discount_pct"] for p in rows) / len(rows), 1)
        avg_rating = round(sum(p["rating"] for p in rows) / len(rows), 2)
        sentiment = round(sum(r["sentiment"] for r in brand_reviews) / len(brand_reviews), 1)

        positive = Counter(r["theme"] for r in brand_reviews if r["polarity"] == "positive")
        negative = Counter(r["theme"] for r in brand_reviews if r["polarity"] == "negative")

        summaries.append({
            "brand": brand,
            "avgPrice": avg_price,
            "avgDiscount": avg_discount,
            "avgRating": avg_rating,
            "reviewCount": sum(p["review_count"] for p in rows),
            "sampleReviews": len(brand_reviews),
            "sentiment": sentiment,
            "positioning": "Marketplace brand",
            "topPros": [t for t, _ in positive.most_common(4)],
            "topCons": [t for t, _ in negative.most_common(4)],
            "valueScore": round(sentiment / (avg_price / 1000), 2),
        })

    # -------------------------
    # STEP 4: SAVE FILES
    # -------------------------
    (DATA_DIR / "products.json").write_text(json.dumps(products, indent=2))
    (DATA_DIR / "reviews.json").write_text(json.dumps(reviews, indent=2))
    (DATA_DIR / "brand_summary.json").write_text(json.dumps(summaries, indent=2))

    print("✅ Data transformed for dashboard!")


def extract_theme(text: str) -> str:
    """
    Very simple keyword-based theme extraction
    (You can upgrade this later with NLP/LLM)
    """
    text = text.lower()

    if "wheel" in text:
        return "smooth wheels"
    if "handle" in text:
        return "handle quality"
    if "zip" in text:
        return "zipper issue"
    if "light" in text:
        return "lightweight"
    if "space" in text or "room" in text:
        return "spacious"

    return "general quality"


if __name__ == "__main__":
    main()