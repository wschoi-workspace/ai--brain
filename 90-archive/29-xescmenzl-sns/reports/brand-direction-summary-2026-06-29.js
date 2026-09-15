const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Project Rent";
pres.title = "SESC MENSES Brand Direction Summary";

// Color palette - Warm Craft
const C = {
  dark: "2C2220",
  primary: "B85042",    // terracotta
  accent: "D4A574",     // warm gold
  cream: "F5F0EB",
  sand: "E7E0D5",
  text: "3C3330",
  textLight: "8A7E78",
  white: "FFFFFF",
  divider: "D1C7BE",
};

const FONT = { head: "Georgia", body: "Calibri" };

// Helper: fresh shadow
const cardShadow = () => ({ type: "outer", blur: 4, offset: 1, angle: 135, color: "000000", opacity: 0.08 });

// ── Slide 1: Cover ──
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  // Accent line
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 0.06, h: 2.2, fill: { color: C.primary } });
  s.addText("SESC MENSES", {
    x: 1.1, y: 1.2, w: 8, h: 0.7,
    fontFace: FONT.head, fontSize: 16, color: C.accent, charSpacing: 8, bold: true, margin: 0
  });
  s.addText("House of Charcuterie", {
    x: 1.1, y: 1.8, w: 8, h: 0.5,
    fontFace: FONT.head, fontSize: 14, color: C.textLight, italic: true, margin: 0
  });
  s.addText([
    { text: "Brand Direction\nSummary", options: { fontSize: 40, color: C.cream, fontFace: FONT.head, bold: true } },
  ], { x: 1.1, y: 2.5, w: 7, h: 1.5, margin: 0 });
  s.addText("2026.06.29  |  by Project Rent", {
    x: 1.1, y: 4.6, w: 5, h: 0.4,
    fontFace: FONT.body, fontSize: 11, color: C.textLight, margin: 0
  });
}

// ── Slide 2: Brand Core - Definition ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("BRAND CORE", {
    x: 0.7, y: 0.4, w: 4, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.85, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // Main definition
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.2, w: 8.6, h: 1.0, fill: { color: C.white }, shadow: cardShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.2, w: 0.06, h: 1.0, fill: { color: C.primary } });
  s.addText([
    { text: "One-line Definition", options: { fontSize: 10, color: C.textLight, breakLine: true } },
    { text: '"장인의 기술로 한국의 일상을 다시 존중하는 브랜드"', options: { fontSize: 20, color: C.text, fontFace: FONT.head, bold: true } },
  ], { x: 1.1, y: 1.3, w: 7.8, h: 0.8, margin: 0 });

  // Paradigm shift table
  s.addText("Paradigm Shift", {
    x: 0.7, y: 2.5, w: 4, h: 0.4,
    fontFace: FONT.head, fontSize: 14, color: C.text, bold: true, margin: 0
  });

  const rows = [
    ["Before", "After"],
    ["부대찌개를 고급화", "부대찌개를 장인의 언어로 번역"],
    ["비싼 재료를 넣는다", "재료의 존재 이유를 다시 정의"],
    ["샤퀴테리 브랜드", "Craft Reinterpretation Brand"],
    ["기술(Craft) 중심", "존중(Respect) 중심"],
  ];

  const headerOpts = { fill: { color: C.primary }, color: C.white, bold: true, fontSize: 11, fontFace: FONT.body, align: "center", valign: "middle" };
  const cellBeforeOpts = { fill: { color: C.sand }, color: C.textLight, fontSize: 11, fontFace: FONT.body, valign: "middle" };
  const cellAfterOpts = { fill: { color: C.white }, color: C.text, fontSize: 11, fontFace: FONT.body, bold: true, valign: "middle" };

  const tableData = [
    [{ text: rows[0][0], options: headerOpts }, { text: rows[0][1], options: headerOpts }],
    ...rows.slice(1).map(r => [
      { text: r[0], options: cellBeforeOpts },
      { text: r[1], options: cellAfterOpts },
    ])
  ];

  s.addTable(tableData, {
    x: 0.7, y: 3.0, w: 8.6, colW: [4.3, 4.3],
    border: { pt: 0.5, color: C.divider },
    rowH: [0.4, 0.4, 0.4, 0.4, 0.4],
  });
}

