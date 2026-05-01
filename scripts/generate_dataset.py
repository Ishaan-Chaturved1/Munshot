from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

BRANDS = {
    "Safari": {
        "base": 4100,
        "discount": 49,
        "rating": 4.12,
        "sentiment": 66,
        "positioning": "Value-focused family travel",
        "pros": ["lightweight body", "roomy packing", "deal pricing", "easy rolling"],
        "cons": ["zipper snags", "shell scuffs", "handle wobble"],
    },
    "Skybags": {
        "base": 4550,
        "discount": 45,
        "rating": 4.18,
        "sentiment": 70,
        "positioning": "Youthful design at accessible prices",
        "pros": ["stylish colors", "smooth wheels", "good compartments", "lightweight body"],
        "cons": ["lock feels basic", "scratches quickly", "zipper snags"],
    },
    "American Tourister": {
        "base": 6250,
        "discount": 39,
        "rating": 4.31,
        "sentiment": 78,
        "positioning": "Premium mass-market reliability",
        "pros": ["durable shell", "smooth wheels", "brand trust", "balanced weight"],
        "cons": ["higher price", "delivery dents", "limited expandability"],
    },
    "VIP": {
        "base": 5750,
        "discount": 35,
        "rating": 4.22,
        "sentiment": 73,
        "positioning": "Established Indian luggage brand",
        "pros": ["sturdy handle", "durable shell", "service network", "classic design"],
        "cons": ["heavy for size", "higher price", "wheel noise"],
    },
    "Aristocrat": {
        "base": 3650,
        "discount": 52,
        "rating": 4.05,
        "sentiment": 62,
        "positioning": "Entry-value volume play",
        "pros": ["low price", "adequate storage", "lightweight body", "frequent deals"],
        "cons": ["thin material", "wheel durability", "handle wobble"],
    },
    "Nasher Miles": {
        "base": 5350,
        "discount": 43,
        "rating": 4.26,
        "sentiment": 76,
        "positioning": "Design-forward value premium",
        "pros": ["distinctive design", "smooth wheels", "roomy packing", "good finish"],
        "cons": ["color mismatch", "zipper stiffness", "limited service"],
    },
}

CATEGORIES = ["Cabin hard luggage", "Medium check-in", "Large check-in", "Soft trolley"]
SIZES = ["55 cm", "65 cm", "75 cm", "78 cm"]
ASPECTS = ["wheels", "handle", "material", "zipper", "size", "durability", "value"]

POSITIVE_TEMPLATES = [
    "The {aspect} felt reliable on a {trip} trip and the {theme} stood out.",
    "Good {theme} for the price; the suitcase handled {trip} travel well.",
    "I liked the {theme}, especially because the {aspect} did not need extra care.",
    "The product feels practical, with {theme} and dependable {aspect}.",
]

NEGATIVE_TEMPLATES = [
    "The {aspect} needs improvement; I noticed {theme} after {trip} use.",
    "Decent suitcase, but the {theme} makes the {aspect} feel less premium.",
    "The price is fine, yet {theme} showed up around the {aspect}.",
    "Useful for short travel, though {theme} affects confidence in the {aspect}.",
]

