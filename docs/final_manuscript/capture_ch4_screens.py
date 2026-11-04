"""Capture the Chapter 4 screenshots (Figures 5 to 10) from a LOCAL copy of the
system running on the anonymized demo data (ml/_hmap_db_demo_*.sql), with the
development login (stub mode, "CESU Administrator"). No real patient data.

Prerequisites (see the Ch.4 notes): MariaDB on 127.0.0.1:3399 loaded with the
demo dump, `php artisan serve --port 8000` with DB_DATABASE=hmap_db_demo and
HMAP_HRMO_MODE=stub, and the ML service on 127.0.0.1:5050.

Locally, Laravel serves the API at /api (on the server nginx strips /hmap),
so requests to /hmap/api/... and /hmap/barangays.geojson are redirected.

    python docs/final_manuscript/capture_ch4_screens.py
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://localhost:8000"   # must match ASSET_URL in laravel/.env, or the scripts are blocked
OUT = Path(__file__).parent / "figures" / "ch4" / "screens"
OUT.mkdir(parents=True, exist_ok=True)
YEAR, WEEK = "2025", "5"


async def rewrite(route):
    url = route.request.url
    for a, b in (("/hmap/api/", "/api/"), ("/hmap/barangays.geojson", "/barangays.geojson")):
        if a in url:
            await route.continue_(url=url.replace(a, b))
            return
    await route.continue_()


async def settle(page, seconds=2.5):
    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        pass
    await asyncio.sleep(seconds)


async def set_year_week(page):
    nums = page.locator('input[type="number"]')
    await nums.nth(0).fill(YEAR)
    await nums.nth(1).fill(WEEK)
    await nums.nth(1).press("Tab")
    await settle(page, 3.5)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        # Light theme for print; the trend chart in its histogram (epidemic curve) view
        await ctx.add_init_script("localStorage.setItem('hmap.theme', 'light');"
                                  "localStorage.setItem('hmap.trend.view', 'histogram');")
        page = await ctx.new_page()
        await page.route("**/*", rewrite)

        # Figure 5: dashboard
        await page.goto(f"{BASE}/hmap", wait_until="domcontentloaded")
        await page.wait_for_selector("text=Geographic distribution", timeout=30_000)
        await set_year_week(page)
        await page.screenshot(path=str(OUT / "dashboard.png"))
        print("dashboard.png")

        # Figure 9: risk tiers (map) and recommended response
        # the sticky header would cover the top of a cropped panel
        style = await page.add_style_tag(content="header { position: static !important; }")
        panel = page.locator("section", has=page.locator("h2", has_text="Recommended response"))
        await panel.scroll_into_view_if_needed()
        await settle(page, 1.5)
        await panel.screenshot(path=str(OUT / "recommendations.png"))
        print("recommendations.png")
        await style.evaluate("el => el.remove()")
        await page.evaluate("window.scrollTo(0, 0)")

        # Figure 6: case entry form
        await page.get_by_role("button", name="Case Entry").click()
        await settle(page)
        await page.screenshot(path=str(OUT / "case_entry.png"))
        print("case_entry.png")

        # Figure 7: weekly report, Category I and II summary
        await page.get_by_role("button", name="Weekly Report").click()
        await page.wait_for_selector("text=Summary (Cat I + II)", timeout=20_000)
        await set_year_week(page)
        await page.screenshot(path=str(OUT / "weekly_report.png"))
        print("weekly_report.png")

        # Figure 8: hotspot (cluster) map, 2025, first cluster selected
        await page.get_by_role("button", name="Clusters").click()
        await page.wait_for_selector("text=Dengue Clusters", timeout=20_000)
        await settle(page)
        await page.locator("select").first.select_option(YEAR)
        await settle(page, 3.5)
        first = page.locator("text=/^\\d+ cases$/").first
        if await first.count():
            await first.click()
            await settle(page, 2.5)
        await page.screenshot(path=str(OUT / "cluster_map.png"))
        print("cluster_map.png")

        # Figure 10: alerts menu over the Reports page
        await page.get_by_role("button", name="Reports").click()
        await settle(page)
        await page.get_by_role("button", name="Alerts").click()
        await settle(page, 1.5)
        await page.screenshot(path=str(OUT / "alerts.png"))
        print("alerts.png")

        await browser.close()


asyncio.run(main())