// ── Slide 3: Brand Architecture ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("BRAND ARCHITECTURE", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.85, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // Top brand box
  s.addShape(pres.shapes.RECTANGLE, { x: 2.5, y: 1.2, w: 5, h: 0.9, fill: { color: C.dark }, shadow: cardShadow() });
  s.addText([
    { text: "SESC MENSES", options: { fontSize: 16, color: C.accent, fontFace: FONT.head, bold: true, breakLine: true } },
    { text: "House of Charcuterie", options: { fontSize: 10, color: C.textLight, italic: true } },
  ], { x: 2.5, y: 1.25, w: 5, h: 0.8, align: "center", valign: "middle", margin: 0 });

  // Vertical line
  s.addShape(pres.shapes.LINE, { x: 5, y: 2.1, w: 0, h: 0.4, line: { color: C.divider, width: 1.5 } });

  // Tagline
  s.addShape(pres.shapes.RECTANGLE, { x: 2.5, y: 2.5, w: 5, h: 0.55, fill: { color: C.white }, shadow: cardShadow() });
  s.addText('"A House That Translates Craft into Culture"', {
    x: 2.5, y: 2.5, w: 5, h: 0.55,
    fontFace: FONT.head, fontSize: 11, color: C.primary, italic: true, align: "center", valign: "middle", margin: 0
  });

  // Arrow down
  s.addShape(pres.shapes.LINE, { x: 5, y: 3.05, w: 0, h: 0.35, line: { color: C.divider, width: 1.5 } });

  // 3 columns
  const colLabels = [
    { title: "Budae\nby SESC MENSES", sub: "첫 번째 프로젝트", color: C.primary },
    { title: "Future\nKorean Classics", sub: "김치찌개, 순대, 전골...", color: C.accent },
    { title: "Future\nProducts", sub: "리테일, 밀키트 확장", color: C.textLight },
  ];
  const colW = 2.6;
  const startX = (10 - colW * 3 - 0.4 * 2) / 2;
  colLabels.forEach((col, i) => {
    const cx = startX + i * (colW + 0.4);
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 3.5, w: colW, h: 1.2, fill: { color: C.white }, shadow: cardShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 3.5, w: colW, h: 0.06, fill: { color: col.color } });
    s.addText([
      { text: col.title, options: { fontSize: 13, color: C.text, fontFace: FONT.head, bold: true, breakLine: true } },
      { text: col.sub, options: { fontSize: 10, color: C.textLight } },
    ], { x: cx + 0.2, y: 3.65, w: colW - 0.4, h: 0.95, margin: 0 });
  });

  // Bottom note
  s.addText([
    { text: "샤퀴테리 = 존중을 표현하는 기술  |  ", options: { fontSize: 10, color: C.textLight } },
    { text: "부대찌개 = 존중을 한국적으로 번역한 첫 번째 작품", options: { fontSize: 10, color: C.primary, bold: true } },
  ], { x: 0.7, y: 5.0, w: 8.6, h: 0.35, align: "center", margin: 0 });
}

// ── Slide 4: Narrative Engine ──
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addText("NARRATIVE ENGINE", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.accent, charSpacing: 4, bold: true, margin: 0
  });
  s.addText('"생존에서 장인으로"', {
    x: 0.7, y: 0.75, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 14, color: C.cream, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.2, w: 8.6, h: 0.005, fill: { color: C.textLight } });

  // Two columns: Europe vs Korea
  const colW2 = 4.0;
  // Europe
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.5, w: colW2, h: 2.2, fill: { color: "3C3330" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.5, w: colW2, h: 0.06, fill: { color: C.accent } });
  s.addText([
    { text: "Europe", options: { fontSize: 14, color: C.accent, fontFace: FONT.head, bold: true, breakLine: true } },
    { text: "\n", options: { fontSize: 6, breakLine: true } },
    { text: "생존의 기술 (육가공 보존법)", options: { fontSize: 11, color: C.cream, breakLine: true } },
    { text: "       |  시간의 흐름", options: { fontSize: 10, color: C.textLight, breakLine: true } },
    { text: "장인의 미식으로 진화", options: { fontSize: 12, color: C.accent, bold: true } },
  ], { x: 1.0, y: 1.7, w: colW2 - 0.6, h: 1.8, margin: 0 });

  // Korea
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.5, w: colW2, h: 2.2, fill: { color: "3C3330" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.5, w: colW2, h: 0.06, fill: { color: C.primary } });
  s.addText([
    { text: "Korea", options: { fontSize: 14, color: C.primary, fontFace: FONT.head, bold: true, breakLine: true } },
    { text: "\n", options: { fontSize: 6, breakLine: true } },
    { text: "생존의 기술 (부대찌개)", options: { fontSize: 11, color: C.cream, breakLine: true } },
    { text: "       |  시간의 흐름", options: { fontSize: 10, color: C.textLight, breakLine: true } },
    { text: "대중음식으로 고착 (푸짐함, 가성비)", options: { fontSize: 12, color: C.primary, bold: true } },
  ], { x: 5.6, y: 1.7, w: colW2 - 0.6, h: 1.8, margin: 0 });

  // Question
  s.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 4.1, w: 7, h: 1.0, fill: { color: C.primary } });
  s.addText([
    { text: "SESC MENSES의 질문", options: { fontSize: 10, color: C.cream, breakLine: true } },
    { text: '"부대찌개도 샤퀴테리처럼\n장인의 기술로 다시 해석될 수 있지 않은가?"', options: { fontSize: 16, color: C.white, fontFace: FONT.head, italic: true } },
  ], { x: 1.8, y: 4.15, w: 6.4, h: 0.9, align: "center", valign: "middle", margin: 0 });
}