TRIPS = ["airport", "train", "weekend", "family", "business"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def product_title(brand: str, category: str, size: str, index: int) -> str:
    model = ["Aero", "Nova", "Cruze", "Flex", "Stellar", "Prime", "Orbit", "Neo", "Vector", "Edge"][index % 10]
    return f"{brand} {model} {size} {category}"


def generate() -> tuple[list[dict], list[dict], list[dict]]:
    random.seed(42)
    products: list[dict] = []
    reviews: list[dict] = []
    summaries: list[dict] = []

    for brand, cfg in BRANDS.items():
        for index in range(10):
            category = CATEGORIES[index % len(CATEGORIES)]
            size = SIZES[index % len(SIZES)]
            price = int(clamp(random.gauss(cfg["base"], cfg["base"] * 0.13), 2400, 11500) / 50) * 50
            discount = int(clamp(random.gauss(cfg["discount"], 6), 18, 65))
            list_price = int(price / (1 - discount / 100) / 50) * 50
            rating = round(clamp(random.gauss(cfg["rating"], 0.13), 3.55, 4.75), 1)
            review_count = random.randint(320, 4200)
            sentiment = int(clamp(random.gauss(cfg["sentiment"], 7), 42, 92))
            product_id = f"{brand[:3].upper()}-{index + 1:02d}"
            pros = random.sample(cfg["pros"], 3)
            cons = random.sample(cfg["cons"], 3)
            products.append(
                {
                    "product_id": product_id,
                    "brand": brand,
                    "title": product_title(brand, category, size, index),
                    "category": category,
                    "size": size,
                    "price": price,
                    "list_price": list_price,
                    "discount_pct": discount,
                    "rating": rating,
                    "review_count": review_count,
                    "sentiment": sentiment,
                    "positioning": cfg["positioning"],
                    "top_pros": pros,
                    "top_cons": cons,
                    "amazon_url": "https://www.amazon.in/",
                }
            )

            for review_index in range(12):
                positive = random.random() < sentiment / 100
                theme = random.choice(pros if positive else cons)
                aspect = random.choice(ASPECTS)
                template = random.choice(POSITIVE_TEMPLATES if positive else NEGATIVE_TEMPLATES)
                score = int(clamp(random.gauss(sentiment if positive else sentiment - 24, 9), 15, 96))
                reviews.append(
                    {
                        "review_id": f"{product_id}-R{review_index + 1:02d}",
                        "product_id": product_id,
                        "brand": brand,
                        "rating": int(clamp(round(score / 20), 1, 5)),
                        "sentiment": score,
                        "aspect": aspect,
                        "theme": theme,
                        "polarity": "positive" if positive else "negative",
                        "review_text": template.format(aspect=aspect, theme=theme, trip=random.choice(TRIPS)),
                    }
                )

    by_brand: dict[str, list[dict]] = defaultdict(list)
    reviews_by_brand: dict[str, list[dict]] = defaultdict(list)
    for product in products:
        by_brand[product["brand"]].append(product)
    for review in reviews:
        reviews_by_brand[review["brand"]].append(review)

    for brand, rows in by_brand.items():
        brand_reviews = reviews_by_brand[brand]
        positive = Counter(r["theme"] for r in brand_reviews if r["polarity"] == "positive")
        negative = Counter(r["theme"] for r in brand_reviews if r["polarity"] == "negative")
        avg_price = round(sum(p["price"] for p in rows) / len(rows))
        avg_discount = round(sum(p["discount_pct"] for p in rows) / len(rows), 1)
        avg_rating = round(sum(p["rating"] for p in rows) / len(rows), 2)
        sentiment = round(sum(r["sentiment"] for r in brand_reviews) / len(brand_reviews), 1)
        summaries.append(
            {
                "brand": brand,
                "avgPrice": avg_price,
                "avgDiscount": avg_discount,
                "avgRating": avg_rating,
                "reviewCount": sum(p["review_count"] for p in rows),
                "sampleReviews": len(brand_reviews),
                "sentiment": sentiment,
                "positioning": BRANDS[brand]["positioning"],
                "topPros": [name for name, _ in positive.most_common(4)],
                "topCons": [name for name, _ in negative.most_common(4)],
                "valueScore": round(sentiment / (avg_price / 1000), 2),
            }
        )

    return products, reviews, sorted(summaries, key=lambda item: item["brand"])


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    products, reviews, summaries = generate()
    for name, rows in {
        "products": products,
        "reviews": reviews,
        "brand_summary": summaries,
    }.items():
        write_json(DATA_DIR / f"{name}.json", rows)
        write_csv(DATA_DIR / f"{name}.csv", rows)
    print(f"Wrote {len(products)} products, {len(reviews)} reviews, {len(summaries)} brand summaries.")


if __name__ == "__main__":
    main()
