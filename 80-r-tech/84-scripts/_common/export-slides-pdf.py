"""
RXR Master Framework Slides → PDF (Playwright)
Usage: python export-slides-pdf.py
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

HTML = Path(__file__).parent / "rxr-master-framework-slides.html"
PDF  = Path(__file__).parent / "rxr-master-framework-slides.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(HTML.as_uri())
    page.wait_for_timeout(2000)  # 폰트 로딩 대기

    page.pdf(
        path=str(PDF),
        width="1280px",
        height="720px",
        print_background=True,
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
    )
    browser.close()
    print(f"PDF saved: {PDF}")
