from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"

POSITIVE_REVIEWS = [
    "Wheels are very smooth and easy to roll",
    "Good quality material and sturdy build",
    "Spacious design, fits everything",
    "Lightweight and easy to carry",
    "Great value for money",
]

NEGATIVE_REVIEWS = [
    "Zipper feels weak and gets stuck",
    "Handle is not very strong",
    "Material quality is average",
    "Wheels are not smooth",
    "Not worth the price",
]


def generate_review(rating):
    if rating >= 4:
        return random.choice(POSITIVE_REVIEWS)
    else:
        return random.choice(NEGATIVE_REVIEWS)


def main():
    input_file = RAW_DIR / "amazon_products_seed.json"

    if not input_file.exists():
        print("Run product scraper first!")
        return

    products = json.loads(input_file.read_text())

    all_reviews = []

    for idx, p in enumerate(products):
        product_id = f"P-{idx+1:03d}"
        brand = p.get("brand")

        num_reviews = random.randint(8, 15)

        for _ in range(num_reviews):
            rating = round(random.uniform(3.0, 5.0), 1)

            all_reviews.append({
                "product_id": product_id,
                "brand": brand,
                "review_text": generate_review(rating),
                "rating": rating
            })

    output = RAW_DIR / "amazon_reviews.json"
    output.write_text(json.dumps(all_reviews, indent=2))

    print(f"✅ Generated {len(all_reviews)} reviews")


if __name__ == "__main__":
    main()