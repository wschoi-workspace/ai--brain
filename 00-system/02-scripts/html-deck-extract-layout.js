#!/usr/bin/env node
/**
 * HTML 덱 → 레이아웃 JSON (html-deck-to-pptx.py 입력)
 *
 * 브라우저에서 실제 렌더된 좌표를 뽑는다. flexbox/grid를 다시 구현하지 않기 위함.
 * 출력 좌표계는 1920×1080 기준 — 변환 스크립트가 1px=6350EMU, 1px=0.5pt를 가정한다.
 *
 * 사용: node html-deck-extract-layout.js <input.html> <out.json> [슬라이드폭px]
 *   슬라이드폭 기본 1280 (→ 1.5배 스케일). 1920 덱이면 1920을 넘긴다.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const src = path.resolve(process.argv[2]);
  const out = path.resolve(process.argv[3]);
  const baseW = parseFloat(process.argv[4] || '1280');

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Math.ceil(baseW) + 200, height: 1000 } });
  await page.goto('file://' + src, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);

  const data = await page.evaluate((baseW) => {
    const S = 1920 / baseW;

    const parseColor = (str) => {
      if (!str) return null;
      const m = String(str).match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(',').map((s) => parseFloat(s));
      return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
    };
    const toHex = (c) =>
      [c.r, c.g, c.b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('').toUpperCase();

    // 부모 체인까지 훑어 불투명 배경으로 합성 (반투명 틴트가 원색이 되는 것 방지)
    const solidBg = (el) => {
      if (!el || el === document.documentElement) return { r: 255, g: 255, b: 255 };
      const c = parseColor(getComputedStyle(el).backgroundColor);
      if (c && c.a >= 0.999) return c;
      const base = solidBg(el.parentElement);
      if (!c || !c.a) return base;
      return { r: c.r * c.a + base.r * (1 - c.a), g: c.g * c.a + base.g * (1 - c.a), b: c.b * c.a + base.b * (1 - c.a) };
    };
    const overParent = (el, c) => {
      if (!c || !c.a) return null;
      if (c.a >= 0.999) return toHex(c);
      const base = solidBg(el.parentElement);
      return toHex({ r: c.r * c.a + base.r * (1 - c.a), g: c.g * c.a + base.g * (1 - c.a), b: c.b * c.a + base.b * (1 - c.a) });
    };

    const num = (v) => { const n = parseFloat(v); return isNaN(n) ? 0 : n; };
    const px = (v) => num(v) * S;

    const slides = [...document.querySelectorAll('.slide')];

    const sideOf = (el, cs, w, colorKey) => {
      const bw = num(w);
      if (bw <= 0) return null;
      const hex = overParent(el, parseColor(cs[colorKey]));
      return hex ? [Math.max(bw * S, 1), hex] : null;
    };

    return slides.map((slide) => {
      // 비활성 슬라이드는 display:none이라 좌표가 전부 0으로 나온다.
      // 측정하는 동안만 active로 바꾸고 원상복구한다 (한 장짜리 덱은 그대로 통과).
      const wasActive = slide.classList.contains('active');
      const prevActive = document.querySelector('.slide.active');
      let toggled = false;
      if (slide.getBoundingClientRect().height < 1) {
        if (prevActive && prevActive !== slide) prevActive.classList.remove('active');
        slide.classList.add('active');
        toggled = true;
      }
      const restore = () => {
        if (!toggled) return;
        if (!wasActive) slide.classList.remove('active');
        if (prevActive && prevActive !== slide) prevActive.classList.add('active');
      };

      const sr = slide.getBoundingClientRect();
      const R = (el) => {
        const r = el.getBoundingClientRect();
        return [(r.left - sr.left) * S, (r.top - sr.top) * S, r.width * S, r.height * S];
      };

      const boxes = [], texts = [], tables = [];
      const slideBg = toHex(solidBg(slide));

      // ── boxes: 배경 또는 테두리가 있는 요소
      for (const el of slide.querySelectorAll('*')) {
        const tag = el.tagName.toLowerCase();
        if (['table', 'thead', 'tbody', 'tr', 'td', 'th', 'br'].includes(tag)) continue;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = R(el);
        if (r[2] < 1 || r[3] < 1) continue;

        const bg = overParent(el, parseColor(cs.backgroundColor));
        const sd = [
          sideOf(el, cs, cs.borderTopWidth, 'borderTopColor'),
          sideOf(el, cs, cs.borderRightWidth, 'borderRightColor'),
          sideOf(el, cs, cs.borderBottomWidth, 'borderBottomColor'),
          sideOf(el, cs, cs.borderLeftWidth, 'borderLeftColor'),
        ];
        if (bg || sd.some(Boolean)) boxes.push({ r, bg, sd });

        // ::before 마커(불릿 등) — pseudo는 rect를 못 잡으므로 수동 재현
        const pb = getComputedStyle(el, '::before');
        if (pb && pb.content && pb.content !== 'none') {
          const pw = num(pb.width), ph = num(pb.height);
          const pbg = overParent(el, parseColor(pb.backgroundColor));
          if (pw > 0 && ph > 0 && pbg) {
            boxes.push({
              r: [r[0] + num(pb.left) * S, r[1] + num(pb.top) * S, pw * S, ph * S],
              bg: pbg, sd: [null, null, null, null],
            });
          }
        }
      }

      // ── runs: 인라인 자식까지 흡수 (br은 문단 분리 신호)
      const runsOf = (host) => {
        const acc = [];
        const walk = (node, cs) => {
          for (const n of node.childNodes) {
            if (n.nodeType === 3) {
              const t = n.textContent.replace(/\s+/g, ' ');
              if (t.trim()) acc.push({ t, c: overParent(node, parseColor(cs.color)), w: parseInt(cs.fontWeight) || 400, fs: num(cs.fontSize) * S });
              continue;
            }
            if (n.nodeType !== 1) continue;
            if (n.tagName === 'BR') { acc.push({ br: true }); continue; }
            const ncs = getComputedStyle(n);
            if (!ncs.display.startsWith('inline')) continue; // 블록 자식은 별도 텍스트 호스트로 잡힌다
            walk(n, ncs);
          }
        };
        walk(host, getComputedStyle(host));
        return acc;
      };

      // ── texts: 직계 텍스트 노드를 가진 요소 (표 내부 제외)
      // 인라인 자식은 부모 runs가 이미 흡수했으므로 다시 등록하지 않는다(텍스트 중복 방지).
      const hosts = new Set();
      for (const el of slide.querySelectorAll('*')) {
        if (el.closest('table')) continue;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!hasText) continue;
        if (cs.display.startsWith('inline')) {
          let p = el.parentElement, absorbed = false;
          while (p && p !== slide) { if (hosts.has(p)) { absorbed = true; break; } p = p.parentElement; }
          if (absorbed) continue;
        }
        const runs = runsOf(el);
        if (!runs.length) continue;
        hosts.add(el);
        const fs = num(cs.fontSize) * S;
        const lh = cs.lineHeight === 'normal' ? fs * 1.4 : num(cs.lineHeight) * S;
        texts.push({
          r: R(el), fs, lh,
          ls: cs.letterSpacing === 'normal' ? 0 : num(cs.letterSpacing) * S,
          al: cs.textAlign, tt: cs.textTransform,
          pl: px(cs.paddingLeft), pr: px(cs.paddingRight), pt: px(cs.paddingTop), pb: px(cs.paddingBottom),
          runs,
        });
      }

      // ── tables: 네이티브 표로
      for (const tb of slide.querySelectorAll('table')) {
        const rows = [...tb.rows].map((tr) => ({
          h: tr.getBoundingClientRect().height * S,
          cells: [...tr.cells].map((td) => {
            const cs = getComputedStyle(td);
            return {
              cw: td.getBoundingClientRect().width * S,
              pl: px(cs.paddingLeft), pr: px(cs.paddingRight),
              fs: num(cs.fontSize) * S,
              c: overParent(td, parseColor(cs.color)),
              w: parseInt(cs.fontWeight) || 400,
              ls: cs.letterSpacing === 'normal' ? 0 : num(cs.letterSpacing) * S,
              al: cs.textAlign, tt: cs.textTransform,
              bt: num(cs.borderTopWidth) > 0 ? overParent(td, parseColor(cs.borderTopColor)) : null,
              bb: num(cs.borderBottomWidth) > 0 ? overParent(td, parseColor(cs.borderBottomColor)) : null,
              runs: runsOf(td),
            };
          }),
        }));
        tables.push({ r: R(tb), rows });
      }

      restore();
      return { bg: slideBg, boxes, tables, texts };
    });
  }, baseW);

  fs.writeFileSync(out, JSON.stringify(data));
  const n = data.length;
  const sum = (k) => data.reduce((a, s) => a + s[k].length, 0);
  console.log(`slides ${n} · boxes ${sum('boxes')} · texts ${sum('texts')} · tables ${sum('tables')}`);
  await browser.close();
})();
