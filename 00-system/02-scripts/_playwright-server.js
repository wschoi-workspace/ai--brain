async (page) => {
  // Node.js http 모듈로 인라인 서버 띄우기
  const http = process.mainModule
    ? process.mainModule.require('http')
    : global.__http;

  // page.evaluate로 fetch 우회 불가, 대신 CDN 의존 없이 setContent 사용
  // HTML 전체를 page context에서 읽는 방법: page._client로 접근
  const cdpSession = await page.context().newCDPSession(page);
  await cdpSession.send('Page.enable');

  // Blob URL 방식으로 로드 시도
  await page.goto('about:blank');

  const result = await page.evaluate(async () => {
    try {
      const resp = await fetch('http://localhost:7892/rfp-ideation-compare-K존.html');
      return resp.ok ? 'server ok' : 'server error ' + resp.status;
    } catch(e) {
      return 'no server: ' + e.message;
    }
  });

  return result;
}
