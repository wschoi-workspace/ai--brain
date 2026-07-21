// PROJECT RENT 홈페이지 문의 접수 → 아리사 텔레그램 알림 + 구글시트 취합 (Cloudflare Pages Function)
// Secrets: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SHEET_WEBHOOK_URL, SHEET_SECRET

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const clip = (v, max) => String(v ?? '').trim().slice(0, max);

export async function onRequestPost({ request, env }) {
  let data;
  try {
    data = await request.json();
  } catch {
    return json({ ok: false, error: 'invalid body' }, 400);
  }

  const type = clip(data.type, 50);
  const name = clip(data.name, 100);
  const company = clip(data.company, 100) || '-';
  const email = clip(data.email, 200);
  const phone = clip(data.phone, 50);
  const message = clip(data.message, 3000);

  if (!name || !email || !phone || !message) {
    return json({ ok: false, error: 'missing fields' }, 400);
  }

  const ts = new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' });

  // 구글시트 취합 (Apps Script 웹훅) — 실패해도 접수 자체는 유지
  let sheetOk = false;
  if (env.SHEET_WEBHOOK_URL && env.SHEET_SECRET) {
    try {
      const sr = await fetch(env.SHEET_WEBHOOK_URL, {
        method: 'POST',
        redirect: 'follow',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret: env.SHEET_SECRET, ts, type, name, company, email, phone, message }),
      });
      sheetOk = sr.ok;
    } catch {
      /* 시트 실패는 접수를 막지 않음 — 텔레그램 알림이 1차 채널 */
    }
  }

  const text =
    `📩 [홈페이지] ${type} 문의 접수\n\n` +
    `이름: ${name}\n회사: ${company}\n이메일: ${email}\n전화: ${phone}\n\n` +
    `내용:\n${message}\n\n접수: ${ts}`;

  try {
    const res = await fetch(
      `https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
      }
    );
    const result = await res.json();
    return json({ ok: !!result.ok, sheet: sheetOk }, result.ok ? 200 : 502);
  } catch {
    return json({ ok: sheetOk, sheet: sheetOk, error: 'notify failed' }, sheetOk ? 200 : 502);
  }
}