// ── Slide 5: Meal Design Overview ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("MEAL DESIGN", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addText("메뉴가 아니라 하루의 시나리오", {
    x: 0.7, y: 0.75, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 14, color: C.text, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.15, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // Core principle
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.4, w: 8.6, h: 0.6, fill: { color: C.white }, shadow: cardShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.4, w: 0.06, h: 0.6, fill: { color: C.primary } });
  s.addText('핵심 원칙:  점심과 저녁은 완전히 다른 비즈니스다.', {
    x: 1.1, y: 1.4, w: 7.8, h: 0.6,
    fontFace: FONT.head, fontSize: 14, color: C.text, bold: true, valign: "middle", margin: 0
  });

  // Comparison table
  const headerRow = ["", "Lunch: The First Meal", "Dinner: The Last Table"];
  const dataRows = [
    ["시간 전략", '시간을 절약해주는 브랜드', '시간을 보내게 만드는 브랜드'],
    ["고객이 주문", '부대찌개', '세스크멘슬의 세계관'],
    ["브랜드 역할", '브랜드를 만나는 시간', '브랜드를 이해하는 시간'],
    ["설계 원리", '한 가지를 가장 완벽하게', '메뉴판이 아니라 코스의 흐름'],
    ["KPI", '다시 생각나는 점심', '세계관 경험 완성'],
  ];

  const hOpts = { fill: { color: C.dark }, color: C.cream, bold: true, fontSize: 10, fontFace: FONT.body, align: "center", valign: "middle" };
  const labelOpts = { fill: { color: C.sand }, color: C.text, bold: true, fontSize: 10, fontFace: FONT.body, valign: "middle" };
  const lunchOpts = { fill: { color: C.white }, color: C.text, fontSize: 10, fontFace: FONT.body, valign: "middle" };
  const dinnerOpts = { fill: { color: C.white }, color: C.primary, fontSize: 10, fontFace: FONT.body, bold: true, valign: "middle" };

  const tData = [
    [{ text: headerRow[0], options: hOpts }, { text: headerRow[1], options: hOpts }, { text: headerRow[2], options: hOpts }],
    ...dataRows.map(r => [
      { text: r[0], options: labelOpts },
      { text: r[1], options: lunchOpts },
      { text: r[2], options: dinnerOpts },
    ])
  ];

  s.addTable(tData, {
    x: 0.7, y: 2.3, w: 8.6, colW: [1.6, 3.5, 3.5],
    border: { pt: 0.5, color: C.divider },
    rowH: [0.4, 0.45, 0.45, 0.45, 0.45, 0.45],
  });
}

