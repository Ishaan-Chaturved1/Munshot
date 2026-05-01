from __future__ import annotations

import json
import time
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

# -------------------------
# PATHS
# -------------------------

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"

# -------------------------
# CONFIG
# -------------------------

MAX_REVIEWS_PER_PRODUCT = 10  # keep small

# -------------------------
# HELPERS
# -------------------------

def safe_text(locator):
    try:
        return locator.inner_text(timeout=3000)
    except:
        return None


# -------------------------
# SCRAPE REVIEWS
# -------------------------

def scrape_reviews_for_product(page, product_url: str, product_id: str, brand: str):
    reviews_data = []

    try:
        print(f"\n🔗 Opening product: {product_url}")

        page.goto(product_url, wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 4))

        # -------------------------
        # CAPTCHA CHECK
        # -------------------------
        if "captcha" in page.url.lower():
            print("🚨 CAPTCHA detected! Solve it manually in browser")
            input("Press ENTER after solving captcha...")

        # -------------------------
        # TRY CLICKING "SEE ALL REVIEWS"
        # -------------------------
        try:
            print("➡️ Clicking 'See all reviews'")
            page.locator("text=See all reviews").first.click()
            time.sleep(3)
        except:
            print("⚠️ Button not found, using fallback URL")

            if "/dp/" in product_url:
                pid = product_url.split("/dp/")[1].split("/")[0]
                page.goto(f"https://www.amazon.in/product-reviews/{pid}")
                time.sleep(3)
            else:
                return []

        # -------------------------
        # SCROLL (IMPORTANT)
        # -------------------------
        page.mouse.wheel(0, 3000)
        time.sleep(2)

        # -------------------------
        # SCRAPE REVIEWS
        # -------------------------
        while len(reviews_data) < MAX_REVIEWS_PER_PRODUCT:

            try:
                page.wait_for_selector("div[data-hook='review']", timeout=8000)
            except:
                print("❌ No reviews found (possibly blocked)")
                break

            review_blocks = page.locator("div[data-hook='review']")
            count = review_blocks.count()

            print(f"Found {count} reviews on page")

            if count == 0:
                break

            for i in range(count):
                r = review_blocks.nth(i)

                try:
                    text = safe_text(r.locator("[data-hook='review-body']"))
                    rating_text = safe_text(r.locator("[data-hook='review-star-rating']"))

                    rating = float(rating_text.split()[0]) if rating_text else None

                    if text:
                        reviews_data.append({
                            "product_id": product_id,
                            "brand": brand,
                            "review_text": text.strip(),
                            "rating": rating
                        })

                    if len(reviews_data) >= MAX_REVIEWS_PER_PRODUCT:
                        break

                except:
                    continue

            # -------------------------
            # NEXT PAGE
            # -------------------------
            next_btn = page.locator("li.a-last a")

            if next_btn.count() == 0:
                print("No more pages")
                break

            try:
                next_btn.click()
                time.sleep(random.uniform(2, 4))
            except:
                break

    except Exception as e:
        print(f"❌ Error: {e}")

    return reviews_data


# -------------------------
# MAIN
# -------------------------

def main():
    RAW_DIR.mkdir(exist_ok=True)

    input_file = RAW_DIR / "amazon_products_seed.json"

    if not input_file.exists():
        print("⚠️ Run product scraper first!")
        return

    products = json.loads(input_file.read_text())

    all_reviews = []

    with sync_playwright() as p:
        # 🔥 IMPORTANT: headless=False (human-like)
        browser = p.chromium.launch(headless=False)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            ),
            locale="en-IN"
        )

        for idx, product in enumerate(products):
            product_url = product.get("amazon_url")
            brand = product.get("brand")

            if not product_url or "/dp/" not in product_url:
                print(f"⚠️ Skipping invalid URL: {product_url}")
                continue

            product_id = f"P-{idx+1:03d}"

            print(f"\n📦 Scraping {brand} | {product_id}")

            reviews = scrape_reviews_for_product(
                page, product_url, product_id, brand
            )

            print(f"✅ Got {len(reviews)} reviews")

            all_reviews.extend(reviews)

            time.sleep(random.uniform(3, 5))

        browser.close()

    # -------------------------
    # SAVE
    # -------------------------
    output_file = RAW_DIR / "amazon_reviews.json"
    output_file.write_text(json.dumps(all_reviews, indent=2), encoding="utf-8")

    print(f"\n🎉 Saved {len(all_reviews)} reviews to {output_file}")


if __name__ == "__main__":
    main()