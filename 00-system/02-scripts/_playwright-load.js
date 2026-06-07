async (page) => {
  const { createReadStream } = await import('node:fs');
  const { readFile } = await import('node:fs/promises');
  const html = await readFile(
    '/Users/choi_ai/Library/CloudStorage/Dropbox/02-프로젝트렌트RENT/02_Project-ING/2026/글로벌K존_유니원/rfp-ideation-compare-K존.html',
    'utf-8'
  );
  await page.setContent(html, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 2500));
  return 'loaded';
}