// ── Slide 6: Lunch Detail ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("LUNCH: THE FIRST MEAL", {
    x: 0.7, y: 0.4, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addText('"좋은 하루는 좋은 첫 끼에서 시작됩니다."', {
    x: 0.7, y: 0.75, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 13, color: C.text, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.15, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // 4 menu cards
  const menus = [
    { name: "Signature Korean\nCharcuterie Stew", desc: "모든 햄/소시지가 이 찌개를\n위해 설계된 샤퀴테리" },
    { name: "Pot Rice\n(솥밥)", desc: '"탄수화물이 아니라\n첫 끼에 대한 존중"' },
    { name: "Seasonal Side", desc: "계절 피클/절임/장아찌\n국물 밸런스" },
    { name: "Today's\nCharcuterie", desc: "한 점. 점심에도\n샤퀴테리 브랜드 각인" },
  ];
  const cardW = 1.9;
  const gap = 0.2;
  const totalW = cardW * 4 + gap * 3;
  const sx = (10 - totalW) / 2;
  menus.forEach((m, i) => {
    const cx = sx + i * (cardW + gap);
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.4, w: cardW, h: 2.0, fill: { color: C.white }, shadow: cardShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.4, w: cardW, h: 0.05, fill: { color: C.primary } });
    s.addText([
      { text: m.name, options: { fontSize: 12, color: C.text, fontFace: FONT.head, bold: true, breakLine: true } },
      { text: "\n", options: { fontSize: 6, breakLine: true } },
      { text: m.desc, options: { fontSize: 10, color: C.textLight } },
    ], { x: cx + 0.15, y: 1.55, w: cardW - 0.3, h: 1.7, margin: 0 });
  });

  // Experience flow
  s.addText("Experience Flow", {
    x: 0.7, y: 3.7, w: 4, h: 0.35,
    fontFace: FONT.head, fontSize: 12, color: C.text, bold: true, margin: 0
  });

  const steps = ["도착", "5분 이내 제공", "15~20분 식사", "따뜻한 점심", "오후 시작"];
  const stepW = 1.5;
  const stepGap = 0.15;
  const stepsStartX = (10 - stepW * 5 - stepGap * 4) / 2;
  steps.forEach((st, i) => {
    const stx = stepsStartX + i * (stepW + stepGap);
    s.addShape(pres.shapes.RECTANGLE, { x: stx, y: 4.2, w: stepW, h: 0.55, fill: { color: i === 0 || i === 4 ? C.primary : C.dark } });
    s.addText(st, { x: stx, y: 4.2, w: stepW, h: 0.55, fontSize: 10, color: C.cream, fontFace: FONT.body, align: "center", valign: "middle", margin: 0 });
  });

  s.addText('KPI: "다시 생각나는 점심"  |  시간을 절약해주는 브랜드', {
    x: 0.7, y: 5.0, w: 8.6, h: 0.35,
    fontFace: FONT.body, fontSize: 10, color: C.textLight, align: "center", margin: 0
  });
}

// ── Slide 7: Dinner Detail ──
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addText("DINNER: THE LAST TABLE", {
    x: 0.7, y: 0.4, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.accent, charSpacing: 4, bold: true, margin: 0
  });
  s.addText('"좋은 하루는 좋은 식탁에서 완성됩니다."', {
    x: 0.7, y: 0.75, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 13, color: C.cream, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.15, w: 8.6, h: 0.005, fill: { color: C.textLight } });

  // Course flow
  const courses = [
    { name: "Begin", menu: "Charcuterie Board", desc: "숙성 햄/테린/파테\n+ 와인" },
    { name: "Fire", menu: "Grilled Sausage", desc: "부위별/숙성별/훈연별\n테이스팅" },
    { name: "Stew", menu: "Korean Charcuterie\nStew", desc: "테이블의 중심\n함께 나누는 음식" },
    { name: "Finish", menu: "Pot Rice +\nFinish Course", desc: "리조토/치즈/계란/볶음밥\n택1" },
    { name: "Pairing", menu: "Wine/Beer/\nHighball", desc: "샤퀴테리 기준\n큐레이션" },
  ];
  const cW = 1.6;
  const cGap = 0.1;
  const cTotal = cW * 5 + cGap * 4;
  const cStartX = (10 - cTotal) / 2;
  courses.forEach((c, i) => {
    const cx = cStartX + i * (cW + cGap);
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.4, w: cW, h: 2.3, fill: { color: "3C3330" } });
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.4, w: cW, h: 0.05, fill: { color: i === 2 ? C.primary : C.accent } });
    s.addText([
      { text: c.name, options: { fontSize: 10, color: C.accent, fontFace: FONT.body, charSpacing: 3, bold: true, breakLine: true } },
      { text: c.menu, options: { fontSize: 12, color: C.cream, fontFace: FONT.head, bold: true, breakLine: true } },
      { text: "\n", options: { fontSize: 4, breakLine: true } },
      { text: c.desc, options: { fontSize: 9, color: C.textLight } },
    ], { x: cx + 0.12, y: 1.55, w: cW - 0.24, h: 2.0, margin: 0 });
  });

  // Signature menus
  s.addText("Signature Menus", {
    x: 0.7, y: 4.0, w: 4, h: 0.35,
    fontFace: FONT.head, fontSize: 12, color: C.accent, bold: true, margin: 0
  });
  // Two cards
  const sigMenus = [
    { name: "Chef's Sausage", desc: "매주/매달/계절 변경\n\"이 메뉴 하나 때문에 다시 오는 이유\"" },
    { name: "Charcuterie Flight", desc: "Classic > Smoked > Aged > Chef's Special\n4종 소량 테이스팅" },
  ];
  sigMenus.forEach((sm, i) => {
    const smx = 0.7 + i * 4.5;
    s.addShape(pres.shapes.RECTANGLE, { x: smx, y: 4.4, w: 4.1, h: 0.9, fill: { color: "3C3330" } });
    s.addShape(pres.shapes.RECTANGLE, { x: smx, y: 4.4, w: 0.06, h: 0.9, fill: { color: C.primary } });
    s.addText([
      { text: sm.name, options: { fontSize: 12, color: C.cream, fontFace: FONT.head, bold: true, breakLine: true } },
      { text: sm.desc, options: { fontSize: 9, color: C.textLight } },
    ], { x: smx + 0.2, y: 4.5, w: 3.7, h: 0.7, margin: 0 });
  });
}

