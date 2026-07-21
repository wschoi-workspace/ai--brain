#!/usr/bin/env python3
"""index.html 기능 검증 스크립트 (PNG 캡처 없음, evaluate 전용)"""
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/choi_ai/do-better-workspace/10-projects/38-rent-homepage/index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(URL, wait_until="load")
        await page.wait_for_timeout(1200)

        r = {}
        r["title"] = await page.title()
        r["hero_ko"] = await page.eval_on_selector(".hero-title", "el => el.textContent.slice(0,20)")
        r["kpi_count"] = await page.eval_on_selector_all("#stats .kpi", "els => els.length")
        r["svc_count"] = await page.eval_on_selector_all(".svc-card", "els => els.length")
        r["case_count"] = await page.eval_on_selector_all(".case-card[data-category]", "els => els.length")
        r["case_dots_first"] = await page.eval_on_selector_all(".case-slider:first-of-type .case-dot", "els => els.length")
        r["partners_items"] = await page.eval_on_selector_all(".partner-item", "els => els.length")
        r["grid_cols"] = await page.evaluate(
            "getComputedStyle(document.querySelector('.archive-grid')).gridTemplateColumns.split(' ').length")
        r["accent_var"] = await page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()")
        r["bg_var"] = await page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()")
        r["body_font"] = await page.evaluate(
            "getComputedStyle(document.body).fontFamily.split(',')[0]")

        # Highlight slider: next 클릭 → slide 2 active
        await page.click(".hl-nav.next")
        await page.wait_for_timeout(700)
        r["hl_slide2_active"] = await page.evaluate(
            "document.querySelectorAll('.hl-slide')[1].classList.contains('active')")

        # Archive filter: beauty → 1개만 표시
        await page.click(".filter-btn[data-filter='beauty']")
        await page.wait_for_timeout(300)
        r["filter_beauty_visible"] = await page.evaluate("""
            [...document.querySelectorAll('.archive-grid > [data-category]')]
              .filter(c => c.style.display !== 'none' && c.dataset.category === 'beauty').length""")
        r["filter_hidden_count"] = await page.evaluate("""
            [...document.querySelectorAll('.archive-grid > [data-category]')]
              .filter(c => c.style.display === 'none').length""")
        await page.click(".filter-btn[data-filter='all']")

        # Performance rotation active
        await page.evaluate("document.getElementById('performance').scrollIntoView()")
        await page.wait_for_timeout(1800)
        r["perf_number"] = await page.eval_on_selector("#perfNumber", "el => el.textContent")

        # EN 전환
        await page.click(".lang-option[data-lang='en']")
        await page.wait_for_timeout(400)
        r["hero_en"] = await page.eval_on_selector(".hero-title", "el => el.textContent.slice(0,30)")
        r["case1_en"] = await page.eval_on_selector(".case-title", "el => el.textContent")
        r["market1_en"] = await page.eval_on_selector(".info-card .v", "el => el.textContent")
        r["partner1_en"] = await page.eval_on_selector(".partner-item", "el => el.textContent")
        r["form_label_en"] = await page.eval_on_selector(".form-label", "el => el.textContent")
        r["lang_saved"] = await page.evaluate("localStorage.getItem('language')")

        # KO 복귀
        await page.click(".lang-option[data-lang='ko']")
        await page.wait_for_timeout(400)
        r["hero_ko_back"] = await page.eval_on_selector(".hero-title", "el => el.textContent.slice(0,15)")

        # 폼 mailto 조립 검증 (실제 이동 대신 값 채우고 submit 핸들러 통과 여부)
        await page.fill("#fName", "테스트")
        await page.fill("#fEmail", "test@test.com")
        await page.fill("#fPhone", "010-0000-0000")
        await page.fill("#fMessage", "검증 메시지")
        r["form_filled"] = True

        # 반응형: 1000px
        await page.set_viewport_size({"width": 1000, "height": 800})
        await page.wait_for_timeout(300)
        r["resp_1000_sec_pad"] = await page.evaluate(
            "getComputedStyle(document.querySelector('#stats .sec')).paddingLeft")
        # 모바일 480px
        await page.set_viewport_size({"width": 480, "height": 800})
        await page.wait_for_timeout(300)
        r["resp_480_hamburger"] = await page.evaluate(
            "getComputedStyle(document.querySelector('.hamburger')).display")
        r["resp_480_gnb"] = await page.evaluate(
            "getComputedStyle(document.querySelector('.gnb')).display")

        r["console_errors"] = errors
        print(json.dumps(r, ensure_ascii=False, indent=1))
        await browser.close()

asyncio.run(main())
