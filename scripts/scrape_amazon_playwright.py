import argparse
import time
import json
import os
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.amazon.in/s?k="


def build_search_url(query):
    return BASE_URL + query.replace(" ", "+")


def scrape_brand(page, brand, max_products):
    print(f"\n🔍 Searching: {brand}")
    url = build_search_url(brand)

    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)  # Let JS render

    # CAPTCHA detection (early)
    if "captcha" in page.content().lower() or "Type the characters" in page.content():
        print("❌ Blocked by CAPTCHA. Change IP / use VPN.")
        return []

    # Wait for results
    try:
        page.wait_for_selector(
            "div[data-component-type='s-search-result']",
            timeout=20000
        )
    except:
        print("⚠️ First attempt failed, retrying...")
        page.reload()
        page.wait_for_timeout(4000)
        try:
            page.wait_for_selector(
                "div[data-component-type='s-search-result']",
                timeout=15000
            )
        except:
            print("❌ Failed to load products.")
            page.screenshot(path=f"debug_{brand}.png")
            return []

    products = page.query_selector_all("div[data-component-type='s-search-result']")
    print(f"   Found {len(products)} raw cards")

    results = []

    for item in products:
        if len(results) >= max_products:
            break

        try:
            # ── Title: try multiple selectors ──────────────────────────────
            title = None
            for sel in [
                "h2 a span",
                "h2 span",
                "[data-cy='title-recipe'] span",
                ".a-size-medium.a-color-base.a-text-normal",
                ".a-size-base-plus.a-color-base.a-text-normal",
            ]:
                el = item.query_selector(sel)
                if el:
                    title = el.inner_text().strip()
                    if title:
                        break

            # ── Link ───────────────────────────────────────────────────────
            link = None
            for sel in ["h2 a", "a.a-link-normal[href*='/dp/']"]:
                el = item.query_selector(sel)
                if el:
                    href = el.get_attribute("href")
                    if href:
                        link = "https://www.amazon.in" + href if href.startswith("/") else href
                        break

            # Skip cards with no title or link
            if not title or not link:
                continue

            # ── Price ──────────────────────────────────────────────────────
            price = "N/A"
            for sel in [
                ".a-price .a-offscreen",   # hidden accessible price (most reliable)
                ".a-price-whole",
                "span[data-a-color='base'] .a-offscreen",
            ]:
                el = item.query_selector(sel)
                if el:
                    raw = el.inner_text().strip()
                    if raw:
                        price = raw
                        break

            # ── Rating ─────────────────────────────────────────────────────
            rating = "N/A"
            for sel in [
                ".a-icon-alt",
                "span[aria-label*='out of']",
                "i.a-icon-star-small span",
            ]:
                el = item.query_selector(sel)
                if el:
                    raw = el.inner_text().strip() or el.get_attribute("aria-label") or ""
                    if raw:
                        rating = raw
                        break

            # ── Reviews count ──────────────────────────────────────────────
            reviews = "N/A"
            el = item.query_selector("span[aria-label*='ratings']") or \
                 item.query_selector(".a-size-base.s-underline-text")
            if el:
                reviews = el.inner_text().strip() or el.get_attribute("aria-label") or "N/A"

            results.append({
                "brand": brand,
                "title": title,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "link": link
            })

        except Exception as e:
            print(f"   ⚠️ Skipped a card: {e}")
            continue

    print(f"✅ Scraped {len(results)} products for '{brand}'")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brands", nargs="+", required=True)
    parser.add_argument("--max-products", type=int, default=5)
    args = parser.parse_args()

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        # Hide navigator.webdriver flag
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()

        # Warm-up: visit homepage first to appear more human
        print("🌐 Warming up via amazon.in homepage...")
        page.goto("https://www.amazon.in", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        for brand in args.brands:
            try:
                results = scrape_brand(page, brand, args.max_products)
                all_results.extend(results)
                # Random-ish delay between brands
                delay = 3 + (len(brand) % 3)
                print(f"   ⏳ Waiting {delay}s before next brand...")
                time.sleep(delay)
            except Exception as e:
                print(f"❌ Error scraping '{brand}': {e}")

        browser.close()

    os.makedirs("data", exist_ok=True)
    output_path = "data/products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(all_results)} products → {output_path}")


if __name__ == "__main__":
    main()