// ── Slide 8: Pricing Strategy ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("PRICING STRATEGY", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.85, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // Big quote
  s.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 1.3, w: 7, h: 1.0, fill: { color: C.white }, shadow: cardShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 1.3, w: 0.06, h: 1.0, fill: { color: C.primary } });
  s.addText('"가격이 아니라 경험의 깊이를 달리한다."', {
    x: 1.8, y: 1.3, w: 6.4, h: 1.0,
    fontFace: FONT.head, fontSize: 22, color: C.text, italic: true, valign: "middle", margin: 0
  });

  // Two columns
  // Lunch
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.7, w: 4.1, h: 2.2, fill: { color: C.white }, shadow: cardShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.7, w: 4.1, h: 0.05, fill: { color: C.accent } });
  s.addText([
    { text: "Lunch", options: { fontSize: 16, color: C.text, fontFace: FONT.head, bold: true, breakLine: true } },
    { text: "\n", options: { fontSize: 6, breakLine: true } },
    { text: "단일 세트 구성", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "합리적 가격대에서", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: "완성도로 차별화", options: { fontSize: 14, color: C.primary, bold: true } },
  ], { x: 1.0, y: 2.85, w: 3.5, h: 1.9, margin: 0 });

  // Dinner
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.7, w: 4.1, h: 2.2, fill: { color: C.white }, shadow: cardShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.7, w: 4.1, h: 0.05, fill: { color: C.primary } });
  s.addText([
    { text: "Dinner", options: { fontSize: 16, color: C.text, fontFace: FONT.head, bold: true, breakLine: true } },
    { text: "\n", options: { fontSize: 6, breakLine: true } },
    { text: "코스 흐름 중심", options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: '"비싼 저녁"이 아니라', options: { fontSize: 12, color: C.text, breakLine: true } },
    { text: '"경험하는 저녁"으로 가격 정당성', options: { fontSize: 14, color: C.primary, bold: true } },
  ], { x: 5.5, y: 2.85, w: 3.5, h: 1.9, margin: 0 });

  s.addText("같은 공간, 같은 대표 메뉴 = 전혀 다른 두 개의 비즈니스 모델", {
    x: 0.7, y: 5.1, w: 8.6, h: 0.35,
    fontFace: FONT.body, fontSize: 11, color: C.textLight, align: "center", margin: 0
  });
}

