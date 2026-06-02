#!/usr/bin/env python3
"""
Meta Ad Library scraper — Playwright + stealth fallback for the
creative-landscape-scorer skill.

Use when the native mcp__meta__meta_ad_library_search tool returns
code 10 (App Review not yet approved — see reference_meta_ad_library_api).

Per feedback_playwright_stealth: always uses playwright-stealth.

USAGE
    python scrape_ad_library.py "Brand Name" [--country US] [--status active|all] [--out DIR]

OUTPUTS (in OUT dir, default C:/tmp/<brand_slug>_ads/)
    <brand_slug>_ads_top.png        — top-of-page screenshot, readable
    <brand_slug>_ads_full.png       — full-page screenshot (often very tall)
    <brand_slug>_ads.html           — raw HTML for grep
    <brand_slug>_ads.json           — {results_text, ad_count, ads:[{text, started, has_video, platforms, links}]}

NOTE
    Meta's search-result count is loose — it matches "brand name" tokens
    anywhere in ad copy across all brands. Always filter the scrape down
    to confirmed-brand ads (visual inspection of screenshots is the
    source of truth, not the result-count integer).
"""
import argparse
import asyncio
import json
import os
import re
import sys
from urllib.parse import quote

from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async  # older API
    _STEALTH_FN = stealth_async
except ImportError:
    from playwright_stealth import Stealth
    _STEALTH_FN = None


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "brand"


async def scrape(brand: str, country: str, status: str, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    slug = _slug(brand)
    url = (
        "https://www.facebook.com/ads/library/"
        f"?active_status={'active' if status == 'active' else 'all'}"
        f"&ad_type=all&country={country.upper()}"
        f"&q={quote(brand)}&search_type=keyword_unordered&media_type=all"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await context.new_page()
        if _STEALTH_FN:
            await _STEALTH_FN(page)
        else:
            await Stealth().apply_stealth_async(page)

        print(f"[scrape] Navigating: {url}", flush=True)
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # Dismiss any cookie/login overlay
        for sel in [
            'div[aria-label*="Close"]',
            'div[role="button"][aria-label*="Decline"]',
            'div[aria-label="Allow all cookies"]',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

        await page.wait_for_timeout(3000)
        page_text = await page.inner_text("body")
        m = re.search(r"(~?\d[\d,]*)\s+results?", page_text)
        results_text = m.group(0) if m else "(no result count)"
        print(f"[scrape] Result count: {results_text}", flush=True)

        # Scroll to load lazy-rendered cards
        for _ in range(10):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1500)

        # Top of page screenshot — most readable
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
        top_path = f"{out_dir}/{slug}_ads_top.png"
        await page.screenshot(path=top_path, full_page=False)
        full_path = f"{out_dir}/{slug}_ads_full.png"
        await page.screenshot(path=full_path, full_page=True)
        html_path = f"{out_dir}/{slug}_ads.html"
        html = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # DOM extraction (selectors are best-effort — Meta's markup shifts;
        # always cross-check with the screenshots).
        ads = await page.evaluate(
            """
            () => {
                // Group by ad-card containers — Meta's CSS class names are
                // hashed and change. Use semantic landmarks and presence of
                // "Library ID" text as the card marker.
                const all = document.querySelectorAll('div');
                const cards = [];
                all.forEach(d => {
                    const t = d.innerText || '';
                    if (/Library ID[:\\s]+\\d{10,}/.test(t.slice(0, 200)) && t.length < 3000) {
                        cards.push(d);
                    }
                });
                return cards.map(c => {
                    const text = c.innerText || '';
                    const startedMatch = text.match(/Started running on ([A-Za-z]+ \\d{1,2}, \\d{4})/);
                    const libMatch = text.match(/Library ID[:\\s]+(\\d{10,})/);
                    const platforms = [];
                    c.querySelectorAll('img[alt]').forEach(img => {
                        const a = img.getAttribute('alt') || '';
                        if (['Facebook','Instagram','Audience Network','Messenger','Threads'].includes(a)
                            && !platforms.includes(a)) platforms.push(a);
                    });
                    return {
                        library_id: libMatch ? libMatch[1] : null,
                        text: text.slice(0, 1500),
                        started: startedMatch ? startedMatch[1] : null,
                        has_video: !!c.querySelector('video') || /watch_video|play_circle/i.test(c.outerHTML),
                        image_count: c.querySelectorAll('img').length,
                        platforms,
                        links: Array.from(c.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(h => !h.includes('facebook.com/ads/library'))
                            .slice(0, 5),
                    };
                });
            }
            """
        )

        # Dedupe by library_id
        seen = set()
        uniq = []
        for ad in ads:
            lid = ad.get("library_id")
            if lid and lid not in seen:
                seen.add(lid)
                uniq.append(ad)

        out = {
            "brand": brand,
            "country": country.upper(),
            "url": url,
            "results_text": results_text,
            "ad_count_rendered": len(uniq),
            "ads": uniq,
        }
        json_path = f"{out_dir}/{slug}_ads.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)

        print(f"[scrape] Done. Rendered {len(uniq)} ads.", flush=True)
        print(f"[scrape] Top screenshot: {top_path}", flush=True)
        print(f"[scrape] Full screenshot: {full_path}", flush=True)
        print(f"[scrape] HTML: {html_path}", flush=True)
        print(f"[scrape] JSON: {json_path}", flush=True)

        await browser.close()
        return out


def main():
    parser = argparse.ArgumentParser(description="Scrape Meta Ad Library (Playwright stealth fallback)")
    parser.add_argument("brand", help="Brand name to search, e.g. 'Flora Fine Foods'")
    parser.add_argument("--country", default="US", help="ISO country code (default: US)")
    parser.add_argument(
        "--status",
        default="active",
        choices=["active", "all"],
        help="active = currently-running ads (default), all = include inactive",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: C:/tmp/<brand_slug>_ads/)",
    )
    args = parser.parse_args()

    out_dir = args.out or f"C:/tmp/{_slug(args.brand)}_ads"
    result = asyncio.run(scrape(args.brand, args.country, args.status, out_dir))
    print(json.dumps({"summary": {k: v for k, v in result.items() if k != "ads"}}, indent=2))


if __name__ == "__main__":
    main()
