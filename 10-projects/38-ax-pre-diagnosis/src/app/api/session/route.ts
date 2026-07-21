import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// GET: 토큰으로 세션 조회
export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get('token');
  if (!token) return NextResponse.json({ error: 'token required' }, { status: 400 });

  const { data, error } = await supabase
    .from('interview_sessions')
    .select('*, interview_answers(*)')
    .eq('token', token)
    .single();

  if (error) return NextResponse.json({ error: 'session not found' }, { status: 404 });
  return NextResponse.json(data);
}

// POST: 새 세션 생성 (관리자용)
export async function POST(req: NextRequest) {
  const { educationCode, count } = await req.json();

  // 교육 세션 조회
  const { data: edu } = await supabase
    .from('education_sessions')
    .select('id')
    .eq('code', educationCode)
    .single();

  if (!edu) return NextResponse.json({ error: 'education not found' }, { status: 404 });

  const tokens: string[] = [];
  for (let i = 0; i < (count || 1); i++) {
    const token = generateToken();
    const { error } = await supabase.from('interview_sessions').insert({
      education_id: edu.id,
      token,
    });
    if (!error) tokens.push(token);
  }

  return NextResponse.json({ tokens, count: tokens.length });
}

// PATCH: 세션 상태 업데이트
export async function PATCH(req: NextRequest) {
  const { token, ...updates } = await req.json();
  if (!token) return NextResponse.json({ error: 'token required' }, { status: 400 });

  const { error } = await supabase
    .from('interview_sessions')
    .update(updates)
    .eq('token', token);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

function generateToken(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