// ── Slide 9: Craft Philosophy ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("CRAFT PHILOSOPHY", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addText('"장인은 비싼 재료를 쓰는 사람이 아니라, 재료의 존재 이유를 다시 정의하는 사람이다."', {
    x: 0.7, y: 0.75, w: 8.6, h: 0.5,
    fontFace: FONT.head, fontSize: 12, color: C.text, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.25, w: 8.6, h: 0.005, fill: { color: C.divider } });

  // 7 items grid: 4 + 3
  const items = [
    { element: "햄", action: "부대찌개를 위해 새로 만든다" },
    { element: "소시지", action: "부대찌개를 위해 새로 설계한다" },
    { element: "지방 비율", action: "국물과의 밸런스를 위해 조정한다" },
    { element: "훈연", action: "찌개 안에서의 향 변화를 고려해 바꾼다" },
    { element: "염도", action: "국물 전체의 균형을 위해 다시 맞춘다" },
    { element: "육수", action: "부용 기반으로 다시 설계한다" },
    { element: "밥", action: "국물과의 페어링으로 다시 설계한다" },
  ];

  // Two rows
  const cw = 2.0;
  const ch = 1.2;
  const gapH = 0.15;
  const gapV = 0.15;
  items.forEach((item, i) => {
    const row = i < 4 ? 0 : 1;
    const col = i < 4 ? i : i - 4;
    const colCount = row === 0 ? 4 : 3;
    const totalRowW = cw * colCount + gapH * (colCount - 1);
    const rowStartX = (10 - totalRowW) / 2;
    const ix = rowStartX + col * (cw + gapH);
    const iy = 1.6 + row * (ch + gapV);

    s.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: cw, h: ch, fill: { color: C.white }, shadow: cardShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: 0.06, h: ch, fill: { color: C.primary } });
    s.addText([
      { text: item.element, options: { fontSize: 16, color: C.primary, fontFace: FONT.head, bold: true, breakLine: true } },
      { text: "\n", options: { fontSize: 4, breakLine: true } },
      { text: item.action, options: { fontSize: 10, color: C.text } },
    ], { x: ix + 0.2, y: iy + 0.1, w: cw - 0.35, h: ch - 0.2, margin: 0 });
  });

  // Bottom statement
  s.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 4.3, w: 7, h: 0.7, fill: { color: C.dark } });
  s.addText('"더 비싸게 만들기 위해서"가 아니라\n"부대찌개라는 한 그릇을 완성하기 위해서"', {
    x: 1.5, y: 4.3, w: 7, h: 0.7,
    fontFace: FONT.head, fontSize: 13, color: C.cream, align: "center", valign: "middle", italic: true, margin: 0
  });
}

// ── Slide 10: Manifesto ──
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addText("MANIFESTO", {
    x: 0.7, y: 0.5, w: 4, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.accent, charSpacing: 6, bold: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.95, w: 8.6, h: 0.005, fill: { color: C.textLight } });

  const manifesto = [
    "우리는 부대찌개를 고급화하지 않습니다.",
    "우리는 부대찌개를 존중합니다.",
    "",
    "생존을 위해 태어난 음식에도,",
    "장인의 기술은 스며들 수 있다고 믿습니다.",
    "",
    "좋은 샤퀴테리가 시간을 존중하듯,",
    "좋은 부대찌개도 재료와 시간을 존중해야 합니다.",
    "",
    "그래서 우리는 햄을 다시 만들고,",
    "소시지를 다시 설계하고,",
    "국물을 다시 끓이고,",
    "밥을 다시 짓습니다.",
    "",
    "우리가 만드는 것은 새로운 음식이 아닙니다.",
    "한국의 스튜를 장인의 언어로 다시 번역하는 일입니다.",
  ];

  const textRuns = manifesto.map((line, i) => {
    if (line === "") return { text: "\n", options: { fontSize: 8, breakLine: true } };
    const isHighlight = i === 1 || i === 15;
    return {
      text: line,
      options: {
        fontSize: isHighlight ? 16 : 14,
        color: isHighlight ? C.accent : C.cream,
        fontFace: FONT.head,
        bold: isHighlight,
        italic: true,
        breakLine: true,
      }
    };
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 1.2, y: 1.2, w: 0.04, h: 3.8, fill: { color: C.primary } });
  s.addText(textRuns, { x: 1.5, y: 1.2, w: 7.5, h: 3.8, margin: 0, valign: "middle" });

  s.addText("SESC MENSES  |  House of Charcuterie", {
    x: 0.7, y: 5.1, w: 8.6, h: 0.3,
    fontFace: FONT.body, fontSize: 9, color: C.textLight, align: "center", margin: 0
  });
}

// ── Slide 11: Evolution from 06-08 ──
{
  const s = pres.addSlide();
  s.background = { color: C.cream };
  s.addText("EVOLUTION", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.primary, charSpacing: 4, bold: true, margin: 0
  });
  s.addText("06-08 > 06-29 논의 진화", {
    x: 0.7, y: 0.75, w: 8, h: 0.4,
    fontFace: FONT.head, fontSize: 14, color: C.text, italic: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.15, w: 8.6, h: 0.005, fill: { color: C.divider } });

  const evoRows = [
    ["06-08", "06-29", "진화"],
    ['"제조 기술 세계관"', '"장인의 번역" + "존중"', "기술 > 태도"],
    ['"밀도 높은 컴포트 미식"', '"Korean Charcuterie Stew"', "내부언어 > 외부 커뮤니케이션"],
    ["4평 쇼룸 vs 리뉴얼", "Lunch/Dinner 이중 모델", "공간논의 > 경험 시나리오"],
    ["서브브랜드 = 부대찌개", '부대찌개 = "첫 번째 프로젝트"', "단일사업 > 확장 플랫폼"],
    ["House of Charcuterie", "Translates Craft into Culture", "카테고리 > 행위 정의"],
  ];

  const eHeaderOpts = { fill: { color: C.dark }, color: C.cream, bold: true, fontSize: 10, fontFace: FONT.body, align: "center", valign: "middle" };
  const eBeforeOpts = { fill: { color: C.sand }, color: C.textLight, fontSize: 10, fontFace: FONT.body, valign: "middle" };
  const eAfterOpts = { fill: { color: C.white }, color: C.text, fontSize: 10, fontFace: FONT.body, bold: true, valign: "middle" };
  const eEvoOpts = { fill: { color: C.white }, color: C.primary, fontSize: 10, fontFace: FONT.body, bold: true, valign: "middle", align: "center" };

  const eData = [
    evoRows[0].map(h => ({ text: h, options: eHeaderOpts })),
    ...evoRows.slice(1).map(r => [
      { text: r[0], options: eBeforeOpts },
      { text: r[1], options: eAfterOpts },
      { text: r[2], options: eEvoOpts },
    ])
  ];

  s.addTable(eData, {
    x: 0.7, y: 1.5, w: 8.6, colW: [3.0, 3.3, 2.3],
    border: { pt: 0.5, color: C.divider },
    rowH: [0.4, 0.5, 0.5, 0.5, 0.5, 0.5],
  });
}

// ── Slide 12: Next Steps ──
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addText("NEXT STEPS", {
    x: 0.7, y: 0.4, w: 6, h: 0.4,
    fontFace: FONT.head, fontSize: 11, color: C.accent, charSpacing: 4, bold: true, margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.85, w: 8.6, h: 0.005, fill: { color: C.textLight } });

  const tasks = [
    "Manifesto 최종 검수 및 클라이언트 공유",
    "브랜드 아키텍처 비주얼 정리 (제안서 v3 반영)",
    "Lunch/Dinner 가격 시뮬레이션 (객단가/원가/회전율)",
    '"Korean Charcuterie Stew" 네이밍 클라이언트 논의',
    "Chef's Sausage / Charcuterie Flight 운영 가능성 셰프 확인",
    "제안서 v2 > v3 업데이트",
    "Finish Course 구체 레시피 방향 셰프 협의",
    "Today's Charcuterie 원가/오퍼레이션 설계",
  ];

  tasks.forEach((task, i) => {
    const ty = 1.15 + i * 0.52;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: ty, w: 8.6, h: 0.44, fill: { color: "3C3330" } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: ty, w: 0.06, h: 0.44, fill: { color: i < 3 ? C.primary : C.accent } });
    s.addText([
      { text: `${String(i + 1).padStart(2, "0")}  `, options: { fontSize: 12, color: C.accent, fontFace: FONT.body, bold: true } },
      { text: task, options: { fontSize: 12, color: C.cream, fontFace: FONT.body } },
    ], { x: 1.0, y: ty, w: 8.0, h: 0.44, valign: "middle", margin: 0 });
  });

  s.addText("by Project Rent  |  2026.06.29", {
    x: 0.7, y: 5.2, w: 8.6, h: 0.3,
    fontFace: FONT.body, fontSize: 9, color: C.textLight, align: "center", margin: 0
  });
}

// Write file
const outPath = "/Users/choi_ai/do-better-workspace/10-projects/29-xescmenzl-sns/reports/brand-direction-summary-2026-06-29.pptx";
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("PPTX saved:", outPath);
}).catch(err => {
  console.error("Error:", err);
});